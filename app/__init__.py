from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Import routes ΜΕΤΑ τη δημιουργία του app
    from . import routes
    return app