import json

import Flask_project_Moubarak_LASSISSI as app_module


def test_local_topics_pages(tmp_path, monkeypatch):
    data_file = tmp_path / "data_base.json"
    data_file.write_text(
        json.dumps({"Exemple": {"Documentation": ["https://example.org"]}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "DATA_FILE", data_file)
    monkeypatch.setattr(app_module, "LOG_FILE", tmp_path / "client_logs.txt")

    client = app_module.app.test_client()
    assert client.get("/").status_code == 200

    topics = client.get("/ws/topics")
    assert topics.status_code == 200
    assert b"Exemple" in topics.data

    items = client.get("/ws/topic/Exemple")
    assert items.status_code == 200
    assert b"Documentation" in items.data

    urls = client.get("/ws/topic/Exemple/Documentation")
    assert urls.status_code == 200
    assert b"https://example.org" in urls.data
