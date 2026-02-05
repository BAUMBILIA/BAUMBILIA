# Documentation de l'API de Gestion Universitaire

Ce document décrit les principales routes de l'API backend.

**URL de Base de l'API :** `/api`

## Authentification (`/api/auth`)

-   **`POST /register`**
    -   Description : Inscrit un nouvel utilisateur.
    -   Permissions : Ouvert (ou admin seulement en production stricte pour le premier admin).
    -   Body (JSON) : `email`, `password`, `nom`, `prenom`, `role` ('etudiant', 'professeur', 'admin'), et champs spécifiques au rôle (ex: `matricule` pour étudiant).
    -   Réponse : `201 Created` avec `user_id`, `email`, `role`. `400 Bad Request`, `409 Conflict`.

-   **`POST /login`**
    -   Description : Connecte un utilisateur existant.
    -   Body (JSON) : `email`, `password`.
    -   Réponse : `200 OK` avec `access_token`, `refresh_token`, détails utilisateur. `401 Unauthorized`.

-   **`POST /refresh`**
    -   Description : Rafraîchit un token d'accès en utilisant un refresh token.
    -   Header : `Authorization: Bearer <refresh_token>`
    -   Réponse : `200 OK` avec nouveau `access_token`.

-   **`GET /protected`** (Exemple)
    -   Description : Route de test pour vérifier un token JWT.
    -   Header : `Authorization: Bearer <access_token>`
    -   Réponse : `200 OK` avec les détails de l'utilisateur du token.

## Étudiants (`/api/student`) - Routes protégées (Étudiant)

-   **`GET /my/grades`**
    -   Description : Récupère les notes de l'étudiant connecté.
    -   Query Params (optionnels) : `annee_academique`, `semestre`, `cours_id`.
    -   Réponse : `200 OK` avec liste des notes (détails du cours inclus).

-   **`GET /my/courses`**
    -   Description : Récupère les cours auxquels l'étudiant est inscrit.
    -   Réponse : `200 OK` avec liste des cours (détails de l'inscription inclus).

-   **`GET /course/<course_id>/content`**
    -   Description : Récupère le contenu d'un cours spécifique auquel l'étudiant est inscrit.
    -   Réponse : `200 OK` avec titre, code et contenu du cours.

## Professeurs (`/api/professor`) - Routes protégées (Professeur)

-   **`GET /courses`**
    -   Description : Récupère les cours enseignés par le professeur connecté.
    -   Réponse : `200 OK` avec liste des cours.

-   **`GET /course/<course_id>/students`**
    -   Description : Récupère les étudiants inscrits à un cours du professeur.
    -   Réponse : `200 OK` avec liste des étudiants.

-   **`POST /grade`**
    -   Description : Ajoute ou met à jour la note d'un étudiant pour un cours.
    -   Body (JSON) : `etudiant_id`, `cours_id`, `note_valeur`, `annee_academique`, `semestre`, `type_evaluation` (optionnel), `bareme_max` (optionnel), `commentaires_professeur` (optionnel), `visible_etudiant` (boolean).
    -   Réponse : `201 Created` ou `200 OK` avec `grade_id`.

-   **`GET /course/<course_id>/grades`**
    -   Description : Récupère toutes les notes pour un cours spécifique du professeur.
    -   Réponse : `200 OK` avec liste des notes (détails étudiant inclus).

-   **`GET /course/<course_id>/details`**
    -   Description : Récupère les détails complets d'un cours du professeur (incluant contenu).
    -   Réponse : `200 OK` avec les détails du cours.

-   **`POST /course/<course_id>/content`**
    -   Description : Ajoute une section de contenu à un cours.
    -   Body (JSON) : `titre_section`, `contenu_html` (optionnel), `ordre` (optionnel), `fichiers_joints` (liste d'objets fichier, optionnel).
    -   Réponse : `201 Created` avec `section_id`.

-   **`PUT /course/<course_id>/content/<section_id>`**
    -   Description : Met à jour une section de contenu.
    -   Body (JSON) : Champs à mettre à jour (`titre_section`, `contenu_html`, etc.).
    -   Réponse : `200 OK`.

-   **`DELETE /course/<course_id>/content/<section_id>`**
    -   Description : Supprime une section de contenu.
    -   Réponse : `200 OK`.

## Administration (`/api/admin`) - Routes protégées (Admin)

### Utilisateurs
-   **`POST /users`** : Crée un utilisateur.
-   **`GET /users`** : Liste les utilisateurs (filtres: `role`, `actif`).
-   **`GET /users/<user_id>`** : Récupère un utilisateur.
-   **`PUT /users/<user_id>`** : Met à jour un utilisateur.
-   **`DELETE /users/<user_id>`** : Désactive un utilisateur.

### Filières (Programs)
-   **`POST /programs`** : Crée une filière.
-   **`GET /programs`** : Liste les filières.
-   **`GET /programs/<program_id>`** : Récupère une filière.
-   **`PUT /programs/<program_id>`** : Met à jour une filière.
-   **`DELETE /programs/<program_id>`** : Supprime une filière (avec vérification de dépendances).

### Cours (Courses)
-   **`POST /courses`** : Crée un cours.
-   **`GET /courses`** : Liste les cours.
-   **`GET /courses/<course_id>`** : Récupère un cours.
-   **`PUT /courses/<course_id>`** : Met à jour un cours.
-   **`DELETE /courses/<course_id>`** : Supprime un cours (avec vérification de dépendances).

### Inscriptions
-   **`POST /enrollments`**
    -   Description : Inscrit un étudiant à un cours.
    -   Body (JSON) : `etudiant_id`, `cours_id`, `annee_academique`, `semestre`.
    -   Réponse : `200 OK`.
-   **`DELETE /enrollments/student/<etudiant_id>/course/<cours_id>`**
    -   Description : Désinscrit un étudiant d'un cours pour une période donnée.
    -   Query Params : `annee_academique`, `semestre` (requis).
    -   Réponse : `200 OK`.

## Messagerie (`/api/messages`) - Routes protégées (Tout utilisateur authentifié)

-   **`POST /send`**
    -   Description : Envoie un message.
    -   Body (JSON) : `destinataire_ids` (liste), `sujet`, `corps_message`, `pieces_jointes` (optionnel), `conversation_id` (optionnel).
    -   Réponse : `201 Created` avec `message_id`.

-   **`GET /inbox`**
    -   Description : Récupère la boîte de réception.
    -   Query Params (optionnels) : `page`, `per_page`.
    -   Réponse : `200 OK` avec liste paginée de messages.

-   **`GET /sent`**
    -   Description : Récupère les messages envoyés.
    -   Query Params (optionnels) : `page`, `per_page`.
    -   Réponse : `200 OK` avec liste paginée de messages.

-   **`POST /<message_id>/read`**
    -   Description : Marque un message comme lu.
    -   Réponse : `200 OK`.

## Intelligence Artificielle (`/api/ai`) - Routes protégées

-   **`POST /summarize`**
    -   Description : Résume un texte.
    -   Body (JSON) : `text`, `max_length` (optionnel).
    -   Réponse : `200 OK` avec `summary`.

-   **`POST /ask-contextual`**
    -   Description : Pose une question sur un texte de contexte.
    -   Body (JSON) : `text_context`, `question`.
    -   Réponse : `200 OK` avec `answer`.

-   **`POST /chat`**
    -   Description : Interaction de chat générique.
    -   Body (JSON) : `messages` (liste d'objets `{"role": "...", "content": "..."}`), `model` (optionnel), `temperature` (optionnel), `max_tokens` (optionnel).
    -   Réponse : `200 OK` avec `response` (contenu du message de l'assistant).

-   **`POST /generate-quiz`**
    -   Description : Génère des questions de quiz à partir d'un contenu de cours.
    -   Body (JSON) : `course_content_text`, `num_questions` (optionnel), `question_type` (optionnel), `difficulty` (optionnel).
    -   Réponse : `200 OK` avec `generated_questions`.

---
*Note : Toutes les routes protégées nécessitent un token JWT valide dans le header `Authorization: Bearer <token>`.*
*Les réponses d'erreur typiques incluent `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`, `503 Service Unavailable` (pour les services externes comme Groq).*
