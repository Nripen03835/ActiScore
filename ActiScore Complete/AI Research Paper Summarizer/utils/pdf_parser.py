import PyPDF2
import pdfplumber
import io
import magic
import re

class PDFParser:
    def __init__(self):
        self.supported_mime_types = [
            'application/pdf',
            'text/plain'
        ]
    
    def is_pdf(self, file_stream):
        """Check if the uploaded file is a PDF"""
        file_stream.seek(0)
        file_start = file_stream.read(1024)
        file_stream.seek(0)
        
        # Check for PDF magic number
        if file_start.startswith(b'%PDF'):
            return True
        
        # Use python-magic for more accurate detection
        try:
            mime = magic.from_buffer(file_start, mime=True)
            return mime == 'application/pdf'
        except:
            # Fallback: check file extension or content
            return False
    
    def extract_text_from_pdf(self, file_stream):
        """Extract text from PDF file using multiple methods for better accuracy"""
        file_stream.seek(0)
        
        extracted_text = ""
        
        # Method 1: Try pdfplumber (better for modern PDFs)
        try:
            with pdfplumber.open(file_stream) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            
            if extracted_text.strip():
                return self.clean_text(extracted_text)
        except Exception as e:
            print(f"pdfplumber failed: {e}")
        
        # Method 2: Try PyPDF2 (fallback for older PDFs)
        try:
            file_stream.seek(0)
            pdf_reader = PyPDF2.PdfReader(file_stream)
            extracted_text = ""
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            
            return self.clean_text(extracted_text)
        except Exception as e:
            print(f"PyPDF2 failed: {e}")
        
        # Method 3: Try combined approach
        try:
            file_stream.seek(0)
            combined_text = ""
            
            # Try pdfplumber for main content
            with pdfplumber.open(file_stream) as pdf:
                for page in pdf.pages:
                    # Extract tables if any
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            for row in table:
                                combined_text += ' '.join([str(cell) for cell in row if cell]) + " "
                    
                    # Extract text
                    text = page.extract_text()
                    if text:
                        combined_text += text + " "
            
            return self.clean_text(combined_text)
        except Exception as e:
            print(f"Combined approach failed: {e}")
        
        return ""
    
    def clean_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'\b\d+\s*\n', ' ', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)  # Handle hyphenated words
        text = re.sub(r'\s*\.\s*', '. ', text)  # Fix spacing around periods
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\?\!\(\)\-]', ' ', text)
        
        return text.strip()
    
    def parse_file(self, file_stream, filename):
        """Main method to parse uploaded file"""
        file_stream.seek(0)
        
        # Check file type
        if filename.lower().endswith('.pdf') or self.is_pdf(file_stream):
            return self.extract_text_from_pdf(file_stream)
        elif filename.lower().endswith('.txt'):
            # Read text file
            file_stream.seek(0)
            return file_stream.read().decode('utf-8')
        else:
            raise ValueError("Unsupported file format. Please upload PDF or TXT files.")