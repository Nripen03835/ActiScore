import sqlite3
import os
from config import config

def init_database():
    """Initialize the SQLite database with required tables"""
    
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            email TEXT,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add photo_path column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE students ADD COLUMN photo_path TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            emotion TEXT,
            confidence REAL,
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    ''')
    
    # Create emotions table for analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            emotion TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data
    sample_students = [
        ('John Doe', 'S001', 'john@university.edu', None),
        ('Jane Smith', 'S002', 'jane@university.edu', None),
        ('Mike Johnson', 'S003', 'mike@university.edu', None),
        ('Sarah Wilson', 'S004', 'sarah@university.edu', None),
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO students (name, student_id, email, photo_path) VALUES (?, ?, ?, ?)',
        sample_students
    )
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()