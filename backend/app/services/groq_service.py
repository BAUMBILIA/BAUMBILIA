# backend/app/services/groq_service.py
import os
from groq import Groq
from backend.config import AppConfig # Pour accéder à GROQ_API_KEY

class GroqService:
    def __init__(self):
        self.api_key = AppConfig.GROQ_API_KEY
        if not self.api_key:
            print("Avertissement: Clé API Groq (GROQ_API_KEY) non configurée. Le service Groq ne fonctionnera pas.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

    def generate_chat_completion(self, messages, model="mixtral-8x7b-32768", temperature=0.7, max_tokens=1024):
        """
        Génère une réponse à partir d'une liste de messages en utilisant l'API Groq.
        :param messages: Liste de dictionnaires, ex: [{"role": "user", "content": "Explique la relativité."}]
        :param model: Le modèle à utiliser (par défaut: mixtral-8x7b-32768).
        :param temperature: Contrôle l'aléatoire de la sortie.
        :param max_tokens: Nombre maximum de tokens à générer.
        :return: Le contenu de la réponse de l'assistant, ou None en cas d'erreur.
        """
        if not self.client:
            return "Erreur: Client Groq non initialisé (clé API manquante)."

        try:
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                # top_p=1, # Optionnel
                # stop=None, # Optionnel
                # stream=False, # Optionnel
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Erreur lors de l'appel à l'API Groq: {e}")
            return f"Erreur lors de la communication avec le service IA: {str(e)}"

    def summarize_text(self, text_to_summarize, model="mixtral-8x7b-32768", max_length_summary="environ 150 mots"):
        """
        Demande à Groq de résumer un texte donné.
        :param text_to_summarize: Le texte à résumer.
        :param model: Modèle à utiliser.
        :param max_length_summary: Indication de la longueur souhaitée pour le résumé.
        :return: Le résumé généré ou un message d'erreur.
        """
        if not self.client:
            return "Erreur: Client Groq non initialisé."

        prompt_messages = [
            {
                "role": "system",
                "content": f"Tu es un assistant expert en résumé de texte. Résume le texte suivant de manière concise, en respectant une longueur d'{max_length_summary}."
            },
            {
                "role": "user",
                "content": f"Voici le texte à résumer :\n\n---\n{text_to_summarize}\n---"
            }
        ]
        return self.generate_chat_completion(prompt_messages, model=model, max_tokens=512) # Augmenter max_tokens si besoin pour le résumé

    def answer_question_about_text(self, text_context, question, model="mixtral-8x7b-32768"):
        """
        Demande à Groq de répondre à une question basée sur un texte de contexte.
        :param text_context: Le texte fournissant le contexte.
        :param question: La question à poser.
        :param model: Modèle à utiliser.
        :return: La réponse générée ou un message d'erreur.
        """
        if not self.client:
            return "Erreur: Client Groq non initialisé."

        prompt_messages = [
            {
                "role": "system",
                "content": "Tu es un assistant IA capable de répondre à des questions en te basant uniquement sur le texte de contexte fourni. Si la réponse n'est pas dans le texte, indique-le clairement."
            },
            {
                "role": "user",
                "content": f"Contexte:\n---\n{text_context}\n---\n\nQuestion: {question}"
            }
        ]
        return self.generate_chat_completion(prompt_messages, model=model, max_tokens=512)

    def generate_quiz_questions(self, course_content_text, num_questions=5, question_type="choix multiples", difficulty="moyen"):
        """
        Génère des questions de quiz/examen basées sur le contenu d'un cours.
        :param course_content_text: Le texte du contenu du cours.
        :param num_questions: Nombre de questions à générer.
        :param question_type: Type de questions (ex: "choix multiples", "vrai/faux", "réponse courte").
        :param difficulty: Difficulté des questions (ex: "facile", "moyen", "difficile").
        :return: Les questions générées ou un message d'erreur.
        """
        if not self.client:
            return "Erreur: Client Groq non initialisé."

        prompt_messages = [
            {
                "role": "system",
                "content": f"Tu es un assistant expert en création de matériel pédagogique. En te basant STRICTEMENT sur le contenu de cours fourni, génère {num_questions} questions de type '{question_type}' de difficulté '{difficulty}'. "
                           f"Pour les questions à choix multiples, fournis 4 options (A, B, C, D) et indique clairement la bonne réponse (par exemple, en la marquant avec '*'). "
                           f"Pour les questions vrai/faux, indique la bonne réponse. Pour les réponses courtes, fournis une réponse type concise. "
                           f"Assure-toi que les questions ne portent que sur les informations présentes dans le texte fourni."
            },
            {
                "role": "user",
                "content": f"Contenu du cours:\n---\n{course_content_text}\n---\n\nGénère les questions."
            }
        ]
        # Augmenter max_tokens si on attend beaucoup de questions ou des questions longues
        return self.generate_chat_completion(prompt_messages, model="mixtral-8x7b-32768", max_tokens=2048)


# Exemple d'utilisation (pourrait être dans une route)
if __name__ == '__main__':
    # Nécessite que GROQ_API_KEY soit dans l'environnement ou .env
    # Charger les variables d'environnement si on exécute ce fichier directement pour test
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../.env')) # Ajuster le chemin vers .env

    # Ré-importer AppConfig après load_dotenv si GROQ_API_KEY vient de .env
    # Ceci est un peu maladroit pour un test direct, mieux vaut tester via une route Flask.
    # from backend.config import AppConfig as TestAppConfig
    # AppConfig.GROQ_API_KEY = TestAppConfig.GROQ_API_KEY # S'assurer qu'il est rechargé

    # Pour que ce test fonctionne, il faut que GROQ_API_KEY soit disponible
    # au moment de l'instanciation de GroqService.
    # Si AppConfig.GROQ_API_KEY est None au démarrage, le client ne sera pas créé.
    # Il faudrait s'assurer que la config est chargée AVANT l'import de GroqService dans les routes.

    print(f"Clé API Groq pour le test direct: {AppConfig.GROQ_API_KEY}")
    groq_service = GroqService()

    if groq_service.client:
        sample_text = """L'intelligence artificielle (IA) est un domaine de l'informatique qui vise à créer des machines capables de simuler l'intelligence humaine.
        Elle englobe diverses sous-disciplines telles que l'apprentissage automatique (machine learning), le traitement du langage naturel (NLP) et la vision par ordinateur.
        Les applications de l'IA sont nombreuses et touchent des secteurs variés comme la santé, la finance, les transports et l'éducation."""

        print("\n--- Test de Résumé ---")
        summary = groq_service.summarize_text(sample_text)
        print(f"Résumé: {summary}")

        print("\n--- Test de Question/Réponse ---")
        question = "Quelles sont les sous-disciplines de l'IA mentionnées ?"
        answer = groq_service.answer_question_about_text(sample_text, question)
        print(f"Question: {question}")
        print(f"Réponse: {answer}")

        question_hors_contexte = "Quelle est la capitale de la France ?"
        answer_hors_contexte = groq_service.answer_question_about_text(sample_text, question_hors_contexte)
        print(f"Question: {question_hors_contexte}")
        print(f"Réponse: {answer_hors_contexte}")

    else:
        print("Client Groq non initialisé. Vérifiez la clé API et la configuration.")

print("Service Groq (GroqService) défini.")
