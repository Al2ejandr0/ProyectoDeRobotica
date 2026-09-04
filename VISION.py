import cv2
import mediapipe as mp

class DetectorRostro:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=5, 
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        """Volvemos a FaceMesh para obtener todos los puntos de la malla facial y se detecta varias caras para luego filtrar la más cercana"""
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.history_positions = []
        """Utilidades para dibujar la malla en pantalla"""

    def procesar_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        pos = 0.0, 0.0, 0.0
        rostro_detectado = False
        if results.multi_face_landmarks:
            rostro_detectado = True
            rostro_principal = None
            max_area = 0
            for face_landmarks in results.multi_face_landmarks:
                xs = [lm.x for lm in face_landmarks.landmark]
                ys = [lm.y for lm in face_landmarks.landmark]
                area = (max(xs) - min(xs)) * (max(ys) - min(ys))
                if area > max_area:
                    max_area = area
                    rostro_principal = face_landmarks
                    """ Se extrae las coordenadas X e Y relativas para calcular el ancho y alto del rostro y se busca la cara que ocupe mayor área en pantalla """

            if rostro_principal:
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=rostro_principal,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                nariz = rostro_principal.landmark[1]
                pos = nariz.x * 32768, nariz.y * 32768, nariz.z * 32768
                """Enfoque en el rostro pirncipal y construcción de la malla facial"""

        return rostro_detectado, pos