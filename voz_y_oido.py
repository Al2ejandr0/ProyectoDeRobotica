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

def proceso_hablar(texto):
    global ia_hablando, ultimo_tiempo_voz
    ia_hablando = True
    engine = pyttsx3.init()
    engine.setProperty('rate', 165) 
    engine.say(texto)
    engine.runAndWait()
    ultimo_tiempo_voz = time.time() 
    time.sleep(1.0) 
    ia_hablando = False

def hablar(texto):
    print(f"Hero: {texto}")
    hilo_voz = threading.Thread(target=proceso_hablar, args=(texto,))
    hilo_voz.start()

def limpiar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn').lower()

def inicializar_oido():
    if not os.path.exists("model"):
        print("Error: Falta la carpeta 'model' de Vosk")
        return None, None, None

    model = vosk.Model("model")
    rec = vosk.KaldiRecognizer(model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
    stream.start_stream()
    return rec, stream, p