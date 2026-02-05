// frontend/js/student_course_details.js

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('authToken');
    const user = JSON.parse(localStorage.getItem('currentUser'));

    if (!token || !user || user.role !== 'etudiant') {
        alert("Veuillez vous connecter en tant qu'étudiant pour accéder à cette page.");
        window.location.href = '../../login.html'; // Ajuster si nécessaire
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const courseId = urlParams.get('courseId');

    if (!courseId) {
        alert("ID du cours manquant dans l'URL.");
        document.getElementById('courseNameTitle').textContent = "Erreur";
        document.getElementById('courseName').textContent = "Erreur";
        document.getElementById('courseContentAccordion').innerHTML = '<p class="text-center alert-message error">Impossible de charger le cours : ID manquant.</p>';
        return;
    }

    loadCourseDetails(courseId);

    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            window.location.href = '../../index.html';
        });
    }
});

async function fetchApi(url, options = {}) {
    // Fonction fetchApi réutilisée (similaire à etudiant_dashboard.js)
    // Pour un projet plus grand, cette fonction serait dans un module partagé.
    const token = localStorage.getItem('authToken');
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
    options.headers = { ...defaultHeaders, ...options.headers };

    try {
        const response = await fetch(url, options);
        if (response.status === 401) {
            alert("Votre session a expiré. Veuillez vous reconnecter.");
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            window.location.href = '../../login.html';
            return null;
        }
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: "Erreur HTTP." }));
            console.error(`Erreur API ${response.status}: ${errorData.message || response.statusText}`);
            const messageArea = document.getElementById('message-area-course');
            if(messageArea) messageArea.innerHTML = `<div class="alert-message error">Erreur API: ${errorData.message || response.statusText}</div>`;
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error("Erreur de connexion ou parsing:", error);
        const messageArea = document.getElementById('message-area-course');
        if(messageArea) messageArea.innerHTML = `<div class="alert-message error">Erreur de connexion.</div>`;
        return null;
    }
}

async function loadCourseDetails(courseId) {
    const courseNameTitleEl = document.getElementById('courseNameTitle');
    const courseNameEl = document.getElementById('courseName');
    const courseCodeEl = document.getElementById('courseCode');
    const courseDescriptionEl = document.getElementById('courseDescription');
    const courseContentAccordionEl = document.getElementById('courseContentAccordion');

    const courseData = await fetchApi(`/api/student/course/${courseId}/content`);

    if (courseData) {
        courseNameTitleEl.textContent = courseData.titre || "Détails du Cours";
        courseNameEl.textContent = courseData.titre || "N/A";
        courseCodeEl.textContent = courseData.code_cours || "N/A";
        // La description n'est pas dans le retour de /api/student/course/${courseId}/content pour l'instant.
        // Il faudrait l'ajouter à la projection dans la route student_routes.py ou faire un autre appel.
        // Pour l'instant, on la laisse vide ou on la récupère d'une autre manière.
        // courseDescriptionEl.textContent = courseData.description || "Pas de description disponible.";
        // Supposons que la description est récupérée avec /api/student/my/courses et passée ou re-fetchée.
        // Pour cet exemple, nous allons nous concentrer sur le contenu.

        if (courseData.contenu_cours && courseData.contenu_cours.length > 0) {
            courseContentAccordionEl.innerHTML = ''; // Vider le message de chargement
            // Trier les sections par 'ordre' si ce champ existe et est fiable
            const sortedContent = courseData.contenu_cours.sort((a, b) => (a.ordre || 0) - (b.ordre || 0));

            sortedContent.forEach((section, index) => {
                const sectionCard = document.createElement('div');
                sectionCard.className = 'accordion-item dashboard-card'; // Un peu de style

                const sectionHeader = document.createElement('button');
                sectionHeader.className = 'accordion-header';
                sectionHeader.textContent = section.titre_section || `Section ${index + 1}`;
                sectionHeader.onclick = function() {
                    this.classList.toggle('active');
                    const panel = this.nextElementSibling;
                    if (panel.style.display === "block") {
                        panel.style.display = "none";
                    } else {
                        panel.style.display = "block";
                    }
                };

                const sectionPanel = document.createElement('div');
                sectionPanel.className = 'accordion-panel';
                sectionPanel.style.display = "none"; // Caché par défaut

                let panelHTML = `<div class="content-html">${section.contenu_html || '<p>Aucun contenu textuel.</p>'}</div>`;

                if (section.fichiers_joints && section.fichiers_joints.length > 0) {
                    panelHTML += '<h4>Fichiers Joints:</h4><ul>';
                    section.fichiers_joints.forEach(file => {
                        // Supposons que url_stockage est une URL directe ou un identifiant pour un autre endpoint de téléchargement
                        // Pour la démo, on fait un lien direct. En production, ce serait plus sécurisé.
                        panelHTML += `<li><a href="${file.url_stockage}" target="_blank" rel="noopener noreferrer">${file.nom_fichier}</a> (${file.type_fichier})</li>`;
                    });
                    panelHTML += '</ul>';
                }
                sectionPanel.innerHTML = panelHTML;

                sectionCard.appendChild(sectionHeader);
                sectionCard.appendChild(sectionPanel);
                courseContentAccordionEl.appendChild(sectionCard);
            });
        } else {
            courseContentAccordionEl.innerHTML = '<p class="text-center">Aucun contenu disponible pour ce cours.</p>';
        }
    } else {
        courseNameTitleEl.textContent = "Erreur";
        courseNameEl.textContent = "Erreur de chargement";
        if(courseCodeEl) courseCodeEl.textContent = "-";
        courseContentAccordionEl.innerHTML = '<p class="text-center alert-message error">Impossible de charger les détails du cours.</p>';
    }
}

// Ajouter quelques styles CSS pour l'accordéon dans style.css ou ici si spécifique.
// Exemple rapide (à mettre dans style.css idéalement):
/*
.accordion-item { margin-bottom: 10px; }
.accordion-header {
    background-color: #f0f0f0;
    color: #333;
    cursor: pointer;
    padding: 15px;
    width: 100%;
    text-align: left;
    border: none;
    outline: none;
    transition: 0.4s;
    font-size: 1.1rem;
    border-radius: 5px;
}
.accordion-header:hover, .accordion-header.active {
    background-color: #e0e0e0;
}
.accordion-panel {
    padding: 15px;
    background-color: white;
    border: 1px solid #f0f0f0;
    border-top: none;
    border-radius: 0 0 5px 5px;
}
.accordion-panel .content-html img { max-width: 100%; height: auto; }
*/

// --- Chatbot Logic ---
let fullCourseTextContext = ""; // Variable globale pour stocker le contexte du cours

async function initializeChatbot(courseId) {
    const chatbotSendButton = document.getElementById('chatbotSendButton');
    const chatbotInput = document.getElementById('chatbotInput');

    // Récupérer le contenu complet du cours pour le contexte du chatbot
    // On le fait une fois au chargement pour ne pas le re-récupérer à chaque question.
    // La fonction loadCourseDetails est déjà appelée, mais elle peuple l'accordéon.
    // On a besoin du texte brut concaténé.
    // Cette logique pourrait être intégrée dans loadCourseDetails ou appelée séparément.
    const courseDataForContext = await fetchApi(`/api/student/course/${courseId}/content`);
    if (courseDataForContext && courseDataForContext.contenu_cours) {
        fullCourseTextContext = courseDataForContext.contenu_cours.map(section => {
            // Nettoyer un peu le HTML pour un meilleur contexte, ou extraire le texte.
            // Pour une version simple, on prend le HTML tel quel.
            // Une meilleure approche serait d'extraire le texte pur.
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = section.contenu_html || "";
            return `Titre Section: ${section.titre_section}\nContenu:\n${tempDiv.textContent || tempDiv.innerText || ""}\n`;
        }).join("\n\n---\n\n");
    } else {
        addMessageToChatbox("Désolé, je n'ai pas pu charger le contenu du cours pour répondre à vos questions.", "bot-error");
        chatbotInput.disabled = true;
        chatbotSendButton.disabled = true;
    }

    if (chatbotSendButton && chatbotInput) {
        chatbotSendButton.addEventListener('click', handleChatbotQuery);
        chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleChatbotQuery();
            }
        });
    }
}

async function handleChatbotQuery() {
    const chatbotInput = document.getElementById('chatbotInput');
    const question = chatbotInput.value.trim();
    if (!question) return;

    addMessageToChatbox(question, "user-message");
    chatbotInput.value = '';
    document.getElementById('chatbotLoading').style.display = 'block';

    if (!fullCourseTextContext) {
        addMessageToChatbox("Le contexte du cours n'est pas disponible.", "bot-error");
        document.getElementById('chatbotLoading').style.display = 'none';
        return;
    }

    const response = await fetchApi('/api/ai/ask-contextual', {
        method: 'POST',
        body: JSON.stringify({
            text_context: fullCourseTextContext,
            question: question
        })
    });

    document.getElementById('chatbotLoading').style.display = 'none';
    if (response && response.answer) {
        addMessageToChatbox(response.answer, "bot-message");
    } else {
        addMessageToChatbox("Désolé, je n'ai pas pu obtenir de réponse pour le moment.", "bot-error");
    }
}

function addMessageToChatbox(message, type) { // type: "user-message", "bot-message", "bot-error"
    const messagesDiv = document.getElementById('chatbotMessages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(type); // Ajouter des styles CSS pour ces classes
    messageDiv.textContent = message;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll vers le bas
}

// Modifier l'appel initial dans DOMContentLoaded pour inclure l'initialisation du chatbot
document.addEventListener('DOMContentLoaded', () => {
    // ... (code existant pour token, user, courseId, loadCourseDetails, logoutButton) ...
    const token = localStorage.getItem('authToken');
    const user = JSON.parse(localStorage.getItem('currentUser'));

    if (!token || !user || user.role !== 'etudiant') {
        alert("Veuillez vous connecter en tant qu'étudiant pour accéder à cette page.");
        window.location.href = '../../login.html';
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const courseId = urlParams.get('courseId');

    if (!courseId) {
        alert("ID du cours manquant dans l'URL.");
        // ... (gestion d'erreur existante) ...
        return;
    }

    loadCourseDetails(courseId);
    initializeChatbot(courseId); // Initialiser le chatbot après avoir chargé les détails du cours (ou en parallèle)

    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        // ... (code existant pour logout) ...
    }
});


console.log("Script student_course_details.js chargé et mis à jour pour chatbot.");
