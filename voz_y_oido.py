import pyaudio
import vosk
import unicodedata
import sounddevice as sd
import numpy as np
from piper import PiperVoice

MODEL = "piper/es_ES-davefx-medium.onnx"
CONFIG = "piper/es_ES-davefx-medium.onnx.json"
"""Configuración de ruta para el motor de texto a voz"""

ai_speaking = False
"""Indicadores de estado globales para controlar el flujo de audio y la sincronización de hilos"""

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
voice = PiperVoice.load(MODEL, config_path=CONFIG)
"""Carga el modelo de voz Piper para una síntesis de voz de alta calidad"""

def clarity(data, umbral=200):
    audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    mean_square = np.mean(audio_data**2)
    if mean_square <= 0: return False
    rms = np.sqrt(mean_square)
    return rms > umbral
"""Calcula la energía RMS para filtrar el ruido de fondo de bajo volumen"""

def speak(text):
    global ai_speaking 
    ai_speaking = True 
    stream.stop_stream()
    print(f"Hero dice: {text}")
    try:
        for audio_bytes in voice.synthesize(text):
            sd.play(audio_bytes.audio_int16_array, samplerate=22050)
            sd.wait()

    finally:
        ai_speaking = False
        stream.start_stream()
        print("Hero terminó de hablar.")
    """Sintetiza el texto en audio y lo reproduce a través de los altavoces"""

def clean_text(text):
    if not text: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()
"""Normaliza el texto eliminando los acentos y convirtiéndolo a minúsculas"""

def initialize_hearing():
    model = vosk.Model("model")
    rec = vosk.KaldiRecognizer(model, 16000)
    """Inicializar el modelo de conversión de voz a texto"""
    """Configurar el flujo de entrada de audio desde el micrófono"""

    return rec