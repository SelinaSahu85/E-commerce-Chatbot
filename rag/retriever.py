from langchain_community.vectorstores import FAISS

from rag.embeddings import get_embedding_model
from config.setting import VECTORSTORE_PATH


def get_retriever():
    """
    Returns a Retriever object for RAG.
    """

    embeddings = get_embedding_model()

    db = FAISS.load_local(
        str(VECTORSTORE_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,
            "fetch_k": 20,
            "lambda_mult": 0.7
        }
    )

    return retriever


def get_documents(query: str):
    """
    Helper function for debugging retrieval.
    """

    retriever = get_retriever()

    docs = retriever.invoke(query)

    return docs