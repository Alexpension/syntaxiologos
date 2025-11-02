import os
from flask import Flask, render_template, request, flash, send_file
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Δημιουργία φακέλων
os.makedirs('static/results', exist_ok=True)

class GreekPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ΣΥΝΤΑΞΙΟΛΟΓΟΣ - ΑΝΑΛΥΤΙΚΗ ΕΚΘΕΣΗ', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Σελίδα {self.page_no()}', 0, 0, 'C')

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
    """Δημιουργία PDF report με σωστό encoding"""
    pdf = GreekPDF()
    pdf.add_page()
    
    # Στοιχεία Ασφάλισης
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'ΣΤΟΙΧΕΙΑ ΑΣΦΑΛΙΣΗΣ:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"AMKA: {insurance_data['amka']}", 0, 1)
    pdf.cell(0, 8, f"Εργοδοτης: {insurance_data['employer']}", 0, 1)
    pdf.cell(0, 8, f"Ετη Ασφαλισης: {insurance_data['insurance_years']}", 0, 1)
    pdf.cell(0, 8, f"Μεσος Μισθος: {insurance_data['last_5_years_avg']} EUR", 0, 1)
    
    pdf.ln(10)
    
    # Αποτελέσματα Υπολογισμού
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'ΑΠΟΤΕΛΕΣΜΑΤΑ ΥΠΟΛΟΓΙΣΜΟΥ:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Βασικη Συνταξη: {pension_data['basic_pension']} EUR", 0, 1)
    pdf.cell(0, 8, f"Επιδομα: {pension_data['social_benefit']} EUR", 0, 1)
    pdf.cell(0, 8, f"ΣΥΝΟΛΙΚΗ ΣΥΝΤΑΞΗ: {pension_data['total_pension']} EUR", 0, 1)
    pdf.cell(0, 8, f"Ποσοστο Αντικαταστασης: {pension_data['replacement_rate']}%", 0, 1)
    
    pdf.ln(15)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 8, f"Ημερομηνια υπολογισμου: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1)
    
    filename = f"static/results/pension_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename

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
            'amka': f'Manual - {fund.upper()}',
            'employer': f'Tameio {fund.upper()}',
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
        flash(f'Σφαλμα υπολογισμου: {str(e)}')
        return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)