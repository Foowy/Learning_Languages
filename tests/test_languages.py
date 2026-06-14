import pytest
from unittest.mock import MagicMock

def _mock_settings(tmp_path):
    m = MagicMock()
    m.data_dir = str(tmp_path)
    return m

async def test_list_languages_no_lessons_dir(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    response = await client.get("/api/languages")
    assert response.status_code == 200
    assert response.json() == []

async def test_list_languages_japanese(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    jp = tmp_path / "lessons" / "japanese" / "unit1"
    jp.mkdir(parents=True)
    (jp / "lesson01.json").write_text("{}")
    (jp / "lesson02.json").write_text("{}")
    response = await client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["language"] == "japanese"
    assert data[0]["label"] == "🇯🇵 Japanese"
    assert data[0]["lesson_count"] == 2

async def test_list_languages_multiple(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    for lang in ["japanese", "spanish"]:
        d = tmp_path / "lessons" / lang / "unit1"
        d.mkdir(parents=True)
        (d / "lesson01.json").write_text("{}")
    response = await client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    langs = {d["language"] for d in data}
    assert langs == {"japanese", "spanish"}

async def test_list_languages_unknown_folder_capitalized(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    d = tmp_path / "lessons" / "klingon" / "unit1"
    d.mkdir(parents=True)
    (d / "lesson01.json").write_text("{}")
    response = await client.get("/api/languages")
    assert response.status_code == 200
    assert response.json()[0]["label"] == "Klingon"
