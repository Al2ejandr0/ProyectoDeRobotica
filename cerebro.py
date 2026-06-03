import os
import socket
import requests
from dotenv import load_dotenv
from BaseDeDatos import Search_Information

load_dotenv(os.path.dirname(__file__) + "/api_key.env")
"""Load environment variable for API Key"""

def has_internet(host="8.8.8.8", port=53, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except:
        return False
"""Network connection check"""

def call_local_ollama(messages):
    try:
        print("Starting local backup (Ollama)...")
        payload_local = {
            "model": "llama3.2:1b",
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": 2048}
        }
        local_response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload_local,
            timeout=20
        )
        """Independent function for local backup"""
        local_response.raise_for_status()
        return local_response.json()["message"]["content"]
    except Exception as e:
        print(f"Local brain failed due to -> {e}")
        return "Disculpa, tuve un pequeño fallo"

def cerebro_hero(user_question, db):
    min_question = user_question.lower()
    """Chooses between database, cloud (Groq), or local (Ollama)"""

    is_basic_interaction = any(word in min_question for word in [
        "chiste", "broma", "cuentame algo gracioso", "hola", "saludos", "buenos dias", "como estas"
    ])
    """Simple interactions that do not require a database"""

    if is_basic_interaction:
        print("Basic interaction.")
        found_data = ""
    else:
        print("Searching in files (Database)")
        found_data = Search_Information(user_question, db)
        """Searches for information in the database if the question is not complex"""

    instructions = (
        "You're Hero, a cultural assistant"
        "Answer briefly, in a friendly way, with Venezuelan wit and charm"
    )
    instructions += f"Use this data: {found_data}" if found_data else "Use your general knowledge"
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_question}
    ]
    """Personality configuration"""
    
    if has_internet():
        try:
            print("Internet connection (Groq)")
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
                timeout=5
            )
            """Checks connection to use the Groq API"""
            
            if cloud_response.status_code == 200:
                return cloud_response.json()["choices"][0]["message"]["content"]
            else:
                print(f"Cloud error: {cloud_response.text}")
        except Exception as e:
            print(f"Cloud failed: {e}")

    return call_local_ollama(messages)
"""When it fails, it switches to the local ollama model"""