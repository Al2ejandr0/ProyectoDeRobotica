import os
import socket
import requests
from dotenv import load_dotenv
from BaseDeDatos import Search_Information

load_dotenv(os.path.dirname(__file__) + "/api_key.env")

def has_internet(host="8.8.8.8", port=53, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except:
        return False

def call_local_ollama(messages):
    try:
        print("Starting local backup (Ollama - qwen2.5:0.5b)...")
        payload_local = {
            "model": "qwen2.5:0.5b",
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": 1024}
        }
        local_response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json=payload_local,
            timeout=20
        )
        local_response.raise_for_status()
        return local_response.json()["message"]["content"]
    except Exception as e:
        print(f"Local brain failed due to -> {e}")
        return "Disculpa mi pana, tuve un pequeño pestañeo técnico."


# --- FUSIÓN AJUSTADA Y MEJORADA ---
def cerebro_hero(user_question, db, contexto_visual=None, forzar_local=False):
    min_question = user_question.lower().strip()
    
    # 1. Identificamos interacciones básicas estrictas (saludos, chistes)
    is_basic_interaction = any(word in min_question for word in [
        "chiste", "broma", "cuentame algo gracioso", "hola", "saludos", "buenos dias", 
        "como estas", "me llamo", "mi nombre es", "soy", "un placer", "que tal"
    ])

    # 2. Control de búsqueda en Base de Datos
    if is_basic_interaction or contexto_visual:
        print("Basic or greeting interaction detected. Skipping DB search.")
        found_data = ""
    else:
        print(f"Searching in files (Database) for: '{user_question}'")
        found_data = Search_Information(user_question, db)

    # 3. Configuración de la personalidad de Hero
    instructions = (
        "Eres Hero, un robot asistente cultural interactivo de Venezuela. "
        "Responde siempre de forma muy breve (máximo dos oraciones), amigable, con la chispa, el ingenio y el carisma del hablar venezolano. "
        "No uses lexico de otros países como che, solo palabras venezolanas"
    )
    
    # 4. INYECCIÓN DEL HALAGO REAL (Si aplica en este turno)
    if contexto_visual:
        instructions += (
            f" OBSERVACIÓN VISUAL REAL: El usuario que tienes en frente tiene: '{contexto_visual}'. "
            f"Incopora de forma muy natural, espontánea y alegre un cumplido corto sobre esto "
            f"en tu respuesta (por ejemplo: ¡Qué fino el estilo de tu gorra! o ¡Esa camisa te queda genial!). "
            f"Dilo con el flow, el respeto y la calidez de un pana venezolano."
        )

    if found_data:
        instructions += f" Usa estrictamente estos datos del museo para responder: {found_data}"
    
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_question}
    ]
    
    # 5. ENRUTAMIENTO INTELIGENTE CORREGIDO
    # Si se fuerza localmente desde el código, vamos directo a Ollama
    if forzar_local:
        print("Routing directly to Local Ollama (Forced)...")
        return call_local_ollama(messages)

    # PRIORIDAD 1: Nube (Groq). Es más rápido, no gasta RAM de la Pi y entiende mejor los nombres y halagos.
    if has_internet():
        try:
            print("Routing to Cloud (Groq)...")
            headers = {
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages
            }
            cloud_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15 
            )
            
            if cloud_response.status_code == 200:
                return cloud_response.json()["choices"][0]["message"]["content"]
            else:
                print(f"Cloud error ({cloud_response.status_code}): {cloud_response.text}")
        except Exception as e:
            print(f"Cloud failed due to -> {e}")

    # PRIORIDAD 2: Fallback final a Ollama SOLO si no hay internet o si Groq falló
    print("No internet or Cloud failed. Falling back to Local Ollama...")
    return call_local_ollama(messages)