from flask import render_template
from app import create_app

app = create_app()

@app.route('/')
def home():
    return "Συνταξιολόγος - Greek Pension Calculator"

@app.route('/calculate')
def calculate():
    return "Υπολογισμός Σύνταξης - Coming Soon!"