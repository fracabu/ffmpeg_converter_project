from flask import Flask

def create_app():
    app = Flask(__name__)

    # Configurazioni
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['CONVERTED_FOLDER'] = 'converted'

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app
