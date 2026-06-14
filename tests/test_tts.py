import hashlib
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


def fake_save():
    async def _save(path):
        Path(path).write_bytes(b"fake-mp3")
    return AsyncMock(side_effect=_save)


async def test_get_audio_returns_path(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = fake_save()
    with patch("edge_tts.Communicate", return_value=mock_comm):
        from app.services.tts import get_audio
        path = await get_audio("あ", "japanese")
    assert path.suffix == ".mp3"
    assert path.parent == tmp_path

async def test_get_audio_caches(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = fake_save()
    with patch("edge_tts.Communicate", return_value=mock_comm) as mock_cls:
        from app.services.tts import get_audio
        await get_audio("あ", "japanese")
        await get_audio("あ", "japanese")
    assert mock_cls.call_count == 1

async def test_get_audio_uses_correct_voice(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = fake_save()
    with patch("edge_tts.Communicate", return_value=mock_comm) as mock_cls:
        from app.services.tts import get_audio
        await get_audio("안녕", "korean")
    assert mock_cls.call_args[0][1] == "ko-KR-SunHiNeural"

async def test_get_audio_different_languages_different_cache_keys(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = fake_save()
    with patch("edge_tts.Communicate", return_value=mock_comm) as mock_cls:
        from app.services.tts import get_audio
        await get_audio("아", "korean")
        await get_audio("아", "japanese")
    assert mock_cls.call_count == 2
