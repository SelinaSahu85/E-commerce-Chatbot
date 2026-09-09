from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_model():

    model_path = r"C:\Users\Selina.Sahu\Downloads\all-MiniLM-L6-v2"

    embeddings = HuggingFaceEmbeddings(
        model_name=model_path,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    return embeddings