# backend/app/models/student_model.py

"""
Modèle de Données pour Étudiant (Student)

Ces champs sont spécifiques aux utilisateurs ayant le rôle 'etudiant'.
Ils peuvent être stockés directement dans le document de la collection 'users'
si `role == 'etudiant'`, ou dans une collection séparée `student_profiles` liée par `user_id`.
La première approche est plus simple pour les requêtes directes sur l'utilisateur.
La seconde est plus normalisée si les profils étudiants deviennent très complexes.

Pour l'instant, nous considérons ces champs comme faisant partie du document User
quand le rôle est 'etudiant'.
"""

# Champs spécifiques à l'Étudiant (à ajouter au USER_SCHEMA si role == 'etudiant'):
STUDENT_SPECIFIC_SCHEMA = {
    # user_id: "ObjectId (si collection séparée, référence à l'_id de la collection 'users')"
    "matricule": "string (requis, unique, ex: 'E2024001')",
    "filiere_id": "ObjectId (requis, référence à l'_id de la collection 'programs')",
    "niveau": "string (requis, ex: 'L1', 'L2', 'L3', 'M1', 'M2', 'Doctorant')",
    "annee_academique_inscription": "string (ex: '2023-2024')",
    "semestre_actuel": "string (ex: 'S1', 'S2', ...)", # Peut être calculé ou défini
    "groupe_td": "string (optionnel, ex: 'G1', 'A2')",
    "date_naissance": "date (optionnel)",
    "adresse": { # Optionnel
        "rue": "string",
        "ville": "string",
        "code_postal": "string",
        "pays": "string"
    },
    "numero_telephone": "string (optionnel)",
    "notes_references": [ # Alternative pour stocker les notes, si elles sont dans une collection séparée
        # "ObjectId (référence à l' _id dans la collection 'grades')"
    ],
    "cours_inscrits": [ # Liste des cours auxquels l'étudiant est actuellement inscrit
        {
            "cours_id": "ObjectId (référence à l'_id de la collection 'courses')",
            "annee_academique": "string",
            "semestre": "string",
            "statut_inscription": "string (ex: 'inscrit', 'validé', 'échoué', 'en_cours')"
        }
    ],
    # Plus de champs peuvent être ajoutés: photo_profil_url, etc.
}

# Le modèle de Note (Grade) sera défini séparément, mais est étroitement lié.
# Un étudiant aura typiquement un ensemble de notes. Celles-ci pourraient être:
# 1. Embarquées dans le document étudiant (si pas trop nombreuses et pour faciliter la lecture du relevé).
# 2. Stockées dans une collection 'grades' séparée et référencées. (Plus scalable)

# Pour ce projet, avec la nécessité de "relevé de note bien structuré",
# il est probable qu'une collection 'grades' séparée soit meilleure,
# et que le document étudiant contienne des informations sommaires ou des références.
# Cependant, le plan initial suggérait:
# `notes` (liste d'objets : `{cours_id, note, semestre, annee_academique}`) dans Etudiant.
# Je vais suivre cela pour l'instant, mais avec une note sur la scalabilité.

STUDENT_EMBEDDED_GRADES_SCHEMA_EXAMPLE = {
    # ... autres champs de STUDENT_SPECIFIC_SCHEMA ...
    "notes_enregistrees": [
        {
            "grade_id": "ObjectId (unique pour cette note, pourrait être généré)",
            "cours_id": "ObjectId (référence à l'_id de la collection 'courses')",
            "titre_cours": "string (dénormalisé pour affichage rapide)", # Dénormalisation
            "code_cours": "string (dénormalisé)", # Dénormalisation
            "note_valeur": "float | string (ex: 15.5, 'A', 'Validé')", # Flexible selon le système
            "coefficient": "integer (optionnel, si applicable)",
            "semestre": "string (ex: 'S1', 'S2')",
            "annee_academique": "string (ex: '2023-2024')",
            "date_enregistrement": "datetime",
            "enregistre_par_professeur_id": "ObjectId (référence à l'utilisateur professeur)",
            "commentaires": "string (optionnel)"
        }
    ]
}
# Note sur `notes_enregistrees`:
# - Avantage: Facile de récupérer toutes les notes d'un étudiant en une seule requête.
# - Inconvénient: Peut rendre le document étudiant très volumineux si beaucoup de notes.
#   MongoDB a une limite de taille de document (16MB).
#   Les mises à jour fréquentes de ce tableau peuvent être moins performantes.
# Une collection `grades` séparée est généralement recommandée pour la scalabilité.
# `grades` collection: { _id, etudiant_id, cours_id, note_valeur, ... }

print("Modèle Étudiant (Student) défini (schéma conceptuel et options pour les notes).")
