from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from utils.logger import logger
import os

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)


def classify_intent(query: str) -> str:
    """
    Classify query as enquiry or complaint
    """

    prompt = f"""
You are an intent classifier for an E-commerce Customer Support Assistant.

Classify the customer query into ONLY one category:

enquiry
or
complaint

Rules:

enquiry:
- return policy
- exchange policy
- shipping policy
- refund policy
- FAQs
- product information
- payment methods
- general questions

complaint:
- damaged product
- missing item
- wrong product
- refund not received
- delayed order
- defective product
- cancellation issue
- delivery issue
- customer grievance

Customer Query:
{query}

Return ONLY:
enquiry

or

complaint
"""

    try:

        logger.info(f"Classifying Query: {query}")

        response = llm.invoke(prompt)

        content = response.content

        logger.info(f"Raw Response Type: {type(content)}")
        logger.info(f"Raw Response: {content}")

        # Handle list response
        if isinstance(content, list):

            cleaned_parts = []

            for item in content:
                cleaned_parts.append(str(item))

            content = " ".join(cleaned_parts)

        intent = str(content).strip().lower()

        logger.info(f"Extracted Intent: {intent}")

        if "complaint" in intent:
            return "complaint"

        return "enquiry"

    except Exception as e:

        logger.error(f"Intent Classification Failed: {str(e)}")

        logger.info("Using Rule-Based Fallback")

        query_lower = query.lower()

        complaint_keywords = [
            "damaged",
            "broken",
            "cracked",
            "refund",
            "missing",
            "wrong item",
            "wrong product",
            "late delivery",
            "not delivered",
            "complaint",
            "issue",
            "problem",
            "defective",
            "received damaged",
            "cancelled order",
            "screen cracked"
        ]

        if any(keyword in query_lower for keyword in complaint_keywords):
            logger.info("Fallback Intent: complaint")
            return "complaint"

        logger.info("Fallback Intent: enquiry")
        return "enquiry"