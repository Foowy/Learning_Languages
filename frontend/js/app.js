// --- Session helpers ---
function getCurrentUser() {
  return { id: sessionStorage.getItem('userId'), name: sessionStorage.getItem('userName') };
}

function getCurrentLanguage() {
  return sessionStorage.getItem('currentLanguage') || 'japanese';
}

window.apiParams = function() {
  return `user_id=${getCurrentUser().id}&language=${getCurrentLanguage()}`;
};

window.switchUser = function() {
  sessionStorage.removeItem('userId');
  sessionStorage.removeItem('userName');
  sessionStorage.removeItem('currentLanguage');
  renderUserPicker();
};

// --- Pages registry ---
const pages = {
  home: renderDashboard,
  lessons: renderLessons,
  review: renderReview,
  speak: renderSpeak,
};

// --- Lessons list page ---
async function renderLessons() {
  const app = document.getElementById('app');
  const lessons = await fetch('/api/lessons?' + window.apiParams()).then(r => r.json());
  const byUnit = {};
  for (const l of lessons) {
    (byUnit[l.unit] = byUnit[l.unit] || []).push(l);
  }
  app.innerHTML = '<h2 style="margin-bottom:16px">Lessons</h2>' +
    Object.entries(byUnit).map(([unit, ls]) => `
      <div class="card" style="margin-bottom:12px">
        <div class="label">Unit ${unit}</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">
          ${ls.map(l => `
            <button onclick="startLesson(${l.unit},${l.lesson})"
                    class="btn ${l.completed ? 'btn-secondary' : 'btn-primary'}">
              ${l.completed ? '✓' : ''} Lesson ${l.lesson}
            </button>
          `).join('')}
        </div>
      </div>
    `).join('');
}

window.startLesson = function(unit, lesson) {
  window.location.hash = `#lesson/${unit}/${lesson}`;
};

// --- Router ---
function navigate(hash) {
  const [page, ...params] = (hash.replace('#', '') || 'home').split('/');
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.page === page);
  });
  const fn = pages[page];
  if (fn) fn(...params);
}

// --- Nav event handlers ---
document.getElementById('hamburger').addEventListener('click', () => {
  document.getElementById('mobile-menu').classList.toggle('open');
});

document.querySelectorAll('.nav-link[data-page]').forEach(a => {
  a.addEventListener('click', () => {
    document.getElementById('mobile-menu').classList.remove('open');
  });
});

window.addEventListener('hashchange', () => navigate(window.location.hash));

// --- Startup gating ---
function init() {
  const user = getCurrentUser();
  if (!user.id) {
    renderUserPicker();
    return;
  }
  if (!sessionStorage.getItem('currentLanguage')) {
    renderLanguagePicker();
    return;
  }
  navigate(window.location.hash);
}

init();
