import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from datetime import datetime
import json

# Import models and utilities
from models.fer_model import FERModel
from models.ser_model import SERModel
from models.fusion_model import FusionModel
from database.db import db, User, Analysis
from utils.auth import bcrypt

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'actiscore-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///actiscore.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
socketio = SocketIO(app)
db.init_app(app)
with app.app_context():
    db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize models
fer_model = FERModel()
ser_model = SERModel()
fusion_model = FusionModel()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        app.logger.debug(f"Attempting login for email: {email}")
        
        user = User.query.filter_by(email=email).first()
        if user:
            app.logger.debug(f"User found: {user.username}")
            if bcrypt.check_password_hash(user.password, password):
                app.logger.debug("Password hash matched.")
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                app.logger.debug("Password hash mismatch.")
        else:
            app.logger.debug("User not found.")
        
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's previous analyses
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', analyses=analyses)

@app.route('/analyze')
@login_required
def analyze():
    return render_template('analyze.html')

@app.route('/api/analyze/video', methods=['POST'])
@login_required
def analyze_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process video with FER model
        results = fer_model.predict(filepath)
        
        # Save analysis to database
        analysis = Analysis(
            user_id=current_user.id,
            analysis_type='video',
            file_path=filepath,
            results=json.dumps(results)
        )
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify(results)

@app.route('/api/analyze/audio', methods=['POST'])
@login_required
def analyze_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process audio with SER model
        results = ser_model.predict(filepath)
        
        # Save analysis to database
        analysis = Analysis(
            user_id=current_user.id,
            analysis_type='audio',
            file_path=filepath,
            results=json.dumps(results)
        )
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify(results)

@app.route('/api/analyze/fusion', methods=['POST'])
@login_required
def analyze_fusion():
    if 'video' not in request.files or 'audio' not in request.files:
        return jsonify({'error': 'Both video and audio files are required'}), 400
    
    video_file = request.files['video']
    audio_file = request.files['audio']
    
    if video_file.filename == '' or audio_file.filename == '':
        return jsonify({'error': 'Both files must be selected'}), 400
    
    if video_file and audio_file:
        video_filename = secure_filename(video_file.filename)
        audio_filename = secure_filename(audio_file.filename)
        
        video_filepath = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        audio_filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        
        video_file.save(video_filepath)
        audio_file.save(audio_filepath)
        
        # Process with fusion model
        results = fusion_model.predict(video_filepath, audio_filepath)
        
        # Save analysis to database
        analysis = Analysis(
            user_id=current_user.id,
            analysis_type='fusion',
            file_path=f"{video_filepath},{audio_filepath}",
            results=json.dumps(results)
        )
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify(results)

# Real-time analysis with WebSockets
@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False
    emit('connected', {'status': 'connected'})

@socketio.on('stream_video')
def handle_stream_video(data):
    # Process video frame with FER model
    frame_data = data['frame']
    results = fer_model.predict_frame(frame_data)
    emit('video_results', results)

@socketio.on('stream_audio')
def handle_stream_audio(data):
    # Process audio chunk with SER model
    audio_data = data['audio']
    results = ser_model.predict_chunk(audio_data)
    emit('audio_results', results)

@socketio.on('stream_fusion')
def handle_stream_fusion(data):
    # Process both video and audio with fusion model
    frame_data = data['frame']
    audio_data = data['audio']
    results = fusion_model.predict_realtime(frame_data, audio_data)
    emit('fusion_results', results)

# Add this import at the top with other imports
from routes.reports import reports
from routes.collaboration import collaboration, register_socketio_events
from routes.api import api

# Add this line after other blueprint registrations
app.register_blueprint(reports, url_prefix='/reports')
app.register_blueprint(collaboration, url_prefix='/collaboration')
app.register_blueprint(api, url_prefix='/api')

# Register Socket.IO event handlers
register_socketio_events(socketio)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)