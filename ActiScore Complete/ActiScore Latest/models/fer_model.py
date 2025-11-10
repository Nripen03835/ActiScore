import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D, BatchNormalization
from tensorflow.keras.optimizers import Adam
import pandas as pd
from sklearn.model_selection import train_test_split
import base64
import io
from PIL import Image

class FERModel:
    def __init__(self, model_path=None):
        self.emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if model_path and os.path.exists(model_path):
            self.model = load_model(model_path)
        else:
            self.model = self._build_model()
    
    def _build_model(self):
        model = Sequential()
        
        # First convolutional block
        model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48, 48, 1)))
        model.add(BatchNormalization())
        model.add(Conv2D(32, kernel_size=(3, 3), activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        
        # Second convolutional block
        model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
        model.add(BatchNormalization())
        model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        
        # Third convolutional block
        model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
        model.add(BatchNormalization())
        model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
        model.add(BatchNormalization())
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        
        # Fully connected layers
        model.add(Flatten())
        model.add(Dense(512, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dropout(0.5))
        model.add(Dense(256, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dropout(0.5))
        model.add(Dense(len(self.emotions), activation='softmax'))
        
        model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, dataset_path, epochs=50, batch_size=64):
        # Load FER2013 dataset
        data = pd.read_csv(dataset_path)
        
        # Prepare data
        pixels = data['pixels'].tolist()
        width, height = 48, 48
        faces = []
        
        for pixel_sequence in pixels:
            face = [int(pixel) for pixel in pixel_sequence.split(' ')]
            face = np.asarray(face).reshape(width, height)
            faces.append(face.astype('float32'))
        
        faces = np.asarray(faces)
        faces = np.expand_dims(faces, -1)
        
        # Normalize pixel values
        faces = faces / 255.0
        
        # One-hot encode emotions
        emotions = pd.get_dummies(data['emotion']).values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(faces, emotions, test_size=0.2, random_state=42)
        
        # Train model
        self.model.fit(
            X_train, y_train,
            batch_size=batch_size,
            epochs=epochs,
            verbose=1,
            validation_data=(X_test, y_test),
            shuffle=True
        )
        
        # Save model
        self.model.save('models/fer_model.h5')
        
        # Evaluate model
        scores = self.model.evaluate(X_test, y_test)
        return {"loss": scores[0], "accuracy": scores[1]}
    
    def preprocess_face(self, face):
        # Convert to grayscale
        gray_face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        
        # Resize to 48x48
        resized_face = cv2.resize(gray_face, (48, 48))
        
        # Normalize
        normalized_face = resized_face / 255.0
        
        # Reshape for model input
        reshaped_face = normalized_face.reshape(1, 48, 48, 1)
        
        return reshaped_face
    
    def predict(self, video_path):
        cap = cv2.VideoCapture(video_path)
        results = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            frame_results = []
            for (x, y, w, h) in faces:
                # Extract face
                face = frame[y:y+h, x:x+w]
                
                # Preprocess face
                processed_face = self.preprocess_face(face)
                
                # Predict emotion
                predictions = self.model.predict(processed_face)[0]
                
                # Get top emotion
                emotion_idx = np.argmax(predictions)
                emotion = self.emotions[emotion_idx]
                confidence = float(predictions[emotion_idx])
                
                frame_results.append({
                    "emotion": emotion,
                    "confidence": confidence,
                    "position": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                    "all_emotions": {self.emotions[i]: float(predictions[i]) for i in range(len(self.emotions))}
                })
            
            if frame_results:
                results.append(frame_results)
        
        cap.release()
        
        # Aggregate results
        if not results:
            return {"error": "No faces detected"}
        
        # Calculate overall emotion distribution
        all_emotions = {emotion: 0 for emotion in self.emotions}
        total_faces = 0
        
        for frame in results:
            for face in frame:
                for emotion, score in face["all_emotions"].items():
                    all_emotions[emotion] += score
                total_faces += 1
        
        # Normalize
        if total_faces > 0:
            for emotion in all_emotions:
                all_emotions[emotion] /= total_faces
        
        # Get dominant emotion
        dominant_emotion = max(all_emotions, key=all_emotions.get)
        
        return {
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": all_emotions,
            "frame_count": len(results),
            "face_count": total_faces,
            "detailed_results": results[:10]  # Return only first 10 frames for brevity
        }
    
    def predict_frame(self, frame_data):
        # Decode base64 image
        if isinstance(frame_data, str) and frame_data.startswith('data:image'):
            frame_data = frame_data.split(',')[1]
            
        image_data = base64.b64decode(frame_data)
        image = Image.open(io.BytesIO(image_data))
        frame = np.array(image)
        
        # Convert to BGR (OpenCV format)
        if frame.shape[2] == 4:  # If RGBA
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        else:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        results = []
        for (x, y, w, h) in faces:
            # Extract face
            face = frame[y:y+h, x:x+w]
            
            # Preprocess face
            processed_face = self.preprocess_face(face)
            
            # Predict emotion
            predictions = self.model.predict(processed_face)[0]
            
            # Get top emotion
            emotion_idx = np.argmax(predictions)
            emotion = self.emotions[emotion_idx]
            confidence = float(predictions[emotion_idx])
            
            results.append({
                "emotion": emotion,
                "confidence": confidence,
                "position": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                "all_emotions": {self.emotions[i]: float(predictions[i]) for i in range(len(self.emotions))}
            })
        
        return {
            "faces": results,
            "timestamp": np.datetime64('now').astype(str)
        }