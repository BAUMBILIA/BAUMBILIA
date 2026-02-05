// frontend/js/main.js

console.log("JavaScript principal chargé.");

document.addEventListener('DOMContentLoaded', () => {
    // Code à exécuter une fois que le DOM est complètement chargé
    // Par exemple, gestionnaires d'événements pour la navigation,
    // appels AJAX pour charger des données dynamiquement, etc.

    const loginLink = document.querySelector('nav a[href="html/login.html"]');
    if (loginLink) {
        loginLink.addEventListener('click', (event) => {
            // Potentiellement, charger le contenu de login.html dynamiquement
            // ou simplement naviguer. Pour l'instant, c'est une navigation standard.
            console.log("Clic sur le lien de connexion.");
        });
    }
});

// Fonctions utilitaires globales pour le frontend (exemples)
function displayMessage(message, type = 'info') {
    // Crée un élément pour afficher un message à l'utilisateur
    const messageArea = document.getElementById('message-area'); // Supposons qu'un tel élément existe
    if (messageArea) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`; // ex: message info, message error
        messageDiv.textContent = message;
        messageArea.appendChild(messageDiv);
        setTimeout(() => messageDiv.remove(), 5000); // Le message disparaît après 5s
    } else {
        console.warn("Zone de message non trouvée. Message:", message);
        alert(message); // Fallback
    }
}

// Plus de code sera ajouté ici pour interagir avec le backend,
// gérer l'interface utilisateur, etc.
