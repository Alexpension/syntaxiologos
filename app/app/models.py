from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    calculations = db.relationship('PensionCalculation', backref='author', lazy='dynamic')
    pension_data = db.relationship('GreekPensionData', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class PensionCalculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    calculation_date = db.Column(db.DateTime, default=datetime.utcnow)
    current_age = db.Column(db.Integer)
    retirement_age = db.Column(db.Integer)
    current_salary = db.Column(db.Float)
    current_savings = db.Column(db.Float)
    monthly_contribution = db.Column(db.Float)
    expected_return = db.Column(db.Float)
    inflation_rate = db.Column(db.Float)
    final_pension = db.Column(db.Float)
    monthly_pension = db.Column(db.Float)
    
    def __repr__(self):
        return f'<PensionCalculation {self.id}>'

class GreekPensionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filename = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ΝΕΑ ΠΕΔΙΑ για τα εξαγόμενα δεδομένα
    customer_name = db.Column(db.String(200))
    afm = db.Column(db.String(20))
    insurance_years = db.Column(db.Integer)
    retirement_age = db.Column(db.Integer)
    remaining_years = db.Column(db.Integer)
    retirement_date = db.Column(db.String(50))
    status = db.Column(db.String(100))
    confidence_score = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<GreekPensionData {self.filename}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))