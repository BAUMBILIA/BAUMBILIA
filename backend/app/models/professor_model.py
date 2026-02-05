# backend/app/models/professor_model.py

"""
Modèle de Données pour Professeur (Professor)

Ces champs sont spécifiques aux utilisateurs ayant le rôle 'professeur'.
Ils peuvent être stockés directement dans le document de la collection 'users'
si `role == 'professeur'`, ou dans une collection séparée `professor_profiles` liée par `user_id`.
Similairement au modèle Étudiant, nous considérons pour l'instant ces champs
comme faisant partie du document User.
"""

# Champs spécifiques au Professeur (à ajouter au USER_SCHEMA si role == 'professeur'):
PROFESSOR_SPECIFIC_SCHEMA = {
    # user_id: "ObjectId (si collection séparée, référence à l'_id de la collection 'users')"
    "matricule_professeur": "string (optionnel, unique, ex: 'P2024001')",
    "departement_ids": ["ObjectId"], # Références aux _id des départements/filières auxquels le professeur est rattaché
    "titre_academique": "string (optionnel, ex: 'Dr.', 'Pr.', 'Chargé de cours')",
    "specialisations": ["string"], # Liste des domaines de spécialisation
    "bureau": "string (optionnel, ex: 'Bâtiment A, Bureau 101')",
    "numero_telephone_professionnel": "string (optionnel)",
    "heures_permanence": "string (optionnel, ex: 'Lundi 10h-12h, Mercredi 14h-16h')",
    "cours_enseignes_ids": [
        "ObjectId" # Références aux _id des cours que le professeur enseigne actuellement ou a enseignés
    ],
    "publications": [ # Optionnel
        {
            "titre_publication": "string",
            "annee": "integer",
            "lien": "string (URL)"
        }
    ],
    "biographie_courte": "string (optionnel)"
    # Plus de champs peuvent être ajoutés: photo_profil_url, lien vers CV, etc.
}

# Notes:
# - `departement_ids`: Un professeur peut être rattaché à plusieurs départements ou filières.
# - `cours_enseignes_ids`: Liste des cours dont le professeur est responsable ou co-enseignant.
#   Ceci peut aussi être dérivé en cherchant dans la collection 'courses' les cours où `professeur_id`
#   correspond à l'_id de ce professeur. La redondance ici peut accélérer certaines requêtes.

# Fonctions d'interaction spécifiques (en plus de celles du User générique):
# def assign_course_to_professor(db, professor_id, course_id):
#     pass
# def get_courses_taught_by_professor(db, professor_id):
#     pass

print("Modèle Professeur (Professor) défini (schéma conceptuel).")
