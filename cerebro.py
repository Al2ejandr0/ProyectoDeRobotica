import os
import socket
import requests
from dotenv import load_dotenv
from BaseDeDatos import buscar_informacion

# --- CONFIGURACIÓN ---
load_dotenv(os.path.dirname(__file__) + "/api_key.env")

def tiene_internet(host="8.8.8.8", port=53, timeout=1):
    """Comprueba conexión de red."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except:
        return False

def llamar_a_ollama_local(mensajes):
    """Función independiente para el respaldo local."""
    try:
        print("🏠 Nivel 2: Iniciando respaldo local (Ollama)...")
        payload_local = {
            "model": "llama3.2:1b",
            "messages": mensajes,
            "stream": False,
            "options": {"num_ctx": 2048}
        }
        respuesta_local = requests.post(
            "http://localhost:11434/api/chat",
            json=payload_local,
            timeout=20
        )
        respuesta_local.raise_for_status()
        return respuesta_local.json()["message"]["content"]
    except Exception as e:
        print(f"❌ El cerebro local falló por -> {e}")
        return "Disculpa, tuve un pequeño fallo en mis circuitos."

def cerebro_hero(pregunta_usuario, db):
    pregunta_min = pregunta_usuario.lower()
    
    es_interaccion_basica = any(palabra in pregunta_min for palabra in [
        "chiste", "broma", "cuentame algo gracioso", "hola", "saludos", "buenos dias", "como estas"
    ])

    if es_interaccion_basica:
        print("⚡ [FILTRO RÁPIDO] Interacción básica.")
        datos_encontrados = ""
    else:
        print("🔍 [BASE DE DATOS] Buscando en archivos...")
        datos_encontrados = buscar_informacion(pregunta_usuario, db)

    instrucciones = (
        "Eres Hero, un asistente cultural para el robot WRO 2026. "
        "Responde breve (máximo 2 frases), amigable y con chispa venezolana. "
    )
    instrucciones += f"Usa estos datos: {datos_encontrados}" if datos_encontrados else "Usa tu conocimiento general."

    mensajes = [
        {"role": "system", "content": instrucciones},
        {"role": "user", "content": pregunta_usuario}
    ]

    # --- CONTROL DE FLUJO INTELIGENTE ---
    if tiene_internet():
        try:
            print("🚀 Nivel 1: Conectando a la Nube (Groq)...")
            headers = {
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": mensajes
            }
            
            respuesta_nube = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=5
            )
            
            if respuesta_nube.status_code == 200:
                return respuesta_nube.json()["choices"][0]["message"]["content"]
            else:
                print(f"Error de Nube: {respuesta_nube.text}")
                # Si falla, no retornamos nada aquí, dejamos que el código siga al Nivel 2
                
        except Exception as e:
            print(f"⚠️ Nube falló: {e}")

    # Si llegamos aquí, es porque la nube falló o no hubo internet
    return llamar_a_ollama_local(mensajes)