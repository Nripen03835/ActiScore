import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    USE_LOCAL_LLM = os.getenv('USE_LOCAL_LLM', 'true').lower() == 'true'
    
    # FAISS Configuration
    FAISS_INDEX_PATH = 'data/faiss_index'
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    
    # Sample data paths
    SAMPLE_DATA = {
        'attendance': 'database/sample_data/attendance.json',
        'summaries': 'database/sample_data/summaries.json',
        'analytics': 'database/sample_data/analytics.json',
        'research': 'database/sample_data/research.json'
    }