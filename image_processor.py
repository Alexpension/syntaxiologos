try:
    import pytesseract
    from PIL import Image
    import io
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("⚠️  pytesseract not available - OCR disabled")

class ImageProcessor:
    """Επεξεργαστής εικόνων με σωστή κωδικοποίηση Ελληνικών"""
    
    @staticmethod
    def process_file(file_content, filename):
        """Επεξεργασία εικόνας - Βελτιωμένη έκδοση με σωστή κωδικοποίηση"""
        try:
            # Βασικά δεδομένα fallback
            base_data = {
                'gender': 'male',
                'birth_year': 1980,
                'current_age': 45,
                'insurance_years': 20,
                'salary': 1500,
                'heavy_work_years': 0,
                'children': 0,
                'fund': 'ika',
                'data_source': 'Image File',
                'ocr_available': PYTESSERACT_AVAILABLE
            }
            
            # Προσπάθεια OCR μόνο αν είναι διαθέσιμο
            if PYTESSERACT_AVAILABLE:
                extracted_text = ImageProcessor._extract_text_with_ocr(file_content)
                if extracted_text:
                    # Χρήση utf-8 για Ελληνικούς χαρακτήρες
                    base_data['extracted_text'] = extracted_text[:500]  
                    base_data['note'] = 'OCR processing completed'
                    
                    # Προσπάθεια ανάλυσης δεδομένων από το κείμενο
                    parsed_data = ImageProcessor._parse_efka_data(extracted_text)
                    if any([parsed_data.get('insurance_days', 0) > 0, 
                           parsed_data.get('salary', 0) > 0,
                           parsed_data.get('birth_year', 0) > 1900]):
                        base_data.update(parsed_data)
                        base_data['data_source'] = 'Image OCR Analysis'
                else:
                    base_data['note'] = 'OCR failed or no text found'
            else:
                base_data['note'] = 'OCR not available - using default data'
            
            return base_data
            
        except Exception as e:
            return {
                'gender': 'male',
                'birth_year': 1980,
                'current_age': 45,
                'insurance_years': 20,
                'salary': 1500,
                'heavy_work_years': 0,
                'children': 0,
                'fund': 'ika',
                'data_source': 'Image File - Error',
                'error': str(e),
                'note': 'Fallback data due to processing error'
            }
    
    @staticmethod
    def _extract_text_with_ocr(file_content):
        """Εξαγωγή κειμένου με OCR και σωστή κωδικοποίηση"""
        if not PYTESSERACT_AVAILABLE:
            return ""
        
        try:
            # Μετατροπή bytes σε εικόνα
            image = Image.open(io.BytesIO(file_content))
            
            # Εξαγωγή κειμένου με Ελληνικά - χρήση utf-8
            text = pytesseract.image_to_string(image, lang='ell')
            
            # Επιστροφή κειμένου με σωστή κωδικοποίηση
            return text.encode('utf-8', errors='ignore').decode('utf-8')
            
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    @staticmethod
    def _parse_efka_data(text):
        """Ανάλυση δεδομένων e-ΕΦΚΑ από κείμενο OCR"""
        data = {}
        
        try:
            # Αναζήτηση φύλου
            if 'αρσεν' in text.lower() or 'αρσενικ' in text.lower():
                data['gender'] = 'male'
            elif 'θηλυ' in text.lower() or 'θηλυκό' in text.lower():
                data['gender'] = 'female'
            
            # Αναζήτηση ημερών ασφάλισης
            import re
            days_match = re.search(r'(\d{3,})\s*ημερ', text.lower())
            if days_match:
                data['insurance_days'] = int(days_match.group(1))
                data['insurance_years'] = round(data['insurance_days'] / 365, 1)
            
            # Αναζήτηση μισθού
            salary_match = re.search(r'(\d{1,4}[,.]\d{2})\s*ευρ', text.lower())
            if salary_match:
                data['salary'] = float(salary_match.group(1).replace(',', '.'))
            
            # Αναζήτηση έτους γέννησης
            birth_match = re.search(r'(19\d{2})', text)
            if birth_match:
                data['birth_year'] = int(birth_match.group(1))
                from datetime import datetime
                current_year = datetime.now().year
                data['current_age'] = current_year - data['birth_year']
            
            return data
        except Exception as e:
            print(f"Data parsing error: {e}")
            return data