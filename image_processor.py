try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("⚠️  pytesseract not available - OCR disabled")

class ImageProcessor:
    """Επεξεργαστής εικόνων με OCR fallback"""
    
    @staticmethod
    def process_file(file_content, filename):
        """Επεξεργασία εικόνας - Βελτιωμένη έκδοση με fallback"""
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
                    base_data['extracted_text'] = extracted_text[:500]  # Πρώτα 500 chars
                    base_data['note'] = 'OCR processing completed'
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
        """Εξαγωγή κειμένου με OCR"""
        if not PYTESSERACT_AVAILABLE:
            return ""
        
        try:
            from PIL import Image
            import io
            
            # Μετατροπή bytes σε εικόνα
            image = Image.open(io.BytesIO(file_content))
            
            # Εξαγωγή κειμένου με Ελληνικά
            text = pytesseract.image_to_string(image, lang='ell')
            return text.strip()
            
        except Exception as e:
            print(f"OCR error: {e}")
            return ""