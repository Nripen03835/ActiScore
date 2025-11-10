import cv2
import numpy as np
from deepface import DeepFace
from datetime import datetime
import os

class FaceRecognizer:
    def __init__(self):
        self.known_faces = {}
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known faces from the database"""
        from utils.database import DatabaseManager
        db = DatabaseManager()
        conn = db.get_connection()
        
        cursor = conn.cursor()
        cursor.execute('SELECT student_id, name FROM students')
        students = cursor.fetchall()
        
        # In a real implementation, you would have face embeddings stored
        # For this demo, we'll use a simplified approach
        for student_id, name in students:
            self.known_faces[student_id] = {
                'name': name,
                'embeddings': []  # This would contain pre-computed embeddings
            }
        
        conn.close()
    
    def recognize_face(self, frame):
        """Recognize faces in the frame and return results"""
        try:
            # Analyze face using DeepFace
            analysis = DeepFace.analyze(
                frame, 
                actions=['emotion'], 
                enforce_detection=False,
                detector_backend='opencv'
            )
            
            results = []
            
            if isinstance(analysis, list):
                for face in analysis:
                    # For recognition, we would compare with known faces
                    # This is a simplified version - in production, you'd use face recognition
                    recognized_student = self.simple_face_recognition(face)
                    
                    results.append({
                        'region': face['region'],
                        'emotion': face['dominant_emotion'],
                        'confidence': face['emotion'][face['dominant_emotion']],
                        'recognized_student': recognized_student
                    })
            
            return results
            
        except Exception as e:
            print(f"Face analysis error: {e}")
            return []
    
    def simple_face_recognition(self, face_analysis):
        """Simplified face recognition for demo purposes"""
        # In a real implementation, this would compare embeddings
        # For demo, we'll return a mock recognition
        import random
        
        # 70% chance of recognition for demo
        if random.random() > 0.3 and self.known_faces:
            student_id = random.choice(list(self.known_faces.keys()))
            return {
                'student_id': student_id,
                'name': self.known_faces[student_id]['name'],
                'confidence': random.uniform(0.7, 0.95)
            }
        
        return None
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on the frame"""
        for detection in detections:
            region = detection['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Prepare label
            emotion = detection['emotion']
            confidence = detection['confidence']
            student = detection['recognized_student']
            
            if student:
                label = f"{student['name']} ({emotion}: {confidence:.2f})"
                color = (0, 255, 0)  # Green for recognized
            else:
                label = f"Unknown ({emotion}: {confidence:.2f})"
                color = (0, 0, 255)  # Red for unknown
            
            # Draw label background
            cv2.rectangle(frame, (x, y - 30), (x + w, y), color, -1)
            cv2.putText(frame, label, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame