import PyPDF2
import io
import re
from datetime import datetime

class GreekPensionPDFProcessor:
    """
    Επεξεργαστής PDF αρχείων ελληνικής σύνταξης
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def process_pdf(self, pdf_file):
        """
        Επεξεργασία αρχείου PDF και εξαγωγή πληροφοριών σύνταξης
        """
        try:
            # Επαναφορά του file pointer
            pdf_file.seek(0)
            
            # Δημιουργία PDF reader
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
            
            # Εξαγωγή όλου του κειμένου από το PDF
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
            
            print(f"📄 Extracted text length: {len(full_text)} characters")
            
            # Ανάλυση κειμένου για εύρεση πληροφοριών
            extracted_data = self.analyze_pension_text(full_text)
            
            return extracted_data
            
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            return self.get_default_data(str(e))
    
    def analyze_pension_text(self, text):
        """
        Ανάλυση κειμένου PDF για εξαγωγή πληροφοριών σύνταξης
        """
        # Καθαρισμός κειμένου
        clean_text = self.clean_text(text)
        
        # Εξαγωγή δεδομένων
        data = {
            'customer_name': self.extract_customer_name(clean_text),
            'afm': self.extract_afm(clean_text),
            'insurance_years': self.extract_insurance_years(clean_text),
            'retirement_age': self.extract_retirement_age(clean_text),
            'remaining_years': self.calculate_remaining_years(clean_text),
            'retirement_date': self.calculate_retirement_date(),
            'status': self.determine_status(clean_text),
            'confidence_score': self.calculate_confidence(clean_text),
            'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_type': 'PDF',
            'raw_text_sample': clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
        }
        
        return data
    
    def clean_text(self, text):
        """Καθαρισμός και προεπεξεργασία κειμένου"""
        # Αφαίρεση πολλαπλών κενών
        text = re.sub(r'\s+', ' ', text)
        # Μετατροπή σε uppercase για ευκολότερη ανάλυση
        text = text.upper()
        return text.strip()
    
    def extract_customer_name(self, text):
        """Εξαγωγή ονόματος πελάτη"""
        # Πρότυπα για όνομα
        patterns = [
            r'ΟΝΟΜΑΤΕΠΩΝΥΜΟ[:\s]+([Α-ΩΑ-Ω\s]+?)(?:\n|ΑΦΜ|$)',
            r'ΕΠΩΝΥΜΟ[:\s]+([Α-ΩΑ-Ω\s]+?)(?:\n|ΟΝΟΜΑ|$)',
            r'ΠΕΛΑΤΗΣ[:\s]+([Α-ΩΑ-Ω\s]+?)(?:\n|$)',
            r'ΑΠΟΔΟΧΕΑΣ[:\s]+([Α-ΩΑ-Ω\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3:  # Ελάχιστο μήκος για όνομα
                    return name.title()
        
        # Εναλλακτική μέθοδος - ψάχνουμε για ελληνικά ονόματα
        greek_name_match = re.search(r'([Α-ΩΑ-Ω]{3,}\s+[Α-ΩΑ-Ω]{3,})', text)
        if greek_name_match:
            return greek_name_match.group(1).title()
        
        return "Ανώνυμος Πελάτης"
    
    def extract_afm(self, text):
        """Εξαγωγή ΑΦΜ"""
        # Πρότυπα για ΑΦΜ (9 ψηφία)
        afm_patterns = [
            r'ΑΦΜ[:\s]*(\d{9})',
            r'ΦΠΑ[:\s]*(\d{9})',
            r'ΤΑΥΤΟΤΗΤΑ[:\s]*(\d{9})',
            r'\b(\d{9})\b'
        ]
        
        for pattern in afm_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return "000000000"
    
    def extract_insurance_years(self, text):
        """Εξαγωγή ετών ασφάλισης"""
        # Πρότυπα για έτη ασφάλισης
        patterns = [
            r'ΕΤΗ[:\s]*ΑΣΦΑΛΙΣΗΣ[:\s]*(\d+[.,]?\d*)',
            r'ΑΣΦΑΛΙΣΤΙΚΑ[:\s]*ΕΤΗ[:\s]*(\d+[.,]?\d*)',
            r'ΕΝΣΗΜΑ[:\s]*(\d+[.,]?\d*)[\s]*ΕΤΗ',
            r'(\d+[.,]?\d*)[\s]*ΕΤΩΝ[\s]*ΑΣΦΑΛΙΣΗΣ'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                years = match.group(1).replace(',', '.')
                try:
                    return float(years)
                except ValueError:
                    continue
        
        # Προεπιλεγμένες τιμές ανά ηλικία
        if "65" in text or "ΣΥΝΤΑΞΙΟΔΟΤΗΣΗ" in text:
            return 40.0
        elif "60" in text:
            return 35.0
        else:
            return 25.0  # Προεπιλεγμένη τιμή
    
    def extract_retirement_age(self, text):
        """Εξαγωγή ηλικίας συνταξιοδότησης"""
        patterns = [
            r'ΗΛΙΚΙΑ[:\s]*ΣΥΝΤΑΞΙΟΔΟΤΗΣΗΣ[:\s]*(\d+)',
            r'ΣΥΝΤΑΞΙΟΔΟΤΗΣΗ[:\s]*ΣΤΑ[:\s]*(\d+)',
            r'ΗΛΙΚΙΑ[:\s]*(\d+)[\s]*ΕΤΩΝ'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        # Προεπιλεγμένη ηλικία
        return 67
    
    def calculate_remaining_years(self, text):
        """Υπολογισμός υπολοίπων ετών μέχρι σύνταξη"""
        retirement_age = self.extract_retirement_age(text)
        
        # Προσπάθεια εύρεσης τρέχουσας ηλικίας
        age_pattern = r'ΗΛΙΚΙΑ[:\s]*(\d+)'
        age_match = re.search(age_pattern, text)
        
        if age_match:
            current_age = int(age_match.group(1))
            return max(0, retirement_age - current_age)
        
        # Προεπιλεγμένη τιμή
        return retirement_age - 45  # Υποθέτουμε τρέχουσα ηλικία 45
    
    def calculate_retirement_date(self):
        """Υπολογισμός προσεγγιστικής ημερομηνίας συνταξιοδότησης"""
        from datetime import datetime, timedelta
        remaining_years = 15  # Προεπιλεγμένη τιμή
        retirement_date = datetime.now() + timedelta(days=remaining_years * 365)
        return retirement_date.strftime('%Y-%m-%d')
    
    def determine_status(self, text):
        """Προσδιορισμός κατάστασης"""
        if "ΕΝΕΡΓΟΣ" in text or "ΕΡΓΑΖΟΜΕΝΟΣ" in text:
            return "Ενεργός"
        elif "ΣΥΝΤΑΞΙΟΥΧΟΣ" in text or "ΣΥΝΤΑΞΗ" in text:
            return "Συνταξιούχος"
        elif "ΑΝΕΡΓΟΣ" in text:
            return "Άνεργος"
        else:
            return "Άγνωστη Κατάσταση"
    
    def calculate_confidence(self, text):
        """Υπολογισμός βαθμού εμπιστοσύνης για τα εξαγόμενα δεδομένα"""
        confidence = 0.5  # Βασικό score
        
        # Αύξηση confidence βάσει των δεδομένων που βρέθηκαν
        if self.extract_afm(text) != "000000000":
            confidence += 0.2
        if self.extract_customer_name(text) != "Ανώνυμος Πελάτης":
            confidence += 0.15
        if "ΑΣΦΑΛΙΣΗ" in text or "ΕΝΣΗΜΑ" in text:
            confidence += 0.1
        if "ΣΥΝΤΑΞΗ" in text or "ΣΥΝΤΑΞΙΟΔΟΤΗΣΗ" in text:
            confidence += 0.05
        
        return min(confidence, 1.0)  # Μέγιστο 1.0
    
    def get_default_data(self, error_message=""):
        """Προεπιλεγμένα δεδομένα σε περίπτωση σφάλματος"""
        return {
            'customer_name': 'Ανώνυμος Πελάτης',
            'afm': '000000000',
            'insurance_years': 0.0,
            'retirement_age': 67,
            'remaining_years': 0.0,
            'retirement_date': '',
            'status': 'Σφάλμα Επεξεργασίας',
            'confidence_score': 0.0,
            'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file_type': 'PDF',
            'error': error_message
        }


# Βοηθητική συνάρτηση για backward compatibility
def process_ultimate_pension_pdf(pdf_content):
    """
    Βοηθητική συνάρτηση για συμβατότητα με υπάρχοντα code
    """
    processor = GreekPensionPDFProcessor()
    
    # Δημιουργία file-like object από το content
    import io
    pdf_file = io.BytesIO(pdf_content)
    
    result = processor.process_pdf(pdf_file)
    
    # Μετατροπή για συμβατότητα
    return {
        'customer_name': result.get('customer_name', 'Ανώνυμος'),
        'afm': result.get('afm', '000000000'),
        'insurance_years': result.get('insurance_years', 0),
        'retirement_age': result.get('retirement_age', 67),
        'remaining_years': result.get('remaining_years', 0),
        'retirement_date': result.get('retirement_date', ''),
        'status': result.get('status', 'Άγνωστο'),
        'confidence_score': result.get('confidence_score', 0.0)
    }