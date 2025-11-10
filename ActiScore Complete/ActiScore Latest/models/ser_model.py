import os
import numpy as np
import librosa
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, LSTM, BatchNormalization
from tensorflow.keras.optimizers import Adam
import pandas as pd
from sklearn.model_selection import train_test_split
import glob
import sounddevice as sd
import soundfile as sf
import base64
import io

class SERModel:
    def __init__(self, model_path=None):
        self.emotions = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
        
        if model_path and os.path.exists(model_path):
            self.model = load_model(model_path)
        else:
            self.model = self._build_model()
    
    def _build_model(self):
        model = Sequential()
        
        # LSTM layers
        model.add(LSTM(128, input_shape=(40, 1), return_sequences=True))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        
        model.add(LSTM(128, return_sequences=True))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        
        model.add(LSTM(128))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        
        # Dense layers
        model.add(Dense(64, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        
        model.add(Dense(32, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        
        # Output layer
        model.add(Dense(len(self.emotions), activation='softmax'))
        
        model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def extract_features(self, audio_path, max_pad_len=174):
        try:
            # Load audio file
            y, sr = librosa.load(audio_path, sr=22050)
            
            # Extract MFCCs
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
            
            # Transpose to get time as first dimension
            mfccs = mfccs.T
            
            # Pad or truncate to fixed length
            if mfccs.shape[0] < max_pad_len:
                pad_width = max_pad_len - mfccs.shape[0]
                mfccs = np.pad(mfccs, ((0, pad_width), (0, 0)), mode='constant')
            else:
                mfccs = mfccs[:max_pad_len, :]
            
            return mfccs
        except Exception as e:
            print(f"Error extracting features from {audio_path}: {e}")
            return None
    
    def train(self, dataset_path, epochs=50, batch_size=32):
        # Get all audio files
        audio_files = []
        for actor_dir in glob.glob(os.path.join(dataset_path, "Actor_*")):
            for audio_file in glob.glob(os.path.join(actor_dir, "*.wav")):
                audio_files.append(audio_file)
        
        # Extract features and labels
        features = []
        labels = []
        
        for audio_file in audio_files:
            # Extract emotion from filename
            # Format: 03-01-01-01-01-01-01.wav
            # Emotion is the 3rd field (01 = neutral, 02 = calm, etc.)
            filename = os.path.basename(audio_file)
            emotion_code = int(filename.split('-')[2])
            
            # Map emotion code to index
            if emotion_code <= len(self.emotions):
                emotion_idx = emotion_code - 1
                
                # Extract features
                mfccs = self.extract_features(audio_file)
                
                if mfccs is not None:
                    features.append(mfccs)
                    
                    # One-hot encode emotion
                    emotion = np.zeros(len(self.emotions))
                    emotion[emotion_idx] = 1
                    labels.append(emotion)
        
        # Convert to numpy arrays
        features = np.array(features)
        labels = np.array(labels)
        
        # Reshape for LSTM input
        features = features.reshape(features.shape[0], features.shape[1], 1)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
        
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
        self.model.save('models/ser_model.h5')
        
        # Evaluate model
        scores = self.model.evaluate(X_test, y_test)
        return {"loss": scores[0], "accuracy": scores[1]}
    
    def predict(self, audio_path):
        # Extract features
        mfccs = self.extract_features(audio_path)
        
        if mfccs is None:
            return {"error": "Failed to extract features"}
        
        # Reshape for model input
        mfccs = mfccs.reshape(1, mfccs.shape[0], 1)
        
        # Predict emotion
        predictions = self.model.predict(mfccs)[0]
        
        # Get top emotion
        emotion_idx = np.argmax(predictions)
        emotion = self.emotions[emotion_idx]
        confidence = float(predictions[emotion_idx])
        
        # Get all emotion probabilities
        all_emotions = {self.emotions[i]: float(predictions[i]) for i in range(len(self.emotions))}
        
        # Get audio duration
        y, sr = librosa.load(audio_path)
        duration = librosa.get_duration(y=y, sr=sr)
        
        return {
            "dominant_emotion": emotion,
            "confidence": confidence,
            "emotion_distribution": all_emotions,
            "duration": duration,
            "sample_rate": sr
        }
    
    def predict_chunk(self, audio_data):
        # Decode base64 audio
        if isinstance(audio_data, str) and audio_data.startswith('data:audio'):
            audio_data = audio_data.split(',')[1]
            
        audio_bytes = base64.b64decode(audio_data)
        
        # Save to temporary file
        temp_file = 'temp_audio.wav'
        with open(temp_file, 'wb') as f:
            f.write(audio_bytes)
        
        # Extract features
        mfccs = self.extract_features(temp_file)
        
        # Remove temporary file
        os.remove(temp_file)
        
        if mfccs is None:
            return {"error": "Failed to extract features"}
        
        # Reshape for model input
        mfccs = mfccs.reshape(1, mfccs.shape[0], 1)
        
        # Predict emotion
        predictions = self.model.predict(mfccs)[0]
        
        # Get top emotion
        emotion_idx = np.argmax(predictions)
        emotion = self.emotions[emotion_idx]
        confidence = float(predictions[emotion_idx])
        
        # Get all emotion probabilities
        all_emotions = {self.emotions[i]: float(predictions[i]) for i in range(len(self.emotions))}
        
        return {
            "emotion": emotion,
            "confidence": confidence,
            "all_emotions": all_emotions,
            "timestamp": np.datetime64('now').astype(str)
        }