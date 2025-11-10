from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
from utils.summarizer import ResearchSummarizer
from utils.recommender import PaperRecommender
from utils.pdf_parser import PDFParser  # NEW: Import PDF parser
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize components
summarizer = ResearchSummarizer()
recommender = PaperRecommender()
pdf_parser = PDFParser()  # NEW: Initialize PDF parser

# Load sample papers database
with open('data/papers.json', 'r', encoding='utf-8') as f:
    papers_data = json.load(f)

# Initialize recommender with papers data
recommender.fit(papers_data)

# Store search history
search_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html', history=search_history)

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        content = ""
        input_type = "text"
        filename = ""
        
        if 'file' in request.files and request.files['file'].filename:
            # File upload
            file = request.files['file']
            filename = file.filename
            
            # Check if file is selected
            if filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            file.seek(0)
            
            if file_length > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 400
            
            # Parse file based on type
            try:
                content = pdf_parser.parse_file(file.stream, filename)
                input_type = 'file'
            except Exception as e:
                return jsonify({'error': f'Error processing file: {str(e)}'}), 400
            
            if not content.strip():
                return jsonify({'error': 'Could not extract text from the file. The file might be empty, corrupted, or contain only images.'}), 400
                
        else:
            # Text input
            content = request.form.get('text_input', '')
            input_type = 'text'
        
        if not content.strip():
            return jsonify({'error': 'No content provided. Please upload a file or enter text.'}), 400
        
        # Generate summary
        summary = summarizer.summarize(content)
        
        # Extract key contributions
        contributions = summarizer.extract_contributions(content)
        
        # Get similar papers
        similar_papers = recommender.recommend_similar(content, top_k=5)
        
        # Save to history
        history_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'input_type': input_type,
            'filename': filename if filename else None,
            'summary': summary,
            'contributions': contributions,
            'similar_papers': similar_papers
        }
        search_history.insert(0, history_entry)
        
        # Keep only last 20 entries
        if len(search_history) > 20:
            search_history.pop()
        
        return jsonify({
            'summary': summary,
            'contributions': contributions,
            'similar_papers': similar_papers
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        keywords = request.form.get('keywords', '')
        
        if not keywords.strip():
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Get recommendations based on keywords
        recommended_papers = recommender.recommend_by_keywords(keywords, top_k=5)
        
        # Save to history
        history_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'input_type': 'keywords',
            'keywords': keywords,
            'recommended_papers': recommended_papers
        }
        search_history.insert(0, history_entry)
        
        # Keep only last 20 entries
        if len(search_history) > 20:
            search_history.pop()
        
        return jsonify({
            'recommended_papers': recommended_papers
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_pdf():
    try:
        data = request.json
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Set up PDF content
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 750, "Research Paper Analysis Report")
        p.setFont("Helvetica", 12)
        
        y_position = 720
        
        # Add summary
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Summary:")
        p.setFont("Helvetica", 12)
        y_position -= 20
        
        summary_lines = data['summary'].split('. ')
        for line in summary_lines:
            if line.strip():
                # Handle long text by splitting into multiple lines
                words = line.strip().split()
                current_line = ""
                for word in words:
                    test_line = current_line + word + " "
                    if p.stringWidth(test_line) < 500:  # Check if line fits
                        current_line = test_line
                    else:
                        if current_line:
                            p.drawString(50, y_position, current_line.strip())
                            y_position -= 15
                        current_line = word + " "
                        
                        if y_position < 50:
                            p.showPage()
                            y_position = 750
                            p.setFont("Helvetica", 12)
                
                if current_line:
                    p.drawString(50, y_position, current_line.strip() + '.')
                    y_position -= 15
                
                if y_position < 50:
                    p.showPage()
                    y_position = 750
                    p.setFont("Helvetica", 12)
        
        # Add contributions
        y_position -= 10
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Key Contributions:")
        p.setFont("Helvetica", 12)
        y_position -= 20
        
        for i, contribution in enumerate(data['contributions'], 1):
            cont_text = f"{i}. {contribution}"
            # Handle long contributions
            words = cont_text.split()
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                if p.stringWidth(test_line) < 500:
                    current_line = test_line
                else:
                    if current_line:
                        p.drawString(50, y_position, current_line.strip())
                        y_position -= 15
                    current_line = word + " "
                    
                    if y_position < 50:
                        p.showPage()
                        y_position = 750
                        p.setFont("Helvetica", 12)
            
            if current_line:
                p.drawString(50, y_position, current_line.strip())
                y_position -= 15
            
            if y_position < 50:
                p.showPage()
                y_position = 750
                p.setFont("Helvetica", 12)
        
        # Add similar papers
        if 'similar_papers' in data:
            y_position -= 10
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y_position, "Similar Research Papers:")
            p.setFont("Helvetica", 12)
            y_position -= 20
            
            for i, paper in enumerate(data['similar_papers'], 1):
                p.drawString(50, y_position, f"{i}. {paper['title']}")
                y_position -= 15
                p.drawString(70, y_position, f"Authors: {paper['authors']}")
                y_position -= 15
                p.drawString(70, y_position, f"Year: {paper['year']}")
                y_position -= 15
                p.drawString(70, y_position, f"Similarity: {(paper['similarity_score'] * 100):.1f}%")
                y_position -= 10
                
                if y_position < 100:
                    p.showPage()
                    y_position = 750
                    p.setFont("Helvetica", 12)
        
        p.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='research_analysis.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, host='0.0.0.0', port=5003)