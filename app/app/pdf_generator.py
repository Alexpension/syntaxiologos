from fpdf import FPDF
from datetime import datetime

def generate_pension_report(calculation, filename):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PENSION CALCULATION REPORT', 0, 1, 'C')
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Created: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Basic Information - ΧΡΗΣΙΜΟΠΟΙΟΥΜΕ EUR instead of €
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Basic Information', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    basic_data = [
        ('Current Age:', f'{calculation.current_age} years'),
        ('Retirement Age:', f'{calculation.retirement_age} years'),
        ('Working Years:', f'{calculation.retirement_age - calculation.current_age} years'),
        ('Annual Income:', f'EUR {calculation.current_salary:,.2f}'),
        ('Current Savings:', f'EUR {calculation.current_savings:,.2f}'),
        ('Monthly Contribution:', f'EUR {calculation.monthly_contribution:,.2f}')
    ]
    
    for label, value in basic_data:
        pdf.cell(90, 8, label, 0, 0)
        pdf.cell(0, 8, value, 0, 1)
    
    pdf.ln(10)
    
    # Investment Parameters
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Investment Parameters', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    investment_data = [
        ('Expected Annual Return:', f'{calculation.expected_return:.1f}%'),
        ('Inflation Rate:', f'{calculation.inflation_rate:.1f}%')
    ]
    
    for label, value in investment_data:
        pdf.cell(90, 8, label, 0, 0)
        pdf.cell(0, 8, value, 0, 1)
    
    pdf.ln(10)
    
    # Results - ΧΡΗΣΙΜΟΠΟΙΟΥΜΕ EUR instead of €
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Calculation Results', 0, 1)
    pdf.set_font('Arial', 'B', 12)
    
    results_data = [
        ('Total Pension Fund:', f'EUR {calculation.final_pension:,.2f}'),
        ('Monthly Pension:', f'EUR {calculation.monthly_pension:,.2f}'),
        ('Annual Pension:', f'EUR {calculation.monthly_pension * 12:,.2f}')
    ]
    
    for label, value in results_data:
        pdf.cell(90, 8, label, 0, 0)
        pdf.cell(0, 8, value, 0, 1)
    
    pdf.ln(15)
    
    # Notes
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Important Notes:', 0, 1)
    pdf.set_font('Arial', '', 11)
    
    notes = [
        "Monthly pension is adjusted for inflation",
        "Calculation assumes fixed contributions and returns", 
        "Actual investment returns may vary",
        "Expected return is annual percentage before inflation",
        "Based on 4% safe withdrawal rate (SWR)",
        "All amounts are in Euros (EUR)"
    ]
    
    for note in notes:
        pdf.cell(10)
        pdf.cell(0, 8, f"- {note}", 0, 1)
    
    # Additional calculations section
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Calculation Details:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    details = [
        f"Calculation ID: {calculation.id}",
        f"Calculation Date: {calculation.calculation_date.strftime('%d/%m/%Y %H:%M')}",
        f"Years until retirement: {calculation.retirement_age - calculation.current_age}",
        f"Total contributions period: {(calculation.retirement_age - calculation.current_age) * 12} months"
    ]
    
    for detail in details:
        pdf.cell(10)
        pdf.cell(0, 6, detail, 0, 1)
    
    pdf.output(filename)
    return filename