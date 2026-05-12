import cv2
import mediapipe as mp
import vosk
import json
import pyaudio
import os
import pyttsx3
import threading
import time
import unicodedata

# --- 1. CONFIGURACIÓN LANGCHAIN ---
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from langchain_openai import ChatOpenAI

# Si usas un proveedor como Together AI o DashScope para Qwen:
llm_qwen = ChatOpenAI(
    base_url="https://api.together.xyz/v1", # O la URL del proveedor de Qwen
    api_key="TU_LLAVE_DE_QWEN",
    model_name="Qwen/Qwen2.5-72B-Instruct" # El modelo específico
)

def cerebro_qwen(pregunta_usuario):
    # La misma lógica que ya usas, pero con el cerebro de Qwen
    mensajes = [
        SystemMessage(content="Eres Hero, experto en ingeniería y cultura..."),
        HumanMessage(content=pregunta_usuario)
    ]
    return llm_qwen.invoke(mensajes).content

# RECUERDA: Coloca tu llave de OpenAI aquí
os.environ["OPENAI_API_KEY"] = "TU_LLAVE_AQUI"

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

def cerebro_langchain(pregunta_usuario):
    """Función para que Hero responda cualquier cosa fuera del guion"""
    instrucciones = (
        "Eres Hero, una asistente de la cultura venezolana para la WRO 2026. "
        "Fuiste creada por Alejandro Guiñán, Kamila Gómez y Alejandro González. "
        "Responde de forma breve, amable y con identidad venezolana."
    )
    mensajes = [
        SystemMessage(content=instrucciones),
        HumanMessage(content=pregunta_usuario)
    ]
    try:
        respuesta = llm.invoke(mensajes)
        return respuesta.content
    except:
        return "Disculpa, tuve un pequeño problema procesando eso. ¿Podemos intentar con las opciones del menú?"

# --- 2. FUNCIONES DE VOZ Y LIMPIEZA ---
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
    print(f"IA: {texto}")
    hilo_voz = threading.Thread(target=proceso_hablar, args=(texto,))
    hilo_voz.start()

def limpiar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn').lower()

# --- 3. CONFIGURACIÓN TÉCNICA ---
if not os.path.exists("model"):
    print("Falta la carpeta 'model'"); exit()
model = vosk.Model("model")
rec = vosk.KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
stream.start_stream()
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# --- 4. VARIABLES DE ESTADO Y GESTOS ---
estado = "ANALIZANDO"
tiempo_inicio_analisis = 0
tiempo_bloqueo_busqueda = 0 
posiciones_historial = []

def analizar_gesto(puntos_faciales):
    global posiciones_historial
    nariz = puntos_faciales.landmark[1]
    posiciones_historial.append((nariz.x, nariz.y))
    if len(posiciones_historial) > 15: posiciones_historial.pop(0)
    if len(posiciones_historial) < 15: return None
    xs = [p[0] for p in posiciones_historial]
    ys = [p[1] for p in posiciones_historial]
    mov_x, mov_y = max(xs) - min(xs), max(ys) - min(ys)
    if mov_y > 0.05 and mov_y > mov_x: return "si"
    if mov_x > 0.05 and mov_x > mov_y: return "no"
    return None

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# --- 5. BUCLE PRINCIPAL ---
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)
    ahora = time.time()
    gesto_detectado = None

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            mp_drawing.draw_landmarks(frame, face_landmarks, mp_face_mesh.FACEMESH_CONTOURS)
            gesto_detectado = analizar_gesto(face_landmarks)
        
        if estado == "ANALIZANDO":
            if ahora > tiempo_bloqueo_busqueda:
                if tiempo_inicio_analisis == 0: tiempo_inicio_analisis = ahora
                progreso = int(ahora - tiempo_inicio_analisis)
                cv2.putText(frame, f"ANALIZANDO: {progreso}s/5s", (50, 50), 1, 2, (0, 255, 255), 2)
                if progreso >= 5:
                    hablar("Analisis listo. ¿Te gustaria hablar conmigo?")
                    estado = "PREGUNTANDO_INICIO"
                    rec.Reset()
    else:
        estado = "ANALIZANDO"
        tiempo_inicio_analisis = 0

    if not ia_hablando and results.multi_face_landmarks:
        frase = ""
        if stream.get_read_available() > 0:
            data = stream.read(2000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                frase = limpiar_texto(json.loads(rec.Result())['text'])
                if frase: 
                    print(f"Escuchado: {frase}")
                    ultimo_tiempo_voz = ahora 

        # --- LÓGICA DE ESTADOS ---
        if estado == "PREGUNTANDO_INICIO":
            cv2.putText(frame, " SI O NO", (50, 80), 1, 2, (255, 255, 0), 2)
            if "si" in frase or gesto_detectado == "si":
                hablar("Excelente, de ¿cuál de las siguientes opciones te gustaría hablar?. Opción uno. Acerca de Venezuela. Opción dos. Más información sobre mí. O la opción tres. Acabar y salir de esta conversación")
                estado = "MENU_PRINCIPAL"
            elif "no" in frase or gesto_detectado == "no":
                hablar("Fue un placer hablar con usted, espero que tenga un buen día.")
                estado = "ANALIZANDO"; tiempo_inicio_analisis = 0; tiempo_bloqueo_busqueda = ahora + 5

        elif estado == "MENU_PRINCIPAL":
            cv2.putText(frame, "MENU: 1, 2, 3", (50, 80), 1, 2, (0, 255, 0), 2)
            if any(k in frase for k in ["uno", "1", "venezuela"]):
                hablar("Opcion en desarrollo. Selecciona otra.")
            elif any(k in frase for k in ["dos", "2", "conocerte", "conocer", "opcion", "ti"]):
                hablar("Dime, cuál de las siguientes opciones llama más tú atención. Opción A. ¿Quién soy?. Opción B. Acerca del equipo. Opción C. Mi Proposito. Y Por Ultimo la Opción D. Salir o finaliza")
                estado = "SUB_MENU_CONOCEME"
            elif any(k in frase for k in ["tres", "3", "finalizar", "acabar", "terminar", "salir"]):
                hablar("Entendido. Reiniciando protocolo de busqueda.")
                estado = "ANALIZANDO"; tiempo_inicio_analisis = 0; tiempo_bloqueo_busqueda = ahora + 4
            elif frase != "":
                respuesta_ia = cerebro_langchain(frase)
                hablar(respuesta_ia)

        elif estado == "SUB_MENU_CONOCEME":
            cv2.putText(frame, "A, B, C o D", (50, 80), 1, 2, (255, 255, 255), 2)
            opcion_valida = False
            
            # OPCIÓN A: QUIEN SOY (Texto de la imagen)
            if any(k in frase for k in ["a", "quien soy", "quien eres", "acerca de mi"]):
                texto_a = (
                    "Hola Soy Hero, un asistente y guía de la cultura venezolana y junto al equipo de innovadores "
                    "en serie aspiramos a grandes éxitos en la wro de este año. Mi desarrollo hace uso del lenguaje "
                    "de Python con bibliotecas especializadas en inteligencia artificial, como OpenCV, me permite "
                    "procesar video en tiempo real, MediaPipe, me ayuda a analizar el lenguaje corporal y Vosk para "
                    "traduce lo mejor posible las palabras que se me digan en comandos. He sido construido con gran "
                    "esmero para ofrecer una experiencia interactiva única y para convertirme de los mejores proyectos "
                    "presentados en nuestra categoría. ... ¿Deseas seguir conociendo más sobre mí?"
                )
                hablar(texto_a)
                opcion_valida = True
            
            # OPCIÓN B: INTEGRANTES (Texto de la imagen)
            elif any(k in frase for k in ["b", "equipo", "integrantes"]):
                texto_b = (
                    "Excelente, buena pregunta. Para mi construcción estuvieron presentes tres integrantes en especial, "
                    "el cual gracias a su ayuda soy lo que soy ahora y lo que llegaré a ser en un futuro. En primer lugar, "
                    "mencionaré a Alejandro Guiñán, es un joven programador con talentos de 19 años, quien es estudiante "
                    "en ingeniería de informática, actualmente se encuentra en el cuarto semestre, pasando hacia al quinto "
                    "y él se encargo de la parte compleja de los modelados y diseños gráficos de las ilustraciones que "
                    "pueden apreciar. En segunda instancia, menciono a Kamila Gómez, ella es una mujer de 19 años, quien "
                    "es perteneciente a la carrera de ingeniería en sistemas, que está cursando por el cuarto semestre, "
                    "yendo para el quinto y fue pieza clave para el armado y ensamblaje de toda mi estructura, en otras "
                    "palabras, ella construyo todo lo que es mi cuerpo. Por ultimo se encuentra Alejandro González, un joven "
                    "de 19 años que también es estudiante de ingeniería en sistemas que se encuentra cursando el mismo "
                    "semestre que sus compañeros. Su rol en el equipo se basó en desarrollar lo que es mi cerebro, es decir, "
                    "todo lo que es el asistente y la implementación de esto en los componentes que me componen para mi "
                    "correcta funcionalidad. ... ¿Deseas seguir conociendo más sobre mí?"
                )
                hablar(texto_b)
                opcion_valida = True
            
            # OPCIÓN C: PROPÓSITO
            elif any(k in frase for k in ["c", "proposito", "meta"]):
                texto_c = (
                    "Mi propósito es ser una herramienta innovadora que facilite el aprendizaje de la historia y "
                    "tradiciones de Venezuela, utilizando tecnología de última generación para conectar a las personas "
                    "con sus raíces de una manera interactiva y moderna. ... ¿Deseas seguir conociendo más sobre mí?"
                )
                hablar(texto_c)
                opcion_valida = True
            
            if opcion_valida:
                estado = "PREGUNTANDO_CONTINUAR"
                rec.Reset()
            elif any(k in frase for k in ["d", "salir", "finalizar", "terminar"]):
                hablar("Finalizando sesion. Regresando al estado de escaneo.")
                estado = "ANALIZANDO"; tiempo_inicio_analisis = 0; tiempo_bloqueo_busqueda = ahora + 4
            elif frase != "":
                respuesta_ia = cerebro_langchain(frase)
                hablar(respuesta_ia)

        elif estado == "PREGUNTANDO_CONTINUAR":
            cv2.putText(frame, "CONTINUAR? SI/NO", (50, 80), 1, 2, (0, 255, 255), 2)
            if "si" in frase or gesto_detectado == "si":
                hablar("Dime que otra opción llama tú atención. Opción A. ¿Quién soy?. Opción B. Acerca del equipo o Opción C. Mi Proposito.")
                estado = "SUB_MENU_CONOCEME"
                rec.Reset()
            elif "no" in frase or gesto_detectado == "no":
                hablar("Volvamos al menú principal.")
                estado = "MENU_PRINCIPAL"
                rec.Reset()

    cv2.imshow('Hero IA - LangChain Ready', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release(); cv2.destroyAllWindows(); stream.stop_stream(); p.terminate()