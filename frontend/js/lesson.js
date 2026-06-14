let lessonData = null;
let currentPhase = 0; // 0=introduce, 1=speak, 2=write, 3=quiz
let currentCardIdx = 0;
let quizResults = [];

async function renderLesson(unit, lesson) {
  if (!unit || !lesson) { window.location.hash = '#lessons'; return; }
  const lang = sessionStorage.getItem('currentLanguage') || 'japanese';
  lessonData = await fetch(`/api/lessons/${unit}/${lesson}?language=${lang}`).then(r => r.json());
  currentPhase = 0; currentCardIdx = 0; quizResults = [];
  showPhase();
}

function phaseBar() {
  return `<div class="phase-bar">
    ${['Introduce', 'Speak', 'Write', 'Quiz'].map((p, i) => `
      <div class="phase-dot ${i < currentPhase ? 'done' : i === currentPhase ? 'active' : ''}"></div>
    `).join('')}
  </div>`;
}

function showPhase() {
  const lang = sessionStorage.getItem('currentLanguage') || 'japanese';
  if (currentPhase === 0) showIntroduce();
  else if (currentPhase === 1) {
    if (lang === 'asl') { currentPhase = 2; showWrite(); }
    else showSpeak();
  }
  else if (currentPhase === 2) showWrite();
  else showQuiz();
}

function showIntroduce() {
  const card = lessonData.cards[currentCardIdx];
  const lang = sessionStorage.getItem('currentLanguage') || 'japanese';
  const isAsl = lang === 'asl';
  const mediaHtml = (isAsl && card.video)
    ? `<video src="/videos/asl/${card.video}" autoplay loop muted playsinline
              style="max-width:280px;max-height:280px;border-radius:8px;margin:0 auto;display:block"></video>`
    : `<div style="font-size:80px;color:var(--accent-light)">${card.character}</div>`;

  document.getElementById('app').innerHTML = `
    ${phaseBar()}
    <div class="card" style="text-align:center;padding:32px">
      ${mediaHtml}
      <div style="font-size:24px;margin-top:8px">${card.romaji}</div>
      <div class="muted" style="margin-top:4px">${card.meaning}</div>
      ${!isAsl ? `<button class="btn btn-secondary" style="margin-top:20px" onclick="playTTS('${card.character}')">🔊 Hear it</button>` : ''}
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px">
      <span class="muted">${currentCardIdx + 1} / ${lessonData.cards.length}</span>
      <button class="btn btn-primary" onclick="nextIntroduce()">Next →</button>
    </div>
  `;
  if (!isAsl) playTTS(card.character);
}

window.nextIntroduce = function() {
  currentCardIdx++;
  if (currentCardIdx < lessonData.cards.length) showIntroduce();
  else { currentPhase = 1; currentCardIdx = 0; showPhase(); }
};

function showSpeak() {
  const card = lessonData.cards[currentCardIdx];
  const app = document.getElementById('app');
  app.innerHTML = `
    ${phaseBar()}
    <div class="card" style="text-align:center;padding:32px">
      <div style="font-size:64px;color:var(--accent-light)">${card.character}</div>
      <div style="font-size:20px;margin:8px 0">${card.romaji}</div>
      <button class="btn btn-secondary" style="margin-bottom:20px" onclick="playTTS('${card.character}')">🔊 Hear it</button>
      <div>
        <button class="mic-btn" id="mic-btn" onclick="doSpeak('${card.character}')">🎤</button>
        <p class="muted" style="margin-top:8px">Tap to speak</p>
      </div>
      <div id="stt-result" style="margin-top:16px;min-height:24px"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px">
      <span class="muted">${currentCardIdx + 1} / ${lessonData.cards.length}</span>
      <button class="btn btn-primary" onclick="nextSpeak()">Next →</button>
    </div>
  `;
}

window.doSpeak = async function(expected) {
  const btn = document.getElementById('mic-btn');
  const result = document.getElementById('stt-result');
  btn.classList.add('recording');
  result.innerHTML = '<span class="muted">Listening…</span>';
  try {
    const blob = await recordAudio(3000);
    btn.classList.remove('recording');
    result.innerHTML = '<span class="muted">Processing…</span>';
    const data = await recognizeSpeech(blob, expected);
    result.innerHTML = data.match
      ? `<span style="color:var(--green)">✓ Whisper heard: ${data.text}</span>`
      : `<span style="color:#f87171">✗ Whisper heard: "${data.text}" (expected: ${expected})</span>`;
  } catch {
    btn.classList.remove('recording');
    result.innerHTML = '<span style="color:var(--yellow)">Mic unavailable — tap Next to continue</span>';
  }
};

window.nextSpeak = function() {
  currentCardIdx++;
  if (currentCardIdx < lessonData.cards.length) showSpeak();
  else { currentPhase = 2; currentCardIdx = 0; showWrite(); }
};

function showWrite() {
  const card = lessonData.cards[currentCardIdx];
  document.getElementById('app').innerHTML = `
    ${phaseBar()}
    <div class="card" style="text-align:center;padding:24px">
      <div class="muted" style="margin-bottom:8px">Draw: <strong>${card.romaji}</strong> (${card.meaning})</div>
      <canvas id="write-canvas" class="writing-canvas" width="280" height="280"></canvas>
      <div style="display:flex;gap:8px;justify-content:center;margin-top:12px">
        <button class="btn btn-secondary" onclick="clearCanvas()">Clear</button>
        <button class="btn btn-secondary" onclick="showHint('${card.character}')">Hint</button>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px">
      <span class="muted">${currentCardIdx + 1} / ${lessonData.cards.length}</span>
      <button class="btn btn-primary" onclick="nextWrite()">Next →</button>
    </div>
  `;
  initCanvas();
}

function initCanvas() {
  const canvas = document.getElementById('write-canvas');
  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = '#93c5fd'; ctx.lineWidth = 3; ctx.lineCap = 'round';
  let drawing = false;

  const pos = (e) => {
    const r = canvas.getBoundingClientRect();
    const src = e.touches ? e.touches[0] : e;
    return [src.clientX - r.left, src.clientY - r.top];
  };

  canvas.addEventListener('mousedown', e => { drawing = true; ctx.beginPath(); ctx.moveTo(...pos(e)); });
  canvas.addEventListener('mousemove', e => { if (!drawing) return; ctx.lineTo(...pos(e)); ctx.stroke(); });
  canvas.addEventListener('mouseup', () => drawing = false);
  canvas.addEventListener('touchstart', e => { e.preventDefault(); drawing = true; ctx.beginPath(); ctx.moveTo(...pos(e)); }, { passive: false });
  canvas.addEventListener('touchmove', e => { e.preventDefault(); if (!drawing) return; ctx.lineTo(...pos(e)); ctx.stroke(); }, { passive: false });
  canvas.addEventListener('touchend', () => drawing = false);
}

window.clearCanvas = function() {
  const c = document.getElementById('write-canvas');
  c.getContext('2d').clearRect(0, 0, c.width, c.height);
};

window.showHint = function(char) {
  const c = document.getElementById('write-canvas');
  const ctx = c.getContext('2d');
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.font = '200px serif'; ctx.fillStyle = 'rgba(147,197,253,0.15)';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(char, 140, 140);
};

window.nextWrite = function() {
  currentCardIdx++;
  if (currentCardIdx < lessonData.cards.length) showWrite();
  else { currentPhase = 3; showQuiz(); }
};

function showQuiz() {
  const cards = lessonData.cards;
  const questions = [...cards].sort(() => Math.random() - 0.5).slice(0, Math.min(5, cards.length));
  let qIdx = 0;

  function showQuestion() {
    if (qIdx >= questions.length) { showQuizResults(); return; }
    const q = questions[qIdx];
    const distractors = cards.filter(c => c.id !== q.id).sort(() => Math.random() - 0.5).slice(0, Math.min(3, cards.length - 1));
    const options = [...distractors, q].sort(() => Math.random() - 0.5);

    document.getElementById('app').innerHTML = `
      ${phaseBar()}
      <div class="card" style="text-align:center;padding:24px">
        <p class="muted">Which character makes this sound?</p>
        <div style="font-size:32px;margin:16px 0">${q.romaji}</div>
        <div class="quiz-options">
          ${options.map(o => `
            <div class="quiz-opt" onclick="checkAnswer(this,'${o.character}','${q.character}')">
              ${o.character}
            </div>
          `).join('')}
        </div>
      </div>
      <div style="text-align:right;margin-top:12px">
        <span class="muted">${qIdx + 1} / ${questions.length}</span>
      </div>
    `;
  }

  window.checkAnswer = function(el, chosen, correct) {
    document.querySelectorAll('.quiz-opt').forEach(o => o.onclick = null);
    if (chosen === correct) {
      el.classList.add('correct');
      quizResults.push(true);
    } else {
      el.classList.add('wrong');
      document.querySelectorAll('.quiz-opt').forEach(o => {
        if (o.textContent.trim() === correct) o.classList.add('correct');
      });
      quizResults.push(false);
    }
    setTimeout(() => { qIdx++; showQuestion(); }, 900);
  };

  showQuestion();
}

async function showQuizResults() {
  const correct = quizResults.filter(Boolean).length;
  const score = `${correct}/${quizResults.length}`;
  await fetch(
    `/api/lessons/${lessonData.unit}/${lessonData.lesson}/complete?${window.apiParams()}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quiz_score: score }),
    }
  );
  document.getElementById('app').innerHTML = `
    <div class="card" style="text-align:center;padding:40px">
      <div style="font-size:48px">${correct === quizResults.length ? '🎉' : '📝'}</div>
      <h2 style="margin-top:12px">Lesson Complete!</h2>
      <p class="muted" style="margin-top:8px">Score: ${score}</p>
      <div style="display:flex;gap:12px;justify-content:center;margin-top:24px">
        <button class="btn btn-secondary" onclick="window.location.hash='#home'">Home</button>
        <button class="btn btn-primary" onclick="window.location.hash='#lessons'">Next Lesson</button>
      </div>
    </div>
  `;
}

if (typeof pages !== 'undefined') pages.lesson = renderLesson;
