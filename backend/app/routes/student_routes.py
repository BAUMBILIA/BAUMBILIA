# backend/app/routes/student_routes.py
from flask import request, jsonify, Blueprint
from backend.app import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime

student_bp = Blueprint('student_bp', __name__)

# Décorateur personnalisé pour vérifier le rôle 'etudiant'
def student_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        if current_user.get('role') != 'etudiant':
            return jsonify({"message": "Accès réservé aux étudiants"}), 403
        return fn(current_user['user_id'], *args, **kwargs) # Passe l'ID de l'étudiant
    wrapper.__name__ = fn.__name__ + "_wrapper_student"
    return wrapper


@student_bp.route('/my/grades', methods=['GET'])
@student_required
def get_my_grades(current_student_id):
    """
    Récupère toutes les notes de l'étudiant connecté.
    Les notes sont récupérées depuis la collection 'grades'.
    """
    try:
        student_obj_id = ObjectId(current_student_id)

        # Récupérer les notes où etudiant_id correspond et qui sont visibles
        # On peut ajouter des filtres (année académique, semestre) via query params si besoin
        # Pour l'instant, on récupère tout ce qui est visible.
        query_params = request.args
        filter_query = {"etudiant_id": student_obj_id, "visible_etudiant": True}

        if query_params.get('annee_academique'):
            filter_query['annee_academique'] = query_params.get('annee_academique')
        if query_params.get('semestre'):
            filter_query['semestre'] = query_params.get('semestre')
        if query_params.get('cours_id'):
            try:
                filter_query['cours_id'] = ObjectId(query_params.get('cours_id'))
            except:
                return jsonify({"message": "ID de cours invalide dans les paramètres"}), 400

        grades_cursor = mongo.db.grades.find(filter_query)

        grades_list = []
        for grade in grades_cursor:
            grade['_id'] = str(grade['_id'])
            grade['etudiant_id'] = str(grade['etudiant_id'])
            grade['cours_id'] = str(grade['cours_id'])
            if 'professeur_id_enregistrement' in grade:
                grade['professeur_id_enregistrement'] = str(grade['professeur_id_enregistrement'])

            # Pour enrichir avec le nom du cours (dénormalisation à la lecture)
            course_info = mongo.db.courses.find_one(
                {"_id": ObjectId(grade['cours_id'])},
                {"titre": 1, "code_cours": 1} # Projeter seulement les champs nécessaires
            )
            if course_info:
                grade['titre_cours'] = course_info.get('titre')
                grade['code_cours'] = course_info.get('code_cours')

            grades_list.append(grade)

        return jsonify(grades_list), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des notes", "error": str(e)}), 500


@student_bp.route('/my/courses', methods=['GET'])
@student_required
def get_my_courses(current_student_id):
    """
    Récupère la liste des cours auxquels l'étudiant connecté est inscrit.
    L'information d'inscription est dans le document utilisateur de l'étudiant (`cours_inscrits`).
    """
    try:
        student_obj_id = ObjectId(current_student_id)
        student_data = mongo.db.users.find_one(
            {"_id": student_obj_id, "role": "etudiant"},
            {"cours_inscrits": 1, "_id": 0} # Projeter seulement le champ cours_inscrits
        )

        if not student_data or 'cours_inscrits' not in student_data:
            return jsonify([]), 200 # Pas de cours inscrits ou étudiant non trouvé

        enrolled_courses_info = []
        for enrolled_course_ref in student_data.get('cours_inscrits', []):
            course_id = enrolled_course_ref.get('cours_id')
            if isinstance(course_id, str): # Si l'ID est déjà une chaîne (par exemple, lors de l'import)
                try:
                    course_id = ObjectId(course_id)
                except:
                    continue # Ignorer si l'ID n'est pas valide
            elif not isinstance(course_id, ObjectId):
                continue # Ignorer si ce n'est pas un ObjectId valide

            course_details = mongo.db.courses.find_one(
                {"_id": course_id},
                # Projeter les champs nécessaires du cours, exclure le contenu détaillé ici
                {"titre": 1, "code_cours": 1, "description": 1, "credits":1, "semestre":1, "niveau":1, "professeur_id":1}
            )
            if course_details:
                course_details['_id'] = str(course_details['_id'])
                if 'professeur_id' in course_details and isinstance(course_details['professeur_id'], ObjectId):
                     course_details['professeur_id'] = str(course_details['professeur_id'])
                # Ajouter les infos d'inscription spécifiques à l'étudiant pour ce cours
                course_details['inscription_details'] = {
                    "annee_academique": enrolled_course_ref.get('annee_academique'),
                    "semestre_inscription": enrolled_course_ref.get('semestre'),
                    "statut_inscription": enrolled_course_ref.get('statut_inscription')
                }
                enrolled_courses_info.append(course_details)

        return jsonify(enrolled_courses_info), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des cours inscrits", "error": str(e)}), 500


@student_bp.route('/course/<string:course_id>/content', methods=['GET'])
@student_required
def get_course_content_for_student(current_student_id, course_id):
    """
    Permet à un étudiant de récupérer le contenu d'un cours auquel il est inscrit.
    """
    try:
        student_obj_id = ObjectId(current_student_id)
        course_obj_id = ObjectId(course_id)

        # 1. Vérifier si l'étudiant est inscrit à ce cours
        is_enrolled = mongo.db.users.find_one(
            {"_id": student_obj_id, "role": "etudiant", "cours_inscrits.cours_id": course_obj_id}
        )
        if not is_enrolled:
            return jsonify({"message": "Vous n'êtes pas inscrit à ce cours ou le cours n'existe pas."}), 403

        # 2. Récupérer le contenu du cours
        course_content = mongo.db.courses.find_one(
            {"_id": course_obj_id},
            {"titre": 1, "code_cours":1, "contenu_cours": 1, "_id": 0} # Projeter seulement le contenu et titre/code
        )

        if not course_content or 'contenu_cours' not in course_content:
            return jsonify({"message": "Contenu du cours non trouvé.", "titre_cours": course_content.get("titre")}), 404

        # Convertir les section_id en string dans le contenu du cours
        for section in course_content.get('contenu_cours', []):
            if 'section_id' in section and isinstance(section['section_id'], ObjectId):
                section['section_id'] = str(section['section_id'])
            # On pourrait vouloir filtrer les fichiers_joints ou autre ici si nécessaire

        return jsonify(course_content), 200

    except ValueError:
        return jsonify({"message": "ID de cours invalide"}), 400
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération du contenu du cours", "error": str(e)}), 500

# D'autres routes pour étudiants:
# - Envoyer des messages (interaction avec MESSAGE_SCHEMA)
# - Tableau de bord plus détaillé (pourrait être géré par le frontend en appelant ces APIs)

print("Blueprint pour les étudiants (student_bp) créé avec des routes pour notes et contenu de cours.")
