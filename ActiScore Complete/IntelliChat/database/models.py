from datetime import datetime

class AttendanceRecord:
    def __init__(self, student_id, date, status, hours):
        self.student_id = student_id
        self.date = date
        self.status = status
        self.hours = hours

class Summary:
    def __init__(self, title, content, category, created_at):
        self.title = title
        self.content = content
        self.category = category
        self.created_at = created_at

class Analytics:
    def __init__(self, metric, value, trend, insights):
        self.metric = metric
        self.value = value
        self.trend = trend
        self.insights = insights

class ResearchPaper:
    def __init__(self, title, authors, abstract, keywords, published_date):
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.keywords = keywords
        self.published_date = published_date