from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from utils.summarizer import LegalSummarizer
from utils.semantic_search import LegalSemanticSearch
from utils.file_processor import FileProcessor
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import hashlib
from functools import lru_cache

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('faiss_index', exist_ok=True)

# Initialize components
summarizer = LegalSummarizer()
semantic_search = LegalSemanticSearch()
file_processor = FileProcessor()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_pdf(content, title="Legal Document Summary"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor='#2c3e50'
    )
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Content
    content_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=12,
        textColor='#34495e'
    )
    
    paragraphs = content.split('\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), content_style))
            story.append(Spacer(1, 0.1*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def get_text_hash(text):
    """Generate hash for text caching"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# Cache for summaries to avoid reprocessing same text
summary_cache = {}

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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process file and extract text
            text = file_processor.process_file(filepath)
            
            # Store in semantic search
            semantic_search.add_document(text, filename)
            
            # Store the processed text in a temporary file for retrieval
            text_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.txt")
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'text_length': len(text)
            })
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/get_uploaded_text', methods=['POST'])
def get_uploaded_text():
    data = request.get_json()
    filename = data.get('filename', '')
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    try:
        text_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.txt")
        if os.path.exists(text_filepath):
            with open(text_filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            return jsonify({
                'success': True,
                'text': text
            })
        else:
            return jsonify({'error': 'Text content not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error retrieving text: {str(e)}'}), 500

@app.route('/summarize', methods=['POST'])
def summarize_text():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Check cache first
        text_hash = get_text_hash(text)
        if text_hash in summary_cache:
            print("Using cached summary")
            summary = summary_cache[text_hash]
        else:
            summary = summarizer.summarize(text)
            # Cache the summary
            summary_cache[text_hash] = summary
            # Limit cache size
            if len(summary_cache) > 100:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(summary_cache))
                del summary_cache[oldest_key]
        
        return jsonify({
            'success': True,
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary),
            'cached': text_hash in summary_cache
        })
    except Exception as e:
        return jsonify({'error': f'Error generating summary: {str(e)}'}), 500

@app.route('/summarize_fast', methods=['POST'])
def summarize_text_fast():
    """
    Ultra-fast summarization using only extractive method
    """
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Use only fast extractive summarization
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        if not sentences:
            summary = text[:300] + "..." if len(text) > 300 else text
        else:
            # Take key sentences: first, some middle, last
            num_sentences = min(5, len(sentences))
            indices = [0]  # First sentence
            
            # Add some middle sentences
            if len(sentences) > 3:
                mid = len(sentences) // 2
                indices.append(mid)
            
            # Add last sentence
            indices.append(len(sentences) - 1)
            
            # Fill with other sentences if needed
            for i in range(1, len(sentences)-1):
                if len(indices) >= num_sentences:
                    break
                if i not in indices:
                    indices.append(i)
            
            indices.sort()
            summary = '. '.join([sentences[i] for i in indices]) + '.'
        
        return jsonify({
            'success': True,
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary),
            'method': 'extractive_fast'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error generating fast summary: {str(e)}'}), 500

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        results = semantic_search.search(query, top_k=3)
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def download_summary():
    data = request.get_json()
    content = data.get('content', '')
    title = data.get('title', 'Legal Document Summary')
    
    if not content:
        return jsonify({'error': 'No content provided'}), 400
    
    try:
        pdf_buffer = create_pdf(content, title)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"{title.replace(' ', '_')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)