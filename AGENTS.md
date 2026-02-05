# Instructions pour l'Agent de Développement IA

## Général

*   **Langage Principal du Backend:** Python avec Flask.
*   **Langage Principal du Frontend:** HTML, CSS, JavaScript (pas de framework JS majeur spécifié pour l'instant, donc Vanilla JS ou petites bibliothèques).
*   **Base de Données:** MongoDB.
*   **Objectif du Projet:** Créer une application de gestion universitaire complète.
*   **Fonctionnalités Clés:** Gestion des notes, publication de cours, messagerie, dashboards par rôle, intégration IA avec Groq.

## Conventions de Code

*   **Python (Backend):**
    *   Suivre PEP 8.
    *   Utiliser des Blueprints pour organiser les routes.
    *   Séparer la logique métier dans des `services`.
    *   Les modèles MongoDB peuvent être gérés avec PyMongo directement ou via une surcouche simple (pas d'ODM complexe comme MongoEngine requis pour l'instant, sauf si cela devient nécessaire).
    *   Commenter clairement le code, en particulier les fonctions et la logique complexe.
*   **JavaScript (Frontend):**
    *   Utiliser JavaScript moderne (ES6+).
    *   Organiser le code en modules si l'application devient complexe.
    *   Commenter le code.
    *   Les appels API doivent être gérés proprement avec `fetch` et la gestion des erreurs.
*   **HTML/CSS:**
    *   HTML sémantique.
    *   CSS bien structuré (ex: BEM ou une autre méthodologie simple si l'application grandit).
    *   Maintenir la responsivité à l'esprit.

## Tests

*   Viser une bonne couverture de test pour le backend (tests unitaires et d'intégration).
*   Les tests frontend peuvent être plus basiques au début, mais s'assurer que les fonctionnalités clés sont testables.

## Intégration Groq

*   L'API Key pour Groq doit être gérée via les variables d'environnement (`GROQ_API_KEY` dans `backend/config.py`).
*   Les interactions avec Groq doivent être encapsulées dans un module de service (ex: `backend/app/services/groq_service.py`).

## Soumission et Planification

*   Suivre le plan fourni. Si des modifications sont nécessaires, mettre à jour le plan et informer l'utilisateur.
*   Soumettre le code avec des messages de commit clairs et descriptifs.

## Priorités Actuelles (basées sur le plan)

1.  Mise en place de la structure du projet.
2.  Définition des modèles de données MongoDB.
3.  Développement du backend (Authentification en premier).

## Communication

*   Poser des questions si les exigences ne sont pas claires.
*   Fournir des mises à jour régulières sur l'avancement.

---
*Ce document peut être mis à jour au fur et à mesure de l'évolution du projet.*
