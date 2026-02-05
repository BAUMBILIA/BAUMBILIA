# backend/app/models/user_model.py

"""
Modèle de Données pour Utilisateur (User)

Ce modèle est la base pour tous les types d'utilisateurs (étudiants, professeurs, administrateurs).
Chaque document utilisateur dans la collection MongoDB 'users' devrait suivre cette structure.
"""

# Exemple de structure d'un document Utilisateur:
USER_SCHEMA = {
    "_id": "ObjectId (généré automatiquement par MongoDB)",
    "nom": "string (requis)",
    "prenom": "string (requis)",
    "email": "string (requis, unique, utilisé pour la connexion)",
    "mot_de_passe": "string (hashé, requis)",
    "role": "string (requis, valeurs possibles: 'etudiant', 'professeur', 'admin')",
    "date_creation": "datetime (généré automatiquement)",
    "derniere_connexion": "datetime (optionnel)",
    "actif": "boolean (default: True, pour désactiver un compte)",
    # D'autres champs communs peuvent être ajoutés ici
}

# Notes:
# - L'unicité de l'email devra être gérée au niveau de l'application et avec un index MongoDB.
# - Le mot de passe ne doit JAMAIS être stocké en clair. Utiliser bcrypt ou Argon2.
# - Le champ 'role' est crucial pour déterminer les permissions.

# Pour l'interaction avec PyMongo, on pourrait avoir des fonctions comme:
# def create_user(db, user_data):
#     """Crée un nouvel utilisateur."""
#     # ... logique pour insérer dans db.users ...
#     pass

# def find_user_by_email(db, email):
#     """Trouve un utilisateur par son email."""
#     # ... logique pour chercher dans db.users ...
#     pass

# def update_user(db, user_id, update_data):
#     """Met à jour un utilisateur."""
#     # ... logique pour mettre à jour dans db.users ...
#     pass

# etc.
print("Modèle User défini (schéma conceptuel).")
