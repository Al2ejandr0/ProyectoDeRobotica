import cv2
import time
import json
from VISION import DetectorRostro 
from cerebro import cerebro_hero
from voz_y_oido import hablar, limpiar_texto, inicializar_oido, ia_hablando
from BaseDeDatos import buscar_informacion
"""Call all the files in order to run correctly"""

detector = DetectorRostro() 
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
"""The screen resolution of the face detection interface is handled"""

rec, stream, p = inicializar_oido()

estado = "ANALIZANDO"
tiempo_inicio_analisis = 0
tiempo_bloqueo_busqueda = 0
"""Definition of States""" 

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    rostros_detectados, gesto_detectado = detector.procesar_frame(frame)
    ahora = time.time()
    """Concurrent vision processing: Face detection and gesture recognition"""

    if rostros_detectados:
        if estado == "ANALIZANDO":
            if ahora > tiempo_bloqueo_busqueda:
                if tiempo_inicio_analisis == 0: tiempo_inicio_analisis = ahora
                progreso = int(ahora - tiempo_inicio_analisis)
                cv2.putText(frame, f"ESCANEANDO ROSTRO: {progreso}s/2s", (50, 50), 1, 2, (0, 255, 255), 2)
                if progreso >= 2:
                    hablar("¡Hola!. ¿Te gustaría hablar conmigo?")
                    estado = "PREGUNTANDO_INICIO"
                    rec.Reset()
                    """Analysis of the 5-second user for initialization"""

    else:
        estado = "ANALIZANDO"
        tiempo_inicio_analisis = 0
    """State reset if eye contact is lost"""

    frase = ""
    if not ia_hablando and rostros_detectados:
        if stream.get_read_available() > 0:
            if not ia_hablando and rostros_detectados:
                if stream.get_read_available() > 0:
                    data = stream.read(2000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                frase = limpiar_texto(json.loads(rec.Result())['text'])
                if frase: print(f"Escuchado: {frase}")
                """Active listening when not speaking"""

    if estado == "PREGUNTANDO_INICIO":
        if "si" in frase or gesto_detectado == "si":
            hablar("Excelente. ¿De qué quieres hablar? Opción 1: Venezuela. Opción 2: Sobre mí. Opción 3: Salir.")
            estado = "MENU_PRINCIPAL"
        elif "no" in frase or gesto_detectado == "no":
            hablar("Entendido, estaré por aquí si me necesitas.")
            estado = "ANALIZANDO"
            tiempo_inicio_analisis = 0
            tiempo_bloqueo_busqueda = ahora + 5
        elif frase != "":   
            hablar(cerebro_hero(frase))
            """Voice and Gesture Understanding"""

    elif estado == "MENU_PRINCIPAL":
        if any(k in frase for k in ["uno", "1", "venezuela"]):
            hablar("Venezuela es un país hermoso. Pronto te contaré más sobre su historia.")
        elif any(k in frase for k in ["dos", "2", "conocerte", "ti"]):
            hablar("¡Claro! Selecciona: Opción A para saber quién soy, Opción B para conocer a los integrantes, u Opción C para conocer mi propósito.")
            estado = "SUB_MENU_CONOCEME"
        elif any(k in frase for k in ["tres", "3", "salir"]):
            hablar("Reiniciando sistema de búsqueda.")
            estado = "ANALIZANDO"
            tiempo_inicio_analisis = 0
            tiempo_bloqueo_busqueda = ahora + 4
        elif frase != "": 
            hablar(cerebro_hero(frase))
            """Menu Control"""

    elif estado == "SUB_MENU_CONOCEME":
        if any(k in frase for k in ["a", "quien eres", "opcion 1", "hero"]):
            hablar(
                "Hola Soy Hero, un asistente y guía de la cultura venezolana y junto al equipo de innovadores "
                "en serie aspiramos a grandes éxitos en la wro de este año. Mi desarrollo hace uso del lenguaje "
                "de Python con bibliotecas especializadas en inteligencia artificial, como OpenCV, me permite "
                "procesar video en tiempo real, MediaPipe me ayuda a analizar el lenguaje corporal y Vosk para "
                "traducir lo mejor posible las palabras que se me digan en comandos. He sido construido con gran "
                "esmero para ofrecer una experiencia interactiva única y para convertirme de los mejores proyectos "
                "presentados en nuestra categoría."
            )
            estado = "PREGUNTANDO_CONTINUAR"
        elif any(k in frase for k in ["b", "integrantes", "opcion 2", "creadores", "dos", "quienes te hicieron o te costruyecron"]):
            hablar(
                "Excelente, buena pregunta. Para mi construcción estuvieron presentes tres integrantes en especial, "
                "el cual gracias a su ayuda soy lo que soy ahora. En primer lugar, mencionaré a Alejandro Guiñán, "
                "un joven programador de 19 años, estudiante de ingeniería de informática, quien se encargó de la "
                "parte compleja de los modelados y diseños gráficos de las ilustraciones. En segunda instancia, "
                "Kamila Gómez, de 19 años, perteneciente a ingeniería en sistemas, fue pieza clave para el armado y "
                "ensamblaje de toda mi estructura; ella construyó todo lo que es mi cuerpo. Por último se encuentra "
                "Alejandro González, joven de 19 años y también estudiante de ingeniería en sistemas. Su rol se basó "
                "en desarrollar lo que es mi cerebro, es decir, la IA y la implementación de esta en mis componentes."
            )
            estado = "PREGUNTANDO_CONTINUAR"
        elif any(k in frase for k in ["c", "proposito", "opcion 3", "mision"]):
            hablar(
                "Busco crear experiencias memorables para quienes exploran la historia y cultura venezolana. "
                "Mi misión es difundir nuestros relatos épicos y la esencia de nuestra gente, promoviendo el "
                "interés global por nuestra identidad a través de una narrativa que conecta el pasado con lo que somos hoy."
            )
            estado = "PREGUNTANDO_CONTINUAR"
        elif any(k in frase for k in ["salir", "volver"]):
            estado = "MENU_PRINCIPAL"
            
    elif estado == "PREGUNTANDO_CONTINUAR":
        if "si" in frase or gesto_detectado == "si":
            hablar("¿Deseas saber algo más sobre nosotros? Puedes elegir la opción A, B o C.")
            estado = "SUB_MENU_CONOCEME"
        elif "no" in frase or gesto_detectado == "no" or "salir" in frase:
            hablar("Volviendo al menú principal.")
            estado = "MENU_PRINCIPAL"
        elif frase != "": 
            hablar(cerebro_hero(frase))

    cv2.imshow('Hero IA - WRO 2026', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break
    """GUI Rendering and safe program termination"""

cap.release()
cv2.destroyAllWindows()
stream.stop_stream()
p.terminate()
"""Resource deallocation and hardware stream shutdown"""