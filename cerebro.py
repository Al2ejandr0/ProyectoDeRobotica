import os
import requests
from dotenv import load_dotenv
from BaseDeDatos import Search_Information

# Cargar variables de entorno desde api_key.env
load_dotenv(os.path.dirname(__file__) + "/api_key.env")

def call_local_ollama(messages):
    """Respaldo local usando Ollama si la nube no está disponible"""
    try:
        print("Iniciando respaldo local (Ollama - qwen2.5:0.5b)...")
        payload_local = {
            "model": "qwen2.5:0.5b",
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": 1024}
        }
        local_response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json=payload_local,
            timeout=10
        )
        local_response.raise_for_status()
        return local_response.json()["message"]["content"]
    except Exception as e:
        print(f"Falló la IA Local -> {e}")
        return "Disculpa mi pana, tuve un pequeño pestañeo técnico."


def cerebro_hero(user_question, db, contexto_visual=None, forzar_local=False):
    min_question = user_question.lower().strip()
    
    # 1. Identificar interacciones básicas (saludos, chistes)
    is_basic_interaction = any(word in min_question for word in [
        "chiste", "broma", "cuentame algo gracioso", "hola", "saludos", "buenos dias", 
        "como estas", "me llamo", "mi nombre es", "soy", "un placer", "que tal"
    ])

    # 2. Control de búsqueda en Base de Datos (RAG)
    if is_basic_interaction or contexto_visual:
        print("Interacción básica o saludo detectado. Omitiendo búsqueda en BD.")
        found_data = ""
    else:
        print(f"Buscando en Base de Datos para: '{user_question}'")
        # Utilizamos tu función original de búsqueda
        found_data = Search_Information(user_question, db)

    # 3. Construcción del "Super Prompt" (Personalidad + RAG)
    instructions = (
        "Eres Hero, un robot asistente cultural interactivo de Venezuela. "
        "Responde siempre de forma muy breve (máximo dos oraciones), amigable, con la chispa, el ingenio y el carisma del hablar venezolano. "
        "No uses léxico de otros países como che, solo palabras venezolanas."
    )
    
    # 4. Inyección del contexto visual
    if contexto_visual:
        instructions += (
            f" \nOBSERVACIÓN VISUAL REAL: El usuario que tienes en frente tiene: '{contexto_visual}'. "
            f"Incorpora de forma muy natural, espontánea y alegre un cumplido corto sobre esto "
            f"en tu respuesta (por ejemplo: ¡Qué fino el estilo de tu gorra!). "
            f"Dilo con el flow, el respeto y la calidez de un pana venezolano."
        )

    # 5. Inyección de Datos Locales
    if found_data:
        instructions += (
            f" \nINFORMACIÓN IMPORTANTE DEL LUGAR: Usa estrictamente estos datos "
            f"para responder a la pregunta de forma precisa: {found_data}"
        )
    elif not is_basic_interaction and not contexto_visual:
        instructions += (
            " \nSi te hacen una pregunta específica sobre historia o el lugar y no tienes información al respecto, "
            "invítalos amablemente a preguntarte sobre otro tema histórico para no inventar datos."
        )
    
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_question}
    ]
    
    # 6. Enrutamiento directo a local si se fuerza explícitamente
    if forzar_local:
        print("Routing directly to Local Ollama (Forced)...")
        return call_local_ollama(messages)

    # PRIORIDAD 1: Nube (Asegúrate de que este endpoint y API Key sean de un proveedor real en la nube)
    api_key = os.getenv("OLLAMA_API_KEY") 
    
    if api_key:
        try:
            print("Routing to Cloud...")
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": "gemma4:31b", 
                "messages": messages,
                "stream": False
            }
            # OJO: Cambia esta URL si usas Groq, OpenAI o un servidor tuyo.
            cloud_response = requests.post(
                "https://api.tu-proveedor-nube.com/v1/chat/completions", 
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if cloud_response.status_code == 200:
                # La estructura del JSON depende del proveedor, asegúrate de que sea compatible
                return cloud_response.json()["choices"][0]["message"]["content"]
            else:
                print(f"Error en API Nube ({cloud_response.status_code}): {cloud_response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Nube offline o sin conexión -> {e}")
        except Exception as e:
            print(f"Error inesperado con la nube -> {e}")
    else:
        print("Advertencia: No se encontró API_KEY en api_key.env")

    # PRIORIDAD 2: Fallback a Ollama si la nube falla o no hay clave
    print("Usando Ollama Local como respaldo...")
    return call_local_ollama(messages)