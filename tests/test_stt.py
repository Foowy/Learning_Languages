from unittest.mock import patch, MagicMock

async def test_transcribe_returns_text():
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": " あ "}
    with patch("app.services.stt.get_model", return_value=mock_model):
        from app.services.stt import transcribe
        result = await transcribe(b"fake_audio", suffix=".wav")
    assert result == "あ"

async def test_transcribe_strips_whitespace():
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "  か  "}
    with patch("app.services.stt.get_model", return_value=mock_model):
        from app.services.stt import transcribe
        result = await transcribe(b"fake_audio")
    assert result == "か"
