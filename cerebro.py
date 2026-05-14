import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama 
from langchain_core.messages import SystemMessage, HumanMessage
#These libraries send AI models both locally and in the cloud so that ours can function in a hybrid way, and also help it to respond and send messages to the user.

load_dotenv(os.path.dirname(__file__) + "/api_key.env")
#Upload the API key from an external file for security and to avoid GitHub blocks

llm_nube = ChatOpenAI(
    base_url="https://api.groq.com/openai/v1", 
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile", 
    timeout=5
#This section is responsible for calling the group model using its key to activate it, so that when it needs to access data that it cannot find locally, it can search for data in the cloud.
)
llm_local = ChatOllama(model="llama3.2:1b")
#Here the local model (ollama) is called to work in cases where there is no internet

def cerebro_hero(pregunta_usuario): #'System Prompt' Establishes the robot's identity, creators, and tone of voice
    instrucciones = (
        "Eres Hero, asistente de la cultura venezolana para la WRO 2026. "
        "Fuiste creada por Alejandro Guiñán, Kamila Gómez y Alejandro González. "
        "Responde de forma breve y amable."
    )
    mensajes = [ #Here, call the functions to be able to communicate the message to the user
        SystemMessage(content=instrucciones), 
        HumanMessage(content=pregunta_usuario)
    ]

    try: #Provides a local processing response if the cloud cannot be used when attempting to use it
        print("Usando Cerebro en la Nube")
        resultado = llm_nube.invoke(mensajes)
        return resultado.content
    except Exception:
        print("Internet fallido. Cambiando a Cerebro Local")
        try:
            resultado = llm_local.invoke(mensajes)
            return resultado.content
        except Exception as e_local:
            print(f"Error local: {e_local}")
            return "Panita, mis dos cerebros están ocupados. ¿Me repites?"