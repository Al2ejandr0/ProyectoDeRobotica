import os
import shutil
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
DB_PATH = "./hero_knowledge_db"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': False},
        cache_folder="./model_cache" 
    )

def initialize_db():
    return Chroma(persist_directory=DB_PATH, embedding_function=get_embeddings())

def LoadAndTrainFile(ruta_txt, db):
    if not os.path.exists(ruta_txt):
        print(f"Error: El archivo {ruta_txt} no existe.")
        return

    loader = TextLoader(ruta_txt, encoding="utf-8")
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150,
        separators=["\n\n\n", "\n\n", "\n---", "\n", " "]
    )
    fragments = text_splitter.split_documents(documents)

    for frag in fragments:
        frag.metadata["source_file"] = os.path.basename(ruta_txt)

    db.add_documents(fragments) 
    print(f"Hero ha leído {os.path.basename(ruta_txt)} y guardó {len(fragments)} fragmentos completos.")

if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    
    if os.path.exists(DB_PATH):
        print("Eliminando base de datos antigua para evitar duplicados fragmentados...")
        shutil.rmtree(DB_PATH)

    db = initialize_db()

    knowledge_files = [
        os.path.join(path, "INFO", "curiosidades.txt"),
        os.path.join(path, "INFO", "Leyendas.txt"),
        os.path.join(path, "INFO", "personajes.txt"),
        os.path.join(path, "INFO", "Naturaleza.txt"),
        os.path.join(path, "INFO", "entretenimiento.txt"),
        os.path.join(path, "INFO", "Cultura(1).txt"),
        os.path.join(path, "INFO", "proposito.txt"),
        os.path.join(path, "INFO", "integrantes.txt"),
        os.path.join(path, "INFO", "Info.txt"),
        os.path.join(path, "INFO", "batalla de carabobo.txt")
    ]
    
    print("Iniciando carga masiva de conocimiento para Hero (Modo Offline)")
    print("-" * 60)
    for files in knowledge_files:
        LoadAndTrainFile(files, db)
    print("-" * 60)
    print("Base de datos vectorial re-generada y guardada localmente con éxito.")