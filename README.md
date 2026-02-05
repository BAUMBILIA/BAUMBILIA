# Gestion Universitaire

Application de gestion universitaire pour les étudiants, professeurs et administrateurs.

## Fonctionnalités Prévues

*   Gestion des notes
*   Tableaux de bord personnalisés (étudiants, professeurs, admin)
*   Publication de cours par les professeurs
*   Messagerie interne
*   Intégration IA (Groq) pour fonctionnalités avancées
*   Notifications par email

## Technologies

*   **Backend:** Python (Flask)
*   **Frontend:** HTML, CSS, JavaScript
*   **Base de données:** MongoDB

## Structure du Projet

```
gestion_universitaire/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── css/
│   ├── js/
│   ├── html/
│   │   ├── admin/
│   │   ├── professeur/
│   │   └── etudiant/
│   └── assets/
├── database/
├── .gitignore
└── README.md
```

## Installation et Lancement (Instructions à venir)

---

## Guide Utilisateur de Base

L'application de gestion universitaire offre différentes fonctionnalités selon votre rôle.

### 1. Connexion
- Tous les utilisateurs accèdent à l'application via la page de **Connexion**.
- Entrez votre email et mot de passe fournis par l'administration (ou créés lors de l'inscription).

### 2. Tableau de Bord Étudiant
Une fois connecté en tant qu'étudiant :
- **Mes Notes :** Consultez vos notes par cours, semestre et année académique. Un graphique peut montrer l'évolution de vos moyennes.
- **Mes Cours :** Visualisez la liste des cours auxquels vous êtes inscrit. Accédez au contenu détaillé de chaque cours (sections, fichiers).
- **Chatbot de Cours :** Sur la page de détails d'un cours, vous pouvez poser des questions sur le contenu du cours à un assistant IA.
- **Messagerie :** (Fonctionnalité à venir) Envoyez et recevez des messages de vos professeurs ou de l'administration.

### 3. Tableau de Bord Professeur
Une fois connecté en tant que professeur :
- **Mes Cours :** Visualisez les cours que vous enseignez.
- **Gestion des Notes :**
    - Sélectionnez un de vos cours pour voir la liste des étudiants inscrits.
    - Cliquez sur un étudiant pour saisir ou modifier sa note pour différentes évaluations (examen, contrôle continu, etc.).
    - Visualisez une distribution des notes pour un cours.
- **Gestion du Contenu des Cours :**
    - Sélectionnez un de vos cours.
    - Ajoutez, modifiez ou supprimez des sections de contenu (textes, descriptions).
    - Associez des fichiers (PDF, vidéos, etc.) à chaque section (via URL pour l'instant).
    - Utilisez l'assistant IA pour générer des suggestions de questions de quiz basées sur le contenu de votre cours.
- **Messagerie :** (Fonctionnalité à venir) Communiquez avec vos étudiants ou l'administration.

### 4. Tableau de Bord Administrateur
Une fois connecté en tant qu'administrateur :
- **Gestion des Utilisateurs :**
    - Créez, listez, modifiez (informations, rôle, statut actif/inactif) et désactivez des comptes utilisateurs (étudiants, professeurs, autres admins).
- **Gestion des Filières :**
    - Créez, listez, modifiez et supprimez des filières d'études.
    - Assignez un professeur responsable à chaque filière.
- **Gestion des Cours :**
    - Créez, listez, modifiez et supprimez des cours.
    - Associez des cours à une ou plusieurs filières et assignez un professeur principal.
- **Gestion des Inscriptions :**
    - Inscrivez ou désinscrivez manuellement des étudiants à des cours spécifiques pour une année académique et un semestre donnés.
- **Statistiques :** Visualisez des graphiques, comme le nombre d'étudiants inscrits par filière.

### Fonctionnalités Communes (Prévues ou en cours)
- **Messagerie Interne :** Un système pour envoyer et recevoir des messages entre utilisateurs.
- **Notifications :** Recevez des notifications (par email pour l'instant) pour les événements importants (nouvelle note, nouveau message, etc.).

---

*Ce projet est en cours de développement.*
