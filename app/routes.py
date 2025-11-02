# routes.py - ΜΟΝΟ routes, χωρίς create_app
from flask import current_app as app

@app.route('/')
def home():
    return "Συνταξιολόγος - Greek Pension Calculator ΕΞΕΙ!"

@app.route('/calculate')
def calculate():
    return "Υπολογισμός Σύνταξης - Coming Soon!"

@app.route('/healthz')
def health_check():
    return "OK", 200