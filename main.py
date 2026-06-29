import threading  
from ui import HeroUI
import re 
import cv2        
import numpy as np  
import random     

ui = HeroUI()
ui.running = True
from cerebro import cerebro_hero
"""Calls the necessary files and libraries to execute the code"""

def limpiar_texto(texto):
    """Limpia el Markdown y caracteres especiales para que la voz sea natural"""
    texto = re.sub(r'[\*\#\-]', '', texto)
    texto = re.sub(r'\n+', ' ', texto)
    return " ".join(texto.split())

# =====================================================================
# FUNCIÓN DE VISIÓN: DETECTA GORRAS/SOMBREROS Y COLOR DE ROPA
# =====================================================================
# Cargamos únicamente el detector de rostros
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def obtener_halago_real(cap):
    """Analiza la imagen para detectar gorras o color de ropa"""
    try:
        ret, frame = cap.read()
        if not ret:
            return "una energía excelente"
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        alto, ancho, _ = frame.shape
        
        # Buscamos el rostro para usarlo de referencia espacial
        rostros = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in rostros:
            # 1. INTENTAR DETECTAR GORRA (Muestreamos la zona arriba de la frente)
            ymin, ymax = max(0, int(y - (h * 0.25))), y
            xmin, xmax = x + int(w * 0.2), x + int(w * 0.8)
            if ymin < y: # Si hay espacio arriba de la cabeza en el frame
                muestra_gorra = frame[ymin:ymax, xmin:xmax]
                hsv_gorra = cv2.cvtColor(muestra_gorra, cv2.COLOR_BGR2HSV)
                promedio_gorra = np.mean(hsv_gorra, axis=(0, 1))
                
                # Si el color de arriba es muy saturado, detecta gorra
                if promedio_gorra[1] > 90: 
                    print("Vision: ¡Gorra o accesorio en la cabeza detectado!")
                    return random.choice([
                        "esa gorra o accesorio en tu cabeza que te da tremendo flow",
                        "el gran estilo de lo que llevas en la cabeza hoy"
                    ])

        # 2. FALLBACK: SI NO HAY GORRA, ANALIZAMOS EL COLOR DE LA CAMISA
        ymin_c, ymax_c = int(alto * 0.7), int(alto * 0.9)
        xmin_c, xmax_c = int(ancho * 0.4), int(ancho * 0.6)
        muestra_camisa = frame[ymin_c:ymax_c, xmin_c:xmax_c]
        
        hsv_camisa = cv2.cvtColor(muestra_camisa, cv2.COLOR_BGR2HSV)
        promedio_hsv = np.mean(hsv_camisa, axis=(0, 1))
        
        hue, sat, val = promedio_hsv[0], promedio_hsv[1], promedio_hsv[2]
        
        if sat < 45 and val > 180:
            return "esa camisa blanca que transmite una vibra impecable"
        elif val < 55:
            return "tu outfit oscuro que te da un toque de elegancia serio"
        elif (0 <= hue < 10) or (160 <= hue <= 180):
            return "ese color rojo intenso de tu ropa que demuestra mucha seguridad"
        elif 35 <= hue < 85:
            return "ese tono verde de tu ropa que se ve sumamente fresco"
        elif 85 <= hue < 140:
            return "ese color azul de tu ropa que te combina excelente"
        
        return "el excelente estilo de la ropa que cargas hoy"
        
    except Exception as e:
        print(f"Error en visión de halagos: {e}")
        return "una energía excelente"

def main():

    import time
    from VISION import DetectorRostro 
    import cv2
    import json
    import serial  
    import voz_y_oido 
    from voz_y_oido import stream, speak, clean_text, initialize_hearing
    from BaseDeDatos import Open_DataBase

    print("Loading local database...")
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

    cap = ui.cap
    rec = initialize_hearing()
    """Camera and audio initialization"""

    state = "ANALYZING"
    movement_state = "MOVING"
    analysis_start_time = 0
    search_block_time = 0
    last_detection_time = 0
    WAIT_THRESHOLD = 5.0
    user_name = ""
    can_stop = True
    contexto_actual = None 
    """Program execution states"""


    def speak_and_wait(text):
        ui.set_ui_data("status", "Hablando")
        if len(text) < 3: return
        
        texto_limpio = limpiar_texto(text)
        
        ui.mouth_opened = True
        speak(texto_limpio)
        while voz_y_oido.ai_speaking:
            time.sleep(0.1)
        ui.mouth_opened = False
        time.sleep(0.5)
        clean_audio(stream)
        rec.Reset()
        """Audio and buffer cleaning after speaking"""

    print("Hero ready. Starting interaction")
    ui.set_ui_data("status", "En Movimiento")
    try:
        while ui.running and cap.isOpened():
            ret = ui.rendercam
            if not ret: break
            faces_detected = ui.faces_detected
            gesture_detected = ui.gesture_detected
            now = time.time()
            """Visual user detection"""

            if faces_detected:
                last_detection_time = now
                
                # --- Lógica de centrado del Servo ---
                if movement_state == "STOPPED_INTERACTION":
                    face_x = getattr(ui, 'face_x', 0.5) 
                    tolerancia = 0.07 
                    if face_x < (0.5 - tolerancia):
                        ui.eyes_offset = 16
                        send_command('L')
                    elif face_x > (0.5 + tolerancia):
                        ui.eyes_offset = -16
                        send_command('R')
                
                if state == "ANALYZING" and now > search_block_time:
                    if can_stop and movement_state == "MOVING":
                        print("Face detected: Sending Stop command (D).")
                        send_command('D') 
                        movement_state = "STOPPED_INTERACTION"
                    if analysis_start_time == 0: analysis_start_time = now
                    if (now - analysis_start_time) >= 2 and not voz_y_oido.ai_speaking:
                        
                        # AL CAPTURAR A LA PERSONA, DISPARAMOS LA CÁMARA REAL:
                        contexto_actual = obtener_halago_real(cap)
                        
                        speak_and_wait("Hola mucho gusto, soy Hero, ¿te gustaría conversar conmigo?")
                        state = "WAITING_ACCEPTANCE"
                        analysis_start_time = 0
                        ui.set_ui_data("status", "Esperando Respuesta")
            else:
                can_stop = True
                if movement_state == "STOPPED_INTERACTION":
                    if (now - last_detection_time) > WAIT_THRESHOLD:
                        print("No faces for a long time: Sending Advance command (A).")
                        send_command('A') 
                        movement_state = "MOVING"
                        state = "ANALYZING"
                        contexto_actual = None 
                        ui.set_ui_data("status", "En Movimiento")
                        """MegaPi commands related to movement and conversation states"""

            phrase = ""
            if not voz_y_oido.ai_speaking:
                if stream.get_read_available() > 0:
                    data = stream.read(2000, exception_on_overflow=False)
                    if voz_y_oido.clarity(data, umbral=300):
                        if rec.AcceptWaveform(data):
                            phrase = clean_text(json.loads(rec.Result()).get('text', ''))
                            if phrase: print(f"Heard: {phrase}")
            if phrase != "":
                ui.set_ui_data("status", "Pensando")
                if any(word in phrase for word in ["adios", "chao", "hasta luego", "no quiero mas"]):
                    speak_and_wait("Entendido, fue un gusto conversar contigo. ¡Hasta pronto!")
                    state = "ANALYZING"
                    search_block_time = now + 10
                    print("Sending Advance command (A).")
                    send_command('A') 
                    movement_state = "MOVING"
                    can_stop = False 
                    contexto_actual = None 
                    ui.set_ui_data("status", "En Movimiento")
                    continue
                if state == "WAITING_ACCEPTANCE":
                    if is_affirmative(phrase) or gesture_detected == "si":
                        speak_and_wait("¡Genial! ¿Cómo te llamas?")
                        state = "WAITING_NAME"
                        ui.set_ui_data("status", "Esperando Respuesta")
                    else:
                        speak_and_wait("Entendido, hasta luego.")
                        state = "ANALYZING"
                        search_block_time = now + 10
                        print("Sending Advance command (A).")
                        send_command('A') 
                        movement_state = "MOVING"
                        can_stop = False
                        contexto_actual = None 
                        ui.set_ui_data("status", "En Movimiento")
                elif state == "WAITING_NAME":
                    parts = phrase.split()
                    user_name = parts[-1] if parts else "amigo"
                    
                    respuesta_saludo = cerebro_hero(phrase, db, contexto_visual=contexto_actual)
                    speak_and_wait(respuesta_saludo)
                    
                    # --- AQUÍ LIMPIAMOS LA MEMORIA VISUAL GLOBAL ---
                    contexto_actual = None 
                    
                    state = "FREE_CONVERSATION"
                    ui.set_ui_data("status", "Esperando Respuesta")
                elif state == "FREE_CONVERSATION":
                    response = cerebro_hero(phrase, db)
                    speak_and_wait(response)
                    ui.set_ui_data("status", "Esperando Respuesta")
                    """Flow and form of the program's conversation"""

    finally:
        cap.release()
        if arduino: arduino.close()
        print("System shut down correctly.")
        """Closure of all processes"""

main_thread = threading.Thread(target=main)
main_thread.start()
ui.run()
quit(0)