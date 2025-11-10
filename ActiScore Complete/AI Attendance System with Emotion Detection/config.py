import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DATABASE_PATH = 'database/attendance.db'
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # DeepFace configuration
    DETECTOR_BACKEND = 'opencv'
    MODEL_NAME = 'VGG-Face'
    
    # Camera configuration
    CAMERA_SOURCE = 0  # 0 for default webcam
    
    # Attendance settings
    ATTENDANCE_THRESHOLD = 0.6  # Confidence threshold for recognition
    CHECK_INTERVAL = 30  # Check every 30 seconds

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = DevelopmentConfig()