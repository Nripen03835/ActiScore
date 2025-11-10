import pytesseract
from pdf2image import convert_from_path
import PyPDF2
import os
from PIL import Image

class FileProcessor:
    def __init__(self):
        # Set tesseract path (you might need to adjust this)
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
    
    def process_file(self, filepath):
        file_ext = filepath.lower().split('.')[-1]
        
        if file_ext == 'txt':
            return self._process_txt(filepath)
        elif file_ext == 'pdf':
            return self._process_pdf(filepath)
        elif file_ext in ['png', 'jpg', 'jpeg']:
            return self._process_image(filepath)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _process_txt(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _process_pdf(self, filepath):
        text = ""
        
        # Try text extraction first
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # If little text was extracted, try OCR
            if len(text.strip()) < 100:
                text = self._ocr_pdf(filepath)
        except Exception as e:
            print(f"PDF text extraction failed, using OCR: {e}")
            text = self._ocr_pdf(filepath)
        
        return text
    
    def _ocr_pdf(self, filepath):
        text = ""
        try:
            images = convert_from_path(filepath, dpi=200)
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
        except Exception as e:
            raise Exception(f"OCR processing failed: {e}")
        
        return text
    
    def _process_image(self, filepath):
        try:
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"Image processing failed: {e}")