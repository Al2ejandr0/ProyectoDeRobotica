import os
import requests
from dotenv import load_dotenv
from BaseDeDatos import Search_Information

load_dotenv(os.path.join(os.path.dirname(__file__), "api_key.env"))

HISTORIAL_CONVERSACION = []
MAX_HISTORIAL_MENSAJES = 6

def reiniciar_historial():
    """Limpia el historial cuando el usuario se despide o se pierde el rostro"""
    global HISTORIAL_CONVERSACION
    HISTORIAL_CONVERSACION.clear()
    print("[Memoria Hero]: Historial reiniciado.")

def agregar_al_historial(role, content):
    """Añade un mensaje y recorta el historial si supera el límite"""
    global HISTORIAL_CONVERSACION
    HISTORIAL_CONVERSACION.append({"role": role, "content": content})
    if len(HISTORIAL_CONVERSACION) > MAX_HISTORIAL_MENSAJES:
        HISTORIAL_CONVERSACION = HISTORIAL_CONVERSACION[-MAX_HISTORIAL_MENSAJES:]


def call_local_ollama(messages):
    """Respaldo local usando Ollama si la nube no está disponible"""
    try:
        print("Iniciando respaldo local (Ollama - qwen2.5:0.5b)...")
        payload_local = {
            "model": "qwen2.5:0.5b",
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": 2048}
        }

        local_response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json=payload_local,
            timeout=30
        )
        """Conexión al modelo local"""

        local_response.raise_for_status()
        return local_response.json()["message"]["content"]
    except Exception as e:
        print(f"Falló la IA Local -> {e}")
        return "Disculpa mi pana, tuve un pequeño pestañeo técnico."


def cerebro_hero(user_question, db, contexto_visual=None, forzar_local=False):
    min_question = user_question.lower().strip()
    
    is_basic_interaction = any(word in min_question for word in [
        "chiste", "broma", "cuentame algo gracioso", "hola", "saludos", "buenos dias", 
        "como estas", "me llamo", "mi nombre es", "soy", "un placer", "que tal"
    ])
    """ Identificador de saludos, chistes..."""

    if is_basic_interaction or contexto_visual:
        print("Interacción básica o saludo detectado. Omitiendo búsqueda en BD.")
        found_data = ""
    else:
        print(f"Buscando en Base de Datos para: '{user_question}'")
        found_data = Search_Information(user_question, db)
        """Búsqueda en la base de datos"""

    instructions = (
        "Eres Hero, un robot asistente cultural interactivo de Venezuela. "
        "Responde siempre de forma muy breve, amigable, con la chispa, el ingenio y el carisma del hablar venezolano. "
        "No uses léxico de otros países como che, solo palabras venezolanas."
        "No uses emojis en tus respuestas"
    )
    """Prompt de la personalidad de Hero"""
    
    if contexto_visual:
        instructions += (
            f" OBSERVACIÓN VISUAL REAL: El usuario que tienes en frente tiene: '{contexto_visual}'. "
            f"Incorpora de forma muy natural, espontánea y alegre un cumplido corto sobre esto "
            f"en tu respuesta (por ejemplo: ¡Qué fino el estilo de tu gorra! o ¡Esa camisa te queda genial!). "
            f"Dilo con el flow, el respeto y la calidez de un pana venezolano."
        )
        """Configuración de la actitud al frente de un usuario"""

    if found_data:
        instructions += f"Usa estos datos del museo para responder: {found_data}. \nSi no encuentras datos relevantes en esa informacion, usa datos de internet"

    messages = [{"role": "system", "content": instructions}]
    messages.extend(HISTORIAL_CONVERSACION)
    messages.append({"role": "user", "content": user_question})
    
    respuesta_final = ""

    if forzar_local:
        print("Routing directly to Local Ollama (Forced)...")
        respuesta_final = call_local_ollama(messages)
        """Enrutamiento al modelo local si se fuerza explícitamente"""
    else:
        api_key = os.getenv("OLLAMA_API_KEY")
        if api_key:
            try:
                print("Routing to Cloud (Ollama)...")
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "gemma4:31b",
                    "messages": messages,
                    "stream": False
                }
                cloud_response = requests.post(
                    "https://ollama.com/api/chat",
                    headers=headers,
                    json=payload,
                    timeout=15
                )
                
                if cloud_response.status_code == 200:
                    respuesta_final = cloud_response.json()["message"]["content"]
                else:
                    print(f"Error en API Ollama ({cloud_response.status_code}): {cloud_response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Ollama offline o sin conexión -> {e}")
            except Exception as e:
                print(f"Error inesperado con Ollama -> {e}")
        else:
            print("Advertencia: No se encontró OLLAMA_API_KEY en api_key.env")
            """Prioridad principal (Conexión al modelo de la nube)"""

        if not respuesta_final:
            print("Usando Ollama Local como respaldo...")
            respuesta_final = call_local_ollama(messages)
            """Segunda Prioridad o secundaria (Fallback a Ollama si la nube falla o no hay clave)"""

    if respuesta_final:
        agregar_al_historial("user", user_question)
        agregar_al_historial("assistant", respuesta_final)

    return respuesta_final