import cv2
import time
import json
import serial  
import threading  
from VISION import DetectorRostro 
from cerebro import cerebro_hero
import voz_y_oido 
from voz_y_oido import hablar, limpiar_texto, inicializar_oido

# --- INICIALIZACIÓN ---
print("🤖 Hero: Cargando base de datos local...")
from BaseDeDatos import abrir_base_datos
db = abrir_base_datos()
# ELIMINADO: db = None (Esto era lo que rompía tu sistema)

try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
except:
    arduino = None

def enviar_comando(com):
    if arduino: arduino.write(com.encode())

def limpiar_audio(stream):
    if stream.get_read_available() > 0:
        stream.read(stream.get_read_available(), exception_on_overflow=False)

detector = DetectorRostro() 
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

rec, stream, p = inicializar_oido()

estado = "ANALIZANDO"
tiempo_inicio_analisis = 0
tiempo_bloqueo_busqueda = 0

def hablar_y_esperar(texto):
    if len(texto) < 3: return
    hablar(texto)
    while voz_y_oido.ia_hablando:
        time.sleep(0.1)
    time.sleep(0.3)
    limpiar_audio(stream)
    rec.Reset()

# --- BUCLE PRINCIPAL ---
print("Hero listo. Iniciando interacción...")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    rostros_detectados, gesto_detectado = detector.procesar_frame(frame)
    ahora = time.time()

    # MÁQUINA DE ESTADOS
    if rostros_detectados:
        enviar_comando('S') 
        if estado == "ANALIZANDO" and ahora > tiempo_bloqueo_busqueda:
            if tiempo_inicio_analisis == 0: tiempo_inicio_analisis = ahora
            if (ahora - tiempo_inicio_analisis) >= 2 and not voz_y_oido.ia_hablando:
                hablar_y_esperar("¡Hola! ¿Te gustaría hablar conmigo?")
                estado = "PREGUNTANDO_INICIO"
                tiempo_inicio_analisis = 0
    else:
        if estado == "ANALIZANDO": enviar_comando('F')

    # PROCESAMIENTO DE VOZ
    frase = ""
    if not voz_y_oido.pausar_oido.is_set() and stream.get_read_available() > 0:
        data = stream.read(2000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            frase = limpiar_texto(json.loads(rec.Result()).get('text', ''))
            if frase: print(f"Escuchado: {frase}")

    if frase != "" and not voz_y_oido.ia_hablando:
        if estado == "PREGUNTANDO_INICIO":
            if "si" in frase or gesto_detectado == "si":
                hablar_y_esperar("Excelente. ¿De qué quieres hablar? Opción 1: Venezuela. Opción 2: Sobre mí.")
                estado = "MENU_PRINCIPAL"
            elif "no" in frase or gesto_detectado == "no":
                hablar_y_esperar("Entendido.")
                estado = "ANALIZANDO"
                tiempo_bloqueo_busqueda = ahora + 6
            else:
                respuesta = cerebro_hero(frase, db) # ¡AQUÍ ES DONDE NECESITABA QUE db NO FUERA NULL!
                hablar_y_esperar(respuesta)
            
        elif estado == "MENU_PRINCIPAL":
            if any(k in frase for k in ["uno", "1", "venezuela"]): 
                hablar_y_esperar("Venezuela es un país hermoso.")
            elif any(k in frase for k in ["dos", "2", "conocerte", "ti"]):
                hablar_y_esperar("Selecciona A, B o C.")
                estado = "SUB_MENU_CONOCEME"
            else:
                respuesta = cerebro_hero(frase, db)
                hablar_y_esperar(respuesta)

        elif estado == "SUB_MENU_CONOCEME":
            if "a" in frase: hablar_y_esperar("Soy Hero, asistente cultural.")
            elif "b" in frase: hablar_y_esperar("Alejandro G, Kamila G y Alejandro G.")
            elif "c" in frase: hablar_y_esperar("Promover la cultura venezolana.")
            estado = "PREGUNTANDO_CONTINUAR"
            
        elif estado == "PREGUNTANDO_CONTINUAR":
            if "si" in frase: 
                hablar_y_esperar("Selecciona A, B o C.")
                estado = "SUB_MENU_CONOCEME"
            else: 
                hablar_y_esperar("Volviendo al inicio.")
                estado = "MENU_PRINCIPAL"

    cv2.imshow('Hero IA - WRO 2026', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release(); cv2.destroyAllWindows()