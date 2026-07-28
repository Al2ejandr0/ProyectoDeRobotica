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

    # 2. Control de búsqueda en Base de Datos
    if is_basic_interaction or contexto_visual:
        print("Interacción básica o saludo detectado. Omitiendo búsqueda en BD.")
        found_data = ""
    else:
        print(f"Buscando en Base de Datos para: '{user_question}'")
        found_data = Search_Information(user_question, db)

    # 3. Personalidad de Hero
    instructions = (
        "Eres Hero, un robot asistente cultural interactivo de Venezuela. "
        "Responde siempre de forma muy breve (máximo dos oraciones), amigable, con la chispa, el ingenio y el carisma del hablar venezolano. "
        "No uses léxico de otros países como che, solo palabras venezolanas."
    )
    
    # 4. Inyección del contexto visual
    if contexto_visual:
        instructions += (
            f" OBSERVACIÓN VISUAL REAL: El usuario que tienes en frente tiene: '{contexto_visual}'. "
            f"Incorpora de forma muy natural, espontánea y alegre un cumplido corto sobre esto "
            f"en tu respuesta (por ejemplo: ¡Qué fino el estilo de tu gorra! o ¡Esa camisa te queda genial!). "
            f"Dilo con el flow, el respeto y la calidez de un pana venezolano."
        )

    if found_data:
        instructions += f" Usa strictly estos datos del museo para responder: {found_data}"
    
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_question}
    ]
    
    # 5. Enrutamiento directo a local si se fuerza explícitamente
    if forzar_local:
        print("Routing directly to Local Ollama (Forced)...")
        return call_local_ollama(messages)

    # PRIORIDAD 1: Ollama (Nube)
    api_key = os.getenv("OLLAMA_API_KEY")
    
    if api_key:
        try:
            print("Routing to Cloud (Ollama)...")
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                # Modelo 100% gratuito y muy potente en Ollama:
                "model": "gemma4:31b",
                "messages": messages,
                "stream": False
            }
            cloud_response = requests.post(
                "https://ollama.com/api/chat",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if cloud_response.status_code == 200:
                return cloud_response.json()["message"]["content"]
            else:
                print(f"Error en API Ollama ({cloud_response.status_code}): {cloud_response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Ollama offline o sin conexión -> {e}")
        except Exception as e:
            print(f"Error inesperado con Ollama -> {e}")
    else:
        print("Advertencia: No se encontró Ollama_API_KEY en api_key.env")

    # PRIORIDAD 2: Fallback a Ollama si la nube falla o no hay clave
    print("Usando Ollama Local como respaldo...")
    return call_local_ollama(messages)