# backend/app/routes/admin_routes.py
from flask import request, jsonify, Blueprint
from backend.app import mongo, bcrypt
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId, errors as BsonErrors
import datetime

admin_bp = Blueprint('admin_bp', __name__)

# Décorateur personnalisé pour vérifier le rôle 'admin'
def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        if current_user.get('role') != 'admin':
            return jsonify({"message": "Accès réservé aux administrateurs"}), 403
        return fn(current_user['user_id'], *args, **kwargs) # Passe l'ID de l'admin
    wrapper.__name__ = fn.__name__ + "_wrapper_admin"
    return wrapper

# --- Gestion des Utilisateurs ---

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user(current_admin_id):
    """ Crée un nouvel utilisateur (étudiant, professeur, ou même admin). """
    data = request.get_json()
    if not data: return jsonify({"message": "Aucune donnée fournie"}), 400

    required_fields = ['email', 'password', 'nom', 'prenom', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({"message": f"Champs requis: {', '.join(required_fields)}"}), 400

    if data['role'] not in ['etudiant', 'professeur', 'admin']:
        return jsonify({"message": "Rôle invalide. Doit être 'etudiant', 'professeur', ou 'admin'."}), 400

    if mongo.db.users.find_one({"email": data['email']}):
        return jsonify({"message": "Cet email est déjà utilisé"}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = {
        "nom": data['nom'], "prenom": data['prenom'], "email": data['email'],
        "mot_de_passe": hashed_password, "role": data['role'],
        "date_creation": datetime.datetime.utcnow(), "actif": data.get('actif', True),
        "cree_par_admin_id": ObjectId(current_admin_id)
    }

    # Champs spécifiques au rôle
    if data['role'] == 'etudiant':
        if not data.get('matricule'): return jsonify({"message": "Matricule requis pour un étudiant"}), 400
        # Idéalement, vérifier l'unicité du matricule
        if mongo.db.users.find_one({"role": "etudiant", "matricule": data['matricule']}):
            return jsonify({"message": "Ce matricule étudiant est déjà utilisé"}), 409
        new_user.update({
            "matricule": data['matricule'],
            "filiere_id": ObjectId(data['filiere_id']) if data.get('filiere_id') else None,
            "niveau": data.get('niveau'),
            "notes_enregistrees": [], "cours_inscrits": []
        })
    elif data['role'] == 'professeur':
        # Matricule professeur optionnel ou peut être généré
        if data.get('matricule_professeur') and mongo.db.users.find_one({"role": "professeur", "matricule_professeur": data['matricule_professeur']}):
             return jsonify({"message": "Ce matricule professeur est déjà utilisé"}), 409
        new_user.update({
            "matricule_professeur": data.get('matricule_professeur'),
            "departement_ids": [ObjectId(dep_id) for dep_id in data.get('departement_ids', []) if dep_id],
            "cours_enseignes_ids": []
        })

    try:
        result = mongo.db.users.insert_one(new_user)
        return jsonify({
            "message": "Utilisateur créé avec succès",
            "user_id": str(result.inserted_id),
            "email": new_user["email"]
        }), 201
    except BsonErrors.InvalidId:
         return jsonify({"message": "ID de filière ou de département invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de la création de l'utilisateur", "error": str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users(current_admin_id):
    """ Récupère la liste de tous les utilisateurs avec filtres optionnels. """
    query_params = request.args
    filter_query = {}
    if query_params.get('role'):
        filter_query['role'] = query_params.get('role')
    if query_params.get('actif'):
        filter_query['actif'] = query_params.get('actif').lower() == 'true'

    # Projection pour exclure le mot de passe
    projection = {"mot_de_passe": 0}
    users_cursor = mongo.db.users.find(filter_query, projection)
    users_list = [{**u, '_id': str(u['_id'])} for u in users_cursor] # Convertir ObjectId
    return jsonify(users_list), 200


@admin_bp.route('/users/<string:user_id>', methods=['GET'])
@admin_required
def get_user_by_id(current_admin_id, user_id):
    """ Récupère un utilisateur spécifique par son ID. """
    try:
        user_obj_id = ObjectId(user_id)
        user = mongo.db.users.find_one({"_id": user_obj_id}, {"mot_de_passe": 0})
        if user:
            user['_id'] = str(user['_id'])
            # Convertir d'autres ObjectId si présents (filiere_id, departement_ids, etc.)
            if 'filiere_id' in user and user['filiere_id']: user['filiere_id'] = str(user['filiere_id'])
            if 'departement_ids' in user: user['departement_ids'] = [str(oid) for oid in user['departement_ids']]

            return jsonify(user), 200
        return jsonify({"message": "Utilisateur non trouvé"}), 404
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID utilisateur invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


@admin_bp.route('/users/<string:user_id>', methods=['PUT'])
@admin_required
def update_user(current_admin_id, user_id):
    """ Met à jour les informations d'un utilisateur. """
    data = request.get_json()
    if not data: return jsonify({"message": "Aucune donnée fournie"}), 400

    try:
        user_obj_id = ObjectId(user_id)
        update_fields = {}
        # Champs modifiables : nom, prenom, role, actif, et champs spécifiques au rôle
        if 'nom' in data: update_fields['nom'] = data['nom']
        if 'prenom' in data: update_fields['prenom'] = data['prenom']
        if 'actif' in data: update_fields['actif'] = data['actif']

        # Attention avec la modification de l'email ou du rôle, cela peut avoir des implications.
        if 'email' in data:
            # Vérifier l'unicité si l'email est modifié
            if mongo.db.users.find_one({"email": data['email'], "_id": {"$ne": user_obj_id}}):
                return jsonify({"message": "Nouvel email déjà utilisé par un autre compte"}), 409
            update_fields['email'] = data['email']

        if 'role' in data:
            if data['role'] not in ['etudiant', 'professeur', 'admin']:
                return jsonify({"message": "Rôle invalide"}), 400
            update_fields['role'] = data['role']
            # Ici, on pourrait vouloir nettoyer/ajouter des champs spécifiques au nouveau rôle

        # Champs spécifiques aux rôles
        user_current_role = mongo.db.users.find_one({"_id": user_obj_id}, {"role": 1})
        current_role = user_current_role.get('role') if user_current_role else None
        target_role = data.get('role', current_role) # Si le rôle est modifié, utiliser le nouveau

        if target_role == 'etudiant':
            if 'matricule' in data: update_fields['matricule'] = data['matricule']
            if 'filiere_id' in data: update_fields['filiere_id'] = ObjectId(data['filiere_id']) if data.get('filiere_id') else None
            if 'niveau' in data: update_fields['niveau'] = data['niveau']
        elif target_role == 'professeur':
            if 'matricule_professeur' in data: update_fields['matricule_professeur'] = data['matricule_professeur']
            if 'departement_ids' in data:
                update_fields['departement_ids'] = [ObjectId(dep_id) for dep_id in data.get('departement_ids', []) if dep_id]

        if 'password' in data and data['password']: # Si un nouveau mot de passe est fourni
            update_fields['mot_de_passe'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        if not update_fields: return jsonify({"message": "Aucun champ à mettre à jour"}), 400

        update_fields['date_modification'] = datetime.datetime.utcnow()
        update_fields['modifie_par_admin_id'] = ObjectId(current_admin_id)

        result = mongo.db.users.update_one({"_id": user_obj_id}, {"$set": update_fields})
        if result.matched_count == 0: return jsonify({"message": "Utilisateur non trouvé"}), 404
        return jsonify({"message": "Utilisateur mis à jour avec succès"}), 200

    except BsonErrors.InvalidId:
        return jsonify({"message": "ID utilisateur, filière ou département invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


@admin_bp.route('/users/<string:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_admin_id, user_id):
    """ Supprime un utilisateur (ou le désactive). Une suppression douce est préférable. """
    # Pour une suppression douce, on mettrait 'actif' à False.
    # Pour une vraie suppression : mongo.db.users.delete_one({"_id": user_obj_id})
    try:
        user_obj_id = ObjectId(user_id)
        # Empêcher un admin de se supprimer lui-même via cette route simple
        if str(user_obj_id) == current_admin_id:
            return jsonify({"message": "Un administrateur ne peut pas se supprimer lui-même via cette API."}), 403

        # Option 1: Désactivation (Suppression douce)
        result = mongo.db.users.update_one(
            {"_id": user_obj_id},
            {"$set": {"actif": False, "date_modification": datetime.datetime.utcnow(), "modifie_par_admin_id": ObjectId(current_admin_id)}}
        )
        if result.matched_count == 0: return jsonify({"message": "Utilisateur non trouvé"}), 404
        # mongo.db.tokens_blocklist.delete_many({"user_id": user_id}) # Si on a une blocklist de tokens
        return jsonify({"message": "Utilisateur désactivé avec succès (suppression douce)"}), 200

        # Option 2: Suppression réelle (Attention: peut casser des références si pas géré)
        # result = mongo.db.users.delete_one({"_id": user_obj_id})
        # if result.deleted_count == 0: return jsonify({"message": "Utilisateur non trouvé"}), 404
        # return jsonify({"message": "Utilisateur supprimé définitivement"}), 200

    except BsonErrors.InvalidId:
        return jsonify({"message": "ID utilisateur invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


# --- Gestion des Filières (Programs) ---

@admin_bp.route('/programs', methods=['POST'])
@admin_required
def create_program(current_admin_id):
    """ Crée une nouvelle filière. """
    data = request.get_json()
    if not data or not data.get('nom'):
        return jsonify({"message": "Le nom de la filière est requis"}), 400

    # Vérifier l'unicité du nom de la filière
    if mongo.db.programs.find_one({"nom": data['nom']}):
        return jsonify({"message": "Une filière avec ce nom existe déjà"}), 409

    # Vérifier l'unicité du code_filiere si fourni
    if data.get('code_filiere') and mongo.db.programs.find_one({"code_filiere": data['code_filiere']}):
        return jsonify({"message": "Une filière avec ce code existe déjà"}), 409

    new_program = {
        "nom": data['nom'],
        "code_filiere": data.get('code_filiere'),
        "description": data.get('description', ""),
        "departement": data.get('departement', ""),
        "niveaux_offerts": data.get('niveaux_offerts', []), # ex: ["L1", "L2", "M1"]
        "date_creation": datetime.datetime.utcnow(),
        "date_modification": datetime.datetime.utcnow(),
        "cree_par_admin_id": ObjectId(current_admin_id)
    }
    if data.get('responsable_filiere_id'):
        try:
            # Vérifier que le responsable est un professeur
            prof = mongo.db.users.find_one({"_id": ObjectId(data['responsable_filiere_id']), "role": "professeur"})
            if not prof:
                return jsonify({"message": "ID du responsable de filière invalide ou l'utilisateur n'est pas un professeur."}), 400
            new_program['responsable_filiere_id'] = ObjectId(data['responsable_filiere_id'])
        except BsonErrors.InvalidId:
            return jsonify({"message": "ID du responsable de filière invalide"}), 400

    try:
        result = mongo.db.programs.insert_one(new_program)
        return jsonify({"message": "Filière créée avec succès", "program_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"message": "Erreur lors de la création de la filière", "error": str(e)}), 500


@admin_bp.route('/programs', methods=['GET'])
@admin_required # Ouvert à d'autres rôles authentifiés si besoin, ajuster le décorateur
def get_all_programs(current_admin_id_or_user_id): # Nom de variable plus générique si ouvert
    """ Récupère la liste de toutes les filières. """
    programs_cursor = mongo.db.programs.find()
    programs_list = []
    for p in programs_cursor:
        p['_id'] = str(p['_id'])
        if p.get('responsable_filiere_id'):
            p['responsable_filiere_id'] = str(p['responsable_filiere_id'])
        programs_list.append(p)
    return jsonify(programs_list), 200


@admin_bp.route('/programs/<string:program_id>', methods=['GET'])
@admin_required # Ouvert à d'autres rôles authentifiés si besoin
def get_program_by_id(current_admin_id_or_user_id, program_id):
    """ Récupère une filière spécifique par son ID. """
    try:
        program_obj_id = ObjectId(program_id)
        program = mongo.db.programs.find_one({"_id": program_obj_id})
        if program:
            program['_id'] = str(program['_id'])
            if program.get('responsable_filiere_id'):
                program['responsable_filiere_id'] = str(program['responsable_filiere_id'])
            return jsonify(program), 200
        return jsonify({"message": "Filière non trouvée"}), 404
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de filière invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


@admin_bp.route('/programs/<string:program_id>', methods=['PUT'])
@admin_required
def update_program(current_admin_id, program_id):
    """ Met à jour les informations d'une filière. """
    data = request.get_json()
    if not data: return jsonify({"message": "Aucune donnée fournie"}), 400

    try:
        program_obj_id = ObjectId(program_id)
        update_fields = {}
        if 'nom' in data:
            if mongo.db.programs.find_one({"nom": data['nom'], "_id": {"$ne": program_obj_id}}):
                return jsonify({"message": "Une autre filière avec ce nom existe déjà"}), 409
            update_fields['nom'] = data['nom']
        if 'code_filiere' in data:
            if mongo.db.programs.find_one({"code_filiere": data['code_filiere'], "_id": {"$ne": program_obj_id}}):
                return jsonify({"message": "Une autre filière avec ce code existe déjà"}), 409
            update_fields['code_filiere'] = data['code_filiere']

        for field in ['description', 'departement', 'niveaux_offerts']:
            if field in data:
                update_fields[field] = data[field]

        if 'responsable_filiere_id' in data:
            if data['responsable_filiere_id'] is None: # Permettre de dé-assigner
                 update_fields['responsable_filiere_id'] = None
            else:
                try:
                    prof = mongo.db.users.find_one({"_id": ObjectId(data['responsable_filiere_id']), "role": "professeur"})
                    if not prof:
                        return jsonify({"message": "ID du responsable de filière invalide ou l'utilisateur n'est pas un professeur."}), 400
                    update_fields['responsable_filiere_id'] = ObjectId(data['responsable_filiere_id'])
                except BsonErrors.InvalidId:
                    return jsonify({"message": "ID du responsable de filière invalide"}), 400

        if not update_fields: return jsonify({"message": "Aucun champ à mettre à jour"}), 400

        update_fields['date_modification'] = datetime.datetime.utcnow()
        update_fields['modifie_par_admin_id'] = ObjectId(current_admin_id)

        result = mongo.db.programs.update_one({"_id": program_obj_id}, {"$set": update_fields})
        if result.matched_count == 0: return jsonify({"message": "Filière non trouvée"}), 404
        return jsonify({"message": "Filière mise à jour avec succès"}), 200
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de filière invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


@admin_bp.route('/programs/<string:program_id>', methods=['DELETE'])
@admin_required
def delete_program(current_admin_id, program_id):
    """ Supprime une filière. """
    # Attention: vérifier les dépendances (cours, étudiants inscrits) avant suppression.
    # Pour l'instant, suppression directe.
    try:
        program_obj_id = ObjectId(program_id)

        # Vérification simple : si des cours sont liés à cette filière, empêcher la suppression.
        if mongo.db.courses.find_one({"filiere_ids": program_obj_id}):
            return jsonify({"message": "Impossible de supprimer la filière: des cours y sont associés."}), 409
        # Vérification si des étudiants sont inscrits dans cette filière
        if mongo.db.users.find_one({"role": "etudiant", "filiere_id": program_obj_id}):
            return jsonify({"message": "Impossible de supprimer la filière: des étudiants y sont inscrits."}), 409

        result = mongo.db.programs.delete_one({"_id": program_obj_id})
        if result.deleted_count == 0: return jsonify({"message": "Filière non trouvée"}), 404
        return jsonify({"message": "Filière supprimée avec succès"}), 200
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de filière invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


# --- Gestion des Cours (Courses) ---

@admin_bp.route('/courses', methods=['POST'])
@admin_required
def create_course(current_admin_id):
    """ Crée un nouveau cours. """
    data = request.get_json()
    required_fields = ['titre', 'code_cours', 'credits', 'niveau', 'semestre']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": f"Champs requis: {', '.join(required_fields)}"}), 400

    if mongo.db.courses.find_one({"code_cours": data['code_cours']}):
        return jsonify({"message": "Un cours avec ce code existe déjà"}), 409

    new_course = {
        "titre": data['titre'],
        "code_cours": data['code_cours'],
        "description": data.get('description', ""),
        "credits": data.get('credits'),
        "filiere_ids": [ObjectId(fid) for fid in data.get('filiere_ids', []) if fid], # Liste d'ID de filières
        "niveau": data['niveau'], # ex: L1, M2
        "semestre": data['semestre'], # ex: S1, S2
        "contenu_cours": [], # Initialement vide
        "pre_requis": [ObjectId(prid) for prid in data.get('pre_requis', []) if prid], # Liste d'ID de cours prérequis
        "date_creation": datetime.datetime.utcnow(),
        "date_modification": datetime.datetime.utcnow(),
        "cree_par_admin_id": ObjectId(current_admin_id)
    }

    if data.get('professeur_id'):
        try:
            prof = mongo.db.users.find_one({"_id": ObjectId(data['professeur_id']), "role": "professeur"})
            if not prof:
                return jsonify({"message": "ID du professeur assigné invalide ou l'utilisateur n'est pas un professeur."}), 400
            new_course['professeur_id'] = ObjectId(data['professeur_id'])
        except BsonErrors.InvalidId:
            return jsonify({"message": "ID du professeur assigné invalide."}), 400

    try:
        # Vérifier que les filières existent
        if new_course.get("filiere_ids"):
            for fid in new_course["filiere_ids"]:
                if not mongo.db.programs.find_one({"_id": fid}):
                    return jsonify({"message": f"L'ID de filière {str(fid)} n'existe pas."}), 400
        # Vérifier que les prérequis (cours) existent
        if new_course.get("pre_requis"):
            for prid in new_course["pre_requis"]:
                if not mongo.db.courses.find_one({"_id": prid}):
                    return jsonify({"message": f"L'ID de cours prérequis {str(prid)} n'existe pas."}), 400

        result = mongo.db.courses.insert_one(new_course)

        # Si un professeur est assigné, ajouter ce cours à sa liste `cours_enseignes_ids`
        if new_course.get('professeur_id'):
            mongo.db.users.update_one(
                {"_id": new_course['professeur_id']},
                {"$addToSet": {"cours_enseignes_ids": result.inserted_id}}
            )

        return jsonify({"message": "Cours créé avec succès", "course_id": str(result.inserted_id)}), 201
    except BsonErrors.InvalidId: # Pour les ObjectId dans filiere_ids ou pre_requis si mal formés avant vérification
         return jsonify({"message": "ID de filière ou de prérequis invalide dans la requête."}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de la création du cours", "error": str(e)}), 500


@admin_bp.route('/courses', methods=['GET'])
@admin_required # Ouvert à d'autres rôles authentifiés si besoin
def get_all_courses(current_admin_id_or_user_id):
    """ Récupère la liste de tous les cours avec filtres optionnels. """
    query_params = request.args
    filter_query = {}

    try:
        if query_params.get('filiere_id'):
            filter_query['filiere_ids'] = ObjectId(query_params.get('filiere_id'))

        if query_params.get('professeur_id'):
            filter_query['professeur_id'] = ObjectId(query_params.get('professeur_id'))

        if query_params.get('niveau'):
            filter_query['niveau'] = query_params.get('niveau')

        if query_params.get('semestre'):
            filter_query['semestre'] = query_params.get('semestre')

    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de filière ou de professeur invalide dans les filtres."}), 400

    courses_cursor = mongo.db.courses.find(filter_query)
    courses_list = []
    for c in courses_cursor:
        c['_id'] = str(c['_id'])
        if c.get('professeur_id'): c['professeur_id'] = str(c['professeur_id'])
        if c.get('filiere_ids'): c['filiere_ids'] = [str(fid) for fid in c['filiere_ids']]
        if c.get('pre_requis'): c['pre_requis'] = [str(prid) for prid in c['pre_requis']]
        # Ne pas inclure contenu_cours par défaut pour alléger la liste
        c.pop('contenu_cours', None)
        courses_list.append(c)
    return jsonify(courses_list), 200


@admin_bp.route('/courses/<string:course_id>', methods=['GET'])
@admin_required # Ouvert à d'autres rôles authentifiés si besoin
def get_course_by_id(current_admin_id_or_user_id, course_id):
    """ Récupère un cours spécifique par son ID, incluant le contenu. """
    try:
        course_obj_id = ObjectId(course_id)
        # Inclure le contenu du cours ici, contrairement à la liste générale
        course = mongo.db.courses.find_one({"_id": course_obj_id})
        if course:
            course['_id'] = str(course['_id'])
            if course.get('professeur_id'): course['professeur_id'] = str(course['professeur_id'])
            if course.get('filiere_ids'): course['filiere_ids'] = [str(fid) for fid in course['filiere_ids']]
            if course.get('pre_requis'): course['pre_requis'] = [str(prid) for prid in course['pre_requis']]
            if course.get('contenu_cours'):
                for section in course['contenu_cours']:
                    if section.get('section_id'): section['section_id'] = str(section['section_id'])
            return jsonify(course), 200
        return jsonify({"message": "Cours non trouvé"}), 404
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de cours invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


@admin_bp.route('/courses/<string:course_id>', methods=['PUT'])
@admin_required
def update_course(current_admin_id, course_id):
    """ Met à jour les informations d'un cours. """
    data = request.get_json()
    if not data: return jsonify({"message": "Aucune donnée fournie"}), 400

    try:
        course_obj_id = ObjectId(course_id)

        # Récupérer l'ancien professeur_id si le cours existe et a un professeur
        old_course_data = mongo.db.courses.find_one({"_id": course_obj_id}, {"professeur_id": 1})
        old_prof_id = old_course_data.get('professeur_id') if old_course_data else None

        update_fields = {}
        simple_text_fields = ['titre', 'description', 'credits', 'niveau', 'semestre']
        for field in simple_text_fields:
            if field in data: update_fields[field] = data[field]

        if 'code_cours' in data:
            if mongo.db.courses.find_one({"code_cours": data['code_cours'], "_id": {"$ne": course_obj_id}}):
                return jsonify({"message": "Un autre cours avec ce code existe déjà"}), 409
            update_fields['code_cours'] = data['code_cours']

        if 'filiere_ids' in data:
            try:
                valid_filiere_ids = []
                for fid_str in data.get('filiere_ids', []):
                    fid_obj = ObjectId(fid_str)
                    if not mongo.db.programs.find_one({"_id": fid_obj}):
                        return jsonify({"message": f"L'ID de filière {fid_str} n'existe pas."}), 400
                    valid_filiere_ids.append(fid_obj)
                update_fields['filiere_ids'] = valid_filiere_ids
            except BsonErrors.InvalidId:
                return jsonify({"message": "Un ID de filière est invalide."}), 400

        if 'pre_requis' in data:
            try:
                valid_prereq_ids = []
                for prid_str in data.get('pre_requis', []):
                    prid_obj = ObjectId(prid_str)
                    if not mongo.db.courses.find_one({"_id": prid_obj}): # Vérifier que le cours prérequis existe
                        return jsonify({"message": f"L'ID de cours prérequis {prid_str} n'existe pas."}), 400
                    valid_prereq_ids.append(prid_obj)
                update_fields['pre_requis'] = valid_prereq_ids
            except BsonErrors.InvalidId:
                return jsonify({"message": "Un ID de prérequis est invalide."}), 400

        new_prof_id_str = data.get('professeur_id')
        new_prof_id = None
        if new_prof_id_str is not None: # Si le champ professeur_id est explicitement fourni (même si null)
            if new_prof_id_str: # Si ce n'est pas une chaîne vide ou null
                try:
                    new_prof_id = ObjectId(new_prof_id_str)
                    prof = mongo.db.users.find_one({"_id": new_prof_id, "role": "professeur"})
                    if not prof:
                        return jsonify({"message": "ID du professeur invalide ou l'utilisateur n'est pas un professeur."}), 400
                    update_fields['professeur_id'] = new_prof_id
                except BsonErrors.InvalidId:
                    return jsonify({"message": "ID du professeur invalide."}), 400
            else: # professeur_id est explicitement mis à null/vide, donc on dé-assigne
                update_fields['professeur_id'] = None

        # Le champ `contenu_cours` est géré par les routes spécifiques du professeur, non ici.

        if not update_fields: return jsonify({"message": "Aucun champ valide à mettre à jour"}), 400

        update_fields['date_modification'] = datetime.datetime.utcnow()
        update_fields['modifie_par_admin_id'] = ObjectId(current_admin_id)

        result = mongo.db.courses.update_one({"_id": course_obj_id}, {"$set": update_fields})
        if result.matched_count == 0: return jsonify({"message": "Cours non trouvé"}), 404

        # Mettre à jour la liste des cours du/des professeur(s) concerné(s)
        # Si le professeur a changé:
        # 1. Retirer le cours de l'ancien professeur (si old_prof_id existait et est différent de new_prof_id)
        if old_prof_id and old_prof_id != new_prof_id:
            mongo.db.users.update_one(
                {"_id": old_prof_id},
                {"$pull": {"cours_enseignes_ids": course_obj_id}}
            )
        # 2. Ajouter le cours au nouveau professeur (si new_prof_id existe et est différent de old_prof_id)
        if new_prof_id and new_prof_id != old_prof_id:
            mongo.db.users.update_one(
                {"_id": new_prof_id},
                {"$addToSet": {"cours_enseignes_ids": course_obj_id}}
            )

        return jsonify({"message": "Cours mis à jour avec succès"}), 200
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de cours invalide dans l'URL."}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


@admin_bp.route('/courses/<string:course_id>', methods=['DELETE'])
@admin_required
def delete_course(current_admin_id, course_id):
    """ Supprime un cours. """
    # Attention: vérifier les dépendances (étudiants inscrits, notes existantes) avant suppression.
    try:
        course_obj_id = ObjectId(course_id)

        # Vérification simple : si des notes existent pour ce cours
        if mongo.db.grades.find_one({"cours_id": course_obj_id}):
            return jsonify({"message": "Impossible de supprimer le cours: des notes y sont associées."}), 409
        # Vérification si des étudiants sont inscrits à ce cours via leur profil
        if mongo.db.users.find_one({"role": "etudiant", "cours_inscrits.cours_id": course_obj_id}):
            return jsonify({"message": "Impossible de supprimer le cours: des étudiants y sont inscrits."}), 409

        # Retirer le cours de la liste `cours_enseignes_ids` du professeur assigné
        course_data = mongo.db.courses.find_one({"_id": course_obj_id}, {"professeur_id": 1})
        if course_data and course_data.get('professeur_id'):
            mongo.db.users.update_one(
                {"_id": course_data['professeur_id']},
                {"$pull": {"cours_enseignes_ids": course_obj_id}}
            )

        result = mongo.db.courses.delete_one({"_id": course_obj_id})
        if result.deleted_count == 0: return jsonify({"message": "Cours non trouvé"}), 404

        return jsonify({"message": "Cours supprimé avec succès"}), 200
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de cours invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


# --- Gestion des Inscriptions aux Cours ---

@admin_bp.route('/enrollments', methods=['POST'])
@admin_required
def enroll_student_in_course(current_admin_id):
    """ Inscrit un étudiant à un cours spécifique. """
    data = request.get_json()
    if not data or not data.get('etudiant_id') or not data.get('cours_id'):
        return jsonify({"message": "etudiant_id et cours_id sont requis."}), 400

    etudiant_id_str = data.get('etudiant_id')
    cours_id_str = data.get('cours_id')
    annee_academique = data.get('annee_academique') # Optionnel, mais recommandé
    semestre_inscription = data.get('semestre') # Optionnel, mais recommandé

    if not annee_academique or not semestre_inscription:
        # Essayer de déduire du cours si non fourni, ou retourner une erreur
        # Pour l'instant, on les rend quasi-requis pour la clarté de l'inscription
        return jsonify({"message": "annee_academique et semestre d'inscription sont requis."}), 400

    try:
        etudiant_obj_id = ObjectId(etudiant_id_str)
        cours_obj_id = ObjectId(cours_id_str)

        # Vérifier que l'étudiant existe et est bien un étudiant
        student = mongo.db.users.find_one({"_id": etudiant_obj_id, "role": "etudiant"})
        if not student:
            return jsonify({"message": "Étudiant non trouvé ou l'ID ne correspond pas à un étudiant."}), 404

        # Vérifier que le cours existe
        course = mongo.db.courses.find_one({"_id": cours_obj_id})
        if not course:
            return jsonify({"message": "Cours non trouvé."}), 404

        # Vérifier si l'étudiant est déjà inscrit à ce cours pour cette année/semestre
        # (pour éviter les doublons exacts si on ne gère pas les statuts d'inscription complexes ici)
        already_enrolled = mongo.db.users.find_one({
            "_id": etudiant_obj_id,
            "cours_inscrits": {
                "$elemMatch": {
                    "cours_id": cours_obj_id,
                    "annee_academique": annee_academique,
                    "semestre": semestre_inscription
                }
            }
        })
        if already_enrolled:
            return jsonify({"message": "Étudiant déjà inscrit à ce cours pour cette période."}), 409

        inscription_data = {
            "cours_id": cours_obj_id,
            "annee_academique": annee_academique,
            "semestre": semestre_inscription,
            "date_inscription": datetime.datetime.utcnow(),
            "statut_inscription": data.get("statut_inscription", "inscrit"), # ex: 'inscrit', 'en_attente'
            "inscrit_par_admin_id": ObjectId(current_admin_id)
        }

        result = mongo.db.users.update_one(
            {"_id": etudiant_obj_id},
            {"$addToSet": {"cours_inscrits": inscription_data}} # addToSet évite les doublons exacts de l'objet entier
        )

        if result.modified_count > 0:
            return jsonify({"message": "Étudiant inscrit au cours avec succès."}), 200
        else:
            # Soit l'étudiant n'a pas été trouvé (déjà géré), soit l'objet était identique (peu probable avec date_inscription)
            # Ou l'étudiant a été trouvé mais addToSet n'a rien ajouté (si l'objet exact existait)
            return jsonify({"message": "Inscription non effectuée (peut-être déjà inscrit avec les mêmes détails ou erreur)."}), 400

    except BsonErrors.InvalidId:
        return jsonify({"message": "ID étudiant ou cours invalide."}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de l'inscription de l'étudiant.", "error": str(e)}), 500


@admin_bp.route('/enrollments/student/<string:etudiant_id>/course/<string:cours_id>', methods=['DELETE'])
@admin_required
def unenroll_student_from_course(current_admin_id, etudiant_id, cours_id):
    """ Désinscrit un étudiant d'un cours spécifique. """
    # On pourrait vouloir plus de granularité (ex: désinscription pour une année/semestre spécifique)
    # Pour l'instant, on supprime toutes les inscriptions de cet étudiant à ce cours.
    # Ou, mieux, on cible une inscription spécifique si on a un `enrollment_id` ou des critères (année, semestre).
    # Ici, on va retirer la référence au cours_id du tableau `cours_inscrits`.
    # Pour plus de précision, il faudrait passer l'année académique et le semestre.

    annee_academique = request.args.get('annee_academique')
    semestre_inscription = request.args.get('semestre')

    if not annee_academique or not semestre_inscription:
        return jsonify({"message": "Les paramètres 'annee_academique' et 'semestre' sont requis pour identifier l'inscription à supprimer."}), 400

    try:
        etudiant_obj_id = ObjectId(etudiant_id)
        cours_obj_id = ObjectId(cours_id)

        # Vérifier que l'étudiant existe
        if not mongo.db.users.find_one({"_id": etudiant_obj_id, "role": "etudiant"}):
            return jsonify({"message": "Étudiant non trouvé."}), 404

        # Vérifier que le cours existe (optionnel, mais cohérent)
        if not mongo.db.courses.find_one({"_id": cours_obj_id}):
            return jsonify({"message": "Cours non trouvé."}), 404

        pull_condition = {
            "cours_id": cours_obj_id,
            "annee_academique": annee_academique,
            "semestre": semestre_inscription
        }

        result = mongo.db.users.update_one(
            {"_id": etudiant_obj_id},
            {"$pull": {"cours_inscrits": pull_condition}}
        )

        if result.modified_count > 0:
            # TODO: Potentiellement supprimer les notes associées si la politique le demande.
            # mongo.db.grades.delete_many({"etudiant_id": etudiant_obj_id, "cours_id": cours_obj_id, "annee_academique": annee_academique, "semestre": semestre_inscription})
            return jsonify({"message": "Étudiant désinscrit du cours avec succès pour la période spécifiée."}), 200
        else:
            return jsonify({"message": "Étudiant non trouvé, non inscrit à ce cours pour cette période, ou déjà désinscrit."}), 404

    except BsonErrors.InvalidId:
        return jsonify({"message": "ID étudiant ou cours invalide."}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de la désinscription de l'étudiant.", "error": str(e)}), 500


print("Blueprint pour les administrateurs (admin_bp) créé avec gestion des utilisateurs, filières, cours et inscriptions.")
