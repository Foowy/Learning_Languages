async function renderReview() {
  const app = document.getElementById('app');
  const params = window.apiParams();
  const cards = await fetch('/api/review/due?' + params).then(r => r.json());

  if (cards.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px">
        <p class="muted">No cards due for review.</p>
        <button class="btn btn-primary" style="margin-top:16px" onclick="window.location.hash='#home'">Home</button>
      </div>
    `;
    return;
  }

  let idx = 0;
  let rating = false;

  function showCard() {
    if (idx >= cards.length) {
      app.innerHTML = `
        <div class="card" style="text-align:center;padding:48px">
          <div style="font-size:48px">✓</div>
          <h2 style="margin-top:12px">Session complete!</h2>
          <p class="muted" style="margin-top:8px">${cards.length} cards reviewed</p>
          <button class="btn btn-primary" style="margin-top:20px" onclick="window.location.hash='#home'">Done</button>
        </div>
      `;
      return;
    }
    const card = cards[idx];
    app.innerHTML = `
      <div class="flashcard" id="flashcard" onclick="window.flipCard()">
        <div class="flashcard-front">
          <div style="font-size:72px;color:var(--accent-light)">${card.character}</div>
          <p class="muted" style="margin-top:12px">Tap to reveal</p>
        </div>
        <div class="flashcard-back" style="display:none">
          <div style="font-size:48px;color:var(--accent-light)">${card.character}</div>
          <div style="font-size:20px;margin-top:8px">${card.romaji}</div>
          <div class="muted">${card.meaning}</div>
          <div class="recall-btns" style="margin-top:20px">
            <button class="btn" style="background:#f87171" onclick="window.rate(1)">Again</button>
            <button class="btn" style="background:var(--yellow)" onclick="window.rate(2)">Hard</button>
            <button class="btn btn-primary" onclick="window.rate(3)">Good</button>
            <button class="btn" style="background:var(--green)" onclick="window.rate(4)">Easy</button>
          </div>
        </div>
      </div>
      <p class="muted" style="text-align:right;margin-top:8px">${idx + 1} / ${cards.length}</p>
    `;
  }

  window.flipCard = function() {
    document.querySelector('.flashcard-front').style.display = 'none';
    document.querySelector('.flashcard-back').style.display = 'block';
    document.getElementById('flashcard').onclick = null;
  };

  window.rate = async function(score) {
    if (rating) return;
    rating = true;
    await fetch(`/api/review/update?${params}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_id: cards[idx].id, score }),
    });
    idx++;
    rating = false;
    showCard();
  };

  showCard();
}
