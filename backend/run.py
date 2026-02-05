# backend/run.py
import os
from backend.app import create_app # Assure que create_app est correctement défini dans backend/app/__init__.py
from backend.config import AppConfig

# Crée l'application Flask en utilisant la factory et la configuration
app = create_app(AppConfig)

if __name__ == '__main__':
    # Gunicorn est recommandé pour la production, mais le serveur de développement Flask est ok pour le dev.
    # host='0.0.0.0' pour rendre le serveur accessible depuis l'extérieur du conteneur/VM (si applicable)
    # debug=True active le mode debug de Flask (ne pas utiliser en production avec cette configuration)

    # Récupérer le port depuis les variables d'environnement ou utiliser 5000 par défaut
    port = int(os.environ.get("PORT", 5000))

    # Le mode debug est déjà géré par AppConfig.DEBUG
    # app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
    app.run(host='0.0.0.0', port=port)

print(f"Application Flask démarrée. Accessible sur http://localhost:{AppConfig.get('PORT', 5000) if hasattr(AppConfig, 'get') else port}")
print(f"Mode Debug: {app.debug}")
print(f"Mongo URI: {app.config.get('MONGO_URI')}")
