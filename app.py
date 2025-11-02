from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    age = int(request.form['age'])
    years = int(request.form['years'])
    basic_pension = years * 50
    return f"""
    <h2>Αποτέλεσμα Υπολογισμού</h2>
    <p>Ηλικία: {age} έτη</p>
    <p>Έτη ασφάλισης: {years}</p>
    <p><strong>Εκτιμώμενη σύνταξη: {basic_pension} €/μήνα</strong></p>
    <a href="/">Νέος υπολογισμός</a>
    """

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)