from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

# Import models
from models.fer_model import FERModel
from models.ser_model import SERModel
from models.fusion_model import FusionModel
from database.db import db, Analysis

# Initialize models
fer_model = FERModel()
ser_model = SERModel()
fusion_model = FusionModel()

# Create blueprint
api = Blueprint('api', __name__)

# API Documentation
API_DOCS = {
    "openapi": "3.0.0",
    "info": {
        "title": "ActiScore API",
        "description": "API for ActiScore Multimodal Emotion Analysis System",
        "version": "1.0.0"
    },
    "paths": {
        "/api/v1/analyze/video": {
            "post": {
                "summary": "Analyze video for facial emotions",
                "description": "Upload a video file to analyze facial emotions",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful analysis"
                    }
                }
            }
        },
        "/api/v1/analyze/audio": {
            "post": {
                "summary": "Analyze audio for speech emotions",
                "description": "Upload an audio file to analyze speech emotions",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful analysis"
                    }
                }
            }
        },
        "/api/v1/analyze/fusion": {
            "post": {
                "summary": "Analyze video and audio for multimodal emotions",
                "description": "Upload video and audio files to analyze multimodal emotions",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "video": {
                                        "type": "string",
                                        "format": "binary"
                                    },
                                    "audio": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful analysis"
                    }
                }
            }
        },
        "/api/v1/analyses": {
            "get": {
                "summary": "Get user's analyses",
                "description": "Get a list of the user's analyses",
                "responses": {
                    "200": {
                        "description": "List of analyses"
                    }
                }
            }
        },
        "/api/v1/analyses/{id}": {
            "get": {
                "summary": "Get analysis details",
                "description": "Get details of a specific analysis",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Analysis details"
                    }
                }
            }
        }
    }
}

@api.route('/docs', methods=['GET'])
def get_docs():
    """Get API documentation"""
    return jsonify(API_DOCS)

@api.route('/v1/analyze/video', methods=['POST'])
@login_required
def analyze_video():
    """Analyze video for facial emotions"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
        
        return jsonify({
            'success': True,
            'analysis_id': analysis.id,
            'results': results
        })

@api.route('/v1/analyze/audio', methods=['POST'])
@login_required
def analyze_audio():
    """Analyze audio for speech emotions"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
        
        return jsonify({
            'success': True,
            'analysis_id': analysis.id,
            'results': results
        })

@api.route('/v1/analyze/fusion', methods=['POST'])
@login_required
def analyze_fusion():
    """Analyze video and audio for multimodal emotions"""
    if 'video' not in request.files or 'audio' not in request.files:
        return jsonify({'error': 'Both video and audio files are required'}), 400
    
    video_file = request.files['video']
    audio_file = request.files['audio']
    
    if video_file.filename == '' or audio_file.filename == '':
        return jsonify({'error': 'Both files must be selected'}), 400
    
    if video_file and audio_file:
        video_filename = secure_filename(video_file.filename)
        audio_filename = secure_filename(audio_file.filename)
        
        video_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], video_filename)
        audio_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename)
        
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
        
        return jsonify({
            'success': True,
            'analysis_id': analysis.id,
            'results': results
        })

@api.route('/v1/analyses', methods=['GET'])
@login_required
def get_analyses():
    """Get user's analyses"""
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    
    results = []
    for analysis in analyses:
        results.append({
            'id': analysis.id,
            'type': analysis.analysis_type,
            'created_at': analysis.created_at.isoformat(),
            'is_shared': analysis.is_shared
        })
    
    return jsonify({
        'success': True,
        'analyses': results
    })

@api.route('/v1/analyses/<int:analysis_id>', methods=['GET'])
@login_required
def get_analysis(analysis_id):
    """Get analysis details"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if user has access to the analysis
    if analysis.user_id != current_user.id and not (analysis.is_shared and TeamMember.query.filter_by(team_id=analysis.team_id, user_id=current_user.id).first()):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'success': True,
        'analysis': {
            'id': analysis.id,
            'type': analysis.analysis_type,
            'created_at': analysis.created_at.isoformat(),
            'results': json.loads(analysis.results),
            'is_shared': analysis.is_shared
        }
    })

@api.route('/v1/emotion-timeline', methods=['GET'])
@login_required
def get_emotion_timeline():
    """Get emotion timeline data for dashboard visualization"""
    # This would typically fetch real data from the database
    # For now, return sample data
    return jsonify({
        'success': True,
        'timestamps': ['00:00', '00:05', '00:10', '00:15', '00:20', '00:25', '00:30'],
        'emotions': [
            {'name': 'Happy', 'values': [0.2, 0.3, 0.5, 0.7, 0.6, 0.4, 0.3]},
            {'name': 'Sad', 'values': [0.1, 0.2, 0.1, 0.0, 0.1, 0.2, 0.3]},
            {'name': 'Angry', 'values': [0.3, 0.2, 0.1, 0.0, 0.0, 0.1, 0.1]},
            {'name': 'Surprised', 'values': [0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.0]},
            {'name': 'Neutral', 'values': [0.3, 0.2, 0.1, 0.1, 0.2, 0.2, 0.3]}
        ]
    })

@api.route('/v1/emotion-heatmap', methods=['GET'])
@login_required
def get_emotion_heatmap():
    """Get emotion heatmap data for dashboard visualization"""
    # This would typically fetch real data from the database
    # For now, return sample data
    return jsonify({
        'success': True,
        'emotions': ['Happy', 'Sad', 'Angry', 'Surprised', 'Neutral'],
        'timeLabels': ['00:00', '00:05', '00:10', '00:15', '00:20', '00:25', '00:30'],
        'values': [
            [0.2, 0.3, 0.5, 0.7, 0.6, 0.4, 0.3],
            [0.1, 0.2, 0.1, 0.0, 0.1, 0.2, 0.3],
            [0.3, 0.2, 0.1, 0.0, 0.0, 0.1, 0.1],
            [0.1, 0.1, 0.2, 0.2, 0.1, 0.1, 0.0],
            [0.3, 0.2, 0.1, 0.1, 0.2, 0.2, 0.3]
        ]
    })