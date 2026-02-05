// frontend/js/admin_dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('authToken');
    const user = JSON.parse(localStorage.getItem('currentUser'));

    if (!token || !user || user.role !== 'admin') {
        alert("Accès réservé aux administrateurs.");
        window.location.href = '../../login.html';
        return;
    }

    document.getElementById('adminName').textContent = `${user.prenom} ${user.nom}`;

    // Initial load
    loadUsers();
    loadPrograms();
    loadCourses();
    populateEnrollmentSelects(); // Peuple les selects pour le formulaire d'inscription
    loadEnrollmentByProgramChart(); // Charger le graphique des inscriptions par filière

    // Event Listeners for buttons and forms
    document.getElementById('showAddUserModalBtn')?.addEventListener('click', () => openUserModal());
    document.getElementById('closeUserModalBtn')?.addEventListener('click', () => document.getElementById('userModal').style.display = 'none');
    document.getElementById('userForm')?.addEventListener('submit', handleUserFormSubmit);
    document.getElementById('userRole')?.addEventListener('change', toggleRoleSpecificFields);
    document.getElementById('applyUserFilters')?.addEventListener('click', loadUsers);

    document.getElementById('showAddProgramModalBtn')?.addEventListener('click', () => openProgramModal());
    document.getElementById('closeProgramModalBtn')?.addEventListener('click', () => document.getElementById('programModal').style.display = 'none');
    document.getElementById('programForm')?.addEventListener('submit', handleProgramFormSubmit);

    document.getElementById('showAddCourseModalBtn')?.addEventListener('click', () => openCourseModal());
    document.getElementById('closeCourseModalBtn')?.addEventListener('click', () => document.getElementById('courseModal').style.display = 'none');
    document.getElementById('courseForm')?.addEventListener('submit', handleCourseFormSubmit);

    document.getElementById('enrollmentForm')?.addEventListener('submit', handleEnrollmentFormSubmit);


    // Logout
    document.getElementById('logoutButton')?.addEventListener('click', () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        window.location.href = '../../index.html';
    });

    // Close modal if clicked outside
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = "none";
        }
    }
});

// Generic Fetch API function (to be centralized in a real project)
async function fetchApiAdmin(url, options = {}) {
    const token = localStorage.getItem('authToken');
    options.headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };
    try {
        const response = await fetch(url, options);
        if (response.status === 401) {
            alert("Session expirée."); window.location.href = '../../login.html'; return null;
        }
        const responseData = await response.json();
        if (!response.ok) {
            console.error("API Error:", responseData.message || response.statusText);
            displayAdminGlobalMessage(`Erreur API: ${responseData.message || response.statusText}`, 'error');
            return null;
        }
        return responseData;
    } catch (error) {
        console.error("Fetch Error:", error);
        displayAdminGlobalMessage("Erreur de connexion au serveur.", 'error');
        return null;
    }
}

function displayAdminGlobalMessage(message, type = 'info', duration = 5000) {
    const msgArea = document.getElementById('message-area-global-admin');
    if (msgArea) {
        msgArea.innerHTML = `<div class="alert-message ${type}">${message}</div>`;
        if(duration) setTimeout(() => { msgArea.innerHTML = ''; }, duration);
    }
}
function displayModalMessage(modalId, formId, message, type = 'info') {
    const msgDiv = document.getElementById(`${formId}Message`);
    if (msgDiv) {
        msgDiv.textContent = message;
        msgDiv.className = `message ${type}`;
        msgDiv.style.display = 'block';
    }
}

// --- User Management ---
let allUsersCache = []; // Pour peupler les selects de professeurs, etc.
let allProgramsCache = []; // Pour les filières dans userModal et courseModal
let allCoursesCache = []; // Pour les inscriptions

async function loadUsers() {
    const roleFilter = document.getElementById('filterUserRole').value;
    let url = '/api/admin/users';
    if (roleFilter) {
        url += `?role=${roleFilter}`;
    }
    const users = await fetchApiAdmin(url);
    allUsersCache = users || []; // Mettre en cache même si vide ou erreur pour éviter crashs
    const tableBody = document.getElementById('usersTableBody');
    tableBody.innerHTML = '';
    if (users && users.length) {
        users.forEach(user => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = user.nom;
            row.insertCell().textContent = user.prenom;
            row.insertCell().textContent = user.email;
            row.insertCell().textContent = user.role;
            row.insertCell().textContent = user.matricule || user.matricule_professeur || 'N/A';
            row.insertCell().innerHTML = user.actif ? '<span style="color:green;">Oui</span>' : '<span style="color:red;">Non</span>';
            const actionsCell = row.insertCell();
            actionsCell.innerHTML = `
                <button class="btn btn-sm btn-primary" onclick="openUserModal('${user._id}')">Modifier</button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser('${user._id}', '${user.nom} ${user.prenom}')">Désactiver</button>
            `; // Supprimer est une désactivation
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="7">Aucun utilisateur trouvé.</td></tr>';
    }
    populateProfessorSelects(allUsersCache.filter(u => u.role === 'professeur' && u.actif));
    populateStudentSelects(allUsersCache.filter(u => u.role === 'etudiant' && u.actif));
}

function openUserModal(userId = null) {
    const modal = document.getElementById('userModal');
    const form = document.getElementById('userForm');
    form.reset();
    document.getElementById('userFormMessage').style.display = 'none';
    document.getElementById('userId').value = userId || '';
    toggleRoleSpecificFields(); // Reset fields visibility

    if (userId) {
        document.getElementById('userModalTitle').textContent = 'Modifier Utilisateur';
        const user = allUsersCache.find(u => u._id === userId);
        if (user) {
            document.getElementById('userNom').value = user.nom;
            document.getElementById('userPrenom').value = user.prenom;
            document.getElementById('userEmail').value = user.email;
            document.getElementById('userRole').value = user.role;
            document.getElementById('userActif').checked = user.actif;
            toggleRoleSpecificFields(); // Show fields for current role
            if (user.role === 'etudiant') {
                document.getElementById('userMatricule').value = user.matricule || '';
                document.getElementById('userFiliere').value = user.filiere_id || '';
                document.getElementById('userNiveau').value = user.niveau || '';
            } else if (user.role === 'professeur') {
                document.getElementById('userMatriculeProf').value = user.matricule_professeur || '';
            }
        }
    } else {
        document.getElementById('userModalTitle').textContent = 'Ajouter Utilisateur';
        document.getElementById('userActif').checked = true;
    }
    modal.style.display = 'block';
}

async function handleUserFormSubmit(event) {
    event.preventDefault();
    const userId = document.getElementById('userId').value;
    const data = {
        nom: document.getElementById('userNom').value,
        prenom: document.getElementById('userPrenom').value,
        email: document.getElementById('userEmail').value,
        password: document.getElementById('userPassword').value, // Backend gère si vide
        role: document.getElementById('userRole').value,
        actif: document.getElementById('userActif').checked,
    };
    if (data.role === 'etudiant') {
        data.matricule = document.getElementById('userMatricule').value;
        data.filiere_id = document.getElementById('userFiliere').value;
        data.niveau = document.getElementById('userNiveau').value;
    } else if (data.role === 'professeur') {
        data.matricule_professeur = document.getElementById('userMatriculeProf').value;
    }

    const url = userId ? `/api/admin/users/${userId}` : '/api/admin/users';
    const method = userId ? 'PUT' : 'POST';
    const result = await fetchApiAdmin(url, { method, body: JSON.stringify(data) });
    if (result) {
        displayModalMessage('userModal', 'userForm', result.message, 'success');
        loadUsers(); // Refresh list
        setTimeout(() => document.getElementById('userModal').style.display = 'none', 1500);
    } else {
        displayModalMessage('userModal', 'userForm', "Erreur lors de l'opération.", 'error');
    }
}

async function deleteUser(userId, userName) {
    if (confirm(`Êtes-vous sûr de vouloir désactiver l'utilisateur ${userName} ?`)) {
        const result = await fetchApiAdmin(`/api/admin/users/${userId}`, { method: 'DELETE' });
        if (result) {
            displayAdminGlobalMessage(result.message, 'success');
            loadUsers();
        }
    }
}

function toggleRoleSpecificFields() {
    const role = document.getElementById('userRole').value;
    document.getElementById('etudiantFields').style.display = role === 'etudiant' ? 'block' : 'none';
    document.getElementById('professeurFields').style.display = role === 'professeur' ? 'block' : 'none';
}


// --- Program (Filière) Management ---
async function loadPrograms() {
    const programs = await fetchApiAdmin('/api/admin/programs');
    allProgramsCache = programs || [];
    const tableBody = document.getElementById('programsTableBody');
    tableBody.innerHTML = '';
    if (programs && programs.length) {
        programs.forEach(p => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = p.nom;
            row.insertCell().textContent = p.code_filiere || 'N/A';
            row.insertCell().textContent = p.departement || 'N/A';
            row.insertCell().textContent = (p.niveaux_offerts || []).join(', ');
            const resp = allUsersCache.find(u => u._id === p.responsable_filiere_id);
            row.insertCell().textContent = resp ? `${resp.prenom} ${resp.nom}` : 'N/A';
            actionsHtml = `<button class="btn btn-sm btn-primary" onclick="openProgramModal('${p._id}')">Modifier</button>
                           <button class="btn btn-sm btn-danger" onclick="deleteProgram('${p._id}', '${p.nom}')">Supprimer</button>`;
            row.insertCell().innerHTML = actionsHtml;
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="6">Aucune filière trouvée.</td></tr>';
    }
    populateFiliereSelects(allProgramsCache);
}

function openProgramModal(programId = null) {
    const modal = document.getElementById('programModal');
    const form = document.getElementById('programForm');
    form.reset();
    document.getElementById('programFormMessage').style.display = 'none';
    document.getElementById('programId').value = programId || '';
    populateProfessorSelects(allUsersCache.filter(u => u.role === 'professeur' && u.actif), 'programResponsable', true);


    if (programId) {
        document.getElementById('programModalTitle').textContent = 'Modifier Filière';
        const program = allProgramsCache.find(p => p._id === programId);
        if (program) {
            document.getElementById('programNom').value = program.nom;
            document.getElementById('programCode').value = program.code_filiere || '';
            document.getElementById('programDescription').value = program.description || '';
            document.getElementById('programDepartement').value = program.departement || '';
            document.getElementById('programNiveaux').value = (program.niveaux_offerts || []).join(',');
            document.getElementById('programResponsable').value = program.responsable_filiere_id || '';
        }
    } else {
        document.getElementById('programModalTitle').textContent = 'Ajouter Filière';
    }
    modal.style.display = 'block';
}

async function handleProgramFormSubmit(event) {
    event.preventDefault();
    const programId = document.getElementById('programId').value;
    const data = {
        nom: document.getElementById('programNom').value,
        code_filiere: document.getElementById('programCode').value,
        description: document.getElementById('programDescription').value,
        departement: document.getElementById('programDepartement').value,
        niveaux_offerts: document.getElementById('programNiveaux').value.split(',').map(s => s.trim()).filter(s => s),
        responsable_filiere_id: document.getElementById('programResponsable').value || null
    };
    const url = programId ? `/api/admin/programs/${programId}` : '/api/admin/programs';
    const method = programId ? 'PUT' : 'POST';
    const result = await fetchApiAdmin(url, { method, body: JSON.stringify(data) });
    if (result) {
        displayModalMessage('programModal', 'programForm', result.message, 'success');
        loadPrograms();
        setTimeout(() => document.getElementById('programModal').style.display = 'none', 1500);
    } else {
        displayModalMessage('programModal', 'programForm', "Erreur lors de l'opération.", 'error');
    }
}

async function deleteProgram(programId, programName) {
     if (confirm(`Êtes-vous sûr de vouloir supprimer la filière ${programName} ? Cela peut échouer si des cours ou étudiants y sont liés.`)) {
        const result = await fetchApiAdmin(`/api/admin/programs/${programId}`, { method: 'DELETE' });
        if (result) {
            displayAdminGlobalMessage(result.message, result.message.startsWith("Impossible") ? 'error' : 'success');
            loadPrograms();
        }
    }
}


// --- Course Management ---
async function loadCourses() {
    const courses = await fetchApiAdmin('/api/admin/courses');
    allCoursesCache = courses || [];
    const tableBody = document.getElementById('coursesTableBody');
    tableBody.innerHTML = '';
    if (courses && courses.length) {
        courses.forEach(c => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = c.titre;
            row.insertCell().textContent = c.code_cours;
            row.insertCell().textContent = c.niveau || 'N/A';
            row.insertCell().textContent = c.semestre || 'N/A';
            const prof = allUsersCache.find(u => u._id === c.professeur_id);
            row.insertCell().textContent = prof ? `${prof.prenom} ${prof.nom}` : 'N/A';
            row.insertCell().innerHTML = `
                <button class="btn btn-sm btn-primary" onclick="openCourseModal('${c._id}')">Modifier</button>
                <button class="btn btn-sm btn-danger" onclick="deleteCourse('${c._id}', '${c.titre}')">Supprimer</button>
            `;
        });
    } else {
        tableBody.innerHTML = '<tr><td colspan="6">Aucun cours trouvé.</td></tr>';
    }
    populateCourseSelects(allCoursesCache);
}

function openCourseModal(courseId = null) {
    const modal = document.getElementById('courseModal');
    const form = document.getElementById('courseForm');
    form.reset();
    document.getElementById('courseFormMessage').style.display = 'none';
    document.getElementById('courseId').value = courseId || '';

    populateProfessorSelects(allUsersCache.filter(u => u.role === 'professeur' && u.actif), 'courseProfesseurId', true);
    populateFiliereSelects(allProgramsCache, 'courseFiliereIds', false, true); // isMultiple = true


    if (courseId) {
        document.getElementById('courseModalTitle').textContent = 'Modifier Cours';
        const course = allCoursesCache.find(c => c._id === courseId);
        if (course) {
            document.getElementById('courseTitre').value = course.titre;
            document.getElementById('courseCode').value = course.code_cours;
            document.getElementById('courseDescription').value = course.description || '';
            document.getElementById('courseCredits').value = course.credits;
            document.getElementById('courseNiveau').value = course.niveau;
            document.getElementById('courseSemestre').value = course.semestre;
            document.getElementById('courseProfesseurId').value = course.professeur_id || '';

            const filiereSelect = document.getElementById('courseFiliereIds');
            (course.filiere_ids || []).forEach(fid => {
                const option = filiereSelect.querySelector(`option[value="${fid}"]`);
                if (option) option.selected = true;
            });
        }
    } else {
        document.getElementById('courseModalTitle').textContent = 'Ajouter Cours';
    }
    modal.style.display = 'block';
}

async function handleCourseFormSubmit(event) {
    event.preventDefault();
    const courseId = document.getElementById('courseId').value;
    const filiereIdsSelected = Array.from(document.getElementById('courseFiliereIds').selectedOptions).map(opt => opt.value);
    const data = {
        titre: document.getElementById('courseTitre').value,
        code_cours: document.getElementById('courseCode').value,
        description: document.getElementById('courseDescription').value,
        credits: parseInt(document.getElementById('courseCredits').value),
        niveau: document.getElementById('courseNiveau').value,
        semestre: document.getElementById('courseSemestre').value,
        filiere_ids: filiereIdsSelected,
        professeur_id: document.getElementById('courseProfesseurId').value || null
    };
    const url = courseId ? `/api/admin/courses/${courseId}` : '/api/admin/courses';
    const method = courseId ? 'PUT' : 'POST';
    const result = await fetchApiAdmin(url, { method, body: JSON.stringify(data) });
    if (result) {
        displayModalMessage('courseModal', 'courseForm', result.message, 'success');
        loadCourses();
        setTimeout(() => document.getElementById('courseModal').style.display = 'none', 1500);
    } else {
        displayModalMessage('courseModal', 'courseForm', "Erreur lors de l'opération.", 'error');
    }
}

async function deleteCourse(courseId, courseName) {
    if (confirm(`Êtes-vous sûr de vouloir supprimer le cours ${courseName} ? Cela peut échouer s'il est lié à des notes ou inscriptions.`)) {
        const result = await fetchApiAdmin(`/api/admin/courses/${courseId}`, { method: 'DELETE' });
        if (result) {
            displayAdminGlobalMessage(result.message, result.message.startsWith("Impossible") ? 'error' : 'success');
            loadCourses();
        }
    }
}

// --- Enrollment Management ---
async function populateEnrollmentSelects() {
    // Students and Courses should already be in cache if other loads completed
    populateStudentSelects(allUsersCache.filter(u => u.role === 'etudiant' && u.actif), 'enrollStudentSelect');
    populateCourseSelects(allCoursesCache, 'enrollCourseSelect');
}

async function handleEnrollmentFormSubmit(event) {
    event.preventDefault();
    const data = {
        etudiant_id: document.getElementById('enrollStudentSelect').value,
        cours_id: document.getElementById('enrollCourseSelect').value,
        annee_academique: document.getElementById('enrollAnneeAcad').value,
        semestre: document.getElementById('enrollSemestre').value
    };
    if (!data.etudiant_id || !data.cours_id || !data.annee_academique || !data.semestre) {
        displayAdminGlobalMessage("Tous les champs sont requis pour l'inscription.", "error");
        return;
    }
    const result = await fetchApiAdmin('/api/admin/enrollments', { method: 'POST', body: JSON.stringify(data) });
    if (result) {
        displayAdminGlobalMessage(result.message, 'success');
        document.getElementById('enrollmentForm').reset(); // Clear form
    } else {
         displayAdminGlobalMessage(result ? result.message : "Erreur inscription.", 'error');
    }
}


// --- Helper functions to populate selects ---
function populateProfessorSelects(professors, selectId, includeEmptyOption = false) {
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = ''; // Clear
    if (includeEmptyOption) {
        const emptyOpt = document.createElement('option');
        emptyOpt.value = "";
        emptyOpt.textContent = "-- Aucun --";
        select.appendChild(emptyOpt);
    }
    professors.forEach(prof => {
        const option = document.createElement('option');
        option.value = prof._id;
        option.textContent = `${prof.prenom} ${prof.nom} (${prof.email})`;
        select.appendChild(option);
    });
}

function populateStudentSelects(students, selectId, includeEmptyOption = false) {
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = '';
    if (includeEmptyOption) {
        select.add(new Option("-- Aucun --", ""));
    }
    students.forEach(stud => {
        select.add(new Option(`${stud.prenom} ${stud.nom} (${stud.matricule || stud.email})`, stud._id));
    });
}

function populateFiliereSelects(programs, selectId, includeEmptyOption = false, isMultiple = false) {
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = '';
    if (includeEmptyOption && !isMultiple) { // Empty option not typical for multi-select
        select.add(new Option("-- Aucune --", ""));
    }
    programs.forEach(prog => {
        select.add(new Option(`${prog.nom} (${prog.code_filiere || ''})`, prog._id));
    });
}

function populateCourseSelects(courses, selectId, includeEmptyOption = false) {
     const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = '';
    if (includeEmptyOption) {
        select.add(new Option("-- Aucun --", ""));
    }
    courses.forEach(course => {
        select.add(new Option(`${course.titre} (${course.code_cours})`, course._id));
    });
}


// --- Enrollment by Program Chart ---
let enrollmentByProgramChartInstance = null;

async function loadEnrollmentByProgramChart() {
    // Les données des filières (allProgramsCache) et des étudiants (allUsersCache)
    // devraient déjà être chargées par loadPrograms() et loadUsers().
    // S'assurer qu'elles sont disponibles avant de construire le graphique.
    // Pour plus de robustesse, on pourrait les re-fetcher ou attendre leur chargement.

    if (!allProgramsCache.length || !allUsersCache.length) {
        // Attendre un peu et réessayer si les caches ne sont pas encore peuplés.
        // Ceci est une solution simple, une gestion d'état plus complexe serait mieux.
        setTimeout(loadEnrollmentByProgramChart, 1000);
        console.log("Données pour le graphique des inscriptions par filière pas encore prêtes, nouvel essai dans 1s.");
        return;
    }

    const students = allUsersCache.filter(u => u.role === 'etudiant' && u.actif);
    const programCounts = {};

    allProgramsCache.forEach(program => {
        programCounts[program._id] = { name: program.nom, count: 0 };
    });

    students.forEach(student => {
        if (student.filiere_id && programCounts[student.filiere_id]) {
            programCounts[student.filiere_id].count++;
        } else if (student.filiere_id) {
            // Cas où un étudiant est lié à une filiere_id qui n'est plus dans allProgramsCache (rare)
            if (!programCounts[student.filiere_id]) {
                 programCounts[student.filiere_id] = { name: `ID Filière Inconnue: ${student.filiere_id}`, count: 1};
            } else {
                 programCounts[student.filiere_id].count++;
            }
        }
        // Les étudiants sans filiere_id ne sont pas comptés ici.
    });

    const labels = Object.values(programCounts).map(p => p.name);
    const data = Object.values(programCounts).map(p => p.count);

    const ctx = document.getElementById('enrollmentByProgramChart').getContext('2d');
    if (enrollmentByProgramChartInstance) {
        enrollmentByProgramChartInstance.destroy();
    }

    if (labels.length === 0) {
        ctx.clearRect(0,0, ctx.canvas.width, ctx.canvas.height);
        ctx.font = "16px Arial";
        ctx.textAlign = "center";
        ctx.fillText("Aucune donnée de filière ou d'étudiant pour le graphique.", ctx.canvas.width/2, ctx.canvas.height/2);
        return;
    }

    enrollmentByProgramChartInstance = new Chart(ctx, {
        type: 'pie', // ou 'doughnut' ou 'bar'
        data: {
            labels: labels,
            datasets: [{
                label: "Nombre d'Étudiants",
                data: data,
                backgroundColor: [ // Générer des couleurs ou utiliser une palette prédéfinie
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)',
                    'rgba(83, 102, 255, 0.7)',
                    'rgba(100, 255, 100, 0.7)'
                    // Ajouter plus de couleurs si plus de filières
                ],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: "Répartition des Étudiants par Filière"
                }
            }
        }
    });
}


console.log("Admin dashboard script loaded.");
