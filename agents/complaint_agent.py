"""
Complaint Resolution Agent.

Handles a complaint from initial analysis until a resolution is
recommended:
  A. Analysis (collect order id / issue type / description, detect
     missing info)
  B. Evidence handling (text/PDF via tools.document_processor; images/
     videos routed to a human Evidence Reviewer)
  C. Previous-case checking (tools.duplicate_checker)
  D. Policy validation / eligibility (tools.eligibility, backed by
     Policy RAG + deterministic rules)
  E. Resolution recommendation, handed to the Case Manager for approval

Important checks (duplicate detection, eligibility, state revalidation)
are deterministic tools, not LLM judgment.
"""

from database.repositories import (
    CaseRepository,
    ComplaintRepository,
    OrderRepository,
    ProductRepository,
    EvidenceRepository,
)
from models.resolution import RESOLUTION_TO_WORKFLOW_LABEL

from tools.complaint_validator import validate_complaint
from tools.duplicate_checker import check_duplicate_complaint
from tools.complaint_creator import create_complaint
from tools.eligibility import evaluate_eligibility

from services import case_service, department_service, notification_service, audit_service
from hitl import evidence_review, customer_care

from utils.logger import logger

EVIDENCE_REQUIRED_TYPES = {"DAMAGED_PRODUCT", "DEFECTIVE_PRODUCT", "WRONG_ITEM"}

MIN_DESCRIPTION_LENGTH = 10


def _infer_requested_resolution(issue_type, description):

    text = f"{issue_type} {description}".lower()

    if "replace" in text:
        return "Replacement"

    if "voucher" in text or "compensat" in text:
        return "Voucher"

    if "refund" in text or issue_type == "REFUND_ISSUE":
        return "Refund"

    if issue_type in EVIDENCE_REQUIRED_TYPES or issue_type == "MISSING_ITEM":
        return "Replacement"

    return "Refund"


def evaluate_and_recommend(case_id):
    """
    Runs duplicate checking + policy/eligibility evaluation for a
    complaint and either recommends a resolution (handing off to the
    Case Manager), rejects, escalates, or requests better evidence.
    Called once evidence review is unnecessary or has completed.
    """

    case = CaseRepository.get_by_id(case_id)
    complaint = ComplaintRepository.get_by_case(case_id)

    if case is None or complaint is None:
        logger.error(f"evaluate_and_recommend: case/complaint not found for {case_id}")
        return

    order = OrderRepository.get_by_id(case["order_id"])
    product = ProductRepository.get_by_id(complaint.get("product_id")) if complaint.get("product_id") else None

    evidence = EvidenceRepository.latest_for_case(case_id)
    evidence_result = evidence["result"] if evidence else None

    duplicate_result = check_duplicate_complaint(
        case["order_id"], case["customer_id"], exclude_case_id=case_id
    )

    eligibility = evaluate_eligibility(
        order, product, complaint.get("requested_resolution"), evidence_result, duplicate_result
    )

    resolution_type = eligibility["resolution_type"]
    reason = eligibility["reason"]

    ComplaintRepository.set_recommended_resolution(case_id, resolution_type)

    audit_service.log(case_id, f"Resolution recommended: {resolution_type} - {reason}")

    if resolution_type == "reject":
        case_service.close_case(case_id, reason=reason)
        notification_service.notify_customer(
            case_id, case["customer_id"],
            f"Your complaint could not be approved. Reason: {reason}",
        )
        return

    if resolution_type == "request_better_evidence":
        transition = department_service.advance_case(case_id, "Request Better Evidence", case["current_stage"])
        if transition is None:
            notification_service.notify_customer(
                case_id, case["customer_id"], f"Better evidence is required: {reason}"
            )
        return

    if resolution_type == "escalate":
        review_id = customer_care.create_review_request(
            f"Complaint {case_id} needs manual review: {reason}"
        )
        case_service.update_stage(case_id, current_stage="Customer Care", status="Escalated")
        notification_service.notify_customer(
            case_id, case["customer_id"],
            f"Your case has been escalated for manual review. Review ID: {review_id}",
        )
        return

    # refund / replacement / voucher -> ready for Case Manager approval
    workflow_label = RESOLUTION_TO_WORKFLOW_LABEL.get(resolution_type)

    if workflow_label:
        department_service.advance_case(case_id, "Under Review", case["current_stage"])
    else:
        logger.error(f"Unknown resolution_type '{resolution_type}' for case {case_id}")


def complaint_agent(state):

    logger.info("Complaint Agent Started")

    customer_id = state.get("customer_id", "")
    order_id = state.get("order_id", "")
    issue_type = state.get("issue_type", "")
    description = state.get("description", "")

    # --- A. Analysis: collect required fields ---

    if not order_id:
        state["pending_field"] = "order_id"
        state["response"] = (
            "I can help register your complaint.\n\n"
            "Please provide your Order ID."
        )
        return state

    if not issue_type:
        state["pending_field"] = "issue_type"
        state["response"] = (
            "Please provide Issue Type.\n\n"
            "Examples:\n"
            "- DAMAGED_PRODUCT\n"
            "- WRONG_ITEM\n"
            "- REFUND_ISSUE\n"
            "- MISSING_ITEM"
        )
        return state

    if not description:
        state["pending_field"] = "description"
        state["response"] = "Please describe your issue."
        return state

    is_valid, message = validate_complaint(order_id, issue_type, description)

    if not is_valid:
        # Ask again for whichever piece was invalid (currently only the
        # order id is independently verifiable against the database).
        state["order_id"] = ""
        state["pending_field"] = "order_id"
        state["response"] = message + "\n\nPlease provide a valid Order ID."
        return state

    if len(description.strip()) < MIN_DESCRIPTION_LENGTH:
        state["description"] = ""
        state["pending_field"] = "description"
        state["response"] = (
            "Could you provide a bit more detail about the issue? "
            "This helps us process your complaint correctly."
        )
        return state

    # --- C. Previous-case checking (before creating a new case) ---

    duplicate = check_duplicate_complaint(order_id, customer_id)

    if duplicate["duplicate"]:

        existing_case_id = duplicate["existing_case_id"]

        state["case_id"] = existing_case_id
        state["complaint_status"] = "OPEN"
        state["pending_field"] = ""
        state["response"] = (
            f"You already have an open complaint for this order.\n\n"
            f"Case ID: {existing_case_id}"
        )
        return state

    # --- Create case + complaint ---

    case = case_service.create_case(customer_id, order_id, "Complaint")
    case_id = case["case_id"]

    order = OrderRepository.get_by_id(order_id)
    product_id = order.get("product_id") if order else ""

    requested_resolution = _infer_requested_resolution(issue_type, description)

    evidence_required = "Yes" if issue_type in EVIDENCE_REQUIRED_TYPES else "No"

    create_complaint(
        case_id, customer_id, order_id, product_id,
        complaint_type=issue_type,
        complaint_text=description,
        requested_resolution=requested_resolution,
        evidence_required=evidence_required,
    )

    audit_service.log(case_id, f"Complaint registered: {issue_type}")

    state["case_id"] = case_id
    state["complaint_status"] = "OPEN"
    state["pending_field"] = ""
    state["order_id"] = ""
    state["issue_type"] = ""
    state["description"] = ""

    if evidence_required == "Yes":

        evidence_review.request_evidence(case_id, evidence_type="image", description=description)

        state["response"] = (
            f"Complaint registered successfully.\n\n"
            f"Case ID: {case_id}\n"
            "Please note: this issue requires evidence review. Our Evidence Review "
            "team will verify your product photos/videos and we'll update you once "
            "that's complete."
        )
        return state

    case_service.update_stage(case_id, current_stage="Under Review")

    evaluate_and_recommend(case_id)

    state["response"] = (
        f"Complaint registered successfully.\n\n"
        f"Case ID: {case_id}\n"
        "Your complaint is now under review. We'll update you shortly."
    )

    logger.info(f"Complaint Created: {case_id}")

    return state
