async function renderReview() {
  const app = document.getElementById('app');
  const cards = await fetch('/api/review/due').then(r => r.json());

  if (cards.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px">
        <div style="font-size:48px">✅</div>
        <h2 style="margin-top:12px">All caught up!</h2>
        <p class="muted" style="margin-top:8px">No cards due for review.</p>
        <button class="btn btn-primary" style="margin-top:20px" onclick="window.location.hash='#home'">Back to Home</button>
      </div>
    `;
    return;
  }

  let idx = 0;
  let flipped = false;

  function showCard() {
    if (idx >= cards.length) { showSummary(); return; }
    const card = cards[idx];
    flipped = false;
    app.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <h2>Review</h2>
        <span class="muted">${idx + 1} / ${cards.length}</span>
      </div>
      <div class="flashcard" onclick="flipCard('${card.character}','${card.romaji}','${card.meaning}')">
        <div class="flashcard-char">${card.character}</div>
      </div>
      <p class="muted" style="text-align:center;margin-top:12px">Tap card to reveal</p>
      <button class="btn btn-secondary" style="display:block;margin:12px auto" onclick="playTTS('${card.character}')">🔊 Hear it</button>
      <div id="recall-area"></div>
    `;
  }

  window.flipCard = function(char, romaji, meaning) {
    if (flipped) return;
    flipped = true;
    document.querySelector('.flashcard').innerHTML = `
      <div style="text-align:center">
        <div class="flashcard-char" style="font-size:48px">${char}</div>
        <div class="flashcard-back" style="margin-top:8px">${romaji}</div>
        <div class="muted" style="margin-top:4px">${meaning}</div>
      </div>
    `;
    document.getElementById('recall-area').innerHTML = `
      <p class="muted" style="text-align:center;margin-top:16px;margin-bottom:8px">How well did you remember?</p>
      <div class="recall-btns">
        <button class="recall-btn recall-1" onclick="rate(1)">Forgot</button>
        <button class="recall-btn recall-2" onclick="rate(2)">Hard</button>
        <button class="recall-btn recall-3" onclick="rate(3)">Good</button>
        <button class="recall-btn recall-4" onclick="rate(4)">Easy</button>
      </div>
    `;
  };

  window.rate = async function(score) {
    const card = cards[idx];
    await fetch('/api/review/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_id: card.id, score })
    });
    idx++;
    showCard();
  };

  function showSummary() {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:40px">
        <div style="font-size:48px">🎴</div>
        <h2 style="margin-top:12px">Review Complete</h2>
        <p class="muted" style="margin-top:8px">${cards.length} cards reviewed</p>
        <button class="btn btn-primary" style="margin-top:20px" onclick="window.location.hash='#home'">Back to Home</button>
      </div>
    `;
  }

  showCard();
}
