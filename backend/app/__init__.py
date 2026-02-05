# backend/app/__init__.py
from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail # Ajout de Flask-Mail
from backend.config import AppConfig

# Initialisation des extensions
mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail() # Initialisation de Mail

def create_app(config_class=AppConfig):
    """
    Factory pour créer et configurer l'application Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialiser les extensions avec l'application
    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app) # Initialiser Mail avec l'app

    # Enregistrer les Blueprints (routes)
    # Les blueprints seront importés et enregistrés ici au fur et à mesure de leur création.

    # Exemple: Blueprint pour l'authentification
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth') # Tous les endpoints d'auth seront sous /api/auth

    # Blueprint pour les professeurs
    from .routes.professor_routes import professor_bp
    app.register_blueprint(professor_bp, url_prefix='/api/professor')

    # Blueprint pour les étudiants
    from .routes.student_routes import student_bp
    app.register_blueprint(student_bp, url_prefix='/api/student')

    # Blueprint pour les administrateurs
    from .routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Blueprint pour la messagerie
    from .routes.message_routes import message_bp
    app.register_blueprint(message_bp, url_prefix='/api/messages')

    # Blueprint pour les fonctionnalités IA (Groq)
    from .routes.ai_routes import ai_bp
    app.register_blueprint(ai_bp, url_prefix='/api/ai')

    # Exemple: Blueprint pour les utilisateurs (si gestion CRUD séparée de l'auth)
    # from .routes.user_routes import user_bp
    # app.register_blueprint(user_bp, url_prefix='/api/users')

    # ... autres blueprints pour les cours, notes, etc.

    @app.route('/test')
    def test_route():
        return "Flask App is running!"

    return app
