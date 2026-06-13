async function playTTS(text) {
  const url = `/api/speech/tts?text=${encodeURIComponent(text)}`;
  const audio = new Audio(url);
  return new Promise((resolve, reject) => {
    audio.onended = resolve;
    audio.onerror = reject;
    audio.play().catch(reject);
  });
}

function recordAudio(durationMs = 3000) {
  return new Promise((resolve, reject) => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      recorder.ondataavailable = e => chunks.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        resolve(new Blob(chunks, { type: recorder.mimeType }));
      };
      recorder.start();
      setTimeout(() => recorder.stop(), durationMs);
    }).catch(reject);
  });
}

async function recognizeSpeech(blob, expected = '') {
  const form = new FormData();
  form.append('audio', blob, 'audio.webm');
  const res = await fetch(`/api/speech/recognize?expected=${encodeURIComponent(expected)}`, {
    method: 'POST', body: form
  });
  return res.json();
}
