import PyPDF2
import json
import csv
import io
from datetime import datetime, date
import re
from image_processor import ImageProcessor

class EFKAPDFParser:
    """Εξειδικευμένος parser για PDF του e-ΕΦΚΑ"""
    
    @staticmethod
    def parse_efka_pdf(file_content):
        """Κύρια μέθοδος ανάλυσης PDF e-ΕΦΚΑ"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            full_text = ""
            
            # Εξαγωγή κειμένου από όλες τις σελίδες
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text() or ""
                full_text += f"\n--- Σελίδα {page_num + 1} ---\n{page_text}"
            
            print(f"📄 PDF e-ΕΦΚΑ loaded: {len(full_text)} χαρακτήρες")
            
            # Εξαγωγή βασικών πληροφοριών
            personal_info = EFKAPDFParser._extract_personal_info(full_text)
            insurance_data = EFKAPDFParser._extract_insurance_data(full_text)
            
            # Συνδυασμός δεδομένων
            result = {**personal_info, **insurance_data}
            
            print(f"🎯 Αποτελέσματα ανάλυσης: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Σφάλμα ανάλυσης PDF: {e}")
            raise Exception(f"Αδυναμία ανάλυσης PDF e-ΕΦΚΑ: {str(e)}")
    
    @staticmethod
    def _extract_personal_info(text):
        """Εξαγωγή προσωπικών στοιχείων"""
        info = {}
        
        # ΑΜΚΑ
        amka_match = re.search(r'ΑΜΚΑ[\s:\-]*(\d{11})', text, re.IGNORECASE)
        if amka_match:
            info['amka'] = amka_match.group(1)
            # Εξαγωγή έτους γέννησης από ΑΜΚΑ
            birth_year = FileProcessor.extract_birth_year_from_amka(amka_match.group(1))
            if birth_year:
                info['birth_year'] = birth_year
                info['current_age'] = datetime.now().year - birth_year
        
        # ΑΦΜ
        afm_match = re.search(r'ΑΦΜ[\s:\-]*(\d{9})', text, re.IGNORECASE)
        if afm_match:
            info['afm'] = afm_match.group(1)
        
        # Ονοματεπώνυμο
        name_match = re.search(r'Επώνυμο\s*([^\n\r]+)\s*Όνομα\s*([^\n\r]+)', text)
        if name_match:
            info['last_name'] = name_match.group(1).strip()
            info['first_name'] = name_match.group(2).strip()
            # Εξαγωγή φύλου από όνομα
            info['gender'] = FileProcessor._extract_gender_from_name(info['first_name'])
        
        # Ημερομηνία γέννησης
        birth_match = re.search(r'Ημερομηνία Γέννησης[\s:\-]*(\d{2}/\d{2}/\d{4})', text)
        if birth_match:
            birth_date = FileProcessor._parse_date(birth_match.group(1))
            if birth_date:
                info['birth_year'] = birth_date.year
                info['current_age'] = FileProcessor._calculate_age(birth_date)
        
        # Προεπιλεγμένες τιμές
        if 'gender' not in info:
            info['gender'] = 'male'
        if 'birth_year' not in info:
            info['birth_year'] = 1980
            info['current_age'] = datetime.now().year - 1980
        
        return info
    
    @staticmethod
    def _extract_insurance_data(text):
        """Εξαγωγή ασφαλιστικών δεδομένων από πίνακες"""
        insurance_data = {
            'total_insurance_days': 0,
            'insurance_periods': [],
            'average_salary': 0,
            'salary_data': [],
            'insurance_years': 0
        }
        
        # Εύρεση και ανάλυση πινάκων
        table_sections = EFKAPDFParser._extract_table_sections(text)
        
        total_days = 0
        salaries = []
        
        for section in table_sections:
            periods = EFKAPDFParser._parse_insurance_periods(section)
            insurance_data['insurance_periods'].extend(periods)
            
            for period in periods:
                total_days += period.get('days', 0)
                if period.get('salary', 0) > 0:
                    salaries.append(period['salary'])
        
        insurance_data['total_insurance_days'] = total_days
        insurance_data['insurance_years'] = round(total_days / 365.25, 2)
        
        if salaries:
            insurance_data['average_salary'] = sum(salaries) / len(salaries)
            insurance_data['salary_data'] = salaries
        
        # Προσθήκη default τιμών αν χρειαστεί
        if insurance_data['average_salary'] == 0:
            insurance_data['average_salary'] = 1500
        
        return insurance_data
    
    @staticmethod
    def _extract_table_sections(text):
        """Εξαγωγή τμημάτων πινάκων από το κείμενο"""
        sections = []
        
        # Ψάχνουμε για τον κύριο πίνακα ασφαλιστικής ιστορίας
        table_patterns = [
            r'Από\s*Έως\s*Έτη\s*Μήνες\s*Ημέρες[^\n]*(?:\n.*){10,100}',
            r'Φορέας Κοινωνικής Ασφάλισης[^\n]*(?:\n.*){10,100}',
            r'\d{2}/\d{2}/\d{4}\s*\d{2}/\d{2}/\d{4}.*\d+.*\d+.*\d+'
        ]
        
        for pattern in table_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                sections.append(match.group(0))
        
        return sections
    
    @staticmethod
    def _parse_insurance_periods(table_text):
        """Ανάλυση περιόδων ασφάλισης από πίνακα - ΔΙΟΡΘΩΜΕΝΗ"""
        periods = []
        
        lines = table_text.split('\n')
        for line in lines:
            # Έλεγχος για πραγματικές γραμμές δεδομένων
            if re.search(r'\d{2}/\d{2}/\d{4}.*\d{2}/\d{2}/\d{4}', line):
                # Χρήση των πραγματικών ημερών από τη στήλη "Ημέρες"
                days_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4}).*?\s+(\d+)\s+(\d+)\s+(\d+)', line)
                
                if days_match:
                    start_date = FileProcessor._parse_date(days_match.group(1))
                    end_date = FileProcessor._parse_date(days_match.group(2))
                    actual_days = int(days_match.group(5)) if days_match.group(5).isdigit() else 0
                    
                    # Φίλτρο για ρεαλιστικές τιμές (25-31 ημέρες ανά μήνα)
                    if actual_days > 0 and actual_days <= 31:
                        salary = EFKAPDFParser._extract_salary_from_line(line)
                        
                        period = {
                            'start_date': start_date,
                            'end_date': end_date,
                            'days': actual_days,
                            'salary': salary
                        }
                        periods.append(period)
                        print(f"📅 Περίοδος: {start_date} - {end_date} = {actual_days} ημέρες, Μισθός: {salary}€")
        
        return periods
    
    @staticmethod
    def _extract_salary_from_line(line):
        """Εξαγωγή μισθού από γραμμή πίνακα"""
        # Ψάχνουμε για ποσά στη στήλη "Μικτές αποδοχές"
        salary_patterns = [
            r'(\d+[\,\.]\d{2})\s*€',
            r'(\d+[\,\.]\d{2})\s*EUR',
            r'€\s*(\d+[\,\.]\d{2})',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                salary_str = match.group(1).replace(',', '.')
                try:
                    salary = float(salary_str)
                    if salary > 0:
                        return round(salary, 2)
                except:
                    pass
        
        return 0

class FileProcessor:
    """Επεξεργαστής αρχείων για εξαγωγή πραγματικών δεδομένων σύνταξης"""
    
    @staticmethod
    def extract_birth_year_from_amka(amka):
        """Εξάγει το έτος γέννησης από ΑΜΚΑ"""
        try:
            if len(amka) == 11:
                day = amka[0:2]
                month = amka[2:4]
                year_short = amka[4:6]
                
                year_int = int(year_short)
                current_year_short = datetime.now().year % 100
                
                if year_int > current_year_short:
                    full_year = 1900 + year_int
                else:
                    full_year = 2000 + year_int
                
                print(f"    📅 Εξαγωγή έτους γέννησης από ΑΜΚΑ: {day}/{month}/{full_year}")
                return full_year
                
        except Exception as e:
            print(f"    ⚠️ Σφάλμα εξαγωγής έτους από ΑΜΚΑ: {e}")
        
        return None

    @staticmethod
    def extract_gender_from_amka(amka):
        """Εξάγει το φύλο από ΑΜΚΑ"""
        try:
            if len(amka) == 11:
                last_digit = int(amka[-1])
                gender = 'male' if last_digit % 2 == 1 else 'female'
                print(f"    👤 Εξαγωγή φύλου από ΑΜΚΑ: {gender}")
                return gender
        except Exception as e:
            print(f"    ⚠️ Σφάλμα εξαγωγής φύλου από ΑΜΚΑ: {e}")
        
        return 'male'
    
    @staticmethod
    def process_csv(file_content):
        """Επεξεργασία CSV αρχείου με πραγματικά δεδομένα"""
        try:
            content = file_content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            data = list(csv_reader)
            
            if not data:
                raise Exception("Το αρχείο CSV είναι κενό")
            
            print(f"📊 Βρέθηκαν {len(data)} εγγραφές στο CSV")
            
            total_data = FileProcessor._calculate_totals_from_records(data)
            
            print(f"📈 Εξαγόμενα δεδομένα: {total_data}")
            
            return total_data
            
        except Exception as e:
            print(f"❌ Σφάλμα CSV: {e}")
            raise Exception(f"Σφάλμα ανάγνωσης CSV: {str(e)}")
    
    @staticmethod
    def process_pdf(file_content):
        """Βελτιωμένη επεξεργασία PDF με ειδικό parser για e-ΕΦΚΑ"""
        try:
            # Πρώτα δοκιμάζουμε τον ειδικό parser για e-ΕΦΚΑ
            efka_data = EFKAPDFParser.parse_efka_pdf(file_content)
            
            # Μετατροπή σε μορφή που καταλαβαίνει η εφαρμογή
            standardized_data = {
                'gender': efka_data.get('gender', 'male'),
                'birth_year': efka_data.get('birth_year', 1980),
                'current_age': efka_data.get('current_age', 45),
                'insurance_years': efka_data.get('insurance_years', 20),
                'insurance_days': efka_data.get('total_insurance_days', 0),
                'salary': round(efka_data.get('average_salary', 1500), 2),
                'heavy_work_years': 0,
                'children': 0,
                'fund': 'ika',
                'source': 'efka_pdf_parser'
            }
            
            print(f"📈 Τελικά δεδομένα από PDF e-ΕΦΚΑ: {standardized_data}")
            return standardized_data
            
        except Exception as e:
            print(f"⚠️ EFKA parser failed: {str(e)}")
            # Fallback
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                
                return FileProcessor._extract_detailed_data_from_text(text)
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                raise Exception(f"Αδυναμία ανάλυσης PDF: {str(e)}")
    
    @staticmethod
    def process_json(file_content):
        """Επεξεργασία JSON αρχείου"""
        try:
            data = json.loads(file_content.decode('utf-8'))
            print(f"📋 Δεδομένα JSON: {data}")
            
            extracted_data = FileProcessor._process_json_data(data)
            
            print(f"📈 Εξαγόμενα δεδομένα από JSON: {extracted_data}")
            
            return extracted_data
        except Exception as e:
            print(f"❌ Σφάλμα JSON: {e}")
            raise Exception(f"Σφάλμα ανάγνωσης JSON: {str(e)}")
    
    @staticmethod
    def _calculate_totals_from_records(records):
        """Υπολογισμός συνολικών δεδομένων από εγγραφές CSV"""
        total_insurance_days = 0
        total_salary = 0
        salary_count = 0
        
        first_record = records[0]
        birth_date = None
        gender = 'male'
        fund = 'ika'
        children = 0
        
        print(f"🔍 Αναλύονται {len(records)} εγγραφές...")
        
        for i, record in enumerate(records):
            print(f"  📝 Εγγραφή {i+1}: {record}")
            
            if 'insurance_days' in record and record['insurance_days']:
                try:
                    days = int(record['insurance_days'])
                    total_insurance_days += days
                    print(f"    ➕ Προσθήκη {days} ημερών ασφάλισης")
                except:
                    pass
            
            days_from_dates = FileProcessor._calculate_insurance_days_from_dates(record)
            if days_from_dates > 0:
                total_insurance_days += days_from_dates
                print(f"    📅 Προσθήκη {days_from_dates} ημερών από ημερομηνίες")
            
            if 'salary_amount' in record and record['salary_amount']:
                try:
                    salary = float(record['salary_amount'])
                    total_salary += salary
                    salary_count += 1
                    print(f"    💰 Προσθήκη μισθού: {salary} €")
                except:
                    pass
            
            if record == first_record:
                if 'birth_date' in record and record['birth_date']:
                    birth_date = FileProcessor._parse_date(record['birth_date'])
                    if birth_date:
                        print(f"    🎂 Ημερομηνία γέννησης: {birth_date}")
                
                if 'fund_code' in record and record['fund_code']:
                    fund = FileProcessor._map_fund_code(record['fund_code'])
                    print(f"    🏦 Ταμείο: {fund}")
                
                if 'first_name' in record and record['first_name']:
                    gender = FileProcessor._extract_gender_from_name(record['first_name'])
                    print(f"    👤 Φύλο από όνομα: {gender}")
        
        insurance_years = total_insurance_days / 365.25
        
        avg_salary = total_salary / salary_count if salary_count > 0 else 1500
        
        current_age = FileProcessor._calculate_age(birth_date) if birth_date else 40
        
        result = {
            'gender': gender,
            'birth_year': birth_date.year if birth_date else 1980,
            'current_age': int(current_age),
            'insurance_years': round(insurance_years, 1),
            'insurance_days': total_insurance_days,
            'salary': round(avg_salary, 2),
            'heavy_work_years': 0,
            'children': children,
            'fund': fund,
            'total_records': len(records)
        }
        
        print(f"🎯 Τελικό αποτέλεσμα: {result}")
        return result
    
    @staticmethod
    def _calculate_insurance_days_from_dates(record):
        """Υπολογισμός ημερών ασφάλισης από ημερομηνίες έναρξης/λήξης"""
        try:
            if 'start_date' in record and 'end_date' in record and record['start_date'] and record['end_date']:
                start_date = FileProcessor._parse_date(record['start_date'])
                end_date = FileProcessor._parse_date(record['end_date'])
                
                if start_date and end_date:
                    delta = end_date - start_date
                    days = max(0, delta.days)
                    print(f"    📆 Υπολογισμός ημερών: {start_date} -> {end_date} = {days} ημέρες")
                    return days
        except Exception as e:
            print(f"    ⚠️ Σφάλμα υπολογισμού ημερών: {e}")
        return 0
    
    @staticmethod
    def _parse_date(date_str):
        """Ανάλυση ημερομηνίας από string"""
        if not date_str:
            return None
            
        try:
            date_str = str(date_str).strip()
            
            formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d',
                '%d.%m.%Y', '%Y.%m.%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
                    
        except Exception as e:
            print(f"    ⚠️ Σφάλμα ανάλυσης ημερομηνίας '{date_str}': {e}")
            
        return None
    
    @staticmethod
    def _calculate_age(birth_date):
        """Υπολογισμός ηλικίας από ημερομηνία γέννησης"""
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    
    @staticmethod
    def _map_fund_code(fund_code):
        """Αντιστοίχιση κωδικού ταμείου"""
        if not fund_code:
            return 'ika'
            
        fund_code = str(fund_code).lower().strip()
        fund_mapping = {
            'ika': 'ika', 'εφκα': 'efka', 'efka': 'efka',
            'οαεε': 'oaee', 'oaee': 'oaee', 'εταα': 'etaa', 'etaa': 'etaa',
            'tebe': 'tebe', 'τεβε': 'tebe', 'other': 'other'
        }
        return fund_mapping.get(fund_code, 'ika')
    
    @staticmethod
    def _extract_gender_from_name(first_name):
        """Εξαγωγή φύλου από όνομα"""
        if not first_name:
            return 'male'
            
        first_name = str(first_name).lower().strip()
        
        female_names = ['μαρια', 'αννα', 'ελενη', 'ευα', 'σοφια', 'κωνσταντινα', 
                       'αικατερινη', 'βασιλικη', 'δαφνη', 'χρυσα']
        
        for female_name in female_names:
            if female_name in first_name:
                return 'female'
                
        return 'male'
    
    @staticmethod
    def _extract_detailed_data_from_text(text):
        """Εξαγωγή λεπτομερών δεδομένων από κείμενο PDF (fallback)"""
        extracted = {}
        
        print("🔍 Εξαγωγή δεδομένων από κείμενο PDF (fallback)...")
        
        patterns = {
            'amka': r'(ΑΜΚΑ|Α\.Μ\.Κ\.Α\.?)[\s:\-]*(\d{11})',
            'birth_date': r'(ΓΕΝΝΗΣΗΣ?|ΗΜΕΡΟΜΗΝΙΑ ΓΕΝΝΗΣΗΣ?)[\s:\-]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
            'insurance_days': r'(ΗΜΕΡΕΣ ΑΣΦΑΛΙΣΗΣ?|ΑΣΦΑΛΙΣΜΕΝΕΣ ΗΜΕΡΕΣ)[\s:\-]*(\d+)',
            'insurance_years': r'(ΕΤΗ ΑΣΦΑΛΙΣΗΣ?|ΑΣΦΑΛΙΣΤΙΚΑ ΕΤΗ)[\s:\-]*(\d+)',
            'salary': r'(ΜΙΣΘΟΣ|ΜΕΣΟΣ ΜΙΣΘΟΣ|ΕΙΣΟΔΗΜΑ)[\s:\-]*(\d+[\.,]?\d*)',
            'fund': r'(ΤΑΜΕΙΟ|ΑΣΦΑΛΙΣΤΙΚΟ ΤΑΜΕΙΟ)[\s:\-]*([^\n\r]+)',
            'age': r'(ΗΛΙΚΙΑ|ΕΤΩΝ)[\s:\-]*(\d+)',
            'birth_year': r'(ΕΤΟΣ ΓΕΝΝΗΣΗΣ|ΓΕΝΝΗΘΗΚΑ)[\s:\-]*(\d{4})'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted[field] = match.group(2)
                print(f"    ✅ Βρέθηκε {field}: {match.group(2)}")
        
        if 'amka' in extracted and 'birth_year' not in extracted:
            birth_year = FileProcessor.extract_birth_year_from_amka(extracted['amka'])
            if birth_year:
                extracted['birth_year'] = birth_year
                print(f"    ✅ Βρέθηκε birth_year από ΑΜΚΑ: {birth_year}")
        
        if 'amka' in extracted and 'gender' not in extracted:
            gender = FileProcessor.extract_gender_from_amka(extracted['amka'])
            if gender:
                extracted['gender'] = gender
        
        if 'birth_date' in extracted:
            birth_date = FileProcessor._parse_date(extracted['birth_date'])
            if birth_date:
                extracted['current_age'] = FileProcessor._calculate_age(birth_date)
                extracted['birth_year'] = birth_date.year
                print(f"    🎂 Ηλικία από ημερομηνία: {extracted['current_age']} ετών")
        
        if 'birth_year' in extracted and 'current_age' not in extracted:
            try:
                birth_year = int(extracted['birth_year'])
                current_year = datetime.now().year
                extracted['current_age'] = current_year - birth_year
                print(f"    🎂 Υπολογισμός ηλικίας από birth_year: {extracted['current_age']} ετών")
            except:
                pass
        
        if 'insurance_days' in extracted and 'insurance_years' not in extracted:
            try:
                days = int(extracted['insurance_days'])
                extracted['insurance_years'] = round(days / 365.25, 1)
                print(f"    📅 Μετατροπή {days} ημερών σε {extracted['insurance_years']} έτη")
            except:
                pass
        
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
    def _process_json_data(data):
        """Επεξεργασία δεδομένων JSON"""
        print(f"📋 Επεξεργασία JSON δεδομένων: {type(data)}")
        
        if isinstance(data, list):
            return FileProcessor._calculate_totals_from_records(data)
        else:
            return FileProcessor._standardize_json_data(data)
    
    @staticmethod
    def _standardize_json_data(data):
        """Τυποποίηση δεδομένων JSON"""
        standardized = {}
        
        print(f"🔍 Τυποποίηση JSON: {data}")
        
        mapping = {
            'gender': ['gender', 'sex', 'φύλο'],
            'birth_year': ['birth_year', 'birthYear', 'year_of_birth'],
            'current_age': ['age', 'current_age', 'ηλικία'],
            'insurance_years': ['insurance_years', 'years_insured', 'έτη_ασφάλισης'],
            'insurance_days': ['insurance_days', 'days_insured', 'ημέρες_ασφάλισης'],
            'salary': ['salary', 'income', 'wage', 'μισθός'],
            'heavy_work_years': ['heavy_work_years', 'heavy_years', 'βαρέα_έτη'],
            'children': ['children', 'kids', 'παιδιά'],
            'fund': ['fund', 'insurance_fund', 'ταμείο']
        }
        
        for standard_field, possible_fields in mapping.items():
            for field in possible_fields:
                if field in data:
                    standardized[standard_field] = data[field]
                    print(f"    ✅ Αντιστοίχιση {field} -> {standard_field}: {data[field]}")
                    break
        
        if 'birth_year' in standardized and 'current_age' not in standardized:
            try:
                birth_year = int(standardized['birth_year'])
                current_year = datetime.now().year
                standardized['current_age'] = current_year - birth_year
            except:
                pass
        
        if 'insurance_days' in standardized and 'insurance_years' not in standardized:
            try:
                days = int(standardized['insurance_days'])
                standardized['insurance_years'] = round(days / 365.25, 1)
            except:
                pass
        
        defaults = {
            'gender': 'male',
            'birth_year': 1980,
            'current_age': 45,
            'insurance_years': 25,
            'salary': 1500,
            'heavy_work_years': 0,
            'children': 0,
            'fund': 'ika'
        }
        
        for key, value in defaults.items():
            if key not in standardized:
                standardized[key] = value
        
        return standardized

    @staticmethod
    def process_file(file_content, filename):
        """Κύρια μέθοδος επεξεργασίας αρχείου"""
        print(f"🚀 Επεξεργασία αρχείου: {filename}")
        
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.csv'):
            return FileProcessor.process_csv(file_content)
        elif filename_lower.endswith('.pdf'):
            return FileProcessor.process_pdf(file_content)
        elif filename_lower.endswith('.json'):
            return FileProcessor.process_json(file_content)
        elif any(filename_lower.endswith(fmt) for fmt in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']):
            return ImageProcessor.process_file(file_content, filename)
        else:
            raise Exception("Μη υποστηριζόμενη μορφή αρχείου")