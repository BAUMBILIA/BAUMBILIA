# backend/app/models/course_model.py

"""
Modèle de Données pour Cours (Course)

Ce modèle représente les cours offerts au sein des différentes filières.
"""

# Exemple de structure d'un document Cours:
COURSE_SCHEMA = {
    "_id": "ObjectId (généré automatiquement par MongoDB)",
    "titre": "string (requis, ex: 'Introduction à l'Algorithmique')",
    "code_cours": "string (requis, unique, ex: 'CS101')",
    "description": "string (optionnel)",
    "credits": "integer (requis, ex: 3)",
    "filiere_ids": ["ObjectId"], # Références aux _id des Filières auxquelles ce cours appartient ou est offert
    "niveau": "string (requis, ex: 'L1', 'M2', etc.)", # Niveau cible du cours
    "semestre": "string (requis, ex: 'S1', 'S2', ...)", # Semestre où le cours est typiquement offert
    "professeur_id": "ObjectId (référence à l'_id d'un utilisateur avec le rôle 'professeur', optionnel au début, peut être assigné plus tard)",
    "objectifs_apprentissage": ["string"], # Liste des objectifs
    "contenu_cours": [ # Liste des modules/sections du cours
        {
            "section_id": "ObjectId (unique pour cette section dans ce cours)",
            "titre_section": "string",
            "description_section": "string (optionnel)",
            "contenu_html": "string (pour le texte formaté, les leçons)",
            "fichiers_joints": [
                {
                    "nom_fichier": "string",
                    "url_stockage": "string", # ou chemin vers le fichier
                    "type_fichier": "string (ex: 'pdf', 'docx', 'video/mp4')",
                    "date_upload": "datetime"
                }
            ],
            "ordre": "integer (pour l'affichage séquentiel)"
        }
    ],
    "pre_requis": ["ObjectId"], # Références aux _id d'autres Cours (prérequis)
    "date_creation": "datetime",
    "date_modification": "datetime",
}

# Notes:
# - `filiere_ids`: Un cours peut être pertinent pour plusieurs filières.
# - `contenu_cours`: Structure flexible pour permettre aux professeurs d'ajouter divers types de matériel.
#   - `section_id` pourrait être généré par l'application lors de l'ajout d'une section.
#   - `fichiers_joints`: Nécessitera une gestion du stockage de fichiers (localement ou service cloud).
# - `professeur_id`: Le professeur principal responsable du cours. D'autres professeurs pourraient être co-enseignants (à modéliser si besoin).

# Fonctions d'interaction possibles avec PyMongo:
# def create_course(db, course_data):
#     pass
# def find_course_by_id(db, course_id):
#     pass
# def find_courses_by_program(db, program_id):
#     pass
# def assign_professor_to_course(db, course_id, professor_id):
#     pass
# def add_course_content_section(db, course_id, section_data):
#     pass

print("Modèle Cours (Course) défini (schéma conceptuel).")
