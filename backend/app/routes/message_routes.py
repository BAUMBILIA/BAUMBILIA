# backend/app/routes/message_routes.py
from flask import request, jsonify, Blueprint
from backend.app import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId, errors as BsonErrors
import datetime

message_bp = Blueprint('message_bp', __name__)

# Pas besoin de décorateur de rôle spécifique ici, car étudiants, professeurs et admins peuvent tous envoyer/recevoir des messages.
# @jwt_required suffira, et l'identité de l'expéditeur sera tirée du token.

@message_bp.route('/send', methods=['POST'])
@jwt_required()
def send_message():
    """ Envoie un message à un ou plusieurs destinataires. """
    current_user_identity = get_jwt_identity()
    expediteur_id_str = current_user_identity.get('user_id')

    data = request.get_json()
    if not data: return jsonify({"message": "Aucune donnée fournie"}), 400

    destinataire_ids_str = data.get('destinataire_ids') # Liste d'IDs de destinataires
    sujet = data.get('sujet')
    corps_message = data.get('corps_message')

    if not destinataire_ids_str or not isinstance(destinataire_ids_str, list) or not destinataire_ids_str:
        return jsonify({"message": "La liste 'destinataire_ids' est requise et ne doit pas être vide."}), 400
    if not sujet or not corps_message:
        return jsonify({"message": "Le sujet et le corps du message sont requis."}), 400

    try:
        expediteur_obj_id = ObjectId(expediteur_id_str)
        destinataire_obj_ids = []
        for dest_id_str in destinataire_ids_str:
            try:
                dest_obj_id = ObjectId(dest_id_str)
                # Vérifier si le destinataire existe (optionnel mais bonne pratique)
                if not mongo.db.users.find_one({"_id": dest_obj_id}):
                    return jsonify({"message": f"Destinataire avec ID {dest_id_str} non trouvé."}), 404
                destinataire_obj_ids.append(dest_obj_id)
            except BsonErrors.InvalidId:
                return jsonify({"message": f"ID de destinataire invalide: {dest_id_str}"}), 400

        if expediteur_obj_id in destinataire_obj_ids: # Empêcher l'auto-envoi si ce n'est pas souhaité
            # Ou le permettre, selon la logique métier. Pour l'instant, on le permet.
            pass

        new_message = {
            "expediteur_id": expediteur_obj_id,
            "destinataire_ids": destinataire_obj_ids,
            "sujet": sujet,
            "corps_message": corps_message,
            "date_envoi": datetime.datetime.utcnow(),
            "statut_lecture": [{"utilisateur_id": dest_id, "lu": False, "date_lecture": None} for dest_id in destinataire_obj_ids],
            "pieces_jointes": data.get('pieces_jointes', []), # Structure à valider si utilisée
            "conversation_id": ObjectId(data['conversation_id']) if data.get('conversation_id') else ObjectId() # Nouvelle conversation ou existante
        }

        # Valider la structure des pièces jointes si présentes
        for pj in new_message["pieces_jointes"]:
            if not all(k in pj for k in ("nom_fichier", "url_stockage", "type_fichier")):
                return jsonify({"message": "Chaque pièce jointe doit avoir nom_fichier, url_stockage, et type_fichier."}), 400

        result = mongo.db.messages.insert_one(new_message)

        # TODO: Potentiellement envoyer des notifications (email, push) aux destinataires

        return jsonify({"message": "Message envoyé avec succès", "message_id": str(result.inserted_id)}), 201

    except BsonErrors.InvalidId: # Pour l'expediteur_id si problème avec le token, ou conversation_id
        return jsonify({"message": "ID expéditeur ou conversation invalide."}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de l'envoi du message.", "error": str(e)}), 500


@message_bp.route('/inbox', methods=['GET'])
@jwt_required()
def get_inbox_messages():
    """ Récupère les messages reçus par l'utilisateur connecté (boîte de réception). """
    current_user_identity = get_jwt_identity()
    user_obj_id = ObjectId(current_user_identity.get('user_id'))

    # Pagination (optionnelle, mais bonne pratique pour de nombreuses données)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    skip = (page - 1) * per_page

    # Messages où l'utilisateur est dans destinataire_ids et qui ne sont pas "supprimés" par lui
    # (La suppression douce n'est pas encore implémentée dans le modèle `message_model.py` de manière détaillée)
    messages_cursor = mongo.db.messages.find({
        "destinataire_ids": user_obj_id
        # Ajouter ici une condition pour exclure les messages "supprimés" par l'utilisateur si implémenté
        # ex: "supprime_par": {"$not": {"$elemMatch": {"utilisateur_id": user_obj_id}}}
    }).sort("date_envoi", -1).skip(skip).limit(per_page) # Trier par date d'envoi décroissante

    inbox_messages = []
    for msg in messages_cursor:
        msg['_id'] = str(msg['_id'])
        msg['expediteur_id'] = str(msg['expediteur_id'])
        msg['destinataire_ids'] = [str(uid) for uid in msg.get('destinataire_ids', [])]
        if msg.get('conversation_id'): msg['conversation_id'] = str(msg['conversation_id'])

        # Enrichir avec les infos de l'expéditeur
        sender_info = mongo.db.users.find_one({"_id": ObjectId(msg['expediteur_id'])}, {"nom": 1, "prenom": 1, "email":1, "_id":0})
        msg['expediteur_details'] = sender_info if sender_info else {"nom": "Utilisateur inconnu"}

        # Statut de lecture spécifique à l'utilisateur courant
        user_read_status = next((s for s in msg.get('statut_lecture', []) if s.get('utilisateur_id') == user_obj_id), None)
        msg['mon_statut_lecture'] = user_read_status if user_read_status else {"lu": False, "date_lecture": None}
        # On peut retirer le tableau complet statut_lecture pour alléger si seul le statut de l'utilisateur courant intéresse ici.
        # msg.pop('statut_lecture', None)

        inbox_messages.append(msg)

    total_messages = mongo.db.messages.count_documents({"destinataire_ids": user_obj_id})

    return jsonify({
        "messages": inbox_messages,
        "page": page,
        "per_page": per_page,
        "total_messages": total_messages,
        "total_pages": (total_messages + per_page - 1) // per_page # Calcul du nombre total de pages
    }), 200


@message_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent_messages():
    """ Récupère les messages envoyés par l'utilisateur connecté. """
    current_user_identity = get_jwt_identity()
    user_obj_id = ObjectId(current_user_identity.get('user_id'))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    skip = (page - 1) * per_page

    messages_cursor = mongo.db.messages.find(
        {"expediteur_id": user_obj_id}
    ).sort("date_envoi", -1).skip(skip).limit(per_page)

    sent_messages = []
    for msg in messages_cursor:
        msg['_id'] = str(msg['_id'])
        msg['expediteur_id'] = str(msg['expediteur_id'])
        msg['destinataire_ids'] = [str(uid) for uid in msg.get('destinataire_ids', [])]
        if msg.get('conversation_id'): msg['conversation_id'] = str(msg['conversation_id'])
        # On pourrait vouloir enrichir avec les détails des destinataires ici
        sent_messages.append(msg)

    total_messages = mongo.db.messages.count_documents({"expediteur_id": user_obj_id})

    return jsonify({
        "messages": sent_messages,
        "page": page,
        "per_page": per_page,
        "total_messages": total_messages,
        "total_pages": (total_messages + per_page - 1) // per_page
    }), 200

@message_bp.route('/<string:message_id>/read', methods=['POST'])
@jwt_required()
def mark_message_as_read(message_id):
    """ Marque un message comme lu pour l'utilisateur connecté. """
    current_user_identity = get_jwt_identity()
    user_obj_id = ObjectId(current_user_identity.get('user_id'))

    try:
        message_obj_id = ObjectId(message_id)

        # Mettre à jour le statut de lecture pour cet utilisateur dans ce message
        result = mongo.db.messages.update_one(
            {
                "_id": message_obj_id,
                "destinataire_ids": user_obj_id, # S'assurer que l'utilisateur est bien un destinataire
                "statut_lecture.utilisateur_id": user_obj_id
            },
            {
                "$set": {
                    "statut_lecture.$.lu": True,
                    "statut_lecture.$.date_lecture": datetime.datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            # Peut-être que l'utilisateur n'est pas dans statut_lecture ou n'est pas destinataire
            # Vérifier si le message existe et si l'utilisateur est destinataire
            message = mongo.db.messages.find_one({"_id": message_obj_id, "destinataire_ids": user_obj_id})
            if not message:
                 return jsonify({"message": "Message non trouvé ou vous n'êtes pas destinataire."}), 404
            # Si l'utilisateur est destinataire mais pas dans statut_lecture (cas rare, mauvaise initialisation)
            # On pourrait l'ajouter, mais pour l'instant on retourne une erreur.
            return jsonify({"message": "Impossible de marquer comme lu. Statut de lecture non initialisé correctement ou déjà marqué."}), 400

        if result.modified_count > 0:
            return jsonify({"message": "Message marqué comme lu."}), 200
        else: # matched_count > 0 mais modified_count == 0 (déjà lu)
            return jsonify({"message": "Message déjà marqué comme lu ou aucune modification nécessaire."}), 200

    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de message invalide."}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors du marquage du message comme lu.", "error": str(e)}), 500

# TODO: Routes pour supprimer des messages (logique de suppression douce), archiver, etc.
# TODO: Route pour récupérer les messages d'une conversation_id spécifique.

print("Blueprint pour la messagerie (message_bp) créé.")
