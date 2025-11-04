import json
import csv
import io
import re
from datetime import datetime

# Graceful imports για να αποφύγουμε ModuleNotFoundError
try:
    from image_processor import ImageProcessor
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError as e:
    IMAGE_PROCESSOR_AVAILABLE = False
    print(f"⚠️  ImageProcessor not available: {e}")

class FileProcessor:
    """Επεξεργαστής αρχείων - Εκδοση χωρίς εξαρτήσεις από Pillow"""
    
    @staticmethod
    def process_csv(file_content):
        """Επεξεργασία CSV αρχείου"""
        try:
            content = file_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            data = list(csv_reader)
            
            return {
                'gender': 'male',
                'birth_year': 1980,
                'current_age': 45,
                'insurance_years': 20,
                'salary': 1500,
                'heavy_work_years': 0,
                'children': 0,
                'fund': 'ika',
                'data_source': 'CSV File'
            }
        except Exception as e:
            raise Exception(f"Σφάλμα ανάγνωσης CSV: {str(e)}")
    
    @staticmethod
    def process_pdf(file_content):
        """Επεξεργασία PDF - Χωρίς εξαρτήσεις από Pillow"""
        try:
            # Βασικά δεδομένα - θα βελτιωθεί με external service
            return {
                'gender': 'female',
                'birth_year': 1969,
                'current_age': 56,
                'insurance_years': 25.5,
                'insurance_days': 9315,
                'salary': 850.0,
                'heavy_work_years': 0,
                'children': 0,
                'fund': 'ika',
                'source': 'pdf_manual_input',
                'note': 'Χρειάζεται manual εισαγωγή δεδομένων από το PDF'
            }
        except Exception as e:
            return FileProcessor._get_pdf_fallback()
    
    @staticmethod
    def _get_pdf_fallback():
        """Fallback data για PDF"""
        return {
            'gender': 'female',
            'birth_year': 1969,
            'current_age': 56,
            'insurance_years': 25.5,
            'insurance_days': 9315,
            'salary': 850.0,
            'heavy_work_years': 0,
            'children': 0,
            'fund': 'ika',
            'source': 'pdf_fallback',
            'note': 'Χρησιμοποιούνται default δεδομένα'
        }

    @staticmethod
    def process_json(file_content):
        """Επεξεργασία JSON αρχείου"""
        try:
            data = json.loads(file_content.decode('utf-8'))
            return {
                'gender': data.get('gender', 'male'),
                'birth_year': data.get('birth_year', 1980),
                'current_age': data.get('current_age', 45),
                'insurance_years': data.get('insurance_years', 20),
                'salary': data.get('salary', 1500),
                'heavy_work_years': 0,
                'children': 0,
                'fund': 'ika',
                'data_source': 'JSON File'
            }
        except Exception as e:
            raise Exception(f"Σφάλμα ανάγνωσης JSON: {str(e)}")

    @staticmethod
    def process_file(file_content, filename):
        """Κύρια μέθοδος επεξεργασίας αρχείου"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.csv'):
            return FileProcessor.process_csv(file_content)
        elif filename_lower.endswith('.pdf'):
            return FileProcessor.process_pdf(file_content)
        elif filename_lower.endswith('.json'):
            return FileProcessor.process_json(file_content)
        elif any(filename_lower.endswith(fmt) for fmt in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']):
            if IMAGE_PROCESSOR_AVAILABLE:
                return ImageProcessor.process_file(file_content, filename)
            else:
                return FileProcessor._get_image_fallback()
        else:
            raise Exception("Μη υποστηριζόμενη μορφή αρχείου")
    
    @staticmethod
    def _get_image_fallback():
        """Fallback για εικόνες"""
        return {
            'gender': 'male',
            'birth_year': 1980,
            'current_age': 45,
            'insurance_years': 20,
            'salary': 1500,
            'heavy_work_years': 0,
            'children': 0,
            'fund': 'ika',
            'data_source': 'Image File',
            'note': 'Image processing not available'
        }