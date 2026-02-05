# backend/app/models/program_model.py

"""
Modèle de Données pour Filière (Program/Major)

Ce modèle représente les différentes filières proposées par l'université.
Exemples: Intelligence Artificielle, Business, Marketing Digital, Finance, Management.
"""

# Exemple de structure d'un document Filiere:
PROGRAM_SCHEMA = {
    "_id": "ObjectId (généré automatiquement par MongoDB)",
    "nom": "string (requis, unique, ex: 'Intelligence Artificielle')",
    "code_filiere": "string (optionnel, unique, ex: 'IA-L1')", # Peut être utile pour une identification rapide
    "description": "string (optionnel)",
    "departement": "string (optionnel, ex: 'Sciences et Technologies', 'Économie et Gestion')",
    "niveaux_offerts": ["string"], # ex: ["L1", "L2", "L3", "M1", "M2", "Doctorat"]
    "responsable_filiere_id": "ObjectId (référence à un utilisateur avec le rôle 'professeur', optionnel)",
    "date_creation": "datetime (généré automatiquement)",
    "date_modification": "datetime (généré automatiquement lors de la mise à jour)",
}

# Notes:
# - L'unicité du nom de la filière (et potentiellement du code) devrait être assurée.
# - `responsable_filiere_id` lie un professeur comme responsable de la filière.

# Fonctions d'interaction possibles avec PyMongo:
# def create_program(db, program_data):
#     pass
# def find_program_by_id(db, program_id):
#     pass
# def get_all_programs(db):
#     pass
# def update_program(db, program_id, update_data):
#     pass
# def delete_program(db, program_id):
#     pass

print("Modèle Filiere (Program) défini (schéma conceptuel).")
