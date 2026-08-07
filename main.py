import threading  
import re 
import cv2        
import numpy as np  
import random     
import time
import json
import serial  

from ui import HeroUI
from cerebro import cerebro_hero

# Inicialización de la Interfaz
ui = HeroUI()
ui.running = True

def limpiar_texto(texto):
    """Limpia el Markdown y caracteres especiales para que la voz sea natural"""
    texto = re.sub(r'[\*\#\-]', '', texto)
    texto = re.sub(r'\n+', ' ', texto)
    return " ".join(texto.split())

# =====================================================================
# FUNCIÓN DE VISIÓN: DETECTA GORRAS/SOMBREROS Y COLOR DE ROPA
# =====================================================================
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def obtener_halago_real(frame_compartido):
    """Analiza la imagen de manera segura sin bloquear el hardware"""
    try:
        # SALVAVIDAS: Si la interfaz aún no ha guardado un frame, evita el crash
        if frame_compartido is None:
            print("Vision: Frame compartido no disponible aún.")
            return "una energía excelente"
            
        frame = frame_compartido
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        alto, ancho, _ = frame.shape
        
        # Buscamos el rostro para usarlo de referencia espacial
        rostros = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in rostros:
            # 1. INTENTAR DETECTAR GORRA
            ymin, ymax = max(0, int(y - (h * 0.25))), y
            xmin, xmax = x + int(w * 0.2), x + int(w * 0.8)
            if ymin < y: 
                muestra_gorra = frame[ymin:ymax, xmin:xmax]
                if muestra_gorra.size > 0:
                    hsv_gorra = cv2.cvtColor(muestra_gorra, cv2.COLOR_BGR2HSV)
                    promedio_gorra = np.mean(hsv_gorra, axis=(0, 1))
                    
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
        
        if muestra_camisa.size > 0:
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
    import voz_y_oido 
    from voz_y_oido import stream, speak, clean_text, initialize_hearing
    from BaseDeDatos import Open_DataBase

    print("Loading local database...")
    db = Open_DataBase()

    try:
        arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    except Exception as e:
        print(f"Arduino connection skipped: {e}")
        arduino = None

    def send_command(com):
        if arduino: 
            try:
                arduino.write(com.encode())
                print(f"Command sent to Arduino: {com}")
            except Exception as e:
                print(f"Error sending command to Arduino: {e}")

    def is_affirmative(text):
        positives = ["si", "sí", "claro", "vale", "bueno", "por supuesto", "acepto", "dale", "afirmativo"]
        return any(word in text for word in positives)

    def clean_audio(stream_obj):
        if stream_obj.get_read_available() > 0:
            stream_obj.read(stream_obj.get_read_available(), exception_on_overflow=False)

    rec = initialize_hearing()

    state = "ANALYZING"
    movement_state = "MOVING"
    analysis_start_time = 0
    search_block_time = 0
    last_detection_time = 0
    WAIT_THRESHOLD = 5.0
    user_name = ""
    can_stop = True
    contexto_actual = None 

    def speak_and_wait(text):
        ui.set_ui_data("status", "Hablando")
        if not text or len(text) < 2: 
            return
        texto_limpio = limpiar_texto(text)
        ui.mouth_opened = True
        speak(texto_limpio)
        ui.mouth_opened = False
        while voz_y_oido.ai_speaking:
            time.sleep(0.1)
        time.sleep(0.5)
        clean_audio(stream)
        rec.Reset()

    print("Hero ready. Starting interaction")
    ui.set_ui_data("status", "En Movimiento")
    
    try:
        while ui.running:
            ret = ui.rendercam
            if not ret: 
                time.sleep(0.03) # Evita consumo innecesario de CPU
                continue
                
            faces_detected = ui.faces_detected
            now = time.time()

            if faces_detected:
                last_detection_time = now
                
                if state == "ANALYZING" and now > search_block_time:
                    if movement_state == "MOVING":
                        if can_stop:
                            print("Face detected: Sending Stop command (D).")
                            send_command('D') 
                            movement_state = "STOPPED_INTERACTION"
                        elif ui.mod_delta_pos > 100:
                            print("CAN STOP!")
                            can_stop = True
                    if analysis_start_time == 0: 
                        analysis_start_time = now
                    if (now - analysis_start_time) >= 2 and not voz_y_oido.ai_speaking:
                        
                        # Extraemos el frame de la UI
                        frame_actual = ui.cap.read(0)
                        contexto_actual = obtener_halago_real(frame_actual[1])
                        
                        speak_and_wait("Hola mucho gusto, soy Hero, ¿te gustaría conversar conmigo?")
                        state = "WAITING_ACCEPTANCE"
                        analysis_start_time = 0
                        ui.set_ui_data("status", "Esperando Respuesta")
            else:
                can_stop = True
                if movement_state == "STOPPED_INTERACTION" and (now - last_detection_time) > WAIT_THRESHOLD:
                    print("No faces for a long time: Sending Advance command (A).")
                    send_command('A') 
                    movement_state = "MOVING"
                    state = "ANALYZING"
                    contexto_actual = None 
                    ui.set_ui_data("status", "En Movimiento")

            phrase = ""
            if not voz_y_oido.ai_speaking:
                if stream.get_read_available() > 0:
                    data = stream.read(2000, exception_on_overflow=False)
                    if voz_y_oido.clarity(data, umbral=300):
                        if rec.AcceptWaveform(data):
                            phrase = clean_text(json.loads(rec.Result()).get('text', ''))
                            if phrase: 
                                print(f"Heard: {phrase}")
            
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
                    if is_affirmative(phrase):
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
                    
                    # Llamada a Groq/Ollama con contexto visual
                    try:
                        respuesta_saludo = cerebro_hero(phrase, db, contexto_visual=contexto_actual)
                    except Exception as e:
                        print(f"Error calling cerebro_hero: {e}")
                        respuesta_saludo = f"¡Un placer conocerte, {user_name}! Qué bueno tenerte por aquí."
                        
                    speak_and_wait(respuesta_saludo)
                    
                    # Limpieza de memoria visual para el resto de la interacción
                    contexto_actual = None 
                    state = "FREE_CONVERSATION"
                    ui.set_ui_data("status", "Esperando Respuesta")
                    
                elif state == "FREE_CONVERSATION":
                    try:
                        response = cerebro_hero(phrase, db)
                    except Exception as e:
                        print(f"Error calling cerebro_hero: {e}")
                        response = "Disculpa mi pana, me distraje un segundo. ¿Me lo puedes repetir?"
                        
                    speak_and_wait(response)
                    ui.set_ui_data("status", "Esperando Respuesta")
            
            # Evita saturar el procesador de la Pi
            time.sleep(0.01)

    finally:
        if hasattr(ui, 'cap') and ui.cap.isOpened():
            ui.cap.release()
        if arduino: 
            arduino.close()
        print("System shut down correctly.")

main_thread = threading.Thread(target=main)
main_thread.daemon = True 
main_thread.start()

ui.run()
quit(0)