# backend/config.py
import os
import datetime # Ajout de l'import datetime
from dotenv import load_dotenv

load_dotenv() # Charge les variables d'environnement depuis .env (si présent)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'une-cle-secrete-tres-difficile-a-deviner'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/gestion_universitaire'

    # Configuration JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY # Utilise SECRET_KEY si JWT_SECRET_KEY n'est pas défini
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1) # Durée de validité du token d'accès
    JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=30) # Durée de validité du token de rafraîchissement
    # JWT_TOKEN_LOCATION = ["headers", "cookies"] # Où chercher les tokens
    # JWT_COOKIE_SECURE = False # Mettre à True en production (HTTPS)
    # JWT_COOKIE_SAMESITE = "Lax"

    # Pour Groq
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

    # Configuration pour Flask-Mail (exemple avec SendGrid)
    # L'utilisateur devra configurer ces variables d'environnement.
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.sendgrid.net'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') # Pour SendGrid, c'est 'apikey' (littéralement)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') # Pour SendGrid, c'est la clé API SendGrid
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@votre-domaine.com'
    # MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() == 'true' # Pour les tests, pour ne pas envoyer de vrais emails

class DevelopmentConfig(Config):
    DEBUG = True
    # En développement, on pourrait vouloir supprimer l'envoi réel d'emails
    # MAIL_SUPPRESS_SEND = True

class ProductionConfig(Config):
    DEBUG = False
    # Ajoutez ici des configurations spécifiques à la production
    # Par exemple, des logging plus robustes, etc.

# Détermine la configuration à utiliser (par défaut Development)
AppConfig = DevelopmentConfig if os.environ.get('FLASK_ENV') == 'development' else ProductionConfig
