# backend/app/services/email_service.py
from flask_mail import Message
from backend.app import mail # L'instance Mail initialisée dans __init__.py
from flask import current_app # Pour accéder à app.config
import threading # Pour envoyer les emails en arrière-plan

def send_async_email(app, msg):
    """Fonction pour envoyer l'email dans un thread séparé."""
    with app.app_context(): # Nécessaire pour accéder à la configuration de l'app dans le thread
        try:
            mail.send(msg)
            app.logger.info(f"Email envoyé avec succès à {msg.recipients}")
        except Exception as e:
            app.logger.error(f"Erreur lors de l'envoi de l'email à {msg.recipients}: {e}")


class EmailService:
    @staticmethod
    def send_email(subject, recipients, text_body, html_body=None, sender=None, attachments=None):
        """
        Envoie un email.
        :param subject: Sujet de l'email.
        :param recipients: Liste des adresses email des destinataires.
        :param text_body: Corps de l'email en texte brut.
        :param html_body: Corps de l'email en HTML (optionnel).
        :param sender: Adresse email de l'expéditeur (utilise MAIL_DEFAULT_SENDER si None).
        :param attachments: Liste de tuples (nom_fichier, content_type, données) pour les pièces jointes.
        """
        if not isinstance(recipients, list):
            recipients = [recipients] # S'assurer que c'est une liste

        # Utiliser l'expéditeur par défaut de la configuration si non spécifié
        if sender is None:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')

        # Vérifier si l'envoi d'emails est désactivé (pour tests/dev)
        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            current_app.logger.info(f"Envoi d'email supprimé (MAIL_SUPPRESS_SEND=True). Sujet: {subject}, Destinataires: {recipients}")
            return True # Simuler un envoi réussi

        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        if html_body:
            msg.html = html_body

        if attachments:
            for attachment in attachments:
                try:
                    # S'attendre à ce que chaque attachment soit un objet avec les attributs filename, content_type, data
                    # ou un tuple (filename, content_type, data)
                    if isinstance(attachment, tuple) and len(attachment) == 3:
                        msg.attach(filename=attachment[0], content_type=attachment[1], data=attachment[2])
                    elif hasattr(attachment, 'filename') and hasattr(attachment, 'content_type') and hasattr(attachment, 'data'):
                         msg.attach(filename=attachment.filename, content_type=attachment.content_type, data=attachment.data)
                    else:
                        current_app.logger.warning(f"Format de pièce jointe non reconnu: {attachment}")
                except Exception as e:
                    current_app.logger.error(f"Erreur lors de l'ajout de la pièce jointe {attachment}: {e}")


        # Envoyer l'email de manière asynchrone pour ne pas bloquer la requête principale
        # current_app._get_current_object() est utilisé pour passer l'objet app actuel au thread
        thread = threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg))
        thread.start()
        current_app.logger.info(f"Email pour '{subject}' mis en file d'attente pour envoi à {recipients}.")
        return True # Indique que la tâche d'envoi a été démarrée

    @staticmethod
    def send_registration_email(user_email, user_name):
        """ Envoie un email de bienvenue lors de l'inscription. """
        subject = "Bienvenue à l'Application de Gestion Universitaire !"
        text_body = f"""Bonjour {user_name},

Bienvenue et merci de vous être inscrit à notre application de gestion universitaire.
Nous espérons que vous trouverez cet outil utile.

Cordialement,
L'équipe de l'Application Universitaire
"""
        html_body = f"""
        <html>
            <body>
                <p>Bonjour <strong>{user_name}</strong>,</p>
                <p>Bienvenue et merci de vous être inscrit à notre application de gestion universitaire.</p>
                <p>Nous espérons que vous trouverez cet outil utile.</p>
                <p>Cordialement,<br>
                L'équipe de l'Application Universitaire</p>
            </body>
        </html>
        """
        return EmailService.send_email(subject, [user_email], text_body, html_body)

    @staticmethod
    def send_new_grade_notification(student_email, student_name, course_name, grade_value):
        """ Notifie un étudiant d'une nouvelle note. """
        subject = f"Nouvelle note publiée pour le cours: {course_name}"
        text_body = f"""Bonjour {student_name},

Une nouvelle note a été publiée pour votre cours '{course_name}'.
Votre note est : {grade_value}.

Vous pouvez consulter vos notes sur le portail étudiant.

Cordialement,
Le Service Pédagogique
"""
        html_body = f"""
        <html>
            <body>
                <p>Bonjour <strong>{student_name}</strong>,</p>
                <p>Une nouvelle note a été publiée pour votre cours <strong>{course_name}</strong>.</p>
                <p>Votre note est : <strong>{grade_value}</strong>.</p>
                <p>Vous pouvez consulter vos notes sur le portail étudiant.</p>
                <p>Cordialement,<br>
                Le Service Pédagogique</p>
            </body>
        </html>
        """
        return EmailService.send_email(subject, [student_email], text_body, html_body)

    # D'autres méthodes pour des types spécifiques de notifications peuvent être ajoutées ici
    # ex: send_new_message_notification, send_course_update_notification, etc.

print("Service Email (EmailService) défini.")
