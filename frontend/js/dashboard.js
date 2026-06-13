async function renderDashboard() {
  const app = document.getElementById('app');
  const [lessons, due] = await Promise.all([
    fetch('/api/lessons').then(r => r.json()),
    fetch('/api/review/due').then(r => r.json())
  ]);

  const completed = lessons.filter(l => l.completed);
  const next = lessons.find(l => !l.completed);
  // Streak: stored in localStorage
  const today = new Date().toDateString();
  let streak = parseInt(localStorage.getItem('streak') || '0');
  const lastVisit = localStorage.getItem('lastVisit');
  if (lastVisit !== today) {
    const yesterday = new Date(Date.now() - 86400000).toDateString();
    streak = lastVisit === yesterday ? streak + 1 : 1;
    localStorage.setItem('streak', streak);
    localStorage.setItem('lastVisit', today);
  }

  // Group by unit for progress bars
  const unitMap = {};
  for (const l of lessons) {
    if (!unitMap[l.unit]) unitMap[l.unit] = { total: 0, done: 0 };
    unitMap[l.unit].total++;
    if (l.completed) unitMap[l.unit].done++;
  }

  app.innerHTML = `
    <div style="text-align:center;padding:28px 0 20px">
      <h2>Welcome back</h2>
      <p class="muted" style="margin-top:4px">🔥 ${streak}-day streak · ${completed.length} lessons done</p>
    </div>

    <div style="display:flex;gap:12px;margin-bottom:20px">
      ${next ? `
        <button onclick="startLesson(${next.unit},${next.lesson})" class="btn btn-primary btn-lg" style="flex:1">
          ▶ Continue — Lesson ${next.lesson}
        </button>
      ` : '<div class="btn btn-secondary btn-lg" style="flex:1;justify-content:center">🎉 All lessons complete!</div>'}
      <button onclick="window.location.hash='#review'" class="btn btn-secondary btn-lg" style="min-width:120px">
        🃏 Review<br><span style="font-size:12px">${due.length} due</span>
      </button>
    </div>

    <div class="card" style="margin-bottom:12px">
      <div class="label">Progress</div>
      ${Object.entries(unitMap).map(([unit, { total, done }]) => `
        <div style="margin-top:10px">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span class="muted">Unit ${unit}</span>
            <span class="muted">${done}/${total}</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width:${total ? (done/total*100) : 0}%"></div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}
