from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from datetime import datetime, date, timedelta
import json
import math
import io
import re
import PyPDF2
import traceback
import requests
import base64
import os
import tempfile

# Εισαγωγή βιβλιοθηκών για διάφορες μορφές
try:
    import docx2txt
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

try:
    import pandas as pd
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

try:
    from PIL import Image
    import pytesseract
    IMAGE_OCR_SUPPORT = True
except ImportError:
    IMAGE_OCR_SUPPORT = False

try:
    import pdf2image
    PDF_TO_IMAGE_SUPPORT = True
except ImportError:
    PDF_TO_IMAGE_SUPPORT = False

from app import db
from app.models import User, PensionCalculation, GreekPensionData
from app.forms import LoginForm, RegistrationForm, PensionCalculationForm, GreekPensionUploadForm

bp = Blueprint('main', __name__)

class UniversalPensionAnalyzer:
    """ΠΑΝΤΟΔΥΝΑΜΟΣ ΑΝΑΛΥΤΗΣ - ΒΕΛΤΙΩΜΕΝΗ ΕΚΔΟΣΗ"""
    
    SUPPORTED_FORMATS = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'txt': 'text/plain',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'tiff': 'image/tiff'
    }
    
    def analyze_file(self, file):
        """ΑΝΑΛΥΣΗ ΟΠΟΙΟΥΔΗΠΟΤΕ ΑΡΧΕΙΟΥ"""
        try:
            filename = file.filename.lower()
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            
            print(f"DEBUG: Analyzing file: {filename}, extension: {file_extension}")
            
            if file_extension not in self.SUPPORTED_FORMATS:
                return {
                    'success': False,
                    'error': f'Μη υποστηριζόμενη μορφή αρχείου: {file_extension}. Υποστηριζόμενες μορφές: {", ".join(self.SUPPORTED_FORMATS.keys())}'
                }
            
            file_content = file.read()
            
            # Εξαγωγή κειμένου ανάλογα με τη μορφή
            if file_extension == 'pdf':
                text_content = self._extract_from_pdf(file_content)
            elif file_extension in ['docx', 'doc']:
                text_content = self._extract_from_word(file_content, file_extension)
            elif file_extension in ['xlsx', 'xls']:
                text_content = self._extract_from_excel(file_content, file_extension)
            elif file_extension in ['jpg', 'jpeg', 'png', 'tiff']:
                text_content = self._extract_from_image(file_content, file_extension)
            elif file_extension == 'txt':
                text_content = self._extract_from_text(file_content)
            else:
                text_content = ""
            
            print(f"DEBUG: Extracted text length: {len(text_content)}")
            print(f"DEBUG: First 500 chars: {text_content[:500]}")
            
            # Επεξεργασία κειμένου
            return self._process_extracted_text(text_content, file_extension)
            
        except Exception as e:
            print(f"ERROR in analyze_file: {str(e)}")
            return {
                'success': False,
                'error': f'Σφάλμα ανάλυσης αρχείου: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def _extract_from_pdf(self, file_content):
        """ΕΞΑΓΩΓΗ ΚΕΙΜΕΝΟΥ ΑΠΟ PDF"""
        try:
            pdf_file_obj = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file_obj)
            
            text_content = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                text_content += page_text + "\n"
            
            return text_content
        except Exception as e:
            print(f"DEBUG: PDF extraction failed: {str(e)}")
            return ""
    
    def _extract_from_word(self, file_content, file_extension):
        if not DOCX_SUPPORT:
            return "DOCX support not available"
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            text_content = docx2txt.process(temp_file_path)
            os.unlink(temp_file_path)
            
            return text_content
        except Exception as e:
            print(f"DEBUG: Word extraction failed: {str(e)}")
            return ""
    
    def _extract_from_excel(self, file_content, file_extension):
        if not EXCEL_SUPPORT:
            return "Excel support not available"
        
        try:
            excel_file_obj = io.BytesIO(file_content)
            excel_data = pd.read_excel(excel_file_obj, sheet_name=None)
            
            text_content = ""
            for sheet_name, df in excel_data.items():
                text_content += f"--- Sheet: {sheet_name} ---\n"
                for col in df.columns:
                    text_content += f"{col}: " + " | ".join(map(str, df[col].dropna().values)) + "\n"
                text_content += "\n"
            
            return text_content
        except Exception as e:
            print(f"DEBUG: Excel extraction failed: {str(e)}")
            return ""
    
    def _extract_from_image(self, file_content, file_extension):
        if not IMAGE_OCR_SUPPORT:
            return "Image OCR support not available"
        
        try:
            image_file_obj = io.BytesIO(file_content)
            image = Image.open(image_file_obj)
            text_content = pytesseract.image_to_string(image, lang='ell+eng')
            return text_content
        except Exception as e:
            print(f"DEBUG: Image OCR failed: {str(e)}")
            return ""
    
    def _extract_from_text(self, file_content):
        """ΕΞΑΓΩΓΗ ΚΕΙΜΕΝΟΥ ΑΠΟ TXT"""
        try:
            return file_content.decode('utf-8')
        except:
            try:
                return file_content.decode('utf-16')
            except:
                return file_content.decode('latin-1')
    
    def _process_extracted_text(self, text_content, file_extension):
        """ΕΠΕΞΕΡΓΑΣΙΑ ΕΞΑΓΩΜΕΝΟΥ ΚΕΙΜΕΝΟΥ"""
        print(f"DEBUG: Processing text from {file_extension}, length: {len(text_content)}")
        
        # Καθαρισμός κειμένου
        cleaned_text = self._clean_text(text_content)
        
        # Εξαγωγή δεδομένων
        basic_data = self._extract_basic_data(cleaned_text)
        periods_data = self._analyze_insurance_periods_improved(cleaned_text)
        
        # Συνδυασμός δεδομένων
        extracted_data = {**basic_data, **periods_data}
        
        # Υπολογισμός σύνταξης
        pension_result = self._calculate_greek_pension(extracted_data)
        
        return {
            'success': True,
            'extracted_data': extracted_data,
            'pension_calculation': pension_result,
            'analysis_info': {
                'total_periods_found': len(extracted_data['insurance_periods']),
                'calculation_method': f'Ελληνική συνταξιοδοτική νομοθεσία από {file_extension.upper()}',
                'total_days_calculated': extracted_data['insurance_data'].get('total_days_calculated', 0),
                'total_stamps_calculated': extracted_data['insurance_data'].get('stamps_count', 0),
                'file_type': file_extension,
                'text_extracted': len(text_content) > 0,
                'text_length': len(text_content)
            },
            'debug_info': {
                'text_sample': text_content[:1000],
                'cleaned_text_sample': cleaned_text[:1000],
                'file_type': file_extension
            }
        }
    
    def _clean_text(self, text):
        """ΚΑΘΑΡΙΣΜΟΣ ΚΕΙΜΕΝΟΥ"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\sΑ-Ωα-ωάέήίόύώϊϋΐΰ.,/\d\-]', '', text)
        return text.strip()
    
    def _extract_basic_data(self, text):
        """ΕΞΑΓΩΓΗ ΒΑΣΙΚΩΝ ΔΕΔΟΜΕΝΩΝ"""
        data = {
            'personal_data': {
                'full_name': 'ΑΓΝΩΣΤΟ',
                'amka': 'ΑΓΝΩΣΤΟ', 
                'afm': 'ΑΓΝΩΣΤΟ',
                'current_age': 0,
                'birth_date': 'ΑΓΝΩΣΤΟ'
            },
            'insurance_data': {
                'insurance_category': 'ΑΓΝΩΣΤΟ'
            }
        }
        
        # ΒΕΛΤΙΩΜΕΝΗ ΑΝΑΖΗΤΗΣΗ ΟΝΟΜΑΤΟΣ
        name_patterns = [
            r'(?:Ονοματεπώνυμο|ΟΝΟΜΑΤΕΠΩΝΥΜΟ)[\s:*]*([^\n\r]+)',
            r'(?:Επώνυμο|ΕΠΩΝΥΜΟ)[\s:*]*([^\n\r]+?)\s+(?:Όνομα|ΟΝΟΜΑ)[\s:*]*([^\n\r]+)',
            r'([Α-Ω][α-ωάέήίόύώϊϋΐΰ\s]+\s+[Α-Ω][α-ωάέήίόύώϊϋΐΰ\s]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    data['personal_data']['full_name'] = f"{match.group(1).strip()} {match.group(2).strip()}"
                else:
                    data['personal_data']['full_name'] = match.group(1).strip()
                break
        
        # ΑΝΑΖΗΤΗΣΗ ΑΡΙΘΜΩΝ
        numbers = re.findall(r'\b\d{9,11}\b', text)
        for num in numbers:
            if len(num) == 11:  # ΑΜΚΑ
                data['personal_data']['amka'] = num
                try:
                    birth_date_str = num[:6]
                    birth_date = datetime.strptime(birth_date_str, '%d%m%y')
                    if birth_date.year > datetime.now().year:
                        birth_date = birth_date.replace(year=birth_date.year - 100)
                    today = datetime.now()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    data['personal_data']['current_age'] = age
                    data['personal_data']['birth_date'] = birth_date.strftime('%d/%m/%Y')
                except:
                    pass
            elif len(num) == 9:  # ΑΦΜ
                data['personal_data']['afm'] = num
        
        # ΑΝΑΓΝΩΡΙΣΗ ΦΟΡΕΑ
        if any(word in text.upper() for word in ['ΙΚΑ', 'Ι.Κ.Α.', 'ΑΣΦΑΛΙΣΗ ΙΚΑ']):
            data['insurance_data']['insurance_category'] = 'ΙΚΑ'
        elif any(word in text.upper() for word in ['ΟΑΕΕ', 'Ο.Α.Ε.Ε.', 'ΕΛΕΥΘΕΡΟΣ ΕΠΑΓΓΕΛΜΑΤΙΑΣ']):
            data['insurance_data']['insurance_category'] = 'ΟΑΕΕ'
        elif any(word in text.upper() for word in ['ΕΦΚΑ', 'Ε.Φ.Κ.Α.']):
            data['insurance_data']['insurance_category'] = 'ΕΦΚΑ'
        
        return data
    
    def _analyze_insurance_periods_improved(self, text):
        """ΒΕΛΤΙΩΜΕΝΗ ΑΝΑΛΥΣΗ ΠΕΡΙΟΔΩΝ ΑΣΦΑΛΙΣΗΣ"""
        data = {
            'insurance_data': {},
            'financial_data': {},
            'insurance_periods': []
        }
        
        print(f"DEBUG: Analyzing text for periods: {len(text)} characters")
        
        # ΒΕΛΤΙΩΜΕΝΑ ΠΑΤΤΕΡΝΣ ΓΙΑ ΠΕΡΙΟΔΟΥΣ
        period_patterns = [
            # Μορφή: ΗΗ/ΜΜ/ΕΕΕΕ - ΗΗ/ΜΜ/ΕΕΕΕ
            r'(\d{1,2}/\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{4})',
            # Μορφή: ΗΗ-ΜΜ-ΕΕΕΕ - ΗΗ-ΜΜ-ΕΕΕΕ
            r'(\d{1,2}-\d{1,2}-\d{4})\s*[-–]\s*(\d{1,2}-\d{1,2}-\d{4})',
            # Μορφή: ΗΗ.ΜΜ.ΕΕΕΕ - ΗΗ.ΜΜ.ΕΕΕΕ
            r'(\d{1,2}\.\d{1,2}\.\d{4})\s*[-–]\s*(\d{1,2}\.\d{1,2}\.\d{4})',
            # Μορφή με ελληνικές λέξεις
            r'Από\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})\s*Έως\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
            r'ΑΡΧΗ[:]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})\s*ΤΕΛΟΣ[:]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})'
        ]
        
        periods = []
        all_period_matches = []
        
        # ΑΝΑΖΗΤΗΣΗ ΠΕΡΙΟΔΩΝ ΜΕ ΠΑΤΤΕΡΝΣ
        for pattern in period_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    start_date_str, end_date_str = match.groups()
                    
                    # Καθαρισμός ημερομηνιών
                    start_date_clean = start_date_str.replace('.', '/').replace('-', '/')
                    end_date_clean = end_date_str.replace('.', '/').replace('-', '/')
                    
                    start_date = datetime.strptime(start_date_clean, '%d/%m/%Y')
                    end_date = datetime.strptime(end_date_clean, '%d/%m/%Y')
                    
                    # Έλεγχος λογικής ημερομηνίας
                    if start_date < end_date and start_date.year >= 1980:
                        days_diff = (end_date - start_date).days
                        
                        if 1 <= days_diff <= 3650:  # 1 ημέρα έως 10 χρόνια
                            years = days_diff // 365
                            remaining_days = days_diff % 365
                            months = remaining_days // 30
                            days = remaining_days % 30
                            
                            # Υπολογισμός μισθού βάσει έτους
                            base_year = min(start_date.year, 2023)
                            salary = 800 + (base_year - 2000) * 40
                            
                            period_data = {
                                'start_date': start_date_clean,
                                'end_date': end_date_clean,
                                'years': years,
                                'months': months,
                                'days': days,
                                'total_days': days_diff,
                                'salary': max(800, min(salary, 2500)),
                                'period_duration_days': days_diff
                            }
                            
                            # Έλεγχος για διπλοτυπία
                            period_key = f"{start_date_clean}_{end_date_clean}"
                            if period_key not in [f"{p['start_date']}_{p['end_date']}" for p in periods]:
                                periods.append(period_data)
                                all_period_matches.append(match.groups())
                except Exception as e:
                    print(f"DEBUG: Period parsing error: {e}")
                    continue
        
        # ΕΝΑΛΛΑΚΤΙΚΗ ΜΕΘΟΔΟΣ: ΑΝΑΖΗΤΗΣΗ ΜΟΝΟΧΡΟΝΩΝ ΗΜΕΡΟΜΗΝΙΩΝ
        if not periods:
            print("DEBUG: No period patterns found, trying single date extraction")
            single_dates = self._extract_single_dates(text)
            periods = self._create_periods_from_single_dates(single_dates)
        
        # ΤΑΞΙΝΟΜΗΣΗ ΠΕΡΙΟΔΩΝ
        periods.sort(key=lambda x: datetime.strptime(x['start_date'], '%d/%m/%Y'))
        
        data['insurance_periods'] = periods
        
        if periods:
            total_days = sum(p['total_days'] for p in periods)
            data['insurance_data']['total_days_calculated'] = total_days
            
            years, months, days = self._convert_days_to_ymd(total_days)
            data['insurance_data']['total_years'] = years
            data['insurance_data']['total_months'] = months
            data['insurance_data']['total_days'] = days
            
            data['insurance_data']['stamps_count'] = self._calculate_greek_stamps(periods)
            data['insurance_data']['total_periods'] = len(periods)
            
            salaries = [p['salary'] for p in periods]
            data['financial_data']['avg_salary'] = round(sum(salaries) / len(salaries), 2)
            data['financial_data']['salaries_analyzed'] = len(periods)
            
            data['insurance_data']['first_period'] = periods[0]['start_date']
            data['insurance_data']['last_period'] = periods[-1]['end_date']
        
        print(f"DEBUG: Found {len(periods)} insurance periods")
        
        return data
    
    def _extract_single_dates(self, text):
        """ΕΞΑΓΩΓΗ ΜΟΝΟΧΡΟΝΩΝ ΗΜΕΡΟΜΗΝΙΩΝ"""
        date_pattern = r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})'
        matches = re.finditer(date_pattern, text)
        
        dates_found = []
        for match in matches:
            try:
                day, month, year = match.groups()
                if len(year) == 2:
                    year = '20' + year if int(year) < 50 else '19' + year
                
                date_str = f"{day}/{month}/{year}"
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                
                if 1980 <= date_obj.year <= datetime.now().year:
                    dates_found.append((date_str, date_obj, match.start()))
            except:
                continue
        
        # Ταξινόμηση κατά σειρά εμφάνισης
        dates_found.sort(key=lambda x: x[2])
        return [(date_str, date_obj) for date_str, date_obj, _ in dates_found]
    
    def _create_periods_from_single_dates(self, dates_found):
        """ΔΗΜΙΟΥΡΓΙΑ ΠΕΡΙΟΔΩΝ ΑΠΟ ΜΟΝΟΧΡΟΝΕΣ ΗΜΕΡΟΜΗΝΙΕΣ"""
        periods = []
        
        for i in range(len(dates_found) - 1):
            start_date_str, start_date = dates_found[i]
            end_date_str, end_date = dates_found[i + 1]
            
            days_diff = (end_date - start_date).days
            
            # Έλεγχος για λογική περίοδο (1 μήνας έως 5 χρόνια)
            if 30 <= days_diff <= 1825:
                years = days_diff // 365
                remaining_days = days_diff % 365
                months = remaining_days // 30
                days = remaining_days % 30
                
                # Υπολογισμός μισθού
                base_year = min(start_date.year, 2023)
                salary = 800 + (base_year - 2000) * 40
                
                period_data = {
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'years': years,
                    'months': months,
                    'days': days,
                    'total_days': days_diff,
                    'salary': max(800, min(salary, 2500)),
                    'period_duration_days': days_diff
                }
                
                periods.append(period_data)
        
        return periods
    
    def _convert_days_to_ymd(self, total_days):
        years = total_days // 365
        remaining_days = total_days % 365
        months = remaining_days // 30
        days = remaining_days % 30
        return years, months, days
    
    def _calculate_greek_stamps(self, periods):
        total_stamps = 0
        for period in periods:
            months_from_years = period['years'] * 12
            months_from_months = period['months']
            months_from_days = period['days'] * 0.03333
            total_stamps += months_from_years + months_from_months + months_from_days
        return round(total_stamps, 2)
    
    def _calculate_greek_pension(self, extracted_data):
        personal_data = extracted_data['personal_data']
        insurance_data = extracted_data['insurance_data']
        financial_data = extracted_data['financial_data']
        
        current_age = personal_data.get('current_age', 0)
        insurance_years = insurance_data.get('total_years', 0)
        insurance_months = insurance_data.get('total_months', 0)
        avg_salary = financial_data.get('avg_salary', 1500)
        
        total_insurance_months = insurance_years * 12 + insurance_months
        
        pension_type = "ΕΓΓΥΗΜΕΝΗ ΣΥΝΤΑΞΗ"
        base_pension = 384
        
        if total_insurance_months >= 480:
            base_pension = avg_salary * 0.60
            pension_type = "ΠΛΗΡΗΣ ΣΥΝΤΑΞΗ"
        elif total_insurance_months >= 180:
            proportional_rate = 0.60 * (total_insurance_months / 480)
            base_pension = avg_salary * proportional_rate
            pension_type = "ΜΕΙΩΜΕΝΗ ΣΥΝΤΑΞΗ"
        
        if base_pension < 384:
            base_pension = 384
        
        retirement_age = 67
        if insurance_years >= 40:
            retirement_age = max(62, 67 - 2)
        elif insurance_years >= 35:
            retirement_age = max(65, 67 - 1)
        
        return {
            'base_pension': round(base_pension, 2),
            'total_monthly_pension': round(base_pension, 2),
            'retirement_age': retirement_age,
            'remaining_years': max(retirement_age - current_age, 0),
            'pension_type': pension_type,
            'can_retire_now': current_age >= retirement_age and total_insurance_months >= 180,
            'calculation_details': {
                'insurance_years_used': insurance_years,
                'insurance_months_used': insurance_months,
                'avg_salary_used': avg_salary,
                'replacement_rate': "60.0%",
                'insurance_category': insurance_data.get('insurance_category', 'ΙΚΑ'),
                'total_periods_analyzed': insurance_data.get('total_periods', 0)
            }
        }

# Ο ΚΩΔΙΚΑΣ ΓΙΑ ΤΙΣ ROUTES ΜΕΝΕΙ Ο ΙΔΙΟΣ
@bp.route('/analyze_file', methods=['GET', 'POST'])
@login_required
def analyze_file():
    """ΣΕΛΙΔΑ ΑΝΑΛΥΣΗΣ ΓΙΑ ΟΛΕΣ ΤΙΣ ΜΟΡΦΕΣ ΑΡΧΕΙΩΝ"""
    
    if request.method == 'POST':
        try:
            if 'pension_file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'Δεν βρέθηκε αρχείο'
                }), 400
            
            pension_file = request.files['pension_file']
            
            if pension_file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'Δεν επιλέχθηκε αρχείο'
                }), 400
            
            # Ανάλυση αρχείου
            analyzer = UniversalPensionAnalyzer()
            result = analyzer.analyze_file(pension_file)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Σφάλμα server: {str(e)}'
            }), 500
    
    # GET request - ο κώδικας παραμένει ο ίδιος όπως πριν
    return '''
    <!DOCTYPE html>
    <html lang="el">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Alex Pension1 - Πανομοιότυπη Ανάλυση</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .upload-area {
                border: 2px dashed #6f42c1;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                background: #f8f9fa;
                cursor: pointer;
                transition: all 0.3s;
            }
            .upload-area:hover {
                border-color: #5a32a3;
                background: #f0e6ff;
            }
            .format-badge {
                background: #6f42c1;
                color: white;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 11px;
                margin: 2px;
            }
            .supported-formats {
                background: #e9ecef;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark" style="background-color: #6f42c1;">
            <div class="container">
                <a class="navbar-brand fw-bold" href="/">🎯 Alex Pension1 Pro</a>
                <span class="navbar-text">Πανομοιότυπη Ανάλυση Αρχείων</span>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-12">
                    <div class="card shadow">
                        <div class="card-header text-white" style="background-color: #6f42c1;">
                            <h4 class="mb-0">📁 Ανάλυση Πολλαπλών Μορφών Αρχείων</h4>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-info">
                                <strong>Βελτιωμένο Σύστημα!</strong> Βελτιωμένος αλγόριθμος για αναγνώριση περιόδων ασφάλισης.
                            </div>
                            
                            <div class="supported-formats">
                                <strong>Υποστηριζόμενες Μορφές:</strong>
                                <div class="mt-2">
                                    <span class="format-badge">PDF</span>
                                    <span class="format-badge">DOCX</span>
                                    <span class="format-badge">DOC</span>
                                    <span class="format-badge">XLSX</span>
                                    <span class="format-badge">XLS</span>
                                    <span class="format-badge">TXT</span>
                                    <span class="format-badge">JPG</span>
                                    <span class="format-badge">PNG</span>
                                    <span class="format-badge">TIFF</span>
                                </div>
                            </div>
                            
                            <form id="analysisForm" enctype="multipart/form-data">
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Επιλέξτε αρχείο:</label>
                                    <input type="file" class="form-control" name="pension_file" 
                                           accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.jpg,.jpeg,.png,.tiff" required>
                                    <div class="form-text">
                                        Μέγιστο μέγεθος: 10MB. Το σύστημα θα προσπαθήσει να εξάγει κείμενο από οποιαδήποτε μορφή.
                                    </div>
                                </div>
                                <button type="submit" class="btn text-white btn-lg w-100" style="background-color: #6f42c1;">
                                    🚀 Εκκίνηση Πανομοιότυπης Ανάλυσης
                                </button>
                            </form>
                            
                            <div id="analysisResults" class="mt-4"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            document.getElementById('analysisForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const resultsDiv = document.getElementById('analysisResults');
                const submitBtn = this.querySelector('button[type="submit"]');
                
                resultsDiv.innerHTML = `
                    <div class="alert alert-info text-center">
                        <div class="spinner-border me-2" role="status"></div>
                        <strong>Γίνεται πανομοιότυπη ανάλυση...</strong><br>
                        <small>Αυτό μπορεί να πάρει μερικά δευτερόλεπτα</small>
                    </div>
                `;
                
                submitBtn.disabled = true;
                submitBtn.innerHTML = '⏳ Ανάλυση σε εξέλιξη...';
                
                try {
                    const response = await fetch('/analyze_file', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (!data.success) {
                        resultsDiv.innerHTML = `<div class="alert alert-danger">❌ ${data.error}</div>`;
                    } else {
                        resultsDiv.innerHTML = renderAnalysisResults(data);
                    }
                    
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="alert alert-danger">❌ Σφάλμα: ${error.message}</div>`;
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '🚀 Εκκίνηση Πανομοιότυπης Ανάλυσης';
                }
            });
            
            function renderAnalysisResults(data) {
                const extracted = data.extracted_data;
                const pension = data.pension_calculation;
                const analysis = data.analysis_info;
                const debug = data.debug_info;
                
                const isDemo = !analysis.text_extracted || analysis.total_periods_found === 0;
                const fileType = analysis.file_type || 'unknown';
                
                let html = `
                    <div class="alert alert-${isDemo ? 'warning' : 'success'}">
                        <h5>${isDemo ? '⚠️ Μερική Ανάλυση' : '✅ Επιτυχής Ανάλυση!'}</h5>
                        <p>
                            <strong>${analysis.calculation_method}</strong> - 
                            Βρέθηκαν ${analysis.total_periods_found} περιόδοι ασφάλισης
                            <span class="format-badge">${fileType.toUpperCase()}</span>
                        </p>
                        ${analysis.note ? `<p class="mb-0"><small>${analysis.note}</small></p>` : ''}
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header ${isDemo ? 'bg-warning text-dark' : 'bg-success text-white'}">
                                    <h6 class="mb-0">👤 Προσωπικά Στοιχεία</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>Ονοματεπώνυμο:</strong> ${extracted.personal_data.full_name}</p>
                                    <p><strong>ΑΦΜ:</strong> ${extracted.personal_data.afm}</p>
                                    <p><strong>ΑΜΚΑ:</strong> ${extracted.personal_data.amka}</p>
                                    <p><strong>Ηλικία:</strong> ${extracted.personal_data.current_age} έτη</p>
                                    <p><strong>Ημ. Γέννησης:</strong> ${extracted.personal_data.birth_date}</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header ${isDemo ? 'bg-warning text-dark' : 'bg-info text-white'}">
                                    <h6 class="mb-0">📈 Ασφαλιστικά Στοιχεία</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>Σύνολο Ετών:</strong> ${extracted.insurance_data.total_years || 0}</p>
                                    <p><strong>Σύνολο Μηνών:</strong> ${extracted.insurance_data.total_months || 0}</p>
                                    <p><strong>Συνολικές Ημέρες:</strong> ${analysis.total_days_calculated}</p>
                                    <p><strong>🔖 Ένσημα:</strong> ${analysis.total_stamps_calculated}</p>
                                    <p><strong>🏢 Φορέας:</strong> ${extracted.insurance_data.insurance_category}</p>
                                    <p><strong>📅 Περίοδοι:</strong> ${analysis.total_periods_found}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                if (analysis.total_periods_found > 0) {
                    html += `
                        <div class="card mt-3">
                            <div class="card-header ${isDemo ? 'bg-warning text-dark' : 'bg-primary text-white'}">
                                <h6 class="mb-0">💰 Υπολογισμός Σύνταξης</h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong>Τύπος Σύνταξης:</strong> ${pension.pension_type}</p>
                                        <p><strong>Βασικό Ποσό:</strong> €${pension.base_pension}</p>
                                        <p><strong>Συνολικό Ποσό:</strong> <span class="text-success fw-bold fs-5">€${pension.total_monthly_pension}</span></p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong>Ηλικία Συνταξιοδότησης:</strong> ${pension.retirement_age} έτη</p>
                                        <p><strong>Απομένουν:</strong> ${pension.remaining_years} έτη</p>
                                        <p><strong>Κατάσταση:</strong> ${pension.can_retire_now ? 
                                            '<span class="text-success">✅ Μπορεί να συνταξιοδοτηθεί</span>' : 
                                            '<span class="text-warning">⏳ Δεν μπορεί να συνταξιοδοτηθεί ακόμα</span>'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                // Debug information
                html += `
                    <div class="mt-3">
                        <button class="btn btn-outline-dark btn-sm" onclick="toggleDebug()">
                            🔧 Λεπτομέρειες Ανάλυσης
                        </button>
                        <div id="debugInfo" class="mt-2 p-3 bg-light rounded" style="display: none;">
                            <h6>Λεπτομέρειες Ανάλυσης:</h6>
                            <pre class="bg-white p-2 border rounded">${JSON.stringify(debug, null, 2)}</pre>
                            ${isDemo ? `
                                <div class="alert alert-warning mt-2">
                                    <strong>Συμβουλή:</strong> Για πλήρη ανάλυση, βεβαιωθείτε ότι το αρχείο ${fileType.toUpperCase()} 
                                    περιέχει ημερομηνίες περιόδων ασφάλισης σε μορφή ΗΗ/ΜΜ/ΕΕΕΕ - ΗΗ/ΜΜ/ΕΕΕΕ
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
                
                return html;
            }
            
            function toggleDebug() {
                const debugInfo = document.getElementById('debugInfo');
                debugInfo.style.display = debugInfo.style.display === 'none' ? 'block' : 'none';
            }
        </script>
    </body>
    </html>
    '''

# ΟΙ ΥΠΟΛΟΙΠΕΣ ROUTES ΜΕΝΟΥΝ ΙΔΙΕΣ
@bp.route('/')
def index():
    return redirect('/analyze_file')

@bp.route('/analyze_pdf')
@login_required
def analyze_pdf_redirect():
    return redirect('/analyze_file')

@bp.route('/greek_calculator')
@login_required
def greek_calculator():
    return "Υπολογιστής Σύνταξης - Σε ανάπτυξη"

@bp.route('/dashboard')
@login_required
def dashboard():
    return "Dashboard - Σε ανάπτυξη"

@bp.route('/login')
def login():
    return "Σύνδεση - Σε ανάπτυξη"

@bp.route('/register')
def register():
    return "Εγγραφή - Σε ανάπτυξη"

@bp.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@bp.route('/history')
@login_required
def history():
    return "Ιστορικό - Σε ανάπτυξη"