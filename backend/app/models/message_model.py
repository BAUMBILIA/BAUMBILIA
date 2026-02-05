# backend/app/models/message_model.py

"""
Modèle de Données pour Message (Messagerie Interne)

Ce modèle représente un message échangé entre utilisateurs du système.
"""

# Exemple de structure d'un document Message dans la collection 'messages':
MESSAGE_SCHEMA = {
    "_id": "ObjectId (généré automatiquement par MongoDB)",
    "expediteur_id": "ObjectId (requis, référence à l'_id de l'utilisateur expéditeur)",
    "destinataire_ids": ["ObjectId"], # Liste des _id des utilisateurs destinataires (peut être un ou plusieurs)
    # Ou, pour des groupes/cours:
    # "groupe_destinataire_id": "ObjectId (référence à un groupe, un cours, etc.)",
    # "type_destinataire": "string (ex: 'utilisateur', 'groupe_cours', 'groupe_filiere')",

    "sujet": "string (requis)",
    "corps_message": "string (requis, contenu du message, peut être HTML simple)",
    "date_envoi": "datetime (requis, généré automatiquement)",
    "conversation_id": "ObjectId (optionnel, pour regrouper les messages d'une même conversation/thread)",

    "statut_lecture": [ # Pour suivre qui a lu le message, surtout si plusieurs destinataires
        {
            "utilisateur_id": "ObjectId",
            "date_lecture": "datetime (null si non lu)",
            "lu": "boolean (default: False)"
        }
    ],
    "pieces_jointes": [ # Optionnel
        {
            "nom_fichier": "string",
            "url_stockage": "string",
            "type_fichier": "string",
            "taille_fichier": "integer (en bytes)"
        }
    ],
    "priorite": "string (optionnel, ex: 'normal', 'urgent')",
    "tags": ["string"], # Optionnel, pour catégorisation
    "archive_par": ["ObjectId"], # Liste des utilisateurs ayant archivé ce message
    "supprime_par": [ # Logique de suppression douce
        {
            "utilisateur_id": "ObjectId",
            "date_suppression": "datetime"
            # Un message n'est vraiment supprimé que si tous les participants l'ont "supprimé"
            # ou après une certaine période, ou par un admin.
        }
    ]
}

# Notes:
# - `destinataire_ids`: Permet d'envoyer un message à plusieurs personnes.
# - `statut_lecture`: Important pour une messagerie. Chaque destinataire a son propre statut de lecture.
# - `conversation_id`: Utile pour lier les réponses aux messages originaux.
# - La gestion de la "boîte de réception" de chaque utilisateur sera une requête basée sur `destinataire_ids` et `statut_lecture`.

# Fonctions d'interaction possibles avec PyMongo:
# def send_message(db, message_data):
#     pass
# def get_received_messages(db, user_id, unread_only=False):
#     pass
# def get_sent_messages(db, user_id):
#     pass
# def mark_message_as_read(db, message_id, user_id):
#     pass

print("Modèle Message (Messagerie) défini (schéma conceptuel).")
