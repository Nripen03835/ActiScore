from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from database.db import db, User, Analysis
from utils.auth import bcrypt

def register_routes(app):
    
    @app.route('/')
    @app.route('/home')
    def home():
        return render_template('index.html', title='ActiScore - Emotion Analysis')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Check if user already exists
            user_exists = User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first()
            if user_exists:
                flash('Username or email already exists. Please choose different credentials.', 'danger')
                return redirect(url_for('register'))
            
            # Create new user
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', title='Register')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = request.form.get('remember') == 'on'
            
            user = User.query.filter_by(email=email).first()
            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check email and password.', 'danger')
        
        return render_template('login.html', title='Login')
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
        return render_template('dashboard.html', title='Dashboard', analyses=analyses)
    
    @app.route('/analyze', methods=['GET', 'POST'])
    @login_required
    def analyze():
        if request.method == 'POST':
            analysis_type = request.form.get('analysis_type')
            title = request.form.get('title')
            description = request.form.get('description', '')
            
            # Handle file upload if provided
            file_path = None
            if 'file' in request.files:
                file = request.files['file']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
            
            # Create new analysis record
            analysis = Analysis(
                title=title,
                description=description,
                analysis_type=analysis_type,
                file_path=file_path,
                user_id=current_user.id
            )
            db.session.add(analysis)
            db.session.commit()
            
            # Redirect to appropriate analysis page
            if analysis_type == 'FER':
                return redirect(url_for('facial_analysis', analysis_id=analysis.id))
            elif analysis_type == 'SER':
                return redirect(url_for('speech_analysis', analysis_id=analysis.id))
            else:  # Fusion
                return redirect(url_for('fusion_analysis', analysis_id=analysis.id))
        
        return render_template('analyze.html', title='New Analysis')
    
    @app.route('/facial-analysis/<int:analysis_id>')
    @login_required
    def facial_analysis(analysis_id):
        analysis = Analysis.query.get_or_404(analysis_id)
        if analysis.user_id != current_user.id:
            flash('You do not have permission to view this analysis.', 'danger')
            return redirect(url_for('dashboard'))
        
        return render_template('facial_analysis.html', title='Facial Emotion Analysis', analysis=analysis)
    
    @app.route('/speech-analysis/<int:analysis_id>')
    @login_required
    def speech_analysis(analysis_id):
        analysis = Analysis.query.get_or_404(analysis_id)
        if analysis.user_id != current_user.id:
            flash('You do not have permission to view this analysis.', 'danger')
            return redirect(url_for('dashboard'))
        
        return render_template('speech_analysis.html', title='Speech Emotion Analysis', analysis=analysis)
    
    @app.route('/fusion-analysis/<int:analysis_id>')
    @login_required
    def fusion_analysis(analysis_id):
        analysis = Analysis.query.get_or_404(analysis_id)
        if analysis.user_id != current_user.id:
            flash('You do not have permission to view this analysis.', 'danger')
            return redirect(url_for('dashboard'))
        
        return render_template('fusion_analysis.html', title='Multimodal Fusion Analysis', analysis=analysis)
    
    @app.route('/api/analyze/facial', methods=['POST'])
    @login_required
    def api_analyze_facial():
        # This will be implemented to handle FER analysis
        # For now, return dummy data
        return jsonify({
            'success': True,
            'emotions': {
                'happy': 0.7,
                'sad': 0.05,
                'angry': 0.1,
                'surprised': 0.1,
                'neutral': 0.05
            }
        })
    
    @app.route('/api/analyze/speech', methods=['POST'])
    @login_required
    def api_analyze_speech():
        # This will be implemented to handle SER analysis
        # For now, return dummy data
        return jsonify({
            'success': True,
            'emotions': {
                'happy': 0.2,
                'sad': 0.6,
                'angry': 0.1,
                'neutral': 0.1
            }
        })
    
    @app.route('/api/analyze/fusion', methods=['POST'])
    @login_required
    def api_analyze_fusion():
        # This will be implemented to handle fusion analysis
        # For now, return dummy data
        return jsonify({
            'success': True,
            'emotions': {
                'happy': 0.4,
                'sad': 0.3,
                'angry': 0.1,
                'surprised': 0.1,
                'neutral': 0.1
            },
            'valence': 0.2,
            'arousal': 0.7,
            'dominance': 0.5
        })