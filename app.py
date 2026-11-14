import json
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["DATABASE"] = str(Path(__file__).resolve().parent / "oracle_music.db")


def get_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source TEXT DEFAULT 'oracle',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                local_path TEXT,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id)
            )
            """
        )


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/oracle/playlist")
def create_playlist():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "Untitled Playlist").strip()
    songs = payload.get("songs") or []

    if not isinstance(songs, list):
        return jsonify({"error": "songs must be a list"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO playlists (name, source, created_at) VALUES (?, ?, ?)",
                    (name, "oracle", datetime.utcnow().isoformat()))
        playlist_id = cur.lastrowid

        for song in songs:
            title = (song.get("title") or "Unknown song").strip() or "Unknown song"
            url = (song.get("url") or "").strip()
            if not url:
                continue
            cur.execute(
                """
                INSERT INTO songs (playlist_id, title, url, status, created_at, updated_at)
                VALUES (?, ?, ?, 'queued', ?, ?)
                """,
                (playlist_id, title, url, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
            )

        conn.commit()
        return jsonify({"status": "ok", "playlist_id": playlist_id, "songs": len(songs)}), 201
    finally:
        conn.close()


@app.get("/api/playlists")
def list_playlists():
    conn = get_db()
    try:
        playlists = conn.execute(
            "SELECT * FROM playlists ORDER BY created_at DESC"
        ).fetchall()
        songs = conn.execute(
            "SELECT * FROM songs ORDER BY created_at ASC"
        ).fetchall()

        song_map = {}
        for row in songs:
            song_map.setdefault(row["playlist_id"], []).append(dict(row))

        result = []
        for row in playlists:
            result.append({
                "id": row["id"],
                "name": row["name"],
                "source": row["source"],
                "created_at": row["created_at"],
                "songs": song_map.get(row["id"], []),
            })

        return jsonify({"playlists": result})
    finally:
        conn.close()


@app.get("/api/pi/queue")
def pi_queue():
    limit = int(request.args.get("limit", 10))
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT s.*
            FROM songs s
            WHERE s.status IN ('queued', 'retrying')
            ORDER BY s.created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return jsonify({"songs": [dict(row) for row in rows]})
    finally:
        conn.close()


@app.post("/api/pi/report")
def pi_report():
    payload = request.get_json(silent=True) or {}
    song_id = payload.get("song_id")
    status = payload.get("status") or "downloaded"
    local_path = payload.get("local_path")
    error = payload.get("error")

    if song_id is None:
        return jsonify({"error": "song_id is required"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE songs
            SET status = ?, local_path = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, local_path, error, datetime.utcnow().isoformat(), song_id),
        )
        conn.commit()
        return jsonify({"status": "ok", "song_id": song_id, "updated_status": status})
    finally:
        conn.close()


@app.get("/api/health")
def health_check():
    return jsonify({"ok": True, "service": "oracle-music-tracker"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
