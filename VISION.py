import cv2
import mediapipe as mp
import time

class DetectorRostro:
    def __init__(self):
        #MediaPipe's Face Mesh model is launched to detect 468 facial points
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5,#Minimum threshold for initial detection
            min_tracking_confidence=0.5   #Threshold to maintain tracking between frames
        )
        self.mp_drawing = mp.solutions.drawing_utils
       #Coordinate history for calculating kinematic displacements
        self.posiciones_historial = []

    def analizar_gesto(self, puntos_faciales):
        #Use the tip of your nose as the central reference point for the movement
        nariz = puntos_faciales.landmark[1]
        self.posiciones_historial.append((nariz.x, nariz.y))
        
        #Maintains a 15-frame sliding window for motion analysis
        if len(self.posiciones_historial) > 15: 
            self.posiciones_historial.pop(0)
            
        if len(self.posiciones_historial) < 15: 
            return None

        #Calculate the amplitude of the movement on the horizontal and vertical axes
        xs = [p[0] for p in self.posiciones_historial]
        ys = [p[1] for p in self.posiciones_historial]
        mov_x, mov_y = max(xs) - min(xs), max(ys) - min(ys)

       #Gesture classification logic based on the axis of greatest displacement
        if mov_y > 0.05 and mov_y > mov_x: return "si" #Vertical movement
        if mov_x > 0.05 and mov_x > mov_y: return "no" #Horizontal movement
        return None

    def procesar_frame(self, frame):
        #Color space conversion: OpenCV uses BGR and MediaPipe requires RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)
        gesto = None
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                #Render the facial contour mesh over the original frame
                self.mp_drawing.draw_landmarks(
                    frame, face_landmarks, self.mp_face_mesh.FACEMESH_CONTOURS
                )
                #Execute the gesture recognition logic for the detected face
                gesto = self.analizar_gesto(face_landmarks)
        
        return results.multi_face_landmarks, gesto
    
if __name__ == "__main__":
    print("hola")