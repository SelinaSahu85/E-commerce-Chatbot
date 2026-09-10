from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)


def can_answer_safely(query: str) -> bool:

    prompt = f"""
You are a safety checker for an E-Commerce Customer Support System.

Decide whether the AI can answer this query directly.

Return ONLY one word:

SAFE

or

HITL

HITL cases:
- account deletion
- bank details
- card details
- payment information
- customer personal information
- phone number
- email address
- legal complaints
- consumer court complaints
- account modifications
- privacy related requests

Customer Query:
{query}
"""

    response = llm.invoke(prompt)

    result = response.content.strip().upper()

    return result == "SAFE"