from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Συνταξιολόγος - Greek Pension Calculator ΕΞΕΙ!"

@app.route('/calculate')
def calculate():
    return "Υπολογισμός Σύνταξης - Coming Soon!"

@app.route('/healthz')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)