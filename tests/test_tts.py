import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

async def test_get_audio_returns_path(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = AsyncMock()
    with patch("edge_tts.Communicate", return_value=mock_comm):
        from app.services.tts import get_audio
        path = await get_audio("あ")
    assert path.suffix == ".mp3"
    assert path.parent == tmp_path

async def test_get_audio_caches(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = AsyncMock()
    with patch("edge_tts.Communicate", return_value=mock_comm) as mock_cls:
        from app.services.tts import get_audio
        await get_audio("あ")
        # Simulate cache file existing after first call
        import hashlib
        key = hashlib.md5("あ".encode()).hexdigest()
        (tmp_path / f"{key}.mp3").touch()
        await get_audio("あ")
    assert mock_cls.call_count == 1
