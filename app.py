import os
import sqlite3
from flask import Flask, render_template, request, flash, send_file, session
from fpdf import FPDF
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from file_processor import FileProcessor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['DATABASE'] = 'pension_calculator.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs('static/results', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            gender TEXT NOT NULL,
            birth_year INTEGER NOT NULL,
            current_age INTEGER NOT NULL,
            insurance_years INTEGER NOT NULL,
            heavy_work_years INTEGER DEFAULT 0,
            salary REAL NOT NULL,
            fund TEXT NOT NULL,
            children INTEGER DEFAULT 0,
            basic_pension REAL NOT NULL,
            national_pension REAL NOT NULL,
            social_benefit REAL NOT NULL,
            children_benefit REAL NOT NULL,
            total_pension REAL NOT NULL,
            replacement_rate REAL NOT NULL,
            retirement_age INTEGER NOT NULL,
            years_remaining INTEGER NOT NULL,
            eligible_for_early BOOLEAN NOT NULL,
            eligible_for_heavy BOOLEAN NOT NULL,
            required_years_full INTEGER NOT NULL,
            required_years_early INTEGER NOT NULL,
            required_heavy_years INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def calculate_retirement_age(birth_year, gender, heavy_work_years):
    if heavy_work_years >= 15:
        return 58
    if birth_year <= 1955:
        return 65 if gender == 'male' else 60
    elif birth_year <= 1965:
        return 67 if gender == 'male' else 62
    else:
        return 67

def calculate_replacement_rate(insurance_years, fund):
    fund_rates = {
        'ika': {40: 0.80, 35: 0.70, 30: 0.60, 25: 0.50, 20: 0.45, 15: 0.40},
        'efka': {40: 0.80, 35: 0.70, 30: 0.60, 25: 0.50, 20: 0.45, 15: 0.40},
        'oaee': {40: 0.65, 35: 0.55, 30: 0.45, 25: 0.40, 20: 0.35, 15: 0.30},
        'etaa': {40: 0.70, 35: 0.60, 30: 0.50, 25: 0.45, 20: 0.40, 15: 0.35},
        'other': {40: 0.75, 35: 0.65, 30: 0.55, 25: 0.45, 20: 0.40, 15: 0.35}
    }
    rates = fund_rates.get(fund, fund_rates['ika'])
    for years_threshold, rate in sorted(rates.items(), reverse=True):
        if insurance_years >= years_threshold:
            return rate
    return 0.25

def check_full_pension_eligibility(current_age, insurance_years, retirement_age):
    return (current_age >= retirement_age and insurance_years >= 15)

def check_early_pension_eligibility(current_age, insurance_years, heavy_work_years):
    if heavy_work_years >= 15:
        return (current_age >= 55 and insurance_years >= 25)
    return (current_age >= 62 and insurance_years >= 35)

def check_heavy_work_pension_eligibility(heavy_work_years):
    return heavy_work_years >= 15

def calculate_national_pension(insurance_years, basic_pension):
    if insurance_years >= 15:
        return 384.0
    return 0.0

def calculate_social_benefit(total_pension_before_benefits):
    if total_pension_before_benefits < 800:
        return 150.0
    return 0.0

def calculate_children_benefit(children):
    return children * 50.0

def calculate_early_reduction(years_early):
    return years_early * 0.06

def calculate_greek_pension(form_data):
    gender = form_data['gender']
    birth_year = int(form_data['birth_year'])
    current_age = int(form_data['current_age'])
    insurance_years = int(form_data['insurance_years'])
    heavy_work_years = int(form_data.get('heavy_work_years', 0))
    salary = float(form_data['salary'])
    fund = form_data['fund']
    children = int(form_data.get('children', 0))
    
    retirement_age = calculate_retirement_age(birth_year, gender, heavy_work_years)
    years_remaining = max(0, retirement_age - current_age)
    
    eligible_for_full = check_full_pension_eligibility(current_age, insurance_years, retirement_age)
    eligible_for_early = check_early_pension_eligibility(current_age, insurance_years, heavy_work_years)
    eligible_for_heavy = check_heavy_work_pension_eligibility(heavy_work_years)
    
    replacement_rate = calculate_replacement_rate(insurance_years, fund)
    basic_pension = salary * replacement_rate
    
    national_pension = calculate_national_pension(insurance_years, basic_pension)
    social_benefit = calculate_social_benefit(basic_pension + national_pension)
    children_benefit = calculate_children_benefit(children)
    
    if eligible_for_early and not eligible_for_full:
        reduction_rate = calculate_early_reduction(years_remaining)
        basic_pension *= (1 - reduction_rate)
    
    total_pension = basic_pension + national_pension + social_benefit + children_benefit
    
    return {
        'basic_pension': round(basic_pension, 2),
        'national_pension': round(national_pension, 2),
        'social_benefit': round(social_benefit, 2),
        'children_benefit': round(children_benefit, 2),
        'total_pension': round(total_pension, 2),
        'replacement_rate': round(replacement_rate * 100, 1),
        'retirement_age': retirement_age,
        'years_remaining': years_remaining,
        'eligible_for_full': eligible_for_full,
        'eligible_for_early': eligible_for_early,
        'eligible_for_heavy': eligible_for_heavy,
        'required_years_full': max(0, 15 - insurance_years),
        'required_years_early': max(0, 35 - insurance_years),
        'required_heavy_years': max(0, 15 - heavy_work_years),
        'gender': gender,
        'birth_year': birth_year,
        'current_age': current_age,
        'insurance_years': insurance_years,
        'heavy_work_years': heavy_work_years,
        'salary': salary,
        'fund': fund,
        'children': children,
        'data_source': form_data.get('data_source', 'Χειροκίνητη εισαγωγή')
    }

def create_pdf_report(pension_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, 'SYNTAXIOLOGOS - ΑΝΑΛΥΤΙΚΗ ΕΚΘΕΣΗ ΣΥΝΤΑΞΗΣ', 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, 'ΣΤΟΙΧΕΙΑ ΑΣΦΑΛΙΣΜΕΝΟΥ:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(200, 8, f"Πηγή δεδομένων: {pension_data.get('data_source', 'Χειροκίνητη εισαγωγή')}", 0, 1)
    pdf.cell(200, 8, f"Φύλο: {pension_data['gender']}", 0, 1)
    pdf.cell(200, 8, f"Έτος γέννησης: {pension_data['birth_year']}", 0, 1)
    pdf.cell(200, 8, f"Τρέχουσα ηλικία: {pension_data['current_age']} ετών", 0, 1)
    pdf.cell(200, 8, f"Έτη ασφάλισης: {pension_data['insurance_years']}", 0, 1)
    if pension_data.get('insurance_days'):
        pdf.cell(200, 8, f"Ημέρες ασφάλισης: {pension_data['insurance_days']}", 0, 1)
    pdf.cell(200, 8, f"Έτη βαρέας εργασίας: {pension_data['heavy_work_years']}", 0, 1)
    pdf.cell(200, 8, f"Μισθός: {pension_data['salary']} €", 0, 1)
    pdf.cell(200, 8, f"Ταμείο: {pension_data['fund']}", 0, 1)
    pdf.cell(200, 8, f"Παιδιά: {pension_data['children']}", 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, 'ΥΠΟΛΟΓΙΣΜΟΣ ΣΥΝΤΑΞΗΣ:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(200, 8, f"Βασική σύνταξη: {pension_data['basic_pension']} €", 0, 1)
    pdf.cell(200, 8, f"Εθνική σύνταξη: {pension_data['national_pension']} €", 0, 1)
    pdf.cell(200, 8, f"Επίδομα κοινωνικής ασφάλισης: {pension_data['social_benefit']} €", 0, 1)
    pdf.cell(200, 8, f"Επίδομα τέκνων: {pension_data['children_benefit']} €", 0, 1)
    pdf.cell(200, 8, f"ΣΥΝΟΛΙΚΗ ΣΥΝΤΑΞΗ: {pension_data['total_pension']} €", 0, 1)
    pdf.cell(200, 8, f"Ποσοστό αντικατάστασης: {pension_data['replacement_rate']}%", 0, 1)
    pdf.cell(200, 8, f"Ηλικία συνταξιοδότησης: {pension_data['retirement_age']}", 0, 1)
    pdf.cell(200, 8, f"Έτη που απομένουν: {pension_data['years_remaining']}", 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, 'ΔΙΚΑΙΟΛΟΓΗΣΗ:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(200, 8, f"Πλήρης σύνταξη: {'ΝΑΙ' if pension_data['eligible_for_full'] else 'ΟΧΙ'}", 0, 1)
    pdf.cell(200, 8, f"Προνομιακή σύνταξη: {'ΝΑΙ' if pension_data['eligible_for_early'] else 'ΟΧΙ'}", 0, 1)
    pdf.cell(200, 8, f"Σύνταξη βαρέας εργασίας: {'ΝΑΙ' if pension_data['eligible_for_heavy'] else 'ΟΧΙ'}", 0, 1)
    
    if not pension_data['eligible_for_full']:
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(200, 8, "ΑΠΑΙΤΟΥΜΕΝΑ ΓΙΑ ΠΛΗΡΗ ΣΥΝΤΑΞΗ:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(200, 6, f"Επιπλέον έτη ασφάλισης: {pension_data['required_years_full']}", 0, 1)
        pdf.cell(200, 6, f"Επιπλέον έτη βαρέας εργασίας: {pension_data['required_heavy_years']}", 0, 1)
    
    pdf.ln(15)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(200, 8, f"Ημερομηνία υπολογισμού: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
    pdf.cell(200, 8, "ΣΥΝΤΑΞΙΟΛΟΓΟΣ - Σύστημα Αυτόματων Υπολογισμών Σύνταξης", 0, 1)
    
    filename = f"static/results/pension_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

def save_calculation_to_db(user_id, pension_data):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO calculations 
        (user_id, gender, birth_year, current_age, insurance_years, heavy_work_years, 
         salary, fund, children, basic_pension, national_pension, social_benefit, 
         children_benefit, total_pension, replacement_rate, retirement_age, years_remaining,
         eligible_for_early, eligible_for_heavy, required_years_full, required_years_early, required_heavy_years)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, pension_data['gender'], pension_data['birth_year'], pension_data['current_age'],
        pension_data['insurance_years'], pension_data['heavy_work_years'], pension_data['salary'],
        pension_data['fund'], pension_data['children'], pension_data['basic_pension'],
        pension_data['national_pension'], pension_data['social_benefit'], pension_data['children_benefit'],
        pension_data['total_pension'], pension_data['replacement_rate'], pension_data['retirement_age'],
        pension_data['years_remaining'], pension_data['eligible_for_early'], pension_data['eligible_for_heavy'],
        pension_data['required_years_full'], pension_data['required_years_early'], pension_data['required_heavy_years']
    ))
    conn.commit()
    calculation_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return calculation_id

def get_user_calculations(user_id):
    conn = get_db_connection()
    calculations = conn.execute('''
        SELECT * FROM calculations 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id,)).fetchall()
    conn.close()
    return calculations

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/manual', methods=['GET', 'POST'])
def manual_calculation():
    if request.method == 'GET':
        return render_template('index.html')
    try:
        form_data = {
            'gender': request.form.get('gender', 'male'),
            'birth_year': request.form.get('birth_year', '1980'),
            'current_age': request.form.get('current_age', '40'),
            'insurance_years': request.form.get('insurance_years', '20'),
            'heavy_work_years': request.form.get('heavy_work_years', '0'),
            'salary': request.form.get('salary', '1500'),
            'fund': request.form.get('fund', 'ika'),
            'children': request.form.get('children', '0'),
            'data_source': 'Χειροκίνητη εισαγωγή'
        }
        form_data['birth_year'] = int(form_data['birth_year'])
        form_data['current_age'] = int(form_data['current_age'])
        form_data['insurance_years'] = int(form_data['insurance_years'])
        form_data['heavy_work_years'] = int(form_data['heavy_work_years'])
        form_data['salary'] = float(form_data['salary'])
        form_data['children'] = int(form_data['children'])
        
        pension_data = calculate_greek_pension(form_data)
        pdf_report = create_pdf_report(pension_data)
        
        if 'user_id' in session:
            save_calculation_to_db(session['user_id'], pension_data)
        
        return render_template('results.html', pension_data=pension_data, pdf_report=pdf_report)
    except Exception as e:
        flash(f'Σφάλμα υπολογισμού: {str(e)}')
        return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')
    try:
        if 'file' not in request.files:
            flash('Δεν επιλέχθηκε αρχείο')
            return render_template('upload.html')
        
        file = request.files['file']
        if file.filename == '':
            flash('Δεν επιλέχθηκε αρχείο')
            return render_template('upload.html')
        
        if file:
            filename = file.filename.lower()
            
            # Έλεγχος για PDF e-ΕΦΚΑ
            if filename.endswith('.pdf'):
                flash('🔍 Επεξεργασία PDF e-ΕΦΚΑ... Παρακαλώ περιμένετε')
            
            file_content = file.read()
            extracted_data = FileProcessor.process_file(file_content, file.filename)
            
            # Προσθήκη πηγής δεδομένων
            if filename.endswith('.pdf'):
                extracted_data['data_source'] = 'Αυτόματη ανάλυση PDF e-ΕΦΚΑ'
            elif filename.endswith('.csv'):
                extracted_data['data_source'] = 'Αρχείο CSV'
            elif filename.endswith('.json'):
                extracted_data['data_source'] = 'Αρχείο JSON'
            else:
                extracted_data['data_source'] = 'Αρχείο εικόνας/άλλο'
            
            pension_data = calculate_greek_pension(extracted_data)
            pdf_report = create_pdf_report(pension_data)
            
            if 'user_id' in session:
                save_calculation_to_db(session['user_id'], pension_data)
            
            return render_template('results.html', pension_data=pension_data, pdf_report=pdf_report)
    except Exception as e:
        flash(f'Σφάλμα επεξεργασίας αρχείου: {str(e)}')
        return render_template('upload.html')

@app.route('/csv-template')
def csv_template():
    """Σελίδα με το πρότυπο CSV"""
    return render_template('csv_template.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form.get('full_name', '')
        try:
            conn = get_db_connection()
            existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing_user:
                flash('Το email χρησιμοποιείται ήδη')
                return render_template('register.html')
            password_hash = generate_password_hash(password)
            conn.execute('INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)', (email, password_hash, full_name))
            conn.commit()
            user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.close()
            session['user_id'] = user_id
            session['user_email'] = email
            flash('Επιτυχής εγγραφή!')
            return render_template('index.html')
        except Exception as e:
            flash(f'Σφάλμα εγγραφής: {str(e)}')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            conn.close()
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                flash('Επιτυχής σύνδεση!')
                return render_template('index.html')
            else:
                flash('Λάθος email ή κωδικός')
                return render_template('login.html')
        except Exception as e:
            flash(f'Σφάλμα σύνδεσης: {str(e)}')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Έγινε αποσύνδεση')
    return render_template('index.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        flash('Παρακαλώ συνδεθείτε για να δείτε το ιστορικό')
        return render_template('login.html')
    calculations = get_user_calculations(session['user_id'])
    return render_template('history.html', calculations=calculations)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)

with app.app_context():
    init_db()