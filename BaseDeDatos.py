import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
"""Configuración del modo sin conexión para evitar descargas innecesarias"""

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = "./hero_knowledge_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
"""Definición de rutas y modelo para la persistencia de datos."""

embeddings = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': False},
    cache_folder="./model_cache"
)
"""Instanciar incrustaciones para convertir texto en vectores"""

def Open_DataBase():
    if not os.path.exists(DB_PATH):
        print(f"The folder {DB_PATH} does not exist. Did you run the training?")
    return Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
"""Carga la base de datos de vectores existente desde el directorio local"""

def Search_Information(question, db):
    try:
        if db is None:
            return ""
        results = db.similarity_search(question, k=3)
        if not results:
            return ""
        return "\n".join([doc.page_content for doc in results])
    except Exception as e:
        print(f"Internal error in similarity_search: {e}")
        return ""
"""Realiza una búsqueda de similitud vectorial para encontrar los fragmentos más relevantes"""