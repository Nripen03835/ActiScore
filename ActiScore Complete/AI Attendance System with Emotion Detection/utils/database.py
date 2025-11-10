import sqlite3
import pandas as pd
from datetime import datetime, date
from config import config

class DatabaseManager:
    def __init__(self):
        self.db_path = config.DATABASE_PATH
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def add_attendance(self, student_id, name, emotion, confidence):
        """Add attendance record to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO attendance (student_id, name, emotion, confidence)
            VALUES (?, ?, ?, ?)
        ''', (student_id, name, emotion, confidence))
        
        # Also add to emotions table for analytics
        cursor.execute('''
            INSERT INTO emotions (student_id, emotion)
            VALUES (?, ?)
        ''', (student_id, emotion))
        
        conn.commit()
        conn.close()
    
    def get_today_attendance(self):
        """Get today's attendance records"""
        conn = self.get_connection()
        today = date.today().strftime('%Y-%m-%d')
        
        query = '''
            SELECT * FROM attendance 
            WHERE date(timestamp) = ?
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=[today])
        conn.close()
        return df
    
    def get_attendance_stats(self):
        """Get attendance statistics for dashboard"""
        conn = self.get_connection()
        today = date.today().strftime('%Y-%m-%d')
        
        # Total students
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM students')
        total_students = cursor.fetchone()[0]
        
        # Today's present students
        cursor.execute('''
            SELECT COUNT(DISTINCT student_id) FROM attendance 
            WHERE date(timestamp) = ?
        ''', [today])
        present_today = cursor.fetchone()[0]
        
        # Attendance rate
        attendance_rate = (present_today / total_students * 100) if total_students > 0 else 0
        
        # Emotion distribution
        emotion_query = '''
            SELECT emotion, COUNT(*) as count 
            FROM emotions 
            WHERE date(timestamp) = ?
            GROUP BY emotion
        '''
        emotion_df = pd.read_sql_query(emotion_query, conn, params=[today])
        
        conn.close()
        
        return {
            'total_students': total_students,
            'present_today': present_today,
            'attendance_rate': round(attendance_rate, 2),
            'emotion_distribution': emotion_df.to_dict('records')
        }
    
    def get_attendance_history(self, days=7):
        """Get attendance history for the last N days"""
        conn = self.get_connection()
        
        query = """
            SELECT 
                date(timestamp) as date,
                COUNT(DISTINCT student_id) as present_count,
                (SELECT COUNT(*) FROM students) as total_students
            FROM attendance 
            WHERE date(timestamp) >= date('now', ?)
            GROUP BY date(timestamp)
            ORDER BY date
        """
        
        df = pd.read_sql_query(query, conn, params=[f'-{days} days'])
        df['attendance_rate'] = (df['present_count'] / df['total_students'] * 100).round(2)
        conn.close()
        
        return df

    def get_all_students(self):
        """Get all students from the database"""
        conn = self.get_connection()
        query = 'SELECT * FROM students ORDER BY name'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def delete_student(self, student_id):
        """Delete a student from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        conn.commit()
        conn.close()

    def add_student(self, name, student_id, email, photo_path=None):
        """Add a new student to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO students (name, student_id, email, photo_path)
                VALUES (?, ?, ?, ?)
            ''', (name, student_id, email, photo_path))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Student ID already exists
        finally:
            conn.close()

    def update_student(self, student_id, name, email, photo_path=None):
        """Update student details in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE students
                SET name = ?, email = ?, photo_path = ?
                WHERE student_id = ?
            ''', (name, email, photo_path, student_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating student: {e}")
            return False
        finally:
            conn.close()

    def get_student_by_id(self, student_id):
        """Get a single student's details by student_id"""
        conn = self.get_connection()
        query = 'SELECT * FROM students WHERE student_id = ?'
        df = pd.read_sql_query(query, conn, params=[student_id])
        conn.close()
        if not df.empty:
            return df.iloc[0].to_dict()
        return None