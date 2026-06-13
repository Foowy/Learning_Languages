from unittest.mock import AsyncMock, patch

async def test_tts_returns_audio(client, tmp_path):
    fake_mp3 = tmp_path / "test.mp3"
    fake_mp3.write_bytes(b"fake mp3 data")
    with patch("app.routers.speech.get_audio", new=AsyncMock(return_value=fake_mp3)):
        response = await client.get("/api/speech/tts?text=%E3%81%82")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"

async def test_recognize_returns_transcription(client):
    with patch("app.routers.speech.transcribe", new=AsyncMock(return_value="あ")):
        response = await client.post(
            "/api/speech/recognize?expected=%E3%81%82",
            files={"audio": ("audio.wav", b"fake", "audio/wav")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "あ"
    assert data["match"] is True
