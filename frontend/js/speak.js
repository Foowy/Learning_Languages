async function renderSpeak() {
  const app = document.getElementById('app');
  const lessons = await fetch('/api/lessons').then(r => r.json());
  const completed = lessons.filter(l => l.completed);

  if (completed.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px">
        <p class="muted">Complete at least one lesson to unlock speaking practice.</p>
        <button class="btn btn-primary" style="margin-top:16px" onclick="window.location.hash='#lessons'">Go to Lessons</button>
      </div>
    `;
    return;
  }

  const allCards = [];
  for (const l of completed) {
    const data = await fetch(`/api/lessons/${l.unit}/${l.lesson}`).then(r => r.json());
    allCards.push(...data.cards);
  }

  let current = null;

  function pickRandom() {
    current = allCards[Math.floor(Math.random() * allCards.length)];
    app.innerHTML = `
      <h2 style="margin-bottom:16px">Speaking Practice</h2>
      <div class="card" style="text-align:center;padding:32px">
        <div style="font-size:72px;color:var(--accent-light)">${current.character}</div>
        <div style="font-size:20px;margin-top:8px">${current.romaji}</div>
        <button class="btn btn-secondary" style="margin:16px auto;display:block" onclick="playTTS('${current.character}')">🔊 Hear it</button>
        <button class="mic-btn" id="mic-btn" onclick="doSpeakPractice()">🎤</button>
        <p class="muted" style="margin-top:8px">Tap to speak</p>
        <div id="result" style="margin-top:16px;min-height:28px"></div>
      </div>
      <button class="btn btn-secondary" style="display:block;margin:16px auto" onclick="pickRandom()">Next →</button>
    `;
  }

  window.doSpeakPractice = async function() {
    const btn = document.getElementById('mic-btn');
    const result = document.getElementById('result');
    btn.classList.add('recording');
    result.innerHTML = '<span class="muted">Listening…</span>';
    try {
      const blob = await recordAudio(3000);
      btn.classList.remove('recording');
      result.innerHTML = '<span class="muted">Processing…</span>';
      const data = await recognizeSpeech(blob, current.character);
      result.innerHTML = data.match
        ? `<span style="color:var(--green)">✓ "${data.text}"</span>`
        : `<span style="color:#f87171">Heard: "${data.text}"</span>`;
    } catch {
      btn.classList.remove('recording');
      result.innerHTML = '<span style="color:var(--yellow)">Mic unavailable</span>';
    }
  };

  pickRandom();
}
