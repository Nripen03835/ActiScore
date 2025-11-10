import json
import os
from datetime import datetime, timedelta

def create_sample_data():
    # Create directories if they don't exist
    os.makedirs('database/sample_data', exist_ok=True)
    
    # Sample attendance data
    attendance_data = [
        {
            "student_id": "S001",
            "student_name": "John Doe",
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "status": "Present",
            "hours": 8
        } for i in range(30)
    ]
    
    # Sample summaries
    summaries_data = [
        {
            "title": "Quarterly Business Review",
            "content": "The company showed strong growth in Q3 with a 15% increase in revenue and 20% growth in user base.",
            "category": "Business",
            "created_at": datetime.now().strftime("%Y-%m-%d")
        },
        {
            "title": "Team Performance Analysis",
            "content": "Development team achieved 95% of sprint goals with improved code quality metrics.",
            "category": "Performance",
            "created_at": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        }
    ]
    
    # Sample analytics
    analytics_data = [
        {
            "metric": "User Engagement",
            "value": "78%",
            "trend": "up",
            "insights": "15% increase from last month due to new feature releases"
        },
        {
            "metric": "Customer Acquisition Cost",
            "value": "$45.20",
            "trend": "down",
            "insights": "Improved marketing efficiency reduced CAC by 8%"
        }
    ]
    
    # Sample research papers
    research_data = [
        {
            "title": "Advanced Machine Learning Techniques",
            "authors": ["Dr. Smith", "Dr. Johnson"],
            "abstract": "This paper explores novel approaches to deep learning optimization...",
            "keywords": ["machine learning", "deep learning", "optimization"],
            "published_date": "2023-10-15"
        },
        {
            "title": "Blockchain in Supply Chain Management",
            "authors": ["Prof. Wilson", "Dr. Brown"],
            "abstract": "Research on implementing blockchain technology for transparent supply chains...",
            "keywords": ["blockchain", "supply chain", "transparency"],
            "published_date": "2023-09-20"
        }
    ]
    
    # Save sample data
    with open('database/sample_data/attendance.json', 'w') as f:
        json.dump(attendance_data, f, indent=2)
    
    with open('database/sample_data/summaries.json', 'w') as f:
        json.dump(summaries_data, f, indent=2)
    
    with open('database/sample_data/analytics.json', 'w') as f:
        json.dump(analytics_data, f, indent=2)
    
    with open('database/sample_data/research.json', 'w') as f:
        json.dump(research_data, f, indent=2)

if __name__ == "__main__":
    create_sample_data()