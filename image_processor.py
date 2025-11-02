import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import re
from datetime import datetime, date

class ImageProcessor:
    """Επεξεργαστής εικόνων για εξαγωγή δεδομένων σύνταξης από screenshots"""
    
    @staticmethod
    def process_image(image_content):
        """Επεξεργασία εικόνας και εξαγωγή κειμένου"""
        try:
            # Μετατροπή bytes σε εικόνα
            image = Image.open(io.BytesIO(image_content))
            
            # Προεπεξεργασία εικόνας για καλύτερο OCR
            processed_image = ImageProcessor._preprocess_image(image)
            
            # Εξαγωγή κειμένου με Ελληνικά
            text = pytesseract.image_to_string(processed_image, lang='ell+eng')
            
            print(f"📄 Κείμενο από εικόνα ({len(text)} χαρακτήρες):")
            print("=" * 50)
            print(text)
            print("=" * 50)
            
            # Εξαγωγή δεδομένων από το κείμενο
            extracted_data = ImageProcessor._extract_pension_data(text)
            
            return extracted_data
            
        except Exception as e:
            raise Exception(f"Σφάλμα επεξεργασίας εικόνας: {str(e)}")
    
    @staticmethod
    def _preprocess_image(image):
        """Προεπεξεργασία εικόνας για βελτίωση OCR"""
        # Μετατροπή σε grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Μετατροπή σε numpy array για OpenCV
        img_array = np.array(image)
        
        # Προσαρμογή αντίθεσης
        img_array = cv2.convertScaleAbs(img_array, alpha=1.5, beta=0)
        
        # Κατάργηση θορύβου
        img_array = cv2.medianBlur(img_array, 3)
        
        # Thresholding για καλύτερο κείμενο
        _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Μετατροπή πίσω σε PIL Image
        return Image.fromarray(img_array)
    
    @staticmethod
    def _extract_pension_data(text):
        """Εξαγωγή δεδομένων σύνταξης από κείμενο"""
        extracted = {}
        
        print("🔍 Εξαγωγή δεδομένων από κείμενο...")
        
        # Βελτιωμένα patterns για ελληνικά ασφαλιστικά δεδομένα
        patterns = {
            'amka': [
                r'ΑΜΚΑ[\s:\-]*(\d{11})',
                r'Α\.Μ\.Κ\.Α\.[\s:\-]*(\d{11})',
                r'(\d{11})(?=\D|$)'
            ],
            'afm': [
                r'ΑΦΜ[\s:\-]*(\d{9})',
                r'Α\.Φ\.Μ\.[\s:\-]*(\d{9})',
                r'(\d{9})(?=\D|$)'
            ],
            'name': [
                r'ΟΝΟΜΑΤΕΠΩΝΥΜΟ[\s:\-]*([^\n\r]+)',
                r'ΕΠΩΝΥΜΟ[\s:\-]*([^\n\r]+)',
                r'ΟΝΟΜΑ[\s:\-]*([^\n\r]+)'
            ],
            'birth_date': [
                r'ΗΜΕΡΟΜΗΝΙΑ ΓΕΝΝΗΣΗΣ[\s:\-]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
                r'ΓΕΝΝΗΣΗ[\s:\-]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
                r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})'
            ],
            'insurance_days': [
                r'ΗΜΕΡΕΣ ΑΣΦΑΛΙΣΗΣ[\s:\-]*(\d+)',
                r'ΑΣΦΑΛΙΣΜΕΝΕΣ ΗΜΕΡΕΣ[\s:\-]*(\d+)',
                r'ΗΜΕΡΕΣ[\s:\-]*(\d+)'
            ],
            'salary': [
                r'ΜΙΣΘΟΣ[\s:\-]*(\d+[\.,]?\d*)',
                r'ΕΙΣΟΔΗΜΑ[\s:\-]*(\d+[\.,]?\d*)',
                r'ΜΕΣΟΣ ΟΡΟΣ[\s:\\-]*(\d+[\.,]?\d*)',
                r'(\d+[\.,]?\d*)\s*€'
            ],
            'insurance_years': [
                r'ΕΤΗ ΑΣΦΑΛΙΣΗΣ[\s:\-]*(\d+)',
                r'ΑΣΦΑΛΙΣΤΙΚΑ ΕΤΗ[\s:\-]*(\d+)',
                r'(\d+)\s*ΕΤΗ'
            ],
            'employer': [
                r'ΕΡΓΟΔΟΤΗΣ[\s:\-]*([^\n\r]+)',
                r'ΕΤΑΙΡΕΙΑ[\s:\-]*([^\n\r]+)'
            ],
            'fund': [
                r'ΤΑΜΕΙΟ[\s:\-]*([^\n\r]+)',
                r'ΑΣΦΑΛΙΣΤΙΚΟ ΤΑΜΕΙΟ[\s:\-]*([^\n\r]+)',
                r'ΙΚΑ|ΕΦΚΑ|ΟΑΕΕ|ΕΤΑΑ|ΤΕΒΕ'
            ]
        }
        
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted[field] = match.group(1) if match.groups() else match.group(0)
                    print(f"    ✅ Βρέθηκε {field}: {extracted[field]}")
                    break
        
        # Ειδική επεξεργασία για ονόματα
        if 'name' in extracted:
            extracted['name'] = ImageProcessor._clean_name(extracted['name'])
        
        # Υπολογισμός ηλικίας από ημερομηνία γέννησης
        if 'birth_date' in extracted:
            birth_date = ImageProcessor._parse_date(extracted['birth_date'])
            if birth_date:
                extracted['current_age'] = ImageProcessor._calculate_age(birth_date)
                extracted['birth_year'] = birth_date.year
                print(f"    🎂 Ηλικία από ημερομηνία: {extracted['current_age']} ετών")
        
        # Μετατροπή ημερών σε έτη
        if 'insurance_days' in extracted and 'insurance_years' not in extracted:
            try:
                days = int(extracted['insurance_days'])
                extracted['insurance_years'] = round(days / 365.25, 1)
                print(f"    📅 Μετατροπή {days} ημερών σε {extracted['insurance_years']} έτη")
            except:
                pass
        
        # Καθαρισμός μισθού
        if 'salary' in extracted:
            extracted['salary'] = ImageProcessor._clean_salary(extracted['salary'])
        
        # Αντιστοίχιση ταμείου
        if 'fund' in extracted:
            extracted['fund'] = ImageProcessor._map_fund(extracted['fund'])
        
        # Default τιμές ΜΟΝΟ αν δεν βρέθηκε τίποτα
        defaults = {
            'gender': 'male',
            'current_age': 45,
            'insurance_years': 25,
            'salary': 1500,
            'heavy_work_years': 0,
            'children': 0,
            'fund': 'ika'
        }
        
        for key, value in defaults.items():
            if key not in extracted:
                extracted[key] = value
                print(f"    ⚠️ Χρήση default για {key}: {value}")
        
        return extracted
    
    @staticmethod
    def _clean_name(name):
        """Καθαρισμός ονόματος"""
        clean_name = re.sub(r'(ΟΝΟΜΑΤΕΠΩΝΥΜΟ|ΕΠΩΝΥΜΟ|ΟΝΟΜА)[\s:\-]*', '', name, flags=re.IGNORECASE)
        return clean_name.strip()
    
    @staticmethod
    def _clean_salary(salary_str):
        """Καθαρισμός μισθού"""
        try:
            clean_salary = re.sub(r'[^\d,.]', '', salary_str)
            clean_salary = clean_salary.replace(',', '.')
            return float(clean_salary)
        except:
            return 1500
    
    @staticmethod
    def _parse_date(date_str):
        """Ανάλυση ημερομηνίας"""
        try:
            date_str = str(date_str).strip()
            formats = [
                '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
                '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
        except:
            pass
        return None
    
    @staticmethod
    def _calculate_age(birth_date):
        """Υπολογισμός ηλικίας"""
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    @staticmethod
    def _map_fund(fund_str):
        """Αντιστοίχιση ταμείου"""
        fund_str = str(fund_str).lower()
        
        fund_mapping = {
            'ika': 'ika', 'εφκα': 'efka', 'efka': 'efka',
            'οαεε': 'oaee', 'oaee': 'oaee', 'εταα': 'etaa', 'etaa': 'etaa',
            'tebe': 'tebe', 'τεβε': 'tebe'
        }
        
        for key, value in fund_mapping.items():
            if key in fund_str:
                return value
        
        return 'ika'

    @staticmethod
    def process_file(file_content, filename):
        """Κύρια μέθοδος επεξεργασίας αρχείου εικόνας"""
        supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        filename_lower = filename.lower()
        
        if any(filename_lower.endswith(fmt) for fmt in supported_formats):
            return ImageProcessor.process_image(file_content)
        else:
            raise Exception("Μη υποστηριζόμενη μορφή εικόνας")