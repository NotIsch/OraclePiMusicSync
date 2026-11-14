import os

from app import app, init_db


def setup_test_db(tmp_path):
    db_path = tmp_path / "test_oracle_music.db"
    app.config["DATABASE"] = str(db_path)
    init_db()
    return db_path


def test_create_playlist_and_queue(tmp_path):
    setup_test_db(tmp_path)
    client = app.test_client()

    response = client.post(
        "/api/oracle/playlist",
        json={
            "name": "Night Drive",
            "songs": [
                {"title": "Song 1", "url": "https://youtu.be/test1"},
                {"title": "Song 2", "url": "https://youtu.be/test2"},
            ],
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["status"] == "ok"

    queue = client.get("/api/pi/queue")
    assert queue.status_code == 200
    queued = queue.get_json()["songs"]
    assert len(queued) >= 2
    assert {song["url"] for song in queued} >= {"https://youtu.be/test1", "https://youtu.be/test2"}


def test_pi_report_updates_song_status(tmp_path):
    setup_test_db(tmp_path)
    client = app.test_client()

    client.post(
        "/api/oracle/playlist",
        json={
            "name": "Report Test",
            "songs": [{"title": "Track A", "url": "https://youtu.be/tracka"}],
        },
    )

    song = client.get("/api/pi/queue").get_json()["songs"][0]
    report = client.post(
        "/api/pi/report",
        json={
            "song_id": song["id"],
            "status": "downloaded",
            "local_path": "/tmp/tracka.mp3",
        },
    )

    assert report.status_code == 200
    assert report.get_json()["updated_status"] == "downloaded"

    stored = client.get("/api/playlists").get_json()["playlists"][0]["songs"][0]
    assert stored["status"] == "downloaded"
    assert stored["local_path"] == "/tmp/tracka.mp3"
