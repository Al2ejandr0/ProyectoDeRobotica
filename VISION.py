import cv2
import mediapipe as mp

class DetectorRostro:
    def __init__(self):
        # Volvemos a FaceMesh para obtener todos los puntos de la malla facial
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=5, # Detectamos varias caras para luego filtrar la más cercana
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Utilidades para dibujar la malla en pantalla
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.history_positions = []

    def procesar_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        
        gesto = None
        rostro_detectado = False

        if results.multi_face_landmarks:
            rostro_detectado = True
            
            # 1. EL FILTRO MÁGICO (Target Lock):
            # Buscamos la cara que ocupe mayor área en pantalla (la persona más cercana a Hero)
            rostro_principal = None
            max_area = 0
            
            for face_landmarks in results.multi_face_landmarks:
                # Extraemos las coordenadas X e Y relativas para calcular el ancho y alto del rostro
                xs = [lm.x for lm in face_landmarks.landmark]
                ys = [lm.y for lm in face_landmarks.landmark]
                area = (max(xs) - min(xs)) * (max(ys) - min(ys))
                
                if area > max_area:
                    max_area = area
                    rostro_principal = face_landmarks

            # 2. Trabajamos EXCLUSIVAMENTE con 'rostro_principal'
            if rostro_principal:
                # Dibujamos la malla facial (los puntitos y líneas que querías recuperar)
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=rostro_principal,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                nariz = rostro_principal.landmark[1]
                gesto = self.analizar_gesto(nariz.x, nariz.y)

        return rostro_detectado, gesto

    def analizar_gesto(self, x, y):
        # Prevención de salto fantasma por si otra persona se acerca de golpe
        if self.history_positions:
            ultima_x, ultima_y = self.history_positions[-1]
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