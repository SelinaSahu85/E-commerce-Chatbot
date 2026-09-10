from tools.intent_classifier import classify_intent
from utils.logger import logger


def route_query(state):

    query = state["user_query"]

    logger.info(f"Supervisor received query: {query}")

    intent = classify_intent(query)

    logger.info(f"Detected Intent: {intent}")

    return {
        "intent": intent
    }