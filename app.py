import os
import sqlite3
from flask import Flask, render_template, request, flash, send_file, session
from fpdf import FPDF
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['DATABASE'] = 'pension_calculator.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Δημιουργία φακέλων
os.makedirs('static/results', exist_ok=True)

def get_db_connection():
    """Σύνδεση με τη βάση δεδομένων"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Αρχικοποίηση βάσης δεδομένων"""
    conn = get_db_connection()
    
    # Πίνακας χρηστών
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Πίνακας υπολογισμών
    conn.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            age INTEGER NOT NULL,
            insurance_years INTEGER NOT NULL,
            salary REAL NOT NULL,
            fund TEXT NOT NULL,
            basic_pension REAL NOT NULL,
            social_benefit REAL NOT NULL,
            total_pension REAL NOT NULL,
            replacement_rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def calculate_real_pension(insurance_data):
    """ΠΡΑΓΜΑΤΙΚΟΣ υπολογισμός σύνταξης"""
    years = insurance_data['insurance_years']
    avg_salary = insurance_data['last_5_years_avg']
    
    if years >= 40:
        replacement_rate = 0.80
    elif years >= 35:
        replacement_rate = 0.70
    elif years >= 30:
        replacement_rate = 0.60
    elif years >= 25:
        replacement_rate = 0.50
    elif years >= 20:
        replacement_rate = 0.45
    elif years >= 15:
        replacement_rate = 0.40
    else:
        replacement_rate = 0.35
    
    basic_pension = avg_salary * replacement_rate
    
    if basic_pension < 800:
        social_benefit = 150
    else:
        social_benefit = 0
    
    total_pension = basic_pension + social_benefit
    
    return {
        'basic_pension': round(basic_pension, 2),
        'social_benefit': social_benefit,
        'total_pension': round(total_pension, 2),
        'replacement_rate': replacement_rate * 100
    }

def create_pdf_report(insurance_data, pension_data):
    """PDF report - ONLY ASCII"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title - ONLY ASCII
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, 'SYNTAXIOLOGOS - PENSION REPORT', 0, 1, 'C')
    pdf.ln(10)
    
    # Insurance Data
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, 'INSURANCE DATA:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(200, 8, f"AMKA: {insurance_data['amka']}", 0, 1)
    pdf.cell(200, 8, f"Employer: {insurance_data['employer']}", 0, 1)
    pdf.cell(200, 8, f"Insurance Years: {insurance_data['insurance_years']}", 0, 1)
    pdf.cell(200, 8, f"Avg Salary: {insurance_data['last_5_years_avg']} EUR", 0, 1)
    
    pdf.ln(10)
    
    # Calculation Results
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, 'PENSION CALCULATION:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(200, 8, f"Basic Pension: {pension_data['basic_pension']} EUR", 0, 1)
    pdf.cell(200, 8, f"Social Benefit: {pension_data['social_benefit']} EUR", 0, 1)
    pdf.cell(200, 8, f"TOTAL PENSION: {pension_data['total_pension']} EUR", 0, 1)
    pdf.cell(200, 8, f"Replacement Rate: {pension_data['replacement_rate']}%", 0, 1)
    
    pdf.ln(15)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(200, 8, f"Calculation Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
    
    filename = f"static/results/pension_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

def save_calculation_to_db(user_id, form_data, pension_data):
    """Αποθήκευση υπολογισμού στη βάση"""
    conn = get_db_connection()
    
    conn.execute('''
        INSERT INTO calculations 
        (user_id, age, insurance_years, salary, fund, basic_pension, social_benefit, total_pension, replacement_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        form_data['age'],
        form_data['years'],
        form_data['salary'],
        form_data['fund'],
        pension_data['basic_pension'],
        pension_data['social_benefit'],
        pension_data['total_pension'],
        pension_data['replacement_rate']
    ))
    
    conn.commit()
    calculation_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    
    return calculation_id

def get_user_calculations(user_id):
    """Λήψη ιστορικού υπολογισμών χρήστη"""
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

@app.route('/manual', methods=['POST'])
def manual_calculation():
    """Χειροκίνητη εισαγωγή δεδομένων"""
    try:
        age = int(request.form['age'])
        years = int(request.form['years'])
        salary = float(request.form.get('salary', 1500))
        fund = request.form.get('fund', 'ika')
        
        insurance_data = {
            'amka': f'Manual-{fund.upper()}',
            'employer': f'Fund-{fund.upper()}',
            'insurance_years': years,
            'salary': salary,
            'last_5_years_avg': salary
        }
        
        pension_data = calculate_real_pension(insurance_data)
        pdf_report = create_pdf_report(insurance_data, pension_data)
        
        # Αποθήκευση στη βάση (αν ο χρήστης είναι συνδεδεμένος)
        if 'user_id' in session:
            save_calculation_to_db(session['user_id'], {
                'age': age,
                'years': years,
                'salary': salary,
                'fund': fund
            }, pension_data)
        
        return render_template('results.html',
                             insurance_data=insurance_data,
                             pension_data=pension_data,
                             pdf_report=pdf_report)
                             
    except Exception as e:
        flash(f'Calculation Error: {str(e)}')
        return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Εγγραφή νέου χρήστη"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        full_name = request.form.get('full_name', '')
        
        try:
            conn = get_db_connection()
            
            # Έλεγχος αν υπάρχει ήδη ο χρήστης
            existing_user = conn.execute(
                'SELECT id FROM users WHERE email = ?', (email,)
            ).fetchone()
            
            if existing_user:
                flash('Το email χρησιμοποιείται ήδη')
                return render_template('register.html')
            
            # Δημιουργία νέου χρήστη
            password_hash = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)',
                (email, password_hash, full_name)
            )
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
    """Σύνδεση χρήστη"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM users WHERE email = ?', (email,)
            ).fetchone()
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
    """Αποσύνδεση χρήστη"""
    session.clear()
    flash('Έγινε αποσύνδεση')
    return render_template('index.html')

@app.route('/history')
def history():
    """Ιστορικό υπολογισμών"""
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

# Αρχικοποίηση βάσης δεδομένων κατά την εκκίνηση
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)