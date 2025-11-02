from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class PensionCalculationForm(FlaskForm):
    current_age = IntegerField('Τρέχουσα Ηλικία', validators=[
        DataRequired(), NumberRange(min=18, max=70)
    ])
    retirement_age = IntegerField('Ηλικία Συνταξιοδότησης', validators=[
        DataRequired(), NumberRange(min=55, max=75)
    ])
    current_salary = FloatField('Τρέχον Ετήσιο Εισόδημα (€)', validators=[
        DataRequired(), NumberRange(min=0)
    ])
    current_savings = FloatField('Τρέχουσες Αποταμιεύσεις (€)', validators=[
        NumberRange(min=0)
    ], default=0)
    monthly_contribution = FloatField('Μηνιαία Εισφορά (€)', validators=[
        DataRequired(), NumberRange(min=0)
    ])
    expected_return = FloatField('Αναμενόμενη Ετήσια Απόδοση (%)', validators=[
        DataRequired(), NumberRange(min=0, max=20)
    ], default=6.0)
    inflation_rate = FloatField('Ποσοστό Πληθωρισμού (%)', validators=[
        NumberRange(min=0, max=10)
    ], default=2.0)
    submit = SubmitField('Υπολογισμός Σύνταξης')

class GreekPensionUploadForm(FlaskForm):
    pdf_file = FileField('Ανέβασμα PDF Ασφάλισης', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'Μόνο αρχεία PDF επιτρέπονται!')
    ])
    submit = SubmitField('Ανέβασμα και Ανάλυση PDF')