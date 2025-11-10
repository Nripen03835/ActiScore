import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Dense, Dropout, LSTM, Attention, Concatenate, BatchNormalization
from tensorflow.keras.optimizers import Adam
import cv2
import librosa
from .fer_model import FERModel
from .ser_model import SERModel
import base64
import io
from PIL import Image

class FusionModel:
    def __init__(self, model_path=None, fer_model=None, ser_model=None):
        self.emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        self.valence_arousal = {
            'Angry': {'valence': -0.8, 'arousal': 0.8},
            'Disgust': {'valence': -0.6, 'arousal': 0.2},
            'Fear': {'valence': -0.7, 'arousal': 0.7},
            'Happy': {'valence': 0.9, 'arousal': 0.6},
            'Sad': {'valence': -0.7, 'arousal': -0.4},
            'Surprise': {'valence': 0.4, 'arousal': 0.8},
            'Neutral': {'valence': 0.0, 'arousal': 0.0}
        }
        
        # Initialize FER and SER models
        self.fer_model = fer_model if fer_model else FERModel()
        self.ser_model = ser_model if ser_model else SERModel()
        
        if model_path and os.path.exists(model_path):
            self.model = load_model(model_path)
        else:
            self.model = self._build_model()
    
    def _build_model(self):
        # Video input branch
        video_input = Input(shape=(128,))
        video_dense = Dense(64, activation='relu')(video_input)
        video_bn = BatchNormalization()(video_dense)
        video_dropout = Dropout(0.3)(video_bn)
        
        # Audio input branch
        audio_input = Input(shape=(128,))
        audio_dense = Dense(64, activation='relu')(audio_input)
        audio_bn = BatchNormalization()(audio_dense)
        audio_dropout = Dropout(0.3)(audio_bn)
        
        # Cross-modal attention
        attention_output = Attention()([video_dropout, audio_dropout])
        
        # Concatenate
        concat = Concatenate()([video_dropout, audio_dropout, attention_output])
        
        # Fusion layers
        fusion_dense1 = Dense(128, activation='relu')(concat)
        fusion_bn1 = BatchNormalization()(fusion_dense1)
        fusion_dropout1 = Dropout(0.3)(fusion_bn1)
        
        fusion_dense2 = Dense(64, activation='relu')(fusion_dropout1)
        fusion_bn2 = BatchNormalization()(fusion_dense2)
        fusion_dropout2 = Dropout(0.3)(fusion_bn2)
        
        # Output layer
        output = Dense(len(self.emotions), activation='softmax')(fusion_dropout2)
        
        # Create model
        model = Model(inputs=[video_input, audio_input], outputs=output)
        
        model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, video_features, audio_features, labels, epochs=50, batch_size=32):
        # Split data
        from sklearn.model_selection import train_test_split
        X_video_train, X_video_test, X_audio_train, X_audio_test, y_train, y_test = train_test_split(
            video_features, audio_features, labels, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(
            [X_video_train, X_audio_train], y_train,
            batch_size=batch_size,
            epochs=epochs,
            verbose=1,
            validation_data=([X_video_test, X_audio_test], y_test),
            shuffle=True
        )
        
        # Save model
        self.model.save('models/fusion_model.h5')
        
        # Evaluate model
        scores = self.model.evaluate([X_video_test, X_audio_test], y_test)
        return {"loss": scores[0], "accuracy": scores[1]}
    
    def predict(self, video_path, audio_path):
        # Get FER predictions
        fer_results = self.fer_model.predict(video_path)
        
        # Get SER predictions
        ser_results = self.ser_model.predict(audio_path)
        
        # Simple fusion (weighted average)
        # In a real implementation, we would extract features and use the fusion model
        fer_emotions = fer_results['emotion_distribution']
        ser_emotions = ser_results['emotion_distribution']
        
        # Map SER emotions to FER emotions
        mapped_ser_emotions = {
            'Angry': ser_emotions.get('angry', 0),
            'Disgust': ser_emotions.get('disgust', 0),
            'Fear': ser_emotions.get('fearful', 0),
            'Happy': ser_emotions.get('happy', 0),
            'Sad': ser_emotions.get('sad', 0),
            'Surprise': ser_emotions.get('surprised', 0),
            'Neutral': (ser_emotions.get('neutral', 0) + ser_emotions.get('calm', 0)) / 2
        }
        
        # Weighted fusion (60% video, 40% audio)
        fusion_emotions = {}
        for emotion in self.emotions:
            fusion_emotions[emotion] = 0.6 * fer_emotions.get(emotion, 0) + 0.4 * mapped_ser_emotions.get(emotion, 0)
        
        # Get dominant emotion
        dominant_emotion = max(fusion_emotions, key=fusion_emotions.get)
        
        # Calculate valence-arousal
        valence = self.valence_arousal[dominant_emotion]['valence']
        arousal = self.valence_arousal[dominant_emotion]['arousal']
        
        # Determine intensity
        confidence = fusion_emotions[dominant_emotion]
        if confidence < 0.4:
            intensity = "mild"
        elif confidence < 0.7:
            intensity = "moderate"
        else:
            intensity = "strong"
        
        # Check for compound emotions
        sorted_emotions = sorted(fusion_emotions.items(), key=lambda x: x[1], reverse=True)
        compound_emotion = None
        if sorted_emotions[1][1] > 0.3 * sorted_emotions[0][1]:
            compound_emotion = f"{sorted_emotions[0][0]}-{sorted_emotions[1][0]}"
        
        return {
            "dominant_emotion": dominant_emotion,
            "compound_emotion": compound_emotion,
            "intensity": intensity,
            "confidence": float(fusion_emotions[dominant_emotion]),
            "emotion_distribution": {k: float(v) for k, v in fusion_emotions.items()},
            "valence": float(valence),
            "arousal": float(arousal),
            "video_results": fer_results,
            "audio_results": ser_results
        }
    
    def predict_realtime(self, frame_data, audio_data):
        # Get FER predictions
        fer_results = self.fer_model.predict_frame(frame_data)
        
        # Get SER predictions
        ser_results = self.ser_model.predict_chunk(audio_data)
        
        # Extract emotion distributions
        if 'faces' in fer_results and fer_results['faces']:
            fer_emotions = fer_results['faces'][0]['all_emotions']
        else:
            fer_emotions = {emotion: 0.0 for emotion in self.emotions}
        
        ser_emotions = ser_results['all_emotions']
        
        # Map SER emotions to FER emotions
        mapped_ser_emotions = {
            'Angry': ser_emotions.get('angry', 0),
            'Disgust': ser_emotions.get('disgust', 0),
            'Fear': ser_emotions.get('fearful', 0),
            'Happy': ser_emotions.get('happy', 0),
            'Sad': ser_emotions.get('sad', 0),
            'Surprise': ser_emotions.get('surprised', 0),
            'Neutral': (ser_emotions.get('neutral', 0) + ser_emotions.get('calm', 0)) / 2
        }
        
        # Weighted fusion (60% video, 40% audio)
        fusion_emotions = {}
        for emotion in self.emotions:
            fusion_emotions[emotion] = 0.6 * fer_emotions.get(emotion, 0) + 0.4 * mapped_ser_emotions.get(emotion, 0)
        
        # Get dominant emotion
        dominant_emotion = max(fusion_emotions, key=fusion_emotions.get)
        
        # Calculate valence-arousal
        valence = self.valence_arousal[dominant_emotion]['valence']
        arousal = self.valence_arousal[dominant_emotion]['arousal']
        
        # Determine intensity
        confidence = fusion_emotions[dominant_emotion]
        if confidence < 0.4:
            intensity = "mild"
        elif confidence < 0.7:
            intensity = "moderate"
        else:
            intensity = "strong"
        
        # Check for compound emotions
        sorted_emotions = sorted(fusion_emotions.items(), key=lambda x: x[1], reverse=True)
        compound_emotion = None
        if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0.3 * sorted_emotions[0][1]:
            compound_emotion = f"{sorted_emotions[0][0]}-{sorted_emotions[1][0]}"
        
        return {
            "dominant_emotion": dominant_emotion,
            "compound_emotion": compound_emotion,
            "intensity": intensity,
            "confidence": float(fusion_emotions[dominant_emotion]),
            "emotion_distribution": {k: float(v) for k, v in fusion_emotions.items()},
            "valence": float(valence),
            "arousal": float(arousal),
            "timestamp": np.datetime64('now').astype(str)
        }