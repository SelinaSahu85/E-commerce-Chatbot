from langchain_google_genai import ChatGoogleGenerativeAI
from rag.retriever import get_retriever

from dotenv import load_dotenv
import os

load_dotenv()


def answer_query(query):

    retriever = get_retriever()

    docs = retriever.invoke(query)

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    sources = []

    for doc in docs:

        page_num = doc.metadata.get("page", "N/A")

        sources.append(f"Page {page_num}")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

    prompt = f"""
You are a Myntra Customer Support Assistant.

Use only the information provided below.

Context:
{context}

Question:
{query}

Answer:
"""

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": list(set(sources))
    }