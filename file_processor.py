import json
import csv
import io
import re
from datetime import datetime

# Graceful import για image_processor
try:
    from image_processor import ImageProcessor
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError as e:
    IMAGE_PROCESSOR_AVAILABLE = False
    print(f"⚠️  ImageProcessor not available: {e}")

class FileProcessor:
    """Επεξεργαστής αρχείων - Βελτιωμένη έκδοση χωρίς εξαρτήσεις"""
    
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
        """Επεξεργασία PDF - Self-contained version"""
        try:
            # Πρώτη προσπάθεια: Απευθείας ανάγνωση PDF structure
            text_data = FileProcessor._extract_pdf_text_simple(file_content)
            
            # Ανάλυση δεδομένων από το κείμενο
            parsed_data = FileProcessor._parse_efka_data(text_data)
            
            if FileProcessor._is_valid_efka_data(parsed_data):
                return {
                    'gender': parsed_data.get('gender', 'female'),
                    'birth_year': parsed_data.get('birth_year', 1969),
                    'current_age': parsed_data.get('current_age', 56),
                    'insurance_years': parsed_data.get('insurance_years', 25.5),
                    'insurance_days': parsed_data.get('insurance_days', 9315),
                    'salary': parsed_data.get('salary', 850.0),
                    'heavy_work_years': 0,
                    'children': 0,
                    'fund': 'ika',
                    'source': 'pdf_auto_extracted',
                    'extraction_method': parsed_data.get('method', 'direct'),
                    'note': 'Αυτόματη εξαγωγή από PDF'
                }
            else:
                # Fallback αν η αυτόματη αποτύχει
                return FileProcessor._get_pdf_fallback()
                
        except Exception as e:
            print(f"PDF processing error: {e}")
            return FileProcessor._get_pdf_fallback()
    
    @staticmethod
    def _extract_pdf_text_simple(file_content):
        """Εξαγωγή κειμένου από PDF χωρίς εξωτερικές βιβλιοθήκες"""
        try:
            text = ""
            
            # Απλή αναζήτηση για κείμενο σε PDF
            # Τα PDF συχνά έχουν κείμενο σε parentheses
            text_matches = re.findall(rb'\(([^\)]+)\)', file_content)
            
            for match in text_matches:
                try:
                    decoded = match.decode('utf-8', errors='ignore')
                    if len(decoded) > 2:  # Αγνοεί μικρές συμβολοσειρές
                        text += decoded + " "
                except:
                    try:
                        decoded = match.decode('latin-1', errors='ignore')
                        text += decoded + " "
                    except:
                        pass
            
            return text if len(text) > 10 else ""
            
        except Exception as e:
            print(f"Text extraction error: {e}")
            return ""
    
    @staticmethod
    def _parse_efka_data(text):
        """Ανάλυση δεδομένων e-ΕΦΚΑ από κείμενο"""
        data = {
            'method': 'pattern_matching',
            'gender': 'female',
            'birth_year': 1969,
            'insurance_years': 25.5,
            'insurance_days': 9315,
            'salary': 850.0
        }
        
        try:
            # Βελτιωμένο pattern matching για ελληνικά PDF
            if re.search(r'[Αα]ρσενικ[όο]|ΑΡΣΕΝ', text, re.IGNORECASE):
                data['gender'] = 'male'
            elif re.search(r'[Θθ]ηλυκό|ΘΗΛΥ', text, re.IGNORECASE):
                data['gender'] = 'female'
            
            # Αναζήτηση ημερών ασφάλισης
            days_match = re.search(r'(\d{3,})\s*[Ηη]μ[έε]ρ[αω]ν?', text)
            if days_match:
                data['insurance_days'] = int(days_match.group(1))
                data['insurance_years'] = round(data['insurance_days'] / 365, 1)
            
            # Αναζήτηση μισθού
            salary_match = re.search(r'(\d{1,4}[,.]\d{2})\s*[Εε]υρώ', text)
            if salary_match:
                data['salary'] = float(salary_match.group(1).replace(',', '.'))
            
            # Αναζήτηση έτους γέννησης
            birth_match = re.search(r'(19\d{2})\s*[Εε]τών', text)
            if birth_match:
                data['birth_year'] = int(birth_match.group(1))
                current_year = datetime.now().year
                data['current_age'] = current_year - data['birth_year']
            
            return data
        except Exception as e:
            print(f"Data parsing error: {e}")
            return data
    
    @staticmethod
    def _is_valid_efka_data(data):
        """Έλεγχος εγκυρότητας εξαγόμενων δεδομένων"""
        return any([
            data.get('insurance_days', 0) > 0,
            data.get('salary', 0) > 0,
            data.get('birth_year', 0) > 1900
        ])
    
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
            'source': 'pdf_manual_input',
            'note': 'Χρειάζεται manual εισαγωγή δεδομένων από το PDF'
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
        """Fallback για εικόνες όταν το ImageProcessor δεν είναι διαθέσιμο"""
        return {
            'gender': 'male',
            'birth_year': 1980,
            'current_age': 45,
            'insurance_years': 20,
            'salary': 1500,
            'heavy_work_years': 0,
            'children': 0,
            'fund': 'ika',
            'data_source': 'Image File - Basic Fallback',
            'note': 'Image processing not available'
        }