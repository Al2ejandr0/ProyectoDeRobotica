import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama 
from langchain_core.messages import SystemMessage, HumanMessage

llm_nube = ChatOpenAI(
    base_url="https://api.groq.com/openai/v1", 
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile", 
    timeout=5
)
llm_local = ChatOllama(model="llama3.2:1b")

def cerebro_hero(pregunta_usuario):
    instrucciones = (
        "Eres Hero, asistente de la cultura venezolana para la WRO 2026. "
        "Fuiste creada por Alejandro Guiñán, Kamila Gómez y Alejandro González. "
        "Responde de forma breve y amable."
    )
    mensajes = [
        SystemMessage(content=instrucciones), 
        HumanMessage(content=pregunta_usuario)
    ]

    try:
        print("--- Usando Cerebro en la Nube ---")
        resultado = llm_nube.invoke(mensajes)
        return resultado.content
    except Exception:
        print("--- Internet fallido. Cambiando a Cerebro Local ---")
        try:
            resultado = llm_local.invoke(mensajes)
            return resultado.content
        except Exception as e_local:
            print(f"Error local: {e_local}")
            return "Panita, mis dos cerebros están ocupados. ¿Me repites?"