import os

# ESTO DEBE IR ARRIBA DEL TODO
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = "./hero_knowledge_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Instanciamos los embeddings
embeddings = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': False},
    cache_folder="./model_cache"
)

def abrir_base_datos():
    if not os.path.exists(DB_PATH):
        print(f"⚠️ ¡ALERTA! La carpeta {DB_PATH} no existe. ¿Ejecutaste el entrenamiento?")
    return Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

def buscar_informacion(pregunta, db):
    try:
        if db is None:
            return ""
        resultados = db.similarity_search(pregunta, k=3)
        if not resultados:
            return ""
        return "\n".join([doc.page_content for doc in resultados])
    except Exception as e:
        print(f"❌ Error interno en similarity_search: {e}")
        return ""