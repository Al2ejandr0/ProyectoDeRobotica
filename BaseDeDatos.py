from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = "./hero_knowledge_db"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
"""Transformation of words into vectors"""

embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
"""It helps to represent the meaning of the text numerically"""

def buscar_informacion(consulta):
    try:
        db = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
        resultados = db.similarity_search(consulta, k=3)
        """Search, compare and retrieve the vectors and take the 3 most similar fragments"""
        return "\n".join([doc.page_content for doc in resultados])
   
    except Exception as e:
        print(f"Error de base de datos: {e}")
    return ""