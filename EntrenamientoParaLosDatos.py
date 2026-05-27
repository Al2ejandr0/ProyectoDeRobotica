import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DB_PATH = "./hero_knowledge_db"

def get_embeddings():
    """Carga el modelo de forma local solo cuando se solicita."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': False},
        cache_folder="./model_cache" 
    )

def inicializar_db():
    """Retorna la instancia de Chroma configurada."""
    return Chroma(persist_directory=DB_PATH, embedding_function=get_embeddings())

def cargar_y_entrenar_archivo(ruta_txt):
    if not os.path.exists(ruta_txt):
        print(f"⚠️ Error: El archivo {ruta_txt} no existe.")
        return

    loader = TextLoader(ruta_txt, encoding="utf-8")
    documentos = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    fragmentos = text_splitter.split_documents(documentos)

    db = inicializar_db()
    db.add_documents(fragmentos) 
    print(f"¡Hero ha leído {os.path.basename(ruta_txt)} y guardado {len(fragmentos)} fragmentos!")

if __name__ == "__main__":
    archivos_conocimiento = [
        r"C:\Users\DELL\Downloads\curiosidades.txt",
        r"C:\Users\DELL\Downloads\Leyendas.txt",
        r"C:\Users\DELL\Downloads\personajes.txt",
        r"C:\Users\DELL\Downloads\Naturaleza.txt",
        r"C:\Users\DELL\Downloads\entretenimiento.txt",
        r"C:\Users\DELL\Downloads\Cultura(1).txt"
    ]
    
    print("🤖 [SISTEMA] Iniciando carga masiva de conocimientos para Hero (Modo Offline)...")
    print("-" * 60)
    
    for archivo in archivos_conocimiento:
        cargar_y_entrenar_archivo(archivo)
        
    print("-" * 60)
    print("✅ ¡Base de datos vectorial generada y guardada localmente!")