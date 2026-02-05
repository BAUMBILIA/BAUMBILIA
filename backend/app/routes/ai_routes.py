# backend/app/routes/ai_routes.py
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required # Protéger les routes IA si nécessaire
from backend.app.services.groq_service import GroqService

ai_bp = Blueprint('ai_bp', __name__)
groq_service = GroqService() # Instancier le service

@ai_bp.route('/summarize', methods=['POST'])
@jwt_required() # Exemple de protection, à ajuster selon les besoins
def summarize_text_route():
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"message": "Le champ 'text' est requis pour le résumé."}), 400

    text_to_summarize = data.get('text')
    max_length = data.get('max_length', "environ 100 mots") # Longueur souhaitée du résumé

    if not groq_service.client:
         return jsonify({"message": "Service IA non disponible (clé API manquante ou erreur d'initialisation)."}), 503

    summary = groq_service.summarize_text(text_to_summarize, max_length_summary=max_length)

    if summary.startswith("Erreur:"): # Si le service retourne une erreur gérée
        return jsonify({"message": "Erreur lors de la génération du résumé.", "details": summary}), 500

    return jsonify({"summary": summary}), 200


@ai_bp.route('/ask-contextual', methods=['POST'])
@jwt_required() # Exemple de protection
def ask_contextual_question_route():
    data = request.get_json()
    if not data or not data.get('text_context') or not data.get('question'):
        return jsonify({"message": "Les champs 'text_context' et 'question' sont requis."}), 400

    text_context = data.get('text_context')
    question = data.get('question')

    if not groq_service.client:
         return jsonify({"message": "Service IA non disponible (clé API manquante ou erreur d'initialisation)."}), 503

    answer = groq_service.answer_question_about_text(text_context, question)

    if answer.startswith("Erreur:"): # Si le service retourne une erreur gérée
        return jsonify({"message": "Erreur lors de la génération de la réponse.", "details": answer}), 500

    return jsonify({"answer": answer}), 200


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat_with_ai_route():
    """
    Route générique pour interagir avec le modèle de chat.
    Prend une liste de messages en entrée, comme pour l'API OpenAI.
    Exemple de payload:
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "model": "mixtral-8x7b-32768", // Optionnel
        "temperature": 0.7, // Optionnel
        "max_tokens": 150 // Optionnel
    }
    """
    data = request.get_json()
    if not data or not data.get('messages'):
        return jsonify({"message": "Le champ 'messages' (liste) est requis."}), 400

    messages = data.get('messages')
    model = data.get('model', "mixtral-8x7b-32768") # Valeur par défaut du service
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 1024)

    if not groq_service.client:
         return jsonify({"message": "Service IA non disponible (clé API manquante ou erreur d'initialisation)."}), 503

    response_content = groq_service.generate_chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

    if response_content.startswith("Erreur:"): # Si le service retourne une erreur gérée
        return jsonify({"message": "Erreur lors de la communication avec l'IA.", "details": response_content}), 500

    return jsonify({"response": response_content}), 200

# D'autres routes pourraient être ajoutées pour des fonctionnalités IA spécifiques
# Par exemple:
# - /generate-quiz-questions (prend un contenu de cours, génère des questions)
# - /analyze-student-performance (prend des données de notes, donne des insights) - plus complexe


@ai_bp.route('/generate-quiz', methods=['POST'])
@jwt_required() # Pourrait être restreint aux professeurs avec un décorateur personnalisé
def generate_quiz_questions_route():
    # Vérifier le rôle si nécessaire
    # current_user_identity = get_jwt_identity()
    # if current_user_identity.get('role') not in ['professeur', 'admin']:
    #     return jsonify({"message": "Accès non autorisé à cette fonctionnalité."}), 403

    data = request.get_json()
    if not data or not data.get('course_content_text'):
        return jsonify({"message": "Le champ 'course_content_text' est requis."}), 400

    content_text = data.get('course_content_text')
    num_questions = data.get('num_questions', 5)
    question_type = data.get('question_type', "choix multiples")
    difficulty = data.get('difficulty', "moyen")

    try:
        num_questions = int(num_questions)
        if num_questions <= 0 or num_questions > 20: # Limiter le nombre de questions
            return jsonify({"message": "Le nombre de questions doit être entre 1 et 20."}), 400
    except ValueError:
        return jsonify({"message": "Le nombre de questions doit être un entier."}), 400

    if not groq_service.client:
         return jsonify({"message": "Service IA non disponible."}), 503

    questions = groq_service.generate_quiz_questions(
        content_text,
        num_questions=num_questions,
        question_type=question_type,
        difficulty=difficulty
    )

    if questions.startswith("Erreur:"):
        return jsonify({"message": "Erreur lors de la génération des questions.", "details": questions}), 500

    return jsonify({"generated_questions": questions}), 200


print("Blueprint pour les fonctionnalités IA (ai_bp) créé.")
