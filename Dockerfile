# Utiliser une image Python officielle comme image de base
FROM python:3.9-slim-buster

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt en premier pour profiter du cache Docker
COPY backend/requirements.txt /app/backend/requirements.txt

# Installer les dépendances
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copier tout le reste du code de l'application
# Si le frontend est servi par Flask (petites applis), copiez-le aussi.
# Sinon, le frontend sera géré séparément (ex: Nginx, CDN).
# Pour l'instant, on copie tout le backend.
COPY backend/ /app/backend/
# Si on voulait copier le frontend aussi (pour que Flask le serve via static_folder)
# COPY frontend/ /app/frontend/

# Variables d'environnement (peuvent être écrasées au runtime)
# FLASK_APP est défini par Gunicorn dans la commande CMD
# FLASK_ENV est utilisé par config.py pour choisir entre DevelopmentConfig et ProductionConfig
ENV FLASK_ENV=production
# Le port sur lequel Gunicorn écoutera à l'intérieur du conteneur
ENV PORT=5000
# S'assurer que Python sort tout directement au lieu de bufferiser (utile pour les logs Docker)
ENV PYTHONUNBUFFERED=1

# Exposer le port sur lequel l'application s'exécute à l'intérieur du conteneur
EXPOSE 5000

# Commande pour lancer l'application avec Gunicorn
# backend.run:app fait référence à l'objet 'app' dans le fichier 'backend/run.py'
# Le nombre de workers est généralement (2 * nombre_de_cpus) + 1.
# Pour la simplicité, on commence avec 3.
# bind 0.0.0.0:$PORT pour écouter sur toutes les interfaces sur le port défini par $PORT.
CMD ["gunicorn", "--workers=3", "--bind", "0.0.0.0:5000", "backend.run:app"]

# Note: Si le frontend doit être servi par Nginx dans un autre conteneur,
# ce Dockerfile ne concernerait que le backend.
# Le fichier run.py devrait être ajusté pour ne pas essayer de servir le frontend
# si ce n'est pas son rôle en production.
# Pour l'instant, notre run.py ne sert pas activement le frontend, il lance juste l'API Flask.
# Les fichiers HTML du frontend sont destinés à être ouverts directement ou servis par un serveur statique.
