from langchain_huggingface import HuggingFaceEmbeddings

_EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_embedding_model = None


def get_embedding_model():
    """
    Returns a cached HuggingFace embedding model instance.
    Downloads/loads from the local HF cache on first use.
    """

    global _embedding_model

    if _embedding_model is None:

        _embedding_model = HuggingFaceEmbeddings(
            model_name=_EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embedding_model