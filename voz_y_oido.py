import pyttsx3
import pyaudio
import vosk
import unicodedata
import threading
import time 
import os  
import json

ia_hablando = False 
ultimo_tiempo_voz = time.time() 
"""audio capture and text processing"""

def proceso_hablar(texto):
    global ia_hablando, ultimo_tiempo_voz
    ia_hablando = True
    """Motor TTS (Text-to-Speech)"""

    engine = pyttsx3.init()
    engine.setProperty('rate', 165) 
    """Audio speed of 165 for a more natural voice"""

    engine.say(texto)
    engine.runAndWait()
    ultimo_tiempo_voz = time.time() 
    time.sleep(1.0) 
    """Delay to prevent them from responding to themselves and avoid loops"""

    ia_hablando = False

def hablar(texto):
    print(f"Hero: {texto}")
    hilo_voz = threading.Thread(target=proceso_hablar, args=(texto,))
    hilo_voz.start()
"""Transform what is said into text in the terminal and start speech synthesis in a separate thread"""

def limpiar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn').lower()
"""Remove accents and standardize lowercase letters"""

def inicializar_oido():
    if not os.path.exists("model"):
        print("Error: Falta la carpeta 'model' de Vosk")
        return None, None, None
    """Offline language model verification and audio input flow configuration"""

    model = vosk.Model("model")
    rec = vosk.KaldiRecognizer(model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
    stream.start_stream()
    return rec, stream, p
"""Start or activate the microphone for continuous listening"""