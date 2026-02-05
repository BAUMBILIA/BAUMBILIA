# backend/app/routes/auth_routes.py
from flask import request, jsonify, Blueprint
from backend.app import mongo, bcrypt # mongo et bcrypt initialisés dans __init__.py
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import datetime
from bson import ObjectId # Pour gérer les ObjectId de MongoDB

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Route pour l'inscription d'un nouvel utilisateur.
    Pour l'instant, cette route est ouverte, mais devrait être protégée
    ou utilisée avec prudence (ex: création du premier admin).
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": "Aucune donnée fournie"}), 400

    email = data.get('email')
    password = data.get('password')
    nom = data.get('nom')
    prenom = data.get('prenom')
    role = data.get('role', 'etudiant') # Rôle par défaut 'etudiant'

    if not email or not password or not nom or not prenom:
        return jsonify({"message": "Champs email, mot_de_passe, nom et prénom requis"}), 400

    # Vérifier si l'utilisateur existe déjà
    existing_user = mongo.db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"message": "Cet email est déjà utilisé"}), 409 # Conflict

    # Hasher le mot de passe
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Créer le nouvel utilisateur
    # Note: USER_SCHEMA défini dans user_model.py est un guide.
    # Ici, nous construisons le document à insérer.
    new_user = {
        "nom": nom,
        "prenom": prenom,
        "email": email,
        "mot_de_passe": hashed_password,
        "role": role, # 'etudiant', 'professeur', 'admin'
        "date_creation": datetime.datetime.utcnow(),
        "actif": True
        # Ajouter d'autres champs spécifiques au rôle si nécessaire lors de l'inscription
    }

    # Si le rôle est étudiant, on pourrait vouloir initialiser des champs spécifiques
    if role == 'etudiant':
        new_user["matricule"] = data.get('matricule') # Idéalement généré ou validé
        new_user["filiere_id"] = data.get('filiere_id') # Doit être un ObjectId valide si fourni
        new_user["niveau"] = data.get('niveau')
        # Initialiser notes_enregistrees comme une liste vide
        new_user["notes_enregistrees"] = []
        new_user["cours_inscrits"] = []


    # Si le rôle est professeur
    elif role == 'professeur':
        new_user["matricule_professeur"] = data.get('matricule_professeur')
        new_user["departement_ids"] = [] # Initialiser comme vide
        new_user["cours_enseignes_ids"] = []


    try:
        result = mongo.db.users.insert_one(new_user)
        user_id = result.inserted_id

        # Envoyer un email de bienvenue
        from backend.app.services.email_service import EmailService
        # Utiliser le prénom et le nom pour le nom d'utilisateur dans l'email
        user_full_name = f"{new_user.get('prenom', '')} {new_user.get('nom', '')}".strip()
        if user_full_name: # S'assurer qu'on a un nom à utiliser
             EmailService.send_registration_email(new_user['email'], user_full_name)
        else: # Fallback si nom/prénom non disponibles pour une raison quelconque
             EmailService.send_registration_email(new_user['email'], new_user['email'])


        return jsonify({
            "message": "Utilisateur créé avec succès. Un email de bienvenue a été envoyé.",
            "user_id": str(user_id),
            "email": email,
            "role": role
        }), 201
    except Exception as e:
        # Log l'erreur côté serveur pour le débogage
        # current_app.logger.error(f"Erreur lors de la création de l'utilisateur {email}: {e}")
        return jsonify({"message": "Erreur lors de la création de l'utilisateur", "error": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Aucune donnée fournie"}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email et mot de passe requis"}), 400

    user = mongo.db.users.find_one({"email": email})

    if user and bcrypt.check_password_hash(user['mot_de_passe'], password):
        if not user.get('actif', True): # Vérifier si le compte est actif
            return jsonify({"message": "Ce compte a été désactivé."}), 403

        # L'identité peut être l'ID de l'utilisateur (converti en str) et son rôle
        identity = {
            "user_id": str(user['_id']),
            "role": user['role'],
            "nom": user['nom'],
            "prenom": user['prenom']
        }
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity) # Optionnel, pour le rafraîchissement du token

        # Mettre à jour la date de dernière connexion
        mongo.db.users.update_one(
            {"_id": user['_id']},
            {"$set": {"derniere_connexion": datetime.datetime.utcnow()}}
        )

        return jsonify({
            "message": "Connexion réussie",
            "access_token": access_token,
            "refresh_token": refresh_token, # Optionnel
            "user": {
                "user_id": str(user['_id']),
                "email": user['email'],
                "nom": user['nom'],
                "prenom": user['prenom'],
                "role": user['role']
            }
        }), 200
    else:
        return jsonify({"message": "Email ou mot de passe incorrect"}), 401


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # Nécessite un refresh token valide
def refresh():
    current_user_identity = get_jwt_identity() # Récupère l'identité du refresh token
    # current_user_identity sera le dict {"user_id": "...", "role": "..."}

    new_access_token = create_access_token(identity=current_user_identity)
    return jsonify(access_token=new_access_token), 200

# Route protégée simple pour tester le token JWT
@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity() # Renvoie l'identité stockée dans le token
    # current_user est le dict: {"user_id": "...", "role": "..."}
    user_id = current_user["user_id"]
    # On peut récupérer plus d'infos sur l'utilisateur depuis la DB si besoin
    user_info = mongo.db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 0, "mot_de_passe": 0})

    return jsonify(logged_in_as=current_user, user_details=user_info), 200

# Plus tard, ajouter une route /logout si on utilise des blocklists pour les tokens JWT.
# Pour l'instant, le logout côté client consiste à supprimer le token.
# Pour un vrai logout côté serveur avec JWT, il faut une "token blocklist".
# JWTManager peut être configuré pour cela.

# Exemple de callback pour vérifier si un token est dans la blocklist
# from backend.app import jwt # Assurez-vous que jwt est accessible
# @jwt.token_in_blocklist_loader
# def check_if_token_in_blocklist(jwt_header, jwt_payload):
#     jti = jwt_payload["jti"]
#     # Vous devez stocker les jti des tokens bloqués (ex: dans Redis ou MongoDB)
#     # token_is_revoked = your_blocklist_checking_logic(jti)
#     # return token_is_revoked
#     return False # Pour l'instant, aucun token n'est bloqué

print("Blueprint d'authentification (auth_bp) créé avec /register et /login.")
