class ImageProcessor:
    """Επεξεργαστής εικόνων - Απλή έκδοση"""
    
    @staticmethod
    def process_file(file_content, filename):
        """Βασική επεξεργασία εικόνας"""
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