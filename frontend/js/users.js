async function renderUserPicker() {
  document.querySelector('.top-nav').style.display = 'none';
  const app = document.getElementById('app');
  const users = await fetch('/api/users').then(r => r.json());

  app.innerHTML = `
    <div style="text-align:center;padding:40px 0 20px">
      <h2>Who\'s learning today?</h2>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:16px;justify-content:center;margin-bottom:24px">
      ${users.map(u => `
        <div class="card" style="text-align:center;padding:20px;cursor:pointer;min-width:100px"
             onclick="window.selectUser(${u.id},'${u.name.replace(/'/g, "\\'")}')">
          ${u.avatar_url
            ? `<img src="${u.avatar_url}" style="width:64px;height:64px;border-radius:50%;object-fit:cover;margin-bottom:8px;display:block;margin-left:auto;margin-right:auto">`
            : `<div style="width:64px;height:64px;border-radius:50%;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;margin:0 auto 8px">${(u.name[0] || '?').toUpperCase()}</div>`
          }
          <div>${u.name}</div>
        </div>
      `).join('')}
      <div class="card" style="text-align:center;padding:20px;cursor:pointer;min-width:100px"
           onclick="window.showNewProfileForm()">
        <div style="width:64px;height:64px;border-radius:50%;border:2px dashed var(--border);display:flex;align-items:center;justify-content:center;font-size:32px;margin:0 auto 8px">+</div>
        <div class="muted">New Profile</div>
      </div>
    </div>
    <div id="new-profile-form" style="display:none;max-width:340px;margin:0 auto">
      <div class="card">
        <h3 style="margin-bottom:16px">Create Profile</h3>
        <input id="profile-name" placeholder="Your name"
               style="width:100%;padding:8px;background:var(--surface);border:1px solid var(--border);border-radius:6px;color:var(--text);margin-bottom:12px">
        <label class="muted" style="display:block;margin-bottom:6px">Profile photo (optional)</label>
        <input type="file" id="avatar-input" accept="image/*" style="margin-bottom:16px;color:var(--text)">
        <button class="btn btn-primary" style="width:100%" onclick="window.createProfile()">Create</button>
      </div>
    </div>
  `;
}

window.selectUser = function(id, name) {
  sessionStorage.setItem('userId', id);
  sessionStorage.setItem('userName', name);
  document.querySelector('.top-nav').style.display = '';
  if (!sessionStorage.getItem('currentLanguage')) {
    renderLanguagePicker();
  } else {
    navigate(window.location.hash || '#home');
  }
};

window.showNewProfileForm = function() {
  document.getElementById('new-profile-form').style.display = 'block';
};

window.createProfile = async function() {
  const name = document.getElementById('profile-name').value.trim();
  if (!name) return;
  const res = await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  const user = await res.json();
  const avatarInput = document.getElementById('avatar-input');
  if (avatarInput.files[0]) {
    const form = new FormData();
    form.append('avatar', avatarInput.files[0]);
    await fetch(`/api/users/${user.id}/avatar`, { method: 'POST', body: form });
  }
  window.selectUser(user.id, user.name);
};
