import cv2
import mediapipe as mp
import time

class DetectorRostro:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.posiciones_historial = []

    def analizar_gesto(self, puntos_faciales):
        nariz = puntos_faciales.landmark[1]
        self.posiciones_historial.append((nariz.x, nariz.y))
        
        if len(self.posiciones_historial) > 15: 
            self.posiciones_historial.pop(0)
            
        if len(self.posiciones_historial) < 15: 
            return None

        xs = [p[0] for p in self.posiciones_historial]
        ys = [p[1] for p in self.posiciones_historial]
        mov_x, mov_y = max(xs) - min(xs), max(ys) - min(ys)

        if mov_y > 0.05 and mov_y > mov_x: return "si"
        if mov_x > 0.05 and mov_x > mov_y: return "no"
        return None

    def procesar_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        gesto = None
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, face_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS
                )
                gesto = self.analizar_gesto(face_landmarks)
        
        return results.multi_face_landmarks, gesto
    
if __name__ == "__main__":
    print("hola")