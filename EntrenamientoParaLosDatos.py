import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter # IMPORTANTE
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = "./hero_knowledge_db"
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=model_name)
"""Words are transformed into numerical values ​​(vectors)"""

def inicializar_db():
    return Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
"""Connect to or create the Chroma database using HuggingFace vectors"""

def cargar_y_entrenar_archivo(ruta_txt):
    if not os.path.exists(ruta_txt):
        print(f"Error: El archivo {ruta_txt} no existe.")
        return
    """It reads the files, and if they don't exist, it gives an error and stops the process."""

    # 1. Leer el archivo
    loader = TextLoader(ruta_txt, encoding="utf-8")
    documentos = loader.load()
    """Upload the document, using UTF-8 encoding to avoid errors with accented characters."""

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    fragmentos = text_splitter.split_documents(documentos)
    """It helps to divide the text into different fragments"""

    db = inicializar_db()
    db.add_documents(fragmentos) 
    print(f"¡Hero ha leído {ruta_txt} y guardado {len(fragmentos)} fragmentos!")
    """It helps to divide the text into different fragments"""

if __name__ == "__main__":
    cargar_y_entrenar_archivo("C:\Users\DELL\Documents\Python\WRO2026\INFO\cosa.txt")
"""Add the file path to read it"""