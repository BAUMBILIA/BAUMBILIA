// frontend/js/auth.js
console.log("Script d'authentification chargé.");

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const loginMessage = document.getElementById('login-message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const messageDiv = loginMessage;

            messageDiv.style.display = 'none';
            messageDiv.textContent = '';
            messageDiv.className = 'message'; // Reset classes

            console.log("Tentative de connexion avec:", { email, password });

            try {
                // Remplacer par l'URL réelle de l'API de connexion
                const response = await fetch('/api/auth/login', { // Endpoint API à définir dans Flask
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    messageDiv.textContent = 'Connexion réussie ! Redirection...';
                    messageDiv.classList.add('success'); // Supposons une classe CSS pour le succès
                    messageDiv.style.display = 'block';
                    console.log("Connexion réussie:", data);
                    // Stocker le token (ex: localStorage)
                    // localStorage.setItem('authToken', data.access_token);
                    // Rediriger vers le tableau de bord approprié en fonction du rôle de l'utilisateur
                    // window.location.href = determineDashboardUrl(data.user.role);
                    // Exemple : window.location.href = '/dashboard.html';
                } else {
                    messageDiv.textContent = data.message || "Erreur de connexion. Vérifiez vos identifiants.";
                    messageDiv.classList.add('error'); // Supposons une classe CSS pour l'erreur
                    messageDiv.style.display = 'block';
                    console.error("Erreur de connexion:", data);
                }
            } catch (error) {
                messageDiv.textContent = "Une erreur réseau est survenue. Veuillez réessayer.";
                messageDiv.classList.add('error');
                messageDiv.style.display = 'block';
                console.error("Erreur réseau ou autre lors de la connexion:", error);
            }
        });
    }

    // Fonction pour déterminer l'URL du tableau de bord (à implémenter)
    // function determineDashboardUrl(role) {
    //     if (role === 'etudiant') return 'etudiant/dashboard.html';
    //     if (role === 'professeur') return 'professeur/dashboard.html';
    //     if (role === 'admin') return 'admin/dashboard.html';
    //     return '../index.html'; // Fallback
    // }
});
