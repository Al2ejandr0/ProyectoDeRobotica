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
        """MediaPipe's Face Mesh model is launched to detect 468 facial points"""
        """Minimum threshold for initial detection"""
        """Threshold to maintain tracking between frames"""

        self.mp_drawing = mp.solutions.drawing_utils
        self.posiciones_historial = []
    """Coordinate history for calculating kinematic displacements"""

    def analizar_gesto(self, puntos_faciales):
        nariz = puntos_faciales.landmark[1]
        self.posiciones_historial.append((nariz.x, nariz.y))
        """Use the tip of your nose as the central reference point for the movement"""
        
        if len(self.posiciones_historial) > 15: 
            self.posiciones_historial.pop(0)
        """Maintains a 15-frame sliding window for motion analysis"""
            
        if len(self.posiciones_historial) < 15: 
            return None

        xs = [p[0] for p in self.posiciones_historial]
        ys = [p[1] for p in self.posiciones_historial]
        mov_x, mov_y = max(xs) - min(xs), max(ys) - min(ys)
        """Calculate the amplitude of the movement on the horizontal and vertical axes"""

        if mov_y > 0.05 and mov_y > mov_x: return "si" """Vertical movement"""
        if mov_x > 0.05 and mov_x > mov_y: return "no" """Horizontal movement"""
        return None
    """Gesture classification logic based on the axis of greatest displacement"""

    def procesar_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        gesto = None
        """Color space conversion: OpenCV uses BGR and MediaPipe requires RGB"""
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame, face_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS
                )
                """Render the facial contour mesh over the original frame"""

                gesto = self.analizar_gesto(face_landmarks)
        """Execute the gesture recognition logic for the detected face"""
        
        return results.multi_face_landmarks, gesto
    
if __name__ == "__main__":
    print("hola")