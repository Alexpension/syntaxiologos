from flask_mail import Message
from flask import current_app
from app import mail

def send_email(to, subject, template):
    """Αποστολή email"""
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)

def send_welcome_email(user):
    """Αποστολή welcome email σε νέο χρήστη"""
    subject = "Καλώς ήρθες στο Alex Pension Calculator!"
    template = f"""
    <h2>Καλώς ήρθες, {user.username}!</h2>
    <p>Η εγγραφή σου στο Alex Pension Calculator ολοκληρώθηκε επιτυχώς.</p>
    <p>Μπορείς τώρα να:</p>
    <ul>
        <li>Κάνεις υπολογισμούς σύνταξης</li>
        <li>Αναλύσεις Ελληνικής σύνταξης</li>
        <li>Δημιουργία PDF reports</li>
    </ul>
    <p>Ευχαριστούμε που μας επέλεξες!</p>
    """
    send_email(user.email, subject, template)

def send_calculation_notification(user, calculation):
    """Αποστολή notification για νέο υπολογισμό"""
    subject = "Νέος Υπολογισμός Σύνταξης"
    template = f"""
    <h2>Ο υπολογισμός σύνταξης ολοκληρώθηκε!</h2>
    <p>Γεια σου {user.username},</p>
    <p>Ο νέος σου υπολογισμός σύνταξης έχει ολοκληρωθεί:</p>
    <ul>
        <li><strong>Τελική σύνταξη:</strong> €{calculation.final_pension:,.2f}</li>
        <li><strong>Μηνιαία σύνταξη:</strong> €{calculation.monthly_pension:,.2f}</li>
        <li><strong>Ηλικία συνταξιοδότησης:</strong> {calculation.retirement_age} έτη</li>
    </ul>
    <p>Συνδέσου στην εφαρμογή για να δεις λεπτομέρειες.</p>
    """
    send_email(user.email, subject, template)
