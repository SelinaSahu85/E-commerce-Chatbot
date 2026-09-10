from tools.policy_rag import get_policy_answer
from tools.enquiry_safety import can_answer_safely

from hitl.customer_care import (
    create_review_request
)

from utils.logger import logger


def enquiry_agent(state):

    query = state["user_query"]

    logger.info(
        f"Enquiry Agent Started : {query}"
    )

    safe = can_answer_safely(query)

    if not safe:

        review_id = create_review_request(
            query
        )

        logger.info(
            f"HITL Triggered : {review_id}"
        )

        return {
            "requires_hitl": True,
            "review_id": review_id,
            "response":
                f"""
Your request requires review by Customer Care.

Review ID: {review_id}

A support representative will review your request.
"""
        }

    result = get_policy_answer(query)

    logger.info(
        "Policy RAG completed"
    )

    return {
        "requires_hitl": False,
        "review_id": "",
        "sources": result["sources"],
        "response": result["answer"]
    }