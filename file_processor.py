import PyPDF2
import json
import csv
import io
from datetime import datetime, date
import re

class FileProcessor:
    """Επεξεργαστής αρχείων για εξαγωγή πραγματικών δεδομένων σύνταξης"""
    
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
            
            # Συσσωρευμένα δεδομένα από όλες τις εγγραφές
            total_data = FileProcessor._calculate_totals_from_records(data)
            
            # Εμφάνιση των δεδομένων που εξήχθησαν
            print(f"📈 Εξαγόμενα δεδομένα: {total_data}")
            
            return total_data
            
        except Exception as e:
            print(f"❌ Σφάλμα CSV: {e}")
            raise Exception(f"Σφάλμα ανάγνωσης CSV: {str(e)}")
    
    @staticmethod
    def process_pdf(file_content):
        """Επεξεργασία PDF αρχείου - εξαγωγή δεδομένων από κείμενο"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            
            print(f"📄 Κείμενο από PDF ({len(text)} χαρακτήρες):")
            print(text[:500] + "..." if len(text) > 500 else text)
            
            extracted_data = FileProcessor._extract_detailed_data_from_text(text)
            
            print(f"📈 Εξαγόμενα δεδομένα από PDF: {extracted_data}")
            
            return extracted_data
            
        except Exception as e:
            print(f"❌ Σφάλμα PDF: {e}")
            raise Exception(f"Σφάλμα ανάγνωσης PDF: {str(e)}")
    
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
        current_date = datetime.now().date()
        
        # Μεταβλητές για τον πρώτο χρήστη
        first_record = records[0]
        birth_date = None
        gender = 'male'
        fund = 'ika'
        children = 0
        
        print(f"🔍 Αναλύονται {len(records)} εγγραφές...")
        
        for i, record in enumerate(records):
            print(f"  📝 Εγγραφή {i+1}: {record}")
            
            # Συσσώρευση ημερών ασφάλισης
            if 'insurance_days' in record and record['insurance_days']:
                try:
                    days = int(record['insurance_days'])
                    total_insurance_days += days
                    print(f"    ➕ Προσθήκη {days} ημερών ασφάλισης")
                except:
                    pass
            
            # Υπολογισμός ημερών από ημερομηνίες
            days_from_dates = FileProcessor._calculate_insurance_days_from_dates(record)
            if days_from_dates > 0:
                total_insurance_days += days_from_dates
                print(f"    📅 Προσθήκη {days_from_dates} ημερών από ημερομηνίες")
            
            # Μέσος μισθός
            if 'salary_amount' in record and record['salary_amount']:
                try:
                    salary = float(record['salary_amount'])
                    total_salary += salary
                    salary_count += 1
                    print(f"    💰 Προσθήκη μισθού: {salary} €")
                except:
                    pass
            
            # Εξαγωγή βασικών στοιχείων από πρώτη εγγραφή
            if record == first_record:
                if 'birth_date' in record and record['birth_date']:
                    birth_date = FileProcessor._parse_date(record['birth_date'])
                    if birth_date:
                        print(f"    🎂 Ημερομηνία γέννησης: {birth_date}")
                
                if 'fund_code' in record and record['fund_code']:
                    fund = FileProcessor._map_fund_code(record['fund_code'])
                    print(f"    🏦 Ταμείο: {fund}")
                
                # Προσπάθεια εξαγωγής φύλου
                if 'first_name' in record and record['first_name']:
                    gender = FileProcessor._extract_gender_from_name(record['first_name'])
                    print(f"    👤 Φύλο από όνομα: {gender}")
        
        # Υπολογισμός ετών ασφάλισης από ημέρες
        insurance_years = total_insurance_days / 365.25
        
        # Μέσος μισθός
        avg_salary = total_salary / salary_count if salary_count > 0 else 1500
        
        # Υπολογισμός τρέχουσας ηλικίας
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
            # Καθαρισμός string
            date_str = str(date_str).strip()
            
            # Δοκιμή διαφορετικών μορφών
            formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d',
                '%d.%m.%Y', '%Y.%m.%d', '%d %m %Y', '%Y %m %d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except:
                    continue
                    
            # Προσπάθεια με regex για διάφορες μορφές
            date_patterns = [
                r'(\d{4})[-\.\/](\d{1,2})[-\.\/](\d{1,2})',  # YYYY-MM-DD
                r'(\d{1,2})[-\.\/](\d{1,2})[-\.\/](\d{4})',  # DD-MM-YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        year, month, day = groups[0], groups[1], groups[2]
                    else:  # DD-MM-YYYY
                        day, month, year = groups[0], groups[1], groups[2]
                    
                    return date(int(year), int(month), int(day))
                    
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
        
        # Γυναικεία ονόματα (συνηθισμένα ελληνικά)
        female_names = ['μαρια', 'αννα', 'ελενη', 'ευα', 'σοφια', 'κωνσταντινα', 
                       'αικατερινη', 'βασιλικη', 'δαφνη', 'χρυσα', 'irini', 'dimitra']
        
        # Ανδρικό όνομα αν περιέχει γνωστό γυναικείο
        for female_name in female_names:
            if female_name in first_name:
                return 'female'
                
        return 'male'
    
    @staticmethod
    def _extract_detailed_data_from_text(text):
        """Εξαγωγή λεπτομερών δεδομένων από κείμενο PDF"""
        extracted = {}
        
        print("🔍 Εξαγωγή δεδομένων από κείμενο PDF...")
        
        # Βελτιωμένα regex patterns για ελληνικό κείμενο
        patterns = {
            'amka': r'(ΑΜΚΑ|Α\.Μ\.Κ\.Α\.?)[\s:\-]*(\d{11})',
            'birth_date': r'(ΓΕΝΝΗΣΗΣ?|ΗΜΕΡΟΜΗΝΙΑ ΓΕΝΝΗΣΗΣ?)[\s:\-]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
            'insurance_days': r'(ΗΜΕΡΕΣ ΑΣΦΑΛΙΣΗΣ?|ΑΣΦΑΛΙΣΜΕΝΕΣ ΗΜΕΡΕΣ)[\s:\-]*(\d+)',
            'insurance_years': r'(ΕΤΗ ΑΣΦΑΛΙΣΗΣ?|ΑΣΦΑΛΙΣΤΙΚΑ ΕΤΗ)[\s:\-]*(\d+)',
            'salary': r'(ΜΙΣΘΟΣ|ΜΕΣΟΣ ΜΙΣΘΟΣ|ΕΙΣΟΔΗΜΑ)[\s:\-]*(\d+[\.,]?\d*)',
            'employer': r'(ΕΡΓΟΔΟΤΗΣ|ΕΤΑΙΡΕΙΑ)[\s:\-]*([^\n\r]+)',
            'fund': r'(ΤΑΜΕΙΟ|ΑΣΦΑΛΙΣΤΙΚΟ ΤΑΜΕΙΟ)[\s:\-]*([^\n\r]+)',
            'age': r'(ΗΛΙΚΙΑ|ΕΤΩΝ)[\s:\-]*(\d+)',
            'birth_year': r'(ΕΤΟΣ ΓΕΝΝΗΣΗΣ|ΓΕΝΝΗΘΗΚΑ)[\s:\-]*(\d{4})'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted[field] = match.group(2)
                print(f"    ✅ Βρέθηκε {field}: {match.group(2)}")
        
        # Ειδική επεξεργασία για ημερομηνία γέννησης
        if 'birth_date' in extracted:
            birth_date = FileProcessor._parse_date(extracted['birth_date'])
            if birth_date:
                extracted['current_age'] = FileProcessor._calculate_age(birth_date)
                extracted['birth_year'] = birth_date.year
                print(f"    🎂 Ηλικία από ημερομηνία: {extracted['current_age']} ετών")
        
        # Μετατροπή ημερών σε έτη αν χρειαστεί
        if 'insurance_days' in extracted and 'insurance_years' not in extracted:
            try:
                days = int(extracted['insurance_days'])
                extracted['insurance_years'] = round(days / 365.25, 1)
                print(f"    📅 Μετατροπή {days} ημερών σε {extracted['insurance_years']} έτη")
            except:
                pass
        
        # Αν δεν βρέθηκε ηλικία, δοκίμασε από έτος γέννησης
        if 'birth_year' in extracted and 'current_age' not in extracted:
            try:
                birth_year = int(extracted['birth_year'])
                current_year = datetime.now().year
                extracted['current_age'] = current_year - birth_year
                print(f"    📅 Ηλικία από έτος γέννησης: {extracted['current_age']} ετών")
            except:
                pass
        
        # Αν δεν βρέθηκαν έτη ασφάλισης, δοκίμασε από ηλικία
        if 'insurance_years' not in extracted and 'current_age' in extracted:
            try:
                age = int(extracted['current_age'])
                # Υποθέτουμε ότι ξεκίνησε να εργάζεται στα 20
                extracted['insurance_years'] = max(0, age - 20)
                print(f"    📊 Εκτίμηση ετών ασφάλισης από ηλικία: {extracted['insurance_years']}")
            except:
                pass
        
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
    def _process_json_data(data):
        """Επεξεργασία δεδομένων JSON"""
        print(f"📋 Επεξεργασία JSON δεδομένων: {type(data)}")
        
        if isinstance(data, list):
            # Αν είναι λίστα εγγραφών, υπολόγισε σύνολα
            return FileProcessor._calculate_totals_from_records(data)
        else:
            # Αν είναι απλό αντικείμενο, τυποποίησε τα δεδομένα
            return FileProcessor._standardize_json_data(data)
    
    @staticmethod
    def _standardize_json_data(data):
        """Τυποποίηση δεδομένων JSON"""
        standardized = {}
        
        print(f"🔍 Τυποποίηση JSON: {data}")
        
        mapping = {
            'gender': ['gender', 'sex', 'φύλο', 'fulo'],
            'birth_year': ['birth_year', 'birthYear', 'year_of_birth', 'έτος_γέννησης'],
            'current_age': ['age', 'current_age', 'ηλικία', 'ilikia'],
            'insurance_years': ['insurance_years', 'years_insured', 'έτη_ασφάλισης'],
            'insurance_days': ['insurance_days', 'days_insured', 'ημέρες_ασφάλισης'],
            'salary': ['salary', 'income', 'wage', 'μισθός', 'misthos'],
            'heavy_work_years': ['heavy_work_years', 'heavy_years', 'βαρέα_έτη'],
            'children': ['children', 'kids', 'παιδιά', 'paidia'],
            'fund': ['fund', 'insurance_fund', 'ταμείο', 'tameio']
        }
        
        for standard_field, possible_fields in mapping.items():
            for field in possible_fields:
                if field in data:
                    standardized[standard_field] = data[field]
                    print(f"    ✅ Αντιστοίχιση {field} -> {standard_field}: {data[field]}")
                    break
        
        # Υπολογισμός ηλικίας από birth_year αν χρειαστεί
        if 'birth_year' in standardized and 'current_age' not in standardized:
            try:
                birth_year = int(standardized['birth_year'])
                current_year = datetime.now().year
                standardized['current_age'] = current_year - birth_year
                print(f"    📅 Υπολογισμός ηλικίας από έτος γέννησης: {standardized['current_age']}")
            except:
                pass
        
        # Μετατροπή ημερών σε έτη
        if 'insurance_days' in standardized and 'insurance_years' not in standardized:
            try:
                days = int(standardized['insurance_days'])
                standardized['insurance_years'] = round(days / 365.25, 1)
                print(f"    📅 Μετατροπή {days} ημερών σε {standardized['insurance_years']} έτη")
            except:
                pass
        
        # Default τιμές ΜΟΝΟ αν δεν βρέθηκε τίποτα
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
                print(f"    ⚠️ Χρήση default για {key}: {value}")
        
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
        else:
            raise Exception("Μη υποστηριζόμενη μορφή αρχείου")