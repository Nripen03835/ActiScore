from datetime import datetime, timedelta
import json

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        return timestamp
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def get_time_ranges():
    """Get time ranges for analytics"""
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    return {
        'today': today.strftime('%Y-%m-%d'),
        'week_ago': week_ago.strftime('%Y-%m-%d'),
        'month_ago': month_ago.strftime('%Y-%m-%d')
    }

def prepare_chart_data(attendance_df, emotion_df):
    """Prepare data for charts"""
    # Attendance chart data
    attendance_dates = attendance_df['date'].tolist()
    attendance_rates = attendance_df['attendance_rate'].tolist()
    
    # Emotion chart data
    emotions = [item['emotion'] for item in emotion_df]
    emotion_counts = [item['count'] for item in emotion_df]
    
    return {
        'attendance_dates': json.dumps(attendance_dates),
        'attendance_rates': json.dumps(attendance_rates),
        'emotions': json.dumps(emotions),
        'emotion_counts': json.dumps(emotion_counts)
    }