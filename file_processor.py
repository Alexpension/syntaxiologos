import pandas as pd
import PyPDF2
import json
import csv
import io
from datetime import datetime
import re

class FileProcessor:
    """Επεξεργαστής αρχείων για εξαγωγή δεδομένων σύνταξης"""
    
    @staticmethod
    def process_excel(file_content):
        """Επεξεργασία Excel αρχείου"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            data = df.to_dict('records')
            extracted_data = FileProcessor._extract_common_fields(data)
            return extracted_data
        except Exception as e:
            raise Exception(f"Σφάλμα ανάγνωσης Excel: {str(e)}")
    
    @staticmethod
    def process_csv(file_content):
        """Επεξεργασία CSV αρχείου"""
        try:
            content = file_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            data = list(csv_reader)
            extracted_data = FileProcessor._extract_common_fields(data)
            return extracted_data
        except Exception as e:
            raise Exception(f"Σφάλμα ανάγνωσης CSV: {str(e)}")
    
    @staticmethod
    def process_pdf(file_content):
        """Επεξεργασία PDF αρχείου"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            
            extracted_data = FileProcessor._extract_from_text(text)
            return extracted_data
        except Exception as e:
            raise Exception(f"Σφάλμα ανάγνωσης PDF: {str(e)}")
    
    @staticmethod
    def process_json(file_content):
        """Επεξεργασία JSON αρχείου"""
        try:
            data = json.loads(file_content.decode('utf-8'))
            extracted_data = FileProcessor._standardize_data(data)
            return extracted_data
        except Exception as e:
            raise Exception(f"Σφάλμα ανάγνωσης JSON: {str(e)}")
    
    @staticmethod
    def _extract_common_fields(data):
        """Εξαγωγή κοινών πεδίων από structured data"""
        standardized_data = {}
        for record in data:
            record_lower = {k.lower(): v for k, v in record.items()}
            standardized_data.update({
                'gender': FileProcessor._extract_gender(record_lower),
                'birth_year': FileProcessor._extract_birth_year(record_lower),
                'current_age': FileProcessor._extract_age(record_lower),
                'insurance_years': FileProcessor._extract_insurance_years(record_lower),
                'salary': FileProcessor._extract_salary(record_lower),
                'heavy_work_years': FileProcessor._extract_heavy_work(record_lower),
                'children': FileProcessor._extract_children(record_lower),
                'fund': FileProcessor._extract_fund(record_lower)
            })
        return standardized_data
    
    @staticmethod
    def _extract_from_text(text):
        """Εξαγωγή δεδομένων από απλό κείμενο"""
        extracted = {}
        patterns = {
            'gender': r'(άντρας|ανδρας|άνδρας|γυναίκα|γυναικα|male|female|man|woman)',
            'birth_year': r'(γέννηση|έτος γέννησης|birth year|year).*?(\d{4})',
            'age': r'(ηλικία|ηλικια|age).*?(\d+)',
            'insurance_years': r'(έτη ασφάλισης|ετη ασφαλισης|insurance years|years).*?(\d+)',
            'salary': r'(μισθός|μισθος|salary|income).*?(\d+[\.,]?\d*)',
            'heavy_work': r'(βαρέα|βαρεα|heavy work).*?(\d+)',
            'children': r'(παιδιά|παιδια|children|kids).*?(\d+)'
        }
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if field in ['gender']:
                    extracted[field] = match.group(1)
                else:
                    extracted[field] = match.group(2)
        return extracted
    
    @staticmethod
    def _standardize_data(data):
        """Τυποποίηση δεδομένων σε κοινή μορφή"""
        standardized = {}
        mapping = {
            'gender': ['gender', 'sex', 'φύλο', 'fulo'],
            'birth_year': ['birth_year', 'birthyear', 'year_of_birth', 'έτος_γέννησης'],
            'current_age': ['age', 'current_age', 'ηλικία', 'ilikia'],
            'insurance_years': ['insurance_years', 'years_insured', 'έτη_ασφάλισης'],
            'salary': ['salary', 'income', 'wage', 'μισθός', 'misthos'],
            'heavy_work_years': ['heavy_work', 'heavy_years', 'βαρέα_έτη'],
            'children': ['children', 'kids', 'παιδιά', 'paidia'],
            'fund': ['fund', 'insurance_fund', 'ταμείο', 'tameio']
        }
        for standard_field, possible_fields in mapping.items():
            for field in possible_fields:
                if field in data:
                    standardized[standard_field] = data[field]
                    break
        return standardized
    
    @staticmethod
    def _extract_gender(record):
        gender_map = {
            'male': 'male', 'άνδρας': 'male', 'ανδρας': 'male', 'man': 'male',
            'female': 'female', 'γυναίκα': 'female', 'γυναικα': 'female', 'woman': 'female'
        }
        for key in ['gender', 'sex', 'φύλο', 'fulo']:
            if key in record and record[key] in gender_map:
                return gender_map[record[key]]
        return 'male'
    
    @staticmethod
    def _extract_birth_year(record):
        current_year = datetime.now().year
        for key in ['birth_year', 'birthyear', 'year_of_birth', 'έτος_γέννησης']:
            if key in record and record[key]:
                try:
                    year = int(record[key])
                    if 1900 < year < current_year:
                        return year
                except:
                    continue
        return 1980
    
    @staticmethod
    def _extract_age(record):
        for key in ['age', 'current_age', 'ηλικία', 'ilikia']:
            if key in record and record[key]:
                try:
                    return int(record[key])
                except:
                    continue
        return 40
    
    @staticmethod
    def _extract_insurance_years(record):
        for key in ['insurance_years', 'years_insured', 'έτη_ασφάλισης']:
            if key in record and record[key]:
                try:
                    return int(record[key])
                except:
                    continue
        return 20
    
    @staticmethod
    def _extract_salary(record):
        for key in ['salary', 'income', 'wage', 'μισθός', 'misthos']:
            if key in record and record[key]:
                try:
                    return float(record[key])
                except:
                    continue
        return 1500
    
    @staticmethod
    def _extract_heavy_work(record):
        for key in ['heavy_work', 'heavy_years', 'βαρέα_έτη']:
            if key in record and record[key]:
                try:
                    return int(record[key])
                except:
                    continue
        return 0
    
    @staticmethod
    def _extract_children(record):
        for key in ['children', 'kids', 'παιδιά', 'paidia']:
            if key in record and record[key]:
                try:
                    return int(record[key])
                except:
                    continue
        return 0
    
    @staticmethod
    def _extract_fund(record):
        fund_map = {
            'ika': 'ika', 'efka': 'efka', 'οαεε': 'oaee', 'oaee': 'oaee',
            'εταα': 'etaa', 'etaa': 'etaa', 'other': 'other'
        }
        for key in ['fund', 'insurance_fund', 'ταμείο', 'tameio']:
            if key in record and record[key] in fund_map:
                return fund_map[record[key]]
        return 'ika'

    @staticmethod
    def process_file(file_content, filename):
        """Κύρια μέθοδος επεξεργασίας αρχείου"""
        filename_lower = filename.lower()
        if filename_lower.endswith(('.xlsx', '.xls')):
            return FileProcessor.process_excel(file_content)
        elif filename_lower.endswith('.csv'):
            return FileProcessor.process_csv(file_content)
        elif filename_lower.endswith('.pdf'):
            return FileProcessor.process_pdf(file_content)
        elif filename_lower.endswith('.json'):
            return FileProcessor.process_json(file_content)
        else:
            raise Exception("Μη υποστηριζόμενη μορφή αρχείου")