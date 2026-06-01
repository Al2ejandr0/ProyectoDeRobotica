import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
DB_PATH = "./hero_knowledge_db"
"""Configures environment variables to ensure the model works offline"""

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': False},
        cache_folder="./model_cache" 
    )
"""Initializes the Embeddings model (transforms text into numerical vectors)"""

def initialize_db():
    return Chroma(persist_directory=DB_PATH, embedding_function=get_embeddings())
"""Returns the configured Chroma instance."""

def LoadAndTrainFile(ruta_txt):
    if not os.path.exists(ruta_txt):
        print(f"Error: The file {ruta_txt} does not exist.")
        return
    """Loads and processes selected .txt files, if they don't exist, it displays an error message"""

    loader = TextLoader(ruta_txt, encoding="utf-8")
    documents = loader.load()
    """Prevents errors or confusion with accents"""
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    fragments = text_splitter.split_documents(documents)
    """Divides the text into fragments (chunks) for semantic search"""

    db = initialize_db()
    db.add_documents(fragments) 
    print(f"Hero has read {os.path.basename(ruta_txt)} and saved {len(fragments)} fragments!")
    """Reads and detects the selected .txt files"""

if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    knowledge_files = [
        rf"{path}/INFO/curiosidades.txt",
        rf"{path}/INFO/Leyendas.txt",
        rf"{path}/INFO/personajes.txt",
        rf"{path}/INFO/Naturaleza.txt",
        rf"{path}/INFO/entretenimiento.txt",
        rf"{path}/INFO/Cultura(1).txt",
        rf"{path}/INFO/proposito.txt",
        rf"{path}/INFO/integrantes.txt",
        rf"{path}/INFO/Info.txt"
    ]
    print("Starting massive knowledge loading for Hero (Offline Mode)")
    print("-" * 60)
    for files in knowledge_files:
        LoadAndTrainFile(files)
    print("-" * 60)
    print("Vector database generated and saved locally")
"""List of the different files included for the database"""