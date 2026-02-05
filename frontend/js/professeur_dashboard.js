// frontend/js/professeur_dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('authToken');
    const user = JSON.parse(localStorage.getItem('currentUser'));

    if (!token || !user || user.role !== 'professeur') {
        alert("Veuillez vous connecter en tant que professeur.");
        window.location.href = '../../login.html';
        return;
    }

    document.getElementById('professorName').textContent = `${user.prenom} ${user.nom}`;

    loadProfessorCourses(); // Charge les cours et peuple les selects

    // Gestion des sélecteurs de cours
    const courseSelectGrading = document.getElementById('selectCourseForGrading');
    const courseSelectContent = document.getElementById('selectCourseForContent');

    if (courseSelectGrading) {
        courseSelectGrading.addEventListener('change', (e) => {
            if (e.target.value) {
                const courseId = e.target.value;
                const courseName = e.target.options[e.target.selectedIndex].text;
                document.getElementById('selectedCourseNameGrading').textContent = courseName;
                document.getElementById('selectedCourseNameForChart').textContent = courseName;
                loadStudentsForGrading(courseId);
                loadAndDisplayGradeDistribution(courseId); // Charger aussi le graphique
                document.getElementById('studentsListForGradingContainer').style.display = 'block';
                document.getElementById('gradeDistributionChartContainer').style.display = 'block';
            } else {
                document.getElementById('studentsListForGradingContainer').style.display = 'none';
                document.getElementById('studentsForGradingTableBody').innerHTML = '';
                document.getElementById('gradeDistributionChartContainer').style.display = 'none';
                if (gradeDistributionChartInstance) gradeDistributionChartInstance.destroy();
            }
        });
    }

    if (courseSelectContent) {
        courseSelectContent.addEventListener('change', (e) => {
            if (e.target.value) {
                document.getElementById('selectedCourseNameContent').textContent = e.target.options[e.target.selectedIndex].text;
                loadCourseContentForManagement(e.target.value);
                document.getElementById('courseContentManagementContainer').style.display = 'block';
            } else {
                document.getElementById('courseContentManagementContainer').style.display = 'none';
                document.getElementById('courseContentList').innerHTML = '';
            }
        });
    }

    // Gestion du formulaire de note
    const gradeForm = document.getElementById('gradeForm');
    if (gradeForm) {
        gradeForm.addEventListener('submit', handleGradeFormSubmit);
    }

    // Gestion du formulaire de contenu de cours
    const contentSectionForm = document.getElementById('contentSectionForm');
    if(contentSectionForm) {
        contentSectionForm.addEventListener('submit', handleContentSectionFormSubmit);
    }
    document.getElementById('addContentSectionButton')?.addEventListener('click', openContentModalForAdd);
    document.getElementById('addFileAttachmentField')?.addEventListener('click', addFileInputFieldToModal);


    // Logout button (duplication de main.js, pourrait être centralisé)
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            window.location.href = '../../index.html';
        });
    }
});

// Fonction fetchApi générique (similaire à etudiant_dashboard.js, à mutualiser)
async function fetchApi(url, options = {}) {
    const token = localStorage.getItem('authToken');
    const defaultHeaders = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`};
    options.headers = { ...defaultHeaders, ...options.headers };
    try {
        const response = await fetch(url, options);
        if (response.status === 401) {
            alert("Session expirée."); window.location.href = '../../login.html'; return null;
        }
        if (!response.ok) {
            const err = await response.json().catch(()=>({message: response.statusText}));
            console.error("API Error:", err.message);
            displayGlobalMessageProf(`Erreur API: ${err.message}`, 'error');
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error("Fetch Error:", error);
        displayGlobalMessageProf("Erreur de connexion au serveur.", 'error');
        return null;
    }
}

function displayGlobalMessageProf(message, type = 'info') {
    const msgArea = document.getElementById('message-area-global-prof');
    if (msgArea) {
        msgArea.innerHTML = `<div class="alert-message ${type}">${message}</div>`;
        setTimeout(() => { msgArea.innerHTML = ''; }, 5000);
    }
}


let professorCoursesCache = []; // Cache pour les cours du prof

async function loadProfessorCourses() {
    const coursesData = await fetchApi('/api/professor/courses');
    const courseListDiv = document.getElementById('professorCoursesList');
    const courseSelectGrading = document.getElementById('selectCourseForGrading');
    const courseSelectContent = document.getElementById('selectCourseForContent');

    if (coursesData && Array.isArray(coursesData)) {
        professorCoursesCache = coursesData; // Mettre en cache
        if (courseListDiv) {
            courseListDiv.innerHTML = '';
            if (coursesData.length === 0) {
                courseListDiv.innerHTML = '<p>Vous n\'êtes assigné à aucun cours pour le moment.</p>';
            }
            coursesData.forEach(course => {
                const card = document.createElement('div');
                card.className = 'dashboard-card course-card-prof';
                card.innerHTML = `
                    <h3>${course.titre} (${course.code_cours || 'N/A'})</h3>
                    <p>Niveau: ${course.niveau || 'N/A'} | Semestre: ${course.semestre || 'N/A'}</p>
                    <button class="btn btn-sm btn-info" onclick="selectCourseForGradingFromCard('${course._id}')">Gérer Notes</button>
                    <button class="btn btn-sm btn-primary" onclick="selectCourseForContentFromCard('${course._id}')">Gérer Contenu</button>
                `;
                courseListDiv.appendChild(card);
            });
        }
        // Peupler les selects
        [courseSelectGrading, courseSelectContent].forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">-- Choisissez un cours --</option>';
                coursesData.forEach(course => {
                    const option = document.createElement('option');
                    option.value = course._id;
                    option.textContent = `${course.titre} (${course.code_cours})`;
                    select.appendChild(option);
                });
            }
        });
    } else {
        if(courseListDiv) courseListDiv.innerHTML = '<p>Erreur lors du chargement de vos cours.</p>';
    }
}
function selectCourseForGradingFromCard(courseId) {
    document.getElementById('selectCourseForGrading').value = courseId;
    document.getElementById('selectCourseForGrading').dispatchEvent(new Event('change'));
    document.getElementById('gestion-notes').scrollIntoView({ behavior: 'smooth' });
}
function selectCourseForContentFromCard(courseId) {
    document.getElementById('selectCourseForContent').value = courseId;
    document.getElementById('selectCourseForContent').dispatchEvent(new Event('change'));
    document.getElementById('gestion-contenu').scrollIntoView({ behavior: 'smooth' });
}


async function loadStudentsForGrading(courseId) {
    const tableBody = document.getElementById('studentsForGradingTableBody');
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="5">Chargement des étudiants...</td></tr>';

    const studentsData = await fetchApi(`/api/professor/course/${courseId}/students`);
    if (studentsData && Array.isArray(studentsData)) {
        tableBody.innerHTML = '';
        if (studentsData.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5">Aucun étudiant inscrit à ce cours.</td></tr>';
            return;
        }
        studentsData.forEach(student => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = student.matricule || 'N/A';
            row.insertCell().textContent = student.nom;
            row.insertCell().textContent = student.prenom;
            row.insertCell().textContent = student.email;
            const actionCell = row.insertCell();
            const noteButton = document.createElement('button');
            noteButton.className = 'btn btn-sm btn-success';
            noteButton.textContent = 'Noter';
            noteButton.onclick = () => openGradeModal(student, courseId);
            actionCell.appendChild(noteButton);
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="5">Erreur chargement étudiants.</td></tr>';
    }
}

function openGradeModal(student, courseId) {
    const course = professorCoursesCache.find(c => c._id === courseId);
    document.getElementById('modalStudentName').textContent = `${student.prenom} ${student.nom} (${student.matricule})`;
    document.getElementById('modalCourseName').textContent = course ? course.titre : 'N/A';
    document.getElementById('modalStudentId').value = student._id;
    document.getElementById('modalCourseId').value = courseId;

    // Idéalement, pré-remplir annee/semestre si le cours a une période définie, ou charger une note existante.
    // Pour l'instant, on laisse vide ou avec des valeurs par défaut.
    document.getElementById('anneeAcad').value = new Date().getFullYear() + '-' + (new Date().getFullYear() + 1); // Ex: 2023-2024
    document.getElementById('semestre').value = 'S1'; // A adapter
    document.getElementById('typeEval').value = 'Examen Final';
    document.getElementById('noteValeur').value = '';
    document.getElementById('baremeMax').value = '20';
    document.getElementById('commentairesProf').value = '';
    document.getElementById('visibleEtudiant').checked = false;
    document.getElementById('gradeFormMessage').style.display = 'none';
    document.getElementById('gradeFormMessage').textContent = '';

    document.getElementById('gradeEntryModal').style.display = 'block';
}

async function handleGradeFormSubmit(event) {
    event.preventDefault();
    const studentId = document.getElementById('modalStudentId').value;
    const courseId = document.getElementById('modalCourseId').value;
    const gradeData = {
        etudiant_id: studentId,
        cours_id: courseId,
        annee_academique: document.getElementById('anneeAcad').value,
        semestre: document.getElementById('semestre').value,
        type_evaluation: document.getElementById('typeEval').value,
        note_valeur: document.getElementById('noteValeur').value, // Sera converti en nombre si possible par le backend
        bareme_max: document.getElementById('baremeMax').value || null, // Envoyer null si vide
        commentaires_professeur: document.getElementById('commentairesProf').value,
        visible_etudiant: document.getElementById('visibleEtudiant').checked
    };

    const messageDiv = document.getElementById('gradeFormMessage');
    messageDiv.style.display = 'none';

    const response = await fetchApi('/api/professor/grade', {
        method: 'POST',
        body: JSON.stringify(gradeData)
    });

    if (response) {
        messageDiv.textContent = response.message || "Opération réussie.";
        messageDiv.className = 'message success'; // Supposer une classe CSS pour succès
        messageDiv.style.display = 'block';
        setTimeout(() => {
            document.getElementById('gradeEntryModal').style.display = 'none';
        }, 2000);
    } else {
        messageDiv.textContent = "Erreur lors de l'enregistrement de la note.";
        messageDiv.className = 'message error'; // Supposer une classe CSS pour erreur
        messageDiv.style.display = 'block';
    }
}


// --- Gestion du Contenu de Cours ---
let currentManagingCourseId = null;
let currentCourseContentCache = [];

async function loadCourseContentForManagement(courseId) {
    currentManagingCourseId = courseId;
    const contentListDiv = document.getElementById('courseContentList');
    if (!contentListDiv) return;
    contentListDiv.innerHTML = '<p>Chargement du contenu...</p>';

    // L'API /api/professor/courses ne renvoie pas le contenu_cours détaillé.
    // On doit le fetch séparément ou l'ajouter à la réponse de /api/professor/courses.
    // Pour l'instant, on suppose que les cours en cache ont le contenu ou on le fetch.
    // L'API /api/admin/courses/<id> renvoie le contenu, mais pas celle pour prof.
    // Il faudrait une route /api/professor/course/<id>/details qui renvoie le contenu.
    // Pour la démo, on va utiliser la structure du cours depuis le cache.
    const course = professorCoursesCache.find(c => c._id === courseId);

    if (course && course.contenu_cours) { // Supposons que contenu_cours est dans le cache
        currentCourseContentCache = course.contenu_cours;
        renderCourseContentList(currentCourseContentCache);
    } else { // Sinon, il faudrait un fetch spécifique
        // const detailedCourse = await fetchApi(`/api/professor/course/${courseId}/details`); // Endpoint à créer
        // if(detailedCourse && detailedCourse.contenu_cours) {
        //    currentCourseContentCache = detailedCourse.contenu_cours;
        //    renderCourseContentList(currentCourseContentCache);
        // } else {
        contentListDiv.innerHTML = '<p>Contenu non disponible ou erreur de chargement. (Endpoint /api/professor/course/[id]/details à implémenter ou enrichir /api/professor/courses)</p>';
        currentCourseContentCache = []; // Réinitialiser
        // }
    }
}

function renderCourseContentList(contentArray) {
    const contentListDiv = document.getElementById('courseContentList');
    contentListDiv.innerHTML = ''; // Vider
    if (!contentArray || contentArray.length === 0) {
        contentListDiv.innerHTML = '<p>Aucune section de contenu pour ce cours.</p>';
        return;
    }
    // Trier par ordre si disponible
    contentArray.sort((a,b) => (a.ordre || 0) - (b.ordre || 0));

    contentArray.forEach((section, index) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'accordion-item dashboard-card'; // Réutiliser le style accordéon

        const header = document.createElement('button');
        header.className = 'accordion-header';
        header.textContent = section.titre_section || `Section ${index + 1}`;
        header.onclick = function() { this.classList.toggle('active'); this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'block' ? 'none' : 'block'; };

        const panel = document.createElement('div');
        panel.className = 'accordion-panel';
        panel.style.display = 'none'; // Caché par défaut
        panel.innerHTML = `
            <div class="content-html-preview">${section.contenu_html ? section.contenu_html.substring(0,200)+'...' : 'Pas de contenu HTML.'}</div>
            <p><strong>Fichiers:</strong> ${section.fichiers_joints && section.fichiers_joints.length > 0 ? section.fichiers_joints.map(f => f.nom_fichier).join(', ') : 'Aucun'}</p>
            <p><em>Ordre: ${section.ordre !== undefined ? section.ordre : 'Non défini'}</em></p>
            <button class="btn btn-sm btn-primary" onclick="openContentModalForEdit('${section.section_id}')">Modifier</button>
            <button class="btn btn-sm btn-danger" onclick="deleteContentSection('${section.section_id}')">Supprimer</button>
        `;
        itemDiv.appendChild(header);
        itemDiv.appendChild(panel);
        contentListDiv.appendChild(itemDiv);
    });
}

function openContentModalForAdd() {
    if (!currentManagingCourseId) {
        alert("Veuillez d'abord sélectionner un cours.");
        return;
    }
    document.getElementById('contentModalTitle').textContent = "Ajouter une Section de Contenu";
    document.getElementById('contentSectionForm').reset(); // Reset form
    document.getElementById('contentModalCourseId').value = currentManagingCourseId;
    document.getElementById('contentModalSectionId').value = ''; // Pas de section_id pour l'ajout
    document.getElementById('fileAttachmentsContainer').innerHTML = ''; // Vider les champs de fichiers
    addFileInputFieldToModal(); // Ajouter un premier champ pour fichier joint
    document.getElementById('contentFormMessage').style.display = 'none';
    document.getElementById('contentSectionModal').style.display = 'block';
}

function openContentModalForEdit(sectionId) {
    const section = currentCourseContentCache.find(s => s.section_id === sectionId);
    if (!section) { alert("Section non trouvée."); return; }

    document.getElementById('contentModalTitle').textContent = "Modifier la Section de Contenu";
    document.getElementById('contentModalCourseId').value = currentManagingCourseId;
    document.getElementById('contentModalSectionId').value = sectionId;
    document.getElementById('sectionTitle').value = section.titre_section;
    document.getElementById('sectionHtmlContent').value = section.contenu_html || '';
    document.getElementById('sectionOrder').value = section.ordre !== undefined ? section.ordre : '';

    const filesContainer = document.getElementById('fileAttachmentsContainer');
    filesContainer.innerHTML = ''; // Vider
    if (section.fichiers_joints && section.fichiers_joints.length > 0) {
        section.fichiers_joints.forEach(file => {
            const div = document.createElement('div');
            div.className = 'file-attachment-field';
            // Afficher les fichiers existants, permettre de les supprimer ou d'en ajouter.
            // Pour la simplicité de la démo, on va juste lister et permettre de remplacer toute la liste.
            div.innerHTML = `<span>${file.nom_fichier} (URL: ${file.url_stockage}) - Type: ${file.type_fichier}</span>`;
            filesContainer.appendChild(div);
        });
        // Ajouter un message indiquant que les fichiers existants seront remplacés si de nouveaux sont saisis ci-dessous
        const p = document.createElement('p');
        p.innerHTML = "<small><em>Pour modifier les fichiers, ajoutez de nouveaux champs ci-dessous. La liste actuelle sera remplacée.</em></small>";
        filesContainer.appendChild(p);

    }
    addFileInputFieldToModal(); // Toujours ajouter un champ vide pour potentiellement de nouveaux fichiers

    document.getElementById('contentFormMessage').style.display = 'none';
    document.getElementById('contentSectionModal').style.display = 'block';
}

async function handleContentSectionFormSubmit(event) {
    event.preventDefault();
    const courseId = document.getElementById('contentModalCourseId').value;
    const sectionId = document.getElementById('contentModalSectionId').value; // Vide si ajout

    const fichiersJoints = [];
    document.querySelectorAll('#fileAttachmentsContainer .new-file-field').forEach(fieldSet => {
        const nom = fieldSet.querySelector('.file-nom').value;
        const url = fieldSet.querySelector('.file-url').value;
        const type = fieldSet.querySelector('.file-type').value;
        if (nom && url && type) {
            fichiersJoints.push({ nom_fichier: nom, url_stockage: url, type_fichier: type });
        }
    });

    const contentData = {
        titre_section: document.getElementById('sectionTitle').value,
        contenu_html: document.getElementById('sectionHtmlContent').value,
        ordre: document.getElementById('sectionOrder').value ? parseInt(document.getElementById('sectionOrder').value) : null,
        fichiers_joints: fichiersJoints // Seuls les nouveaux fichiers saisis
    };
    // Si sectionId existe et fichiersJoints est vide, cela signifie qu'on ne veut pas modifier les fichiers existants
    // La logique backend pour PUT devrait gérer cela (ne pas écraser fichiers_joints si non fourni dans le payload)
    // Ou, si on veut permettre la suppression de tous les fichiers: envoyer un tableau vide explicitement.
    // Pour cette démo, si on modifie, et qu'on ne soumet pas de nouveaux fichiers via les champs, on ne touche pas aux fichiers_joints.
    // Le backend actuel pour PUT remplace toute la liste. Donc si on veut garder les anciens, il faudrait les re-soumettre.
    // C'est une simplification de l'UI ici. Une vraie UI de gestion de fichiers serait plus complexe.


    let url = `/api/professor/course/${courseId}/content`;
    let method = 'POST';
    if (sectionId) { // Modification
        url += `/${sectionId}`;
        method = 'PUT';
        // Si on modifie et qu'aucun nouveau fichier n'est ajouté, on ne veut pas écraser les existants avec un tableau vide.
        // Donc, on ne met 'fichiers_joints' dans contentData que si de nouveaux fichiers ont été saisis.
        // La logique actuelle du backend (PUT) REMPLACE la liste des fichiers.
        // Si on veut une gestion plus fine (ajouter/supprimer individuellement), le backend et le frontend doivent être adaptés.
        // Pour l'instant, si on modifie, on s'attend à ce que l'utilisateur re-liste tous les fichiers qu'il veut conserver/ajouter.
    }


    const messageDiv = document.getElementById('contentFormMessage');
    messageDiv.style.display = 'none';

    const response = await fetchApi(url, { method: method, body: JSON.stringify(contentData) });

    if (response) {
        messageDiv.textContent = response.message || "Opération réussie.";
        messageDiv.className = 'message success';
        messageDiv.style.display = 'block';
        // Recharger le contenu du cours et fermer le modal
        const updatedCourse = professorCoursesCache.find(c => c._id === courseId);
        if (updatedCourse) {
            // Re-fetcher le contenu du cours via la route professeur dédiée
            const detailedCourse = await fetchApi(`/api/professor/course/${courseId}/details`);
            if(detailedCourse && detailedCourse.contenu_cours) {
               updatedCourse.contenu_cours = detailedCourse.contenu_cours; // Mettre à jour le cache
               currentCourseContentCache = detailedCourse.contenu_cours;
               renderCourseContentList(currentCourseContentCache);
            }
        }
        setTimeout(() => { document.getElementById('contentSectionModal').style.display = 'none'; }, 2000);
    } else {
        messageDiv.textContent = "Erreur lors de l'enregistrement de la section.";
        messageDiv.className = 'message error';
        messageDiv.style.display = 'block';
    }
}

async function deleteContentSection(sectionId) {
    if (!currentManagingCourseId || !sectionId) return;
    if (!confirm("Êtes-vous sûr de vouloir supprimer cette section de contenu ?")) return;

    const response = await fetchApi(`/api/professor/course/${currentManagingCourseId}/content/${sectionId}`, { method: 'DELETE' });
    if (response) {
        displayGlobalMessageProf(response.message || "Section supprimée.", 'success');
        // Recharger/mettre à jour la liste
        const updatedCourse = professorCoursesCache.find(c => c._id === currentManagingCourseId);
         if (updatedCourse) {
            const detailedCourse = await fetchApi(`/api/professor/course/${currentManagingCourseId}/details`);
            if(detailedCourse && detailedCourse.contenu_cours) {
               updatedCourse.contenu_cours = detailedCourse.contenu_cours;
               currentCourseContentCache = detailedCourse.contenu_cours;
               renderCourseContentList(currentCourseContentCache);
            } else { // Si le cours n'a plus de contenu
                updatedCourse.contenu_cours = [];
                currentCourseContentCache = [];
                renderCourseContentList([]);
            }
        }
    } else {
        displayGlobalMessageProf("Erreur suppression section.", 'error');
    }
}

function addFileInputFieldToModal() {
    const container = document.getElementById('fileAttachmentsContainer');
    const fieldSet = document.createElement('div');
    fieldSet.className = 'file-attachment-field new-file-field'; // 'new-file-field' pour les distinguer des fichiers existants affichés
    fieldSet.innerHTML = `
        <input type="text" placeholder="Nom du fichier" class="form-control file-nom" style="margin-bottom:5px;">
        <input type="url" placeholder="URL du fichier" class="form-control file-url" style="margin-bottom:5px;">
        <input type="text" placeholder="Type MIME (ex: application/pdf)" class="form-control file-type" style="margin-bottom:10px;">
        <hr>
    `;
    container.appendChild(fieldSet);
}

// --- Grade Distribution Chart ---
let gradeDistributionChartInstance = null;

async function loadAndDisplayGradeDistribution(courseId) {
    if (!courseId) {
        document.getElementById('gradeDistributionChartContainer').style.display = 'none';
        if (gradeDistributionChartInstance) gradeDistributionChartInstance.destroy();
        return;
    }

    const gradesData = await fetchApi(`/api/professor/course/${courseId}/grades`);
    if (!gradesData || !Array.isArray(gradesData) || gradesData.length === 0) {
        document.getElementById('gradeDistributionChartContainer').style.display = 'block'; // Afficher le conteneur pour le message
        const canvas = document.getElementById('gradeDistributionChart');
        const ctx = canvas.getContext('2d');
        if (gradeDistributionChartInstance) gradeDistributionChartInstance.destroy();
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Effacer le canvas
        ctx.font = "16px Arial";
        ctx.textAlign = "center";
        ctx.fillText("Aucune note disponible pour ce cours.", canvas.width/2, canvas.height/2);
        return;
    }

    // Traiter les données pour la distribution (exemple: notes sur 20)
    const distribution = {
        "0-4": 0, "5-9": 0, "10-14": 0, "15-20": 0, "Autre": 0
    };
    const BAREME_STANDARD = 20; // Supposer un barème standard pour la distribution

    gradesData.forEach(grade => {
        let noteNum = parseFloat(grade.note_valeur);
        let bareme = parseFloat(grade.bareme_max || BAREME_STANDARD);
        if (isNaN(noteNum) || isNaN(bareme) || bareme === 0) {
            distribution["Autre"]++;
            return;
        }
        // Normaliser la note au barème standard si différent
        if (bareme !== BAREME_STANDARD) {
            noteNum = (noteNum / bareme) * BAREME_STANDARD;
        }

        if (noteNum >= 0 && noteNum <= 4.99) distribution["0-4"]++;
        else if (noteNum >= 5 && noteNum <= 9.99) distribution["5-9"]++;
        else if (noteNum >= 10 && noteNum <= 14.99) distribution["10-14"]++;
        else if (noteNum >= 15 && noteNum <= BAREME_STANDARD) distribution["15-20"]++;
        else distribution["Autre"]++;
    });

    const ctx = document.getElementById('gradeDistributionChart').getContext('2d');
    if (gradeDistributionChartInstance) {
        gradeDistributionChartInstance.destroy();
    }
    gradeDistributionChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(distribution),
            datasets: [{
                label: "Nombre d'étudiants",
                data: Object.values(distribution),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(255, 159, 64, 0.5)',
                    'rgba(255, 205, 86, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(153, 102, 255, 0.5)'
                ],
                borderColor: [
                    'rgb(255, 99, 132)',
                    'rgb(255, 159, 64)',
                    'rgb(255, 205, 86)',
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: "Nombre d'Étudiants" },
                    ticks: { stepSize: 1 } // S'assurer que l'axe Y n'a que des entiers
                },
                x: {
                    title: { display: true, text: "Tranches de Notes (sur 20)" }
                }
            },
            plugins: {
                legend: { display: false }, // La légende du dataset est suffisante
                title: { display: true, text: `Distribution des Notes (Total: ${gradesData.length} notes)` }
            }
        }
    });
    document.getElementById('gradeDistributionChartContainer').style.display = 'block';
}


console.log("Script professeur_dashboard.js chargé.");
