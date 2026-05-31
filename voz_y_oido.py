import subprocess
import threading
import pyaudio
import vosk
import unicodedata
import wave
import os
import sounddevice as sd
import numpy as np
from piper import PiperVoice

MODEL = "piper/es_ES-davefx-medium.onnx"
CONFIG = "piper/es_ES-davefx-medium.onnx.json"
"""Path configuration for the TTS (Text-to-Speech) engine"""

ai_speaking = False
pause_hearing = threading.Event()
"""Global state flags for controlling audio flow and thread synchronization"""

voice = PiperVoice.load(MODEL, config_path=CONFIG)
"""Load the Piper voice model for high-quality speech synthesis"""

def speak(text):
    print(f"Hero dice: {text}")
    """Synthesizes text into audio and plays it through the speakers"""
    
    with wave.open("salida.wav", "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        voice.synthesize(text, wav_file)
        """Save the generated speech to a temporary .wav file"""

    audio_data = []
    for audio_bytes in voice.synthesize(text):
        int_data = np.frombuffer(audio_bytes.audio_int16_bytes, dtype=np.int16)
        audio_data.append(int_data)
        """Process and play the synthesized audio in memory using NumPy"""
    
    full_audio = np.concatenate(audio_data)
    sd.play(full_audio, samplerate=22050)
    sd.wait() 
    """Ensure audio playback finishes before proceeding"""

def clean_text(text):
    if not text: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()
"""Normalizes text by removing accents and converting to lowercase"""

def initialize_hearing():
    model = vosk.Model("model")
    rec = vosk.KaldiRecognizer(model, 16000)
    """Initialize the speech-to-text model"""
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
    stream.start_stream()
    """Configuring the audio input flow from the microphone"""
    
    return rec, stream, p