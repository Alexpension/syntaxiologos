import os
import sqlite3
from flask import Flask, render_template, request, flash, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Δημιουργία φακέλων
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/results', exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_insurance_data(text):
    """Ανάλυση δεδομένων - προσομοίωση OCR"""
    data = {
        'amka': 'Αναγνωρίστηκε από αρχείο',
        'employer': 'Αναγνωρίστηκε από αρχείο', 
        'insurance_years': 25,
        'salary': 1500.0,
        'last_5_years_avg': 1450.0
    }
    return data

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
    """Δημιουργία PDF report"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "ΣΥΝΤΑΞΙΟΛΟΓΟΣ - ΑΝΑΛΥΤΙΚΗ ΕΚΘΕΣΗ", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "ΣΤΟΙΧΕΙΑ ΑΣΦΑΛΙΣΗΣ:", 0, 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, f"ΑΜΚΑ: {insurance_data['amka']}", 0, 1)
    pdf.cell(200, 8, f"Εργοδότης: {insurance_data['employer']}", 0, 1)
    pdf.cell(200, 8, f"Έτη Ασφάλισης: {insurance_data['insurance_years']}", 0, 1)
    pdf.cell(200, 8, f"Μέσος Μισθός: {insurance_data['last_5_years_avg']} €", 0, 1)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "ΑΠΟΤΕΛΕΣΜΑΤΑ ΥΠΟΛΟΓΙΣΜΟΥ:", 0, 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, f"Βασική Σύνταξη: {pension_data['basic_pension']} €", 0, 1)
    pdf.cell(200, 8, f"Επίδομα: {pension_data['social_benefit']} €", 0, 1)
    pdf.cell(200, 8, f"ΣΥΝΟΛΙΚΗ ΣΥΝΤΑΞΗ: {pension_data['total_pension']} €", 0, 1)
    pdf.cell(200, 8, f"Ποσοστό Αντικατάστασης: {pension_data['replacement_rate']}%", 0, 1)
    
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 8, f"Ημερομηνία υπολογισμού: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
    
    filename = f"static/results/pension_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Δεν επιλέχθηκε αρχείο')
        return render_template('index.html')
    
    file = request.files['file']
    if file.filename == '':
        flash('Δεν επιλέχθηκε αρχείο')
        return render_template('index.html')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Προσομοίωση OCR - σταθερά δεδομένα για τώρα
            extracted_text = "Προσομοίωση OCR - Τα δεδομένα θα αναγνωριστούν στο Render"
            
            # Ανάλυση δεδομένων
            insurance_data = parse_insurance_data(extracted_text)
            
            # Υπολογισμός σύνταξης
            pension_data = calculate_real_pension(insurance_data)
            
            # Δημιουργία PDF report
            pdf_report = create_pdf_report(insurance_data, pension_data)
            
            # Καθαρισμός
            os.remove(filepath)
            
            return render_template('results.html', 
                                 insurance_data=insurance_data,
                                 pension_data=pension_data,
                                 pdf_report=pdf_report,
                                 extracted_text=extracted_text)
            
        except Exception as e:
            os.remove(filepath)
            flash(f'Σφάλμα επεξεργασίας: {str(e)}')
            return render_template('index.html')
    
    flash('Μη επιτρεπτός τύπος αρχείου')
    return render_template('index.html')

@app.route('/manual', methods=['POST'])
def manual_calculation():
    """Χειροκίνητη εισαγωγή δεδομένων"""
    try:
        age = int(request.form['age'])
        years = int(request.form['years'])
        salary = float(request.form.get('salary', 1500))
        
        insurance_data = {
            'amka': 'Χειροκίνητη εισαγωγή',
            'employer': 'Χειροκίνητη εισαγωγή',
            'insurance_years': years,
            'salary': salary,
            'last_5_years_avg': salary
        }
        
        pension_data = calculate_real_pension(insurance_data)
        pdf_report = create_pdf_report(insurance_data, pension_data)
        
        return render_template('results.html',
                             insurance_data=insurance_data,
                             pension_data=pension_data,
                             pdf_report=pdf_report)
                             
    except Exception as e:
        flash(f'Σφάλμα υπολογισμού: {str(e)}')
        return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)