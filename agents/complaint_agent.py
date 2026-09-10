import logging

from tools.complaint_validator import validate_complaint
from tools.duplicate_checker import check_duplicate_complaint
from tools.complaint_creator import create_complaint

logger = logging.getLogger(__name__)


def complaint_agent(state):

    logger.info("Complaint Agent Started")

    order_id = state.get("order_id", "")
    issue_type = state.get("issue_type", "")
    description = state.get("description", "")

    # Ask Order ID

    if not order_id:

        state["pending_field"] = "order_id"

        state["response"] = (
            "I can help register your complaint.\n\n"
            "Please provide your Order ID."
        )

        return state

    # Ask Issue Type

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

    # Ask Description

    if not description:

        state["pending_field"] = "description"

        state["response"] = (
            "Please describe your issue."
        )

        return state

    # Validate

    is_valid, message = validate_complaint(
        order_id,
        issue_type,
        description
    )

    if not is_valid:

        state["response"] = message

        return state

    # Duplicate Check

    duplicate = check_duplicate_complaint(
        order_id,
        issue_type
    )

    if duplicate:

        state["complaint_id"] = duplicate["complaint_id"]

        state["response"] = (
            f"Existing complaint found.\n\n"
            f"Complaint ID: {duplicate['complaint_id']}\n"
            f"Status: {duplicate['status']}"
        )

        return state

    # Create Complaint

    complaint = create_complaint(
        order_id,
        issue_type,
        description
    )

    state["complaint_id"] = complaint["complaint_id"]
    state["complaint_status"] = "OPEN"
    state["pending_field"] = ""

    state["response"] = (
        f"Complaint registered successfully.\n\n"
        f"Complaint ID: {complaint['complaint_id']}\n"
        f"Status: OPEN"
    )

    logger.info(
        f"Complaint Created: {complaint['complaint_id']}"
    )

    return state