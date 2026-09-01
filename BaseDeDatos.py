import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
"""Offline mode configuration to avoid unnecessary downloads"""

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = "./hero_knowledge_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
"""Definition of paths and model for data persistence"""

embeddings = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': False},
    cache_folder="./model_cache"
)
"""Instantiate embeddings to convert text to vectors"""

def Open_DataBase():
    if not os.path.exists(DB_PATH):
        print(f"The folder {DB_PATH} does not exist. Did you run the training?")
    return Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
"""Loads the existing vector database from the local directory"""

def Search_Information(question, db):
    try:
        if db is None:
            return ""
        results = db.similarity_search(question, k=3)
        if not results:
            return ""
        print("\n".join([doc.page_content for doc in results]))
        return "\n".join([doc.page_content for doc in results])
    except Exception as e:
        print(f"Internal error in similarity_search: {e}")
        return ""
"""Performs a vector similarity search to find the most relevant fragments"""