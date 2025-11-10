from flask import Flask, render_template, Response, request, jsonify, flash, redirect, url_for
import cv2
import threading
import time
from datetime import datetime, date
import json
import pandas as pd
import base64
import os

from config import config
from models.facial_recognition import FaceRecognizer
from utils.database import DatabaseManager
from utils.helpers import get_time_ranges, prepare_chart_data

app = Flask(__name__)
app.config.from_object(config)

# Global variables
camera = None
face_recognizer = FaceRecognizer()
db_manager = DatabaseManager()
last_attendance_check = {}
camera_active = False # New global variable to control camera feed

# Initialize camera
def init_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(config.CAMERA_SOURCE)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera

# Camera feed generator
def generate_frames():
    global camera_active
    camera = init_camera()
    
    while camera_active:
        success, frame = camera.read()
        if not success:
            break
        
        # Perform face recognition and emotion detection
        detections = face_recognizer.recognize_face(frame)
        
        # Process attendance for recognized faces
        process_attendance(detections)
        
        # Draw detections on frame
        frame = face_recognizer.draw_detections(frame, detections)
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.03)  # Control frame rate

def process_attendance(detections):
    """Process attendance for recognized faces"""
    current_time = time.time()
    
    for detection in detections:
        student = detection.get('recognized_student')
        
        if student and student['confidence'] > config.ATTENDANCE_THRESHOLD:
            student_id = student['student_id']
            
            # Check if we've recently recorded attendance for this student
            last_check = last_attendance_check.get(student_id, 0)
            if current_time - last_check > config.CHECK_INTERVAL:
                # Record attendance
                db_manager.add_attendance(
                    student_id=student_id,
                    name=student['name'],
                    emotion=detection['emotion'],
                    confidence=student['confidence']
                )
                
                # Update last check time
                last_attendance_check[student_id] = current_time
                
                print(f"Attendance recorded for {student['name']}")

# Routes
@app.route('/')
def index():
    """Home page with live camera feed"""
    stats = db_manager.get_attendance_stats()
    return render_template('index.html', stats=stats, camera_active=camera_active)

@app.route('/video_feed')
def video_feed():
    """Video feed route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/dashboard')
def dashboard():
    """Dashboard with analytics"""
    stats = db_manager.get_attendance_stats()
    attendance_history = db_manager.get_attendance_history(days=7)
    recent_attendance = db_manager.get_today_attendance().head(10).to_dict('records')
    
    # Prepare chart data
    chart_data = prepare_chart_data(attendance_history, stats['emotion_distribution'])
    
    return render_template('dashboard.html', 
                         stats=stats,
                         recent_attendance=recent_attendance,
                         chart_data=chart_data)

@app.route('/attendance')
def attendance():
    """Attendance records page"""
    attendance_data = db_manager.get_today_attendance().to_dict('records')
    today_date = date.today().strftime('%B %d, %Y')
    
    return render_template('attendance.html',
                         attendance_data=attendance_data,
                         today_date=today_date)

@app.route('/register', methods=['GET', 'POST'])
def register_student():
    """Student registration page"""
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        photo_data = request.form.get('photo_data')
        
        app.logger.info(f'Registration attempt for student_id: {student_id}')

        if name and student_id:
            # Save photo if provided
            photo_path = None
            if photo_data:
                try:
                    # Decode base64 image
                    img_data = base64.b64decode(photo_data.split(',')[1])
                    
                    # Ensure upload directory exists
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Save image
                    photo_filename = f"{student_id}.jpg"
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
                    with open(photo_path, 'wb') as f:
                        f.write(img_data)
                    app.logger.info(f'Photo saved to: {photo_path}')
                except Exception as e:
                    app.logger.error(f'Error saving photo: {e}')
                    return jsonify({'success': False, 'message': f'Error saving photo: {e}'})

            success = db_manager.add_student(name, student_id, email, photo_path)
            if success:
                app.logger.info(f'Student {student_id} registered successfully')
                face_recognizer.load_known_faces()
                return jsonify({'success': True, 'message': 'Student registered successfully!'})
            else:
                app.logger.warning(f'Student ID {student_id} already exists')
                return jsonify({'success': False, 'message': 'Student ID already exists!'})
        else:
            app.logger.warning('Registration failed: Name or student_id missing')
            return jsonify({'success': False, 'message': 'Please fill in all required fields!'})
        
    return render_template('register.html')

@app.route('/students')
def manage_students():
    """Student management page"""
    students = db_manager.get_all_students().to_dict('records')
    return render_template('students.html', students=students)

@app.route('/students/delete/<student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete a student"""
    db_manager.delete_student(student_id)
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('manage_students'))

@app.route('/students/edit/<student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student details"""
    student = db_manager.get_student_by_id(student_id)
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('manage_students'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if name and email:
            success = db_manager.update_student(student_id, name, email, student['photo_path'])
            if success:
                flash('Student details updated successfully!', 'success')
                return redirect(url_for('manage_students'))
            else:
                flash('Error updating student details.', 'error')
        else:
            flash('Name and Email are required!', 'error')

    return render_template('edit_student.html', student=student)

# API Routes
@app.route('/api/today-attendance')
def api_today_attendance():
    """API endpoint for today's attendance data"""
    attendance_data = db_manager.get_today_attendance().to_dict('records')
    return jsonify(attendance_data)

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API endpoint for dashboard data"""
    stats = db_manager.get_attendance_stats()
    attendance_history = db_manager.get_attendance_history(days=7)
    
    chart_data = prepare_chart_data(attendance_history, stats['emotion_distribution'])
    
    return jsonify({
        'stats': stats,
        'chart_data': chart_data
    })

@app.route('/api/students')
def api_students():
    """API endpoint for student list"""
    conn = db_manager.get_connection()
    students = pd.read_sql_query('SELECT * FROM students', conn)
    conn.close()
    
    return jsonify(students.to_dict('records'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Cleanup function
@app.teardown_appcontext
def close_camera(error):
    global camera
    if camera is not None:
        camera.release()
        camera = None

@app.route('/start_camera', methods=['POST'])
def start_camera():
    global camera_active
    camera_active = True
    flash('Camera started!', 'success')
    return redirect(url_for('index'))

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    global camera_active
    global camera
    camera_active = False
    if camera is not None:
        camera.release()
        camera = None
    flash('Camera stopped!', 'warning')
    return redirect(url_for('index'))

@app.route('/capture_attendance', methods=['POST'])
def capture_attendance():
    """Manually trigger attendance capture for current frame"""
    if camera is None or not camera_active:
        flash('Camera is not active. Please start the camera first.', 'error')
        return redirect(url_for('index'))

    success, frame = camera.read()
    if not success:
        flash('Failed to capture frame from camera.', 'error')
        return redirect(url_for('index'))

    detections = face_recognizer.recognize_face(frame)
    process_attendance(detections)
    flash('Attendance captured for visible students!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Initialize database
    from setup_database import init_database
    init_database()
    
    # Start Flask application
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5001)