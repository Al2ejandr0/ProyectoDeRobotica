import cv2
import mediapipe as mp

class DetectorRostro:
    def __init__(self):
        # Usamos FaceDetection (6 puntos clave, ultra optimizado para Raspberry Pi)
        self.mp_face = mp.solutions.face_detection
        self.face_detection = self.mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)
        self.history_positions = []

    def procesar_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(frame_rgb)
        
        gesto = None
        rostro_detectado = False

        if results.detections:
            rostro_detectado = True
            
            # 1. EL FILTRO MÁGICO (Target Lock):
            # De todas las caras detectadas, busca la que tenga el Bounding Box con mayor área (ancho * alto)
            rostro_principal = max(
                results.detections, 
                key=lambda d: d.location_data.relative_bounding_box.width * d.location_data.relative_bounding_box.height
            )

            # 2. Trabajamos EXCLUSIVAMENTE con 'rostro_principal' (Ignoramos a los demás)
            bboxC = rostro_principal.location_data.relative_bounding_box
            h, w, c = frame.shape
            bbox = (int(bboxC.xmin * w), int(bboxC.ymin * h), 
                    int(bboxC.width * w), int(bboxC.height * h))
            
            # Dibujamos su recuadro en Verde
            cv2.rectangle(frame, bbox, (0, 255, 0), 3)
            
            # Dibujamos SUS 6 puntos clave
            for i in range(6): 
                kp = self.mp_face.get_key_point(rostro_principal, i)
                x_kp = int(kp.x * w)
                y_kp = int(kp.y * h)
                cv2.circle(frame, (x_kp, y_kp), 5, (0, 0, 255), -1)
            
            # Calculamos el gesto SOLO de esta persona (Keypoint 2 es la punta de la nariz)
            nariz = self.mp_face.get_key_point(rostro_principal, self.mp_face.FaceKeyPoint.NOSE_TIP)
            gesto = self.analizar_gesto(nariz.x, nariz.y)

        return rostro_detectado, gesto

    def analizar_gesto(self, x, y):
        # Prevención de salto fantasma: si cambia de una persona a otra bruscamente, limpiamos historial
        if self.history_positions:
            ultima_x, ultima_y = self.history_positions[-1]
            # Si la nariz "salta" más de un 25% del tamaño de la pantalla en un frame, es otra persona
            if abs(x - ultima_x) > 0.25 or abs(y - ultima_y) > 0.25:
                self.history_positions.clear()

        self.history_positions.append((x, y))
        if len(self.history_positions) > 15: self.history_positions.pop(0)
        if len(self.history_positions) < 15: return None

        xs = [p[0] for p in self.history_positions]
        ys = [p[1] for p in self.history_positions]
        mov_x, mov_y = max(xs) - min(xs), max(ys) - min(ys)
        
        if mov_y > 0.05 and mov_y > mov_x: return "si"
        if mov_x > 0.05 and mov_x > mov_y: return "no"
        return None