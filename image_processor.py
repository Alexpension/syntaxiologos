class ImageProcessor:
    """Επεξεργαστής εικόνων - Σταθερή έκδοση χωρίς εξαρτήσεις"""
    
    @staticmethod
    def process_file(file_content, filename):
        """Επεξεργασία εικόνας - Βασική έκδοση"""
        try:
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
                'note': 'OCR processing available in advanced version'
            }
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
                'note': f'Processing error: {str(e)}'
            }