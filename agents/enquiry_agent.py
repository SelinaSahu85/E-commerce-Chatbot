"""
Enquiry Resolution Agent.

Understands the customer's question, retrieves relevant policy/FAQ
content via the Policy RAG tool, checks confidence/safety, answers the
customer, or escalates to Customer Care when information is
unavailable, insufficient, or the request is sensitive.
"""

from tools.policy_rag import get_policy_answer
from tools.enquiry_safety import can_answer_safely

from hitl.customer_care import create_review_request

from database.repositories import EnquiryRepository
from services import case_service, notification_service

from utils.logger import logger


def _escalate(case_id, customer_id, query, reason):

    review_id = create_review_request(query)

    EnquiryRepository.create_enquiry(
        case_id, customer_id, query, answer="", sources=[], escalated=True
    )

    case_service.update_stage(case_id, current_stage="Customer Care", status="Escalated")

    message = (
        "Your request requires review by Customer Care.\n\n"
        f"Review ID: {review_id}\n\n"
        "A support representative will review your request."
    )

    notification_service.notify_customer(case_id, customer_id, message)

    logger.info(f"HITL Triggered ({reason}): {review_id}")

    return {
        "requires_hitl": True,
        "review_id": review_id,
        "case_id": case_id,
        "response": message,
    }


def enquiry_agent(state):

    query = state["user_query"]
    customer_id = state.get("customer_id", "")

    logger.info(f"Enquiry Agent Started : {query}")

    case = case_service.create_case(customer_id, order_id="", case_type="Enquiry")
    case_id = case["case_id"]

    if not can_answer_safely(query):
        return _escalate(case_id, customer_id, query, reason="sensitive/unsafe query")

    result = get_policy_answer(query)

    logger.info("Policy RAG completed")

    if not result.get("sufficient"):
        return _escalate(case_id, customer_id, query, reason="insufficient retrieved information")

    EnquiryRepository.create_enquiry(
        case_id, customer_id, query, answer=result["answer"], sources=result["sources"]
    )

    case_service.close_case(case_id, reason="Enquiry answered")

    return {
        "requires_hitl": False,
        "review_id": "",
        "case_id": case_id,
        "sources": result["sources"],
        "response": result["answer"],
    }
