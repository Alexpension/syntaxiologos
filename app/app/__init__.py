from flask_mail import Mail
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config  # ← Τώρα θα δουλέψει κανονικά!

db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    
    # User loader για Flask-Login
    from app.models import User
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Routes
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app