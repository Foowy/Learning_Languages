async function renderLanguagePicker() {
  document.querySelector('.top-nav').style.display = 'none';
  const app = document.getElementById('app');
  const languages = await fetch('/api/languages').then(r => r.json());
  const userName = sessionStorage.getItem('userName') || 'there';

  if (languages.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px;margin-top:40px">
        <p class="muted">No language content found on the server.</p>
        <p class="muted" style="margin-top:8px;font-size:13px">Drop lesson folders into /data/lessons/ and restart.</p>
      </div>
    `;
    document.querySelector('.top-nav').style.display = '';
    return;
  }

  app.innerHTML = `
    <div style="text-align:center;padding:40px 0 20px">
      <h2>What would you like to learn?</h2>
      <p class="muted" style="margin-top:4px">Hi ${userName}! Pick a language to continue.</p>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:16px;justify-content:center">
      ${languages.map(l => {
        const parts = l.label.split(' ');
        const flag = parts[0];
        const name = parts.slice(1).join(' ');
        return `
          <div class="card" style="text-align:center;padding:28px 24px;cursor:pointer;min-width:140px"
               onclick="window.selectLanguage('${l.language}')">
            <div style="font-size:48px;margin-bottom:8px">${flag}</div>
            <h3>${name}</h3>
            <p class="muted" style="margin-top:4px">${l.lesson_count} lessons</p>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

window.selectLanguage = function(language) {
  sessionStorage.setItem('currentLanguage', language);
  document.querySelector('.top-nav').style.display = '';
  navigate('#home');
};
