import cv2
import time
import json
import serial  
import threading  
from VISION import DetectorRostro 
from cerebro import cerebro_hero
import voz_y_oido 
from voz_y_oido import speak, clean_text, initialize_hearing
"""Calls the necessary files and libraries to execute the code"""

print("Loading local database...")
from BaseDeDatos import Open_DataBase
db = Open_DataBase()
"""Initialization process"""

try:
    arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
except:
    arduino = None
    """Serial connection with the MegaPi"""

def send_command(com):
    if arduino: 
        arduino.write(com.encode())
        print(f"Command sent to Arduino: {com}")
        """Process for executing robot movement commands"""

def is_affirmative(text):
    positives = ["si", "sí", "claro", "vale", "bueno", "por supuesto", "acepto", "dale", "afirmativo"]
    return any(word in text for word in positives)
"""Program logic to identify affirmative words"""

def clean_audio(stream):
    if stream.get_read_available() > 0:
        stream.read(stream.get_read_available(), exception_on_overflow=False)
        """Cleans the audio buffer to avoid echoes or processing old commands"""

detector = DetectorRostro() 
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
rec, stream, p = initialize_hearing()
"""Camera and audio initialization"""

state = "ANALYZING"
movement_state = "MOVING"
analysis_start_time = 0
search_block_time = 0
last_detection_time = 0
WAIT_THRESHOLD = 5.0
user_name = ""
can_stop = True
"""Program execution states"""

def speak_and_wait(text):
    if len(text) < 3: return
    speak(text)
    while voz_y_oido.ai_speaking:
        time.sleep(0.1)
    time.sleep(0.3)
    clean_audio(stream)
    rec.Reset()
    """Audio and buffer cleaning after speaking"""

print("Hero ready. Starting interaction")
try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        faces_detected, gesture_detected = detector.procesar_frame(frame)
        now = time.time()
        """Visual user detection"""

        if faces_detected:
            last_detection_time = now
            
            if state == "ANALYZING" and now > search_block_time:
                if can_stop and movement_state == "MOVING":
                    print("Face detected: Sending Stop command (D).")
                    send_command('D') 
                    movement_state = "STOPPED_INTERACTION"
                if analysis_start_time == 0: analysis_start_time = now
                if (now - analysis_start_time) >= 2 and not voz_y_oido.ai_speaking:
                    speak_and_wait("Hola mucho gusto, soy Hero, ¿te gustaría conversar conmigo?")
                    state = "WAITING_ACCEPTANCE"
                    analysis_start_time = 0
        else:
            can_stop = True
            if movement_state == "STOPPED_INTERACTION":
                if (now - last_detection_time) > WAIT_THRESHOLD:
                    print("No faces for a long time: Sending Advance command (A).")
                    send_command('A') 
                    movement_state = "MOVING"
                    state = "ANALYZING"
                    """MegaPi commands related to movement and conversation states"""

        phrase = ""
        if not voz_y_oido.pause_hearing.is_set() and stream.get_read_available() > 0:
            data = stream.read(2000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                phrase = clean_text(json.loads(rec.Result()).get('text', ''))
                if phrase: print(f"Heard: {phrase}")
        if phrase != "" and not voz_y_oido.ai_speaking:
            if any(word in phrase for word in ["adios", "chao", "hasta luego", "no quiero mas"]):
                speak_and_wait("Entendido, fue un gusto conversar contigo. ¡Hasta pronto!")
                state = "ANALYZING"
                search_block_time = now + 10
                print("Sending Advance command (A).")
                send_command('A') 
                movement_state = "MOVING"
                can_stop = False 
                continue
            if state == "WAITING_ACCEPTANCE":
                if is_affirmative(phrase) or gesture_detected == "si":
                    speak_and_wait("¡Genial! ¿Cómo te llamas?")
                    state = "WAITING_NAME"
                else:
                    speak_and_wait("Entendido, hasta luego.")
                    state = "ANALYZING"
                    search_block_time = now + 10
                    print("Sending Advance command (A).")
                    send_command('A') 
                    movement_state = "MOVING"
                    can_stop = False
            elif state == "WAITING_NAME":
                parts = phrase.split()
                user_name = parts[-1] if parts else "amigo"
                speak_and_wait(f"Fino {user_name}, conversemos de Venezuela, ¿qué te gustaría saber?")
                state = "FREE_CONVERSATION"
            elif state == "FREE_CONVERSATION":
                response = cerebro_hero(phrase, db)
                speak_and_wait(response)
                """Flow and form of the program's conversation"""

        #cv2.imshow('Hero - WRO 2026', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

finally:
    cap.release()
    cv2.destroyAllWindows()
    if arduino: arduino.close()
    print("System shut down correctly.")
    """Closure of all processes"""