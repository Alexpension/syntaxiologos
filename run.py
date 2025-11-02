from app import create_app, db
from app.models import PensionCalculation

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Χρήσιμο για debugging - δίνει πρόσβαση στη βάση από terminal"""
    return {'db': db, 'PensionCalculation': PensionCalculation}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)