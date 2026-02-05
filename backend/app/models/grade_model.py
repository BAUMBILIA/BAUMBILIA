# backend/app/models/grade_model.py

"""
Modèle de Données pour Note (Grade)

Ce modèle représente une note individuelle obtenue par un étudiant dans un cours spécifique.
Il est recommandé d'utiliser une collection séparée 'grades' pour stocker ces informations.
"""

# Exemple de structure d'un document Note dans la collection 'grades':
GRADE_SCHEMA = {
    "_id": "ObjectId (généré automatiquement par MongoDB)",
    "etudiant_id": "ObjectId (requis, référence à l'_id de l'utilisateur étudiant)",
    "cours_id": "ObjectId (requis, référence à l'_id du cours)",
    "professeur_id_enregistrement": "ObjectId (requis, référence à l'_id du professeur qui a enregistré/modifié la note)",
    "note_valeur": "any (requis, peut être float, integer, string comme 'A+', 'Validé', 'Non Acquis')",
    "bareme_max": "float (optionnel, ex: 20, 100, si la note est numérique)",
    "coefficient": "float (optionnel, default: 1, coefficient du cours/examen dans la moyenne)",
    "type_evaluation": "string (optionnel, ex: 'Examen Final', 'Contrôle Continu', 'Projet', 'Partiel')",
    "date_evaluation": "date (optionnel, date à laquelle l'évaluation a eu lieu)",
    "date_enregistrement": "datetime (requis, quand la note a été entrée dans le système)",
    "annee_academique": "string (requis, ex: '2023-2024')",
    "semestre": "string (requis, ex: 'S1', 'S2')",
    "commentaires_professeur": "string (optionnel)",
    "visible_etudiant": "boolean (default: False, peut être mis à True une fois les notes finalisées/publiées)",
    "historique_modifications": [ # Optionnel, pour tracer les changements
        {
            "modifie_par_id": "ObjectId",
            "date_modification": "datetime",
            "ancienne_valeur": "any",
            "nouvelle_valeur": "any",
            "raison": "string (optionnel)"
        }
    ]
}

# Notes:
# - `etudiant_id` et `cours_id` formeront souvent un index composite pour des recherches rapides.
# - `note_valeur` est de type `any` pour permettre différents systèmes de notation. Il faudra une logique applicative pour l'interpréter.
# - `visible_etudiant` est un champ utile pour contrôler quand les étudiants peuvent voir leurs notes.
# - L'historique des modifications est une bonne pratique pour la traçabilité, surtout pour les notes.

# Fonctions d'interaction possibles avec PyMongo:
# def record_grade(db, grade_data):
#     pass
# def update_grade(db, grade_id, new_grade_data, professor_id): # professor_id pour l'historique
#     pass
# def get_grades_for_student(db, student_id, course_id=None, semester=None, academic_year=None):
#     pass
# def get_grades_for_course(db, course_id, student_id=None, semester=None, academic_year=None):
#     pass

print("Modèle Note (Grade) défini (schéma conceptuel pour collection séparée).")
