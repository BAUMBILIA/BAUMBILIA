# backend/app/routes/professor_routes.py
from flask import request, jsonify, Blueprint
from backend.app import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

professor_bp = Blueprint('professor_bp', __name__)

# Décorateur personnalisé pour vérifier le rôle 'professeur'
def professor_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        if current_user.get('role') != 'professeur':
            return jsonify({"message": "Accès réservé aux professeurs"}), 403
        return fn(current_user['user_id'], *args, **kwargs)
    wrapper.__name__ = fn.__name__ + "_wrapper_prof" # Nom unique pour le décorateur
    return wrapper


@professor_bp.route('/courses', methods=['GET'])
@professor_required
def get_professor_courses(current_professor_id):
    """ Récupère les cours enseignés par le professeur connecté. """
    try:
        professor_obj_id = ObjectId(current_professor_id)
        courses_cursor = mongo.db.courses.find({"professeur_id": professor_obj_id})
        courses_list = []
        for course in courses_cursor:
            course['_id'] = str(course['_id'])
            if 'professeur_id' in course and isinstance(course['professeur_id'], ObjectId):
                course['professeur_id'] = str(course['professeur_id'])
            if 'filiere_ids' in course:
                course['filiere_ids'] = [str(fid) for fid in course.get('filiere_ids', []) if isinstance(fid, ObjectId)]
            if 'contenu_cours' in course: # Convertir les section_id en string
                for section in course['contenu_cours']:
                    if 'section_id' in section and isinstance(section['section_id'], ObjectId):
                        section['section_id'] = str(section['section_id'])
            courses_list.append(course)
        return jsonify(courses_list), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des cours", "error": str(e)}), 500


@professor_bp.route('/course/<string:course_id>/students', methods=['GET'])
@professor_required
def get_students_in_course(current_professor_id, course_id):
    """ Récupère la liste des étudiants inscrits à un cours spécifique géré par ce professeur. """
    try:
        course_obj_id = ObjectId(course_id)
        professor_obj_id = ObjectId(current_professor_id)
        course = mongo.db.courses.find_one({"_id": course_obj_id, "professeur_id": professor_obj_id})
        if not course:
            return jsonify({"message": "Cours non trouvé ou non autorisé pour ce professeur"}), 404
        students_cursor = mongo.db.users.find(
            {"role": "etudiant", "cours_inscrits.cours_id": course_obj_id},
            {"_id": 1, "nom": 1, "prenom": 1, "email": 1, "matricule": 1}
        )
        students_list = [{**s, '_id': str(s['_id'])} for s in students_cursor]
        return jsonify(students_list), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des étudiants", "error": str(e)}), 500


@professor_bp.route('/grade', methods=['POST'])
@professor_required
def add_or_update_grade(current_professor_id):
    """ Permet à un professeur d'ajouter ou de mettre à jour la note d'un étudiant pour un cours. """
    data = request.get_json()
    required_fields = ['etudiant_id', 'cours_id', 'note_valeur', 'annee_academique', 'semestre']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": f"Champs requis: {', '.join(required_fields)}"}), 400

    try:
        etudiant_obj_id = ObjectId(data['etudiant_id'])
        cours_obj_id = ObjectId(data['cours_id'])
        professor_obj_id = ObjectId(current_professor_id)

        course = mongo.db.courses.find_one({"_id": cours_obj_id, "professeur_id": professor_obj_id})
        if not course:
            return jsonify({"message": "Cours non trouvé ou non autorisé"}), 403
        student = mongo.db.users.find_one({"_id": etudiant_obj_id, "role": "etudiant", "cours_inscrits.cours_id": cours_obj_id})
        if not student:
            return jsonify({"message": "Étudiant non trouvé ou non inscrit à ce cours"}), 404

        grade_data = {
            "etudiant_id": etudiant_obj_id, "cours_id": cours_obj_id,
            "professeur_id_enregistrement": professor_obj_id,
            "note_valeur": data['note_valeur'], "annee_academique": data['annee_academique'],
            "semestre": data['semestre'], "type_evaluation": data.get('type_evaluation', 'Examen Final'),
            "date_enregistrement": datetime.datetime.utcnow(),
            "visible_etudiant": data.get('visible_etudiant', False)
        }
        for opt_field in ['bareme_max', 'coefficient', 'commentaires_professeur']:
            if opt_field in data: grade_data[opt_field] = data[opt_field]
        if 'date_evaluation' in data:
            grade_data['date_evaluation'] = datetime.datetime.fromisoformat(data['date_evaluation'])

        query_filter = {k: grade_data[k] for k in ["etudiant_id", "cours_id", "annee_academique", "semestre", "type_evaluation"]}
        existing_grade = mongo.db.grades.find_one(query_filter)
        message = ""
        status_code = 200

        if existing_grade:
            update_payload = {"$set": grade_data}
            history_entry = {
                "modifie_par_id": professor_obj_id, "date_modification": datetime.datetime.utcnow(),
                "ancienne_valeur": existing_grade.get("note_valeur"), "nouvelle_valeur": data['note_valeur'],
                "raison": data.get("raison_modification", "Mise à jour par professeur")
            }
            update_payload["$push"] = {"historique_modifications": history_entry}
            mongo.db.grades.update_one(query_filter, update_payload)
            grade_id = existing_grade['_id']
            message = "Note mise à jour avec succès"
        else:
            grade_data["historique_modifications"] = [{
                "modifie_par_id": professor_obj_id, "date_modification": datetime.datetime.utcnow(),
                "ancienne_valeur": None, "nouvelle_valeur": data['note_valeur'], "raison": "Création initiale"
            }]
            result = mongo.db.grades.insert_one(grade_data)
            grade_id = result.inserted_id
            message = "Note ajoutée avec succès"
            status_code = 201

        # Envoyer une notification à l'étudiant si la note est visible
        if grade_data.get("visible_etudiant", False):
            student_info = mongo.db.users.find_one({"_id": etudiant_obj_id}, {"email": 1, "prenom": 1, "nom": 1})
            course_info = mongo.db.courses.find_one({"_id": cours_obj_id}, {"titre": 1})
            if student_info and course_info:
                from backend.app.services.email_service import EmailService
                student_full_name = f"{student_info.get('prenom','')} {student_info.get('nom','')}".strip()
                EmailService.send_new_grade_notification(
                    student_info['email'],
                    student_full_name if student_full_name else "Étudiant",
                    course_info.get('titre', 'N/A'),
                    str(grade_data['note_valeur'])
                )

        return jsonify({"message": message, "grade_id": str(grade_id)}), status_code
    except ValueError as ve: return jsonify({"message": "Données invalides (ID ou date)", "error": str(ve)}), 400
    except Exception as e: return jsonify({"message": "Erreur serveur", "error": str(e)}), 500


@professor_bp.route('/course/<string:course_id>/grades', methods=['GET'])
@professor_required
def get_grades_for_course_by_professor(current_professor_id, course_id):
    """
    Récupère toutes les notes pour un cours spécifique enseigné par ce professeur.
    """
    try:
        course_obj_id = ObjectId(course_id)
        professor_obj_id = ObjectId(current_professor_id)

        # 1. Vérifier si le professeur enseigne bien ce cours
        course = mongo.db.courses.find_one({"_id": course_obj_id, "professeur_id": professor_obj_id})
        if not course:
            return jsonify({"message": "Cours non trouvé ou non autorisé pour ce professeur"}), 403

        # 2. Récupérer toutes les notes pour ce cours (visibles ou non, le prof voit tout)
        # On pourrait ajouter des filtres par année académique/semestre via request.args si besoin
        grades_cursor = mongo.db.grades.find({"cours_id": course_obj_id})

        grades_list = []
        for grade in grades_cursor:
            grade['_id'] = str(grade['_id'])
            grade['etudiant_id'] = str(grade['etudiant_id'])
            grade['cours_id'] = str(grade['cours_id'])
            if 'professeur_id_enregistrement' in grade:
                grade['professeur_id_enregistrement'] = str(grade['professeur_id_enregistrement'])

            # Optionnel: enrichir avec le nom de l'étudiant
            student_info = mongo.db.users.find_one({"_id": ObjectId(grade['etudiant_id'])}, {"nom":1, "prenom":1, "matricule":1})
            if student_info:
                grade['etudiant_details'] = {
                    "nom": student_info.get("nom"),
                    "prenom": student_info.get("prenom"),
                    "matricule": student_info.get("matricule")
                }
            grades_list.append(grade)

        return jsonify(grades_list), 200
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de cours invalide."}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des notes du cours.", "error": str(e)}), 500


@professor_bp.route('/course/<string:course_id>/details', methods=['GET'])
@professor_required
def get_professor_course_details(current_professor_id, course_id):
    """ Récupère les détails complets d'un cours spécifique géré par ce professeur, y compris le contenu. """
    try:
        course_obj_id = ObjectId(course_id)
        professor_obj_id = ObjectId(current_professor_id)

        # Vérifier si le professeur enseigne bien ce cours
        course = mongo.db.courses.find_one({"_id": course_obj_id, "professeur_id": professor_obj_id})
        if not course:
            return jsonify({"message": "Cours non trouvé ou non autorisé pour ce professeur"}), 404

        # Convertir les ObjectId en string pour la réponse JSON
        course['_id'] = str(course['_id'])
        if 'professeur_id' in course and isinstance(course['professeur_id'], ObjectId):
            course['professeur_id'] = str(course['professeur_id'])
        if 'filiere_ids' in course:
            course['filiere_ids'] = [str(fid) for fid in course.get('filiere_ids', []) if isinstance(fid, ObjectId)]
        if 'pre_requis' in course:
            course['pre_requis'] = [str(prid) for prid in course.get('pre_requis', []) if isinstance(prid, ObjectId)]

        if 'contenu_cours' in course:
            for section in course['contenu_cours']:
                if 'section_id' in section and isinstance(section['section_id'], ObjectId):
                    section['section_id'] = str(section['section_id'])
                # Convertir d'autres ObjectId dans les fichiers joints si nécessaire
                if 'fichiers_joints' in section:
                    for fichier in section['fichiers_joints']:
                        # Supposons pas d'autres ObjectId ici pour l'instant
                        pass

        return jsonify(course), 200
    except BsonErrors.InvalidId:
        return jsonify({"message": "ID de cours invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des détails du cours", "error": str(e)}), 500


@professor_bp.route('/course/<string:course_id>/content', methods=['POST'])
@professor_required
def add_course_content(current_professor_id, course_id):
    """ Ajoute une section de contenu à un cours. """
    data = request.get_json()
    if not data or not data.get('titre_section'):
        return jsonify({"message": "Titre de la section requis"}), 400
    try:
        course_obj_id = ObjectId(course_id)
        professor_obj_id = ObjectId(current_professor_id)
        course = mongo.db.courses.find_one({"_id": course_obj_id, "professeur_id": professor_obj_id})
        if not course: return jsonify({"message": "Cours non trouvé ou non autorisé"}), 403

        new_section = {
            "section_id": ObjectId(), "titre_section": data['titre_section'],
            "contenu_html": data.get('contenu_html', ""),
            "fichiers_joints": data.get('fichiers_joints', []),
            "date_ajout": datetime.datetime.utcnow(), "date_modification": datetime.datetime.utcnow()
        }
        if data.get('ordre') is not None: new_section["ordre"] = int(data['ordre'])
        for fichier in new_section["fichiers_joints"]:
            if not all(k in fichier for k in ("nom_fichier", "url_stockage", "type_fichier")):
                return jsonify({"message": "Fichier joint mal formaté"}), 400
            fichier["date_upload"] = datetime.datetime.utcnow()

        mongo.db.courses.update_one(
            {"_id": course_obj_id},
            {"$push": {"contenu_cours": new_section}, "$set": {"date_modification": datetime.datetime.utcnow()}}
        )
        return jsonify({"message": "Contenu ajouté", "section_id": str(new_section["section_id"])}), 201
    except ValueError: return jsonify({"message": "ID de cours ou ordre invalide"}), 400
    except Exception as e: return jsonify({"message": "Erreur serveur", "error": str(e)}), 500

@professor_bp.route('/course/<string:course_id>/content/<string:section_id>', methods=['PUT'])
@professor_required
def update_course_content_section(current_professor_id, course_id, section_id):
    """ Met à jour une section de contenu spécifique. """
    data = request.get_json()
    if not data: return jsonify({"message": "Aucune donnée à mettre à jour"}), 400
    try:
        course_obj_id = ObjectId(course_id)
        section_obj_id = ObjectId(section_id)
        professor_obj_id = ObjectId(current_professor_id)
        course = mongo.db.courses.find_one({"_id": course_obj_id, "professeur_id": professor_obj_id})
        if not course: return jsonify({"message": "Cours non trouvé ou non autorisé"}), 403

        update_fields = {'contenu_cours.$.date_modification': datetime.datetime.utcnow()}
        if 'titre_section' in data: update_fields['contenu_cours.$.titre_section'] = data['titre_section']
        if 'contenu_html' in data: update_fields['contenu_cours.$.contenu_html'] = data['contenu_html']
        if 'ordre' in data: update_fields['contenu_cours.$.ordre'] = int(data['ordre'])
        if 'fichiers_joints' in data:
            for fichier in data.get("fichiers_joints", []):
                 if not all(k in fichier for k in ("nom_fichier", "url_stockage", "type_fichier")):
                    return jsonify({"message": "Fichier joint mal formaté"}), 400
                 if "date_upload" not in fichier: fichier["date_upload"] = datetime.datetime.utcnow()
            update_fields['contenu_cours.$.fichiers_joints'] = data['fichiers_joints']

        if len(update_fields) == 1 and 'contenu_cours.$.date_modification' in update_fields : # only date_modification
             return jsonify({"message": "Aucun champ modifiable fourni"}), 400

        result = mongo.db.courses.update_one(
            {"_id": course_obj_id, "contenu_cours.section_id": section_obj_id},
            {"$set": update_fields}
        )
        if result.matched_count == 0: return jsonify({"message": "Section non trouvée"}), 404
        mongo.db.courses.update_one({"_id": course_obj_id},{"$set": {"date_modification": datetime.datetime.utcnow()}})
        return jsonify({"message": "Section mise à jour"}), 200
    except ValueError: return jsonify({"message": "ID ou ordre invalide"}), 400
    except Exception as e: return jsonify({"message": "Erreur serveur", "error": str(e)}), 500

@professor_bp.route('/course/<string:course_id>/content/<string:section_id>', methods=['DELETE'])
@professor_required
def delete_course_content_section(current_professor_id, course_id, section_id):
    """ Supprime une section de contenu. """
    try:
        course_obj_id = ObjectId(course_id)
        section_obj_id = ObjectId(section_id)
        professor_obj_id = ObjectId(current_professor_id)
        course = mongo.db.courses.find_one({"_id": course_obj_id, "professeur_id": professor_obj_id})
        if not course: return jsonify({"message": "Cours non trouvé ou non autorisé"}), 403

        result = mongo.db.courses.update_one(
            {"_id": course_obj_id},
            {"$pull": {"contenu_cours": {"section_id": section_obj_id}}}
        )
        if result.modified_count > 0:
            mongo.db.courses.update_one({"_id": course_obj_id},{"$set": {"date_modification": datetime.datetime.utcnow()}})
            return jsonify({"message": "Section supprimée"}), 200
        return jsonify({"message": "Section non trouvée ou déjà supprimée"}), 404
    except ValueError: return jsonify({"message": "ID invalide"}), 400
    except Exception as e: return jsonify({"message": "Erreur serveur", "error": str(e)}), 500

print("Blueprint pour les professeurs (professor_bp) créé avec routes pour notes et gestion contenu de cours.")
