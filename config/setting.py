from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = BASE_DIR / "datasets" / "knowledge_base" / "Myntra Policies.pdf"

VECTORSTORE_PATH = BASE_DIR / "vectorstore" / "faiss_index"

EMBEDDING_MODEL_PATH = r"D:\Models\all-MiniLM-L6-v2"