from flask import Flask, render_template, request, jsonify
from rag_system import RAGSystem
from database.sample_data import create_sample_data
import os

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize RAG system
rag_system = RAGSystem()

# Flag to track if data has been initialized
data_initialized = False

@app.before_request
def initialize_data_on_first_request():
    """Create sample data and build index on first request"""
    global data_initialized
    if not data_initialized:
        if not os.path.exists('database/sample_data/attendance.json'):
            create_sample_data()
        rag_system.build_index()
        data_initialized = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get response from RAG system
        response = rag_system.query(user_message)
        
        return jsonify({
            'response': response,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'IntelliChat'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)