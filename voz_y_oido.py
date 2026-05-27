import subprocess
import os
import threading
import pyaudio
import vosk
import unicodedata
from piper import PiperVoice
import wave
import os
import sounddevice as sd
import numpy as np

# Configuración de rutas
MODELO = "piper/es_ES-davefx-medium.onnx"
CONFIG = "piper/es_ES-davefx-medium.onnx.json"

ia_hablando = False
pausar_oido = threading.Event()
voice = PiperVoice.load(MODELO, config_path=CONFIG)

def hablar(texto):
    print(f"Hero dice: {texto}")
    with wave.open("salida.wav", "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        voice.synthesize(texto, wav_file)

    audio_data = []
    for audio_bytes in voice.synthesize(texto):
        int_data = np.frombuffer(audio_bytes.audio_int16_bytes, dtype=np.int16)
        audio_data.append(int_data)
    full_audio = np.concatenate(audio_data)
    sd.play(full_audio, samplerate=22050)
    sd.wait()

def limpiar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn').lower()

def inicializar_oido():
    model = vosk.Model("model")
    rec = vosk.KaldiRecognizer(model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
    stream.start_stream()
    return rec, stream, p