import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from rag.embeddings import get_embedding_model
from config.setting import PDF_PATH, VECTORSTORE_PATH


def build_vectorstore():

    print("Loading PDF...")

    loader = PyPDFLoader(PDF_PATH)

    documents = loader.load()

    print(f"Pages Loaded : {len(documents)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=[
            "\n\n",
            "\n",
            "?",
            ".",
            " "
        ]
    )

    chunks = splitter.split_documents(documents)

    print(f"Chunks Created : {len(chunks)}")

    valid_chunks = []

    for chunk in chunks:

        text = chunk.page_content.strip()

        if text:
            valid_chunks.append(chunk)

    print(f"Valid Chunks : {len(valid_chunks)}")

    if not valid_chunks:
        raise ValueError("No chunks found after splitting")

    embeddings = get_embedding_model()

    test_embedding = embeddings.embed_query(
        "What is Myntra return policy?"
    )

    print(
        f"Embedding Dimension : {len(test_embedding)}"
    )

    vectorstore = FAISS.from_documents(
        valid_chunks,
        embeddings
    )

    os.makedirs("vectorstore", exist_ok=True)

    vectorstore.save_local(
        VECTORSTORE_PATH
    )

    print("Vector Store Saved Successfully")


if __name__ == "__main__":
    build_vectorstore()
