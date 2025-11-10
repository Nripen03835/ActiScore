import os
import uuid
import json
import whisper
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'mp3', 'wav', 'm4a', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_audio(video_path, audio_path):
    """Extract audio from video file"""
    try:
        video = AudioSegment.from_file(video_path)
        video.export(audio_path, format="wav")
        return True
    except Exception as e:
        print(f"Error extracting audio: {str(e)}")
        return False

def transcribe_audio(audio_path):
    """Transcribe audio using Whisper"""
    try:
        model = whisper.load_model("base")  # You can change to "small", "medium", or "large" for better accuracy
        result = model.transcribe(audio_path)
        return result["text"]
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        return None

def summarize_text(text):
    """Summarize the transcribed text (basic implementation)"""
    # This is a simple summarization - you can replace with more sophisticated NLP models
    sentences = text.split('. ')
    if len(sentences) <= 5:
        return text
    
    # Take first, middle and last sentences for a basic summary
    important_sentences = [
        sentences[0],
        sentences[len(sentences)//2],
        sentences[-1]
    ]
    
    summary = '. '.join(important_sentences) + '.'
    return summary

def create_pdf(summary, filename):
    """Create a PDF file from the summary"""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    title = Paragraph("Video Summary", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Summary content
    summary_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=12,
        spaceAfter=12,
        leading=14
    )
    summary_para = Paragraph(summary, summary_style)
    story.append(summary_para)
    
    doc.build(story)
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_id = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        filename = f"{file_id}.{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save uploaded file
        file.save(file_path)
        
        # Process file based on type
        if file_extension in ['mp3', 'wav', 'm4a', 'ogg']:
            # Directly transcribe audio file
            audio_path = file_path
        else:
            # Extract audio from video
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}.wav")
            if not extract_audio(file_path, audio_path):
                return jsonify({'error': 'Failed to extract audio from video'}), 500
        
        # Transcribe audio
        transcription = transcribe_audio(audio_path)
        if not transcription:
            return jsonify({'error': 'Failed to transcribe audio'}), 500
        
        # Generate summary
        summary = summarize_text(transcription)
        
        # Create PDF
        pdf_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}.pdf")
        create_pdf(summary, pdf_filename)
        
        # Clean up temporary files
        try:
            os.remove(file_path)
            if file_extension not in ['mp3', 'wav', 'm4a', 'ogg']:
                os.remove(audio_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'summary': summary,
            'pdf_url': f'/download/{file_id}.pdf'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)