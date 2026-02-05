// frontend/js/etudiant_dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si l'utilisateur est connecté et a le bon rôle (déjà géré dans main.js ou à renforcer ici)
    const token = localStorage.getItem('authToken');
    const user = JSON.parse(localStorage.getItem('currentUser'));

    if (!token || !user || user.role !== 'etudiant') {
        // Rediriger vers la page de connexion si non authentifié ou rôle incorrect
        // window.location.href = '../login.html'; // Assurez-vous que ce chemin est correct
        console.error("Accès non autorisé ou informations utilisateur manquantes.");
        alert("Veuillez vous connecter en tant qu'étudiant pour accéder à cette page.");
        // Idéalement, la redirection se fait avant même le chargement de cette page via un script global.
        // Pour l'instant, on bloque la suite.
        return;
    }

    // Afficher les informations de l'étudiant
    document.getElementById('studentName').textContent = `${user.prenom} ${user.nom}`;
    // Des appels API supplémentaires pourraient être nécessaires pour matricule, filière, niveau si non stockés dans 'currentUser'
    // Pour l'instant, on suppose qu'ils sont là ou on les charge.
    // Exemple: document.getElementById('studentMatricule').textContent = user.matricule || 'N/A';
    // Exemple: document.getElementById('studentFiliere').textContent = user.filiere_nom || 'N/A';
    // Exemple: document.getElementById('studentNiveau').textContent = user.niveau || 'N/A';
    // Ces infos seraient typiquement récupérées via un endpoint /api/student/my/profile

    loadStudentGrades();
    loadStudentCourses();
    // loadRecentMessages(); // Fonction à implémenter

    const applyGradeFiltersButton = document.getElementById('applyGradeFilters');
    if(applyGradeFiltersButton) {
        applyGradeFiltersButton.addEventListener('click', loadStudentGrades);
    }

    // Gestion de la déconnexion (déjà dans main.js, mais peut être rappelé ici si besoin)
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            window.location.href = '../../index.html'; // Ajuster le chemin si nécessaire
        });
    }
});

async function fetchApi(url, options = {}) {
    const token = localStorage.getItem('authToken');
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
    options.headers = { ...defaultHeaders, ...options.headers };

    try {
        const response = await fetch(url, options);
        if (response.status === 401) { // Non autorisé (token expiré?)
            alert("Votre session a expiré. Veuillez vous reconnecter.");
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            window.location.href = '../../login.html'; // Ajuster
            return null; // ou throw new Error("Unauthorized");
        }
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: "Erreur HTTP sans détails JSON." }));
            console.error(`Erreur API ${response.status}: ${errorData.message || response.statusText}`);
            // Afficher un message à l'utilisateur si possible (ex: dans #message-area-global)
            const globalMessageArea = document.getElementById('message-area-global');
            if(globalMessageArea) globalMessageArea.innerHTML = `<div class="alert-message error">Erreur API: ${errorData.message || response.statusText}</div>`;
            return null; // ou throw new Error(errorData.message || response.statusText);
        }
        return await response.json();
    } catch (error) {
        console.error("Erreur de connexion ou de parsing JSON:", error);
        const globalMessageArea = document.getElementById('message-area-global');
        if(globalMessageArea) globalMessageArea.innerHTML = `<div class="alert-message error">Erreur de connexion au serveur.</div>`;
        return null; // ou throw error;
    }
}


async function loadStudentGrades() {
    const tableBody = document.getElementById('studentGradesTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="8" class="text-center">Chargement des notes...</td></tr>';

    const anneeFilter = document.getElementById('filterAnneeNotes').value;
    const semestreFilter = document.getElementById('filterSemestreNotes').value;

    let apiUrl = '/api/student/my/grades?';
    if (anneeFilter) apiUrl += `annee_academique=${encodeURIComponent(anneeFilter)}&`;
    if (semestreFilter) apiUrl += `semestre=${encodeURIComponent(semestreFilter)}&`;

    const gradesData = await fetchApi(apiUrl);

    if (gradesData && Array.isArray(gradesData)) {
        if (gradesData.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="text-center">Aucune note trouvée pour les filtres sélectionnés.</td></tr>';
            updateGradesChart([]);
            document.getElementById('moyenneGenerale').textContent = 'N/A';
            return;
        }

        tableBody.innerHTML = ''; // Vider le contenu précédent
        let totalPoints = 0;
        let totalCoeffs = 0; // Ou nombre de notes si pas de coeffs
        const anneeSet = new Set();

        gradesData.forEach(grade => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = grade.code_cours || 'N/A';
            row.insertCell().textContent = grade.titre_cours || 'N/A';
            row.insertCell().textContent = grade.annee_academique;
            row.insertCell().textContent = grade.semestre;
            row.insertCell().textContent = grade.type_evaluation || 'N/A';
            row.insertCell().textContent = grade.note_valeur;
            row.insertCell().textContent = grade.bareme_max || '20'; // Supposer 20 si non fourni
            row.insertCell().textContent = grade.commentaires_professeur || '';

            // Pour le calcul de la moyenne (simpliste, à adapter selon le système de l'école)
            const note = parseFloat(grade.note_valeur);
            const bareme = parseFloat(grade.bareme_max || 20);
            // Supposons un coefficient de 1 pour chaque note pour cet exemple.
            // Une vraie application aurait des coefficients par cours/évaluation.
            if (!isNaN(note) && !isNaN(bareme) && bareme > 0) {
                // Normaliser la note sur 20 si le barème est différent, pour une moyenne générale indicative
                const noteSur20 = (note / bareme) * 20;
                totalPoints += noteSur20; // Ou note * coeff
                totalCoeffs += 1;    // Ou coeff
            }
            anneeSet.add(grade.annee_academique);
        });

        // Mettre à jour la moyenne générale
        const moyenneGeneraleEl = document.getElementById('moyenneGenerale');
        if (totalCoeffs > 0) {
            moyenneGeneraleEl.textContent = (totalPoints / totalCoeffs).toFixed(2) + " / 20";
        } else {
            moyenneGeneraleEl.textContent = 'N/A';
        }

        // Peupler les filtres d'année académique
        const filterAnneeSelect = document.getElementById('filterAnneeNotes');
        // Conserver la valeur sélectionnée pour ne pas la réinitialiser
        const currentSelectedAnnee = filterAnneeSelect.value;
        filterAnneeSelect.innerHTML = '<option value="">Toutes</option>'; // Réinitialiser
        [...anneeSet].sort().reverse().forEach(annee => { // Trier les années
            const option = document.createElement('option');
            option.value = annee;
            option.textContent = annee;
            filterAnneeSelect.appendChild(option);
        });
        filterAnneeSelect.value = currentSelectedAnnee; // Rétablir la sélection

        // Mettre à jour le graphique
        updateGradesChart(gradesData);

    } else {
        tableBody.innerHTML = '<tr><td colspan="8" class="text-center">Erreur lors du chargement des notes.</td></tr>';
    }
}

async function loadStudentCourses() {
    const coursesListDiv = document.getElementById('studentCoursesList');
    if (!coursesListDiv) return;
    coursesListDiv.innerHTML = '<p>Chargement des cours...</p>';

    const coursesData = await fetchApi('/api/student/my/courses');

    if (coursesData && Array.isArray(coursesData)) {
        if (coursesData.length === 0) {
            coursesListDiv.innerHTML = '<p>Vous n\'êtes inscrit à aucun cours pour le moment.</p>';
            return;
        }
        coursesListDiv.innerHTML = ''; // Vider
        coursesData.forEach(course => {
            const courseCard = document.createElement('div');
            courseCard.className = 'dashboard-card course-card'; // Ajouter une classe spécifique si besoin de styler les cartes de cours
            courseCard.innerHTML = `
                <h3>${course.titre} (${course.code_cours || 'N/A'})</h3>
                <p>${course.description || 'Pas de description.'}</p>
                <p><strong>Niveau:</strong> ${course.niveau || 'N/A'} | <strong>Semestre:</strong> ${course.semestre || 'N/A'} | <strong>Crédits:</strong> ${course.credits || 'N/A'}</p>
                <p><em>Inscription: Année ${course.inscription_details?.annee_academique || 'N/A'}, Semestre ${course.inscription_details?.semestre_inscription || 'N/A'} (${course.inscription_details?.statut_inscription || 'N/A'})</em></p>
                <a href="student_course_details.html?courseId=${course._id}" class="btn btn-info">Voir Contenu du Cours</a>
            `;
            coursesListDiv.appendChild(courseCard);
        });
    } else {
        coursesListDiv.innerHTML = '<p>Erreur lors du chargement des cours.</p>';
    }
}

let gradesChartInstance = null; // Pour garder une référence au graphique et le détruire/mettre à jour

function updateGradesChart(gradesData) {
    const ctx = document.getElementById('gradesChart')?.getContext('2d');
    if (!ctx) return;

    if (gradesChartInstance) {
        gradesChartInstance.destroy(); // Détruire l'ancien graphique avant d'en dessiner un nouveau
    }

    if (!gradesData || gradesData.length === 0) {
        // Afficher un message ou laisser vide si aucune donnée
        // Peut-être dessiner un graphique vide avec un message
        document.getElementById('gradesChartContainer').querySelector('.small-text').textContent = "Aucune donnée de note disponible pour afficher le graphique.";
        return;
    }
     document.getElementById('gradesChartContainer').querySelector('.small-text').textContent = "Un graphique de l'évolution de vos moyennes par semestre pourrait être affiché ici.";


    // Exemple de traitement des données pour le graphique: Moyenne par semestre
    // Il faudrait une logique plus complexe pour grouper par semestre réel et calculer les moyennes.
    // Ceci est un exemple très simplifié.
    const labels = []; // Ex: ['S1 2023', 'S2 2023', 'S1 2024']
    const moyennes = []; // Ex: [12, 14, 13.5]

    // Grouper les notes par année académique et semestre
    const gradesBySemester = gradesData.reduce((acc, grade) => {
        const key = `${grade.semestre} - ${grade.annee_academique}`;
        if (!acc[key]) {
            acc[key] = { totalPoints: 0, count: 0, notes: [] };
        }
        const noteVal = parseFloat(grade.note_valeur);
        const bareme = parseFloat(grade.bareme_max || 20);
        if(!isNaN(noteVal) && !isNaN(bareme) && bareme > 0) {
            acc[key].totalPoints += (noteVal / bareme) * 20; // Note normalisée sur 20
            acc[key].count++;
            acc[key].notes.push((noteVal / bareme) * 20);
        }
        return acc;
    }, {});

    // Trier les clés (semestres) pour un affichage chronologique
    const sortedSemesters = Object.keys(gradesBySemester).sort((a, b) => {
        const [semA, yearA] = a.split(' - ');
        const [semB, yearB] = b.split(' - ');
        if (yearA !== yearB) return yearA.localeCompare(yearB);
        return semA.localeCompare(semB);
    });

    sortedSemesters.forEach(key => {
        labels.push(key);
        const semesterData = gradesBySemester[key];
        moyennes.push(semesterData.count > 0 ? (semesterData.totalPoints / semesterData.count).toFixed(2) : 0);
    });


    gradesChartInstance = new Chart(ctx, {
        type: 'line', // ou 'bar'
        data: {
            labels: labels,
            datasets: [{
                label: 'Moyenne du Semestre (sur 20)',
                data: moyennes,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Important pour que le canvas s'adapte au conteneur
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMax: 20 // Si les notes sont sur 20
                }
            },
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            }
        }
    });
}

// TODO: function loadRecentMessages() { ... }
console.log("Script etudiant_dashboard.js chargé.");
