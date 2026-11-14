#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


def upload_to_oracle(local_file: str, host: str, username: str, key_path: str, remote_path: str):
    if not os.path.exists(local_file):
        raise FileNotFoundError(local_file)

    subprocess.run([
        "scp",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        local_file,
        f"{username}@{host}:{remote_path}/",
    ], check=True)


def download_song(song, base_url, download_dir):
    url = song["url"]
    title = song.get("title") or "download"
    safe_title = "".join(ch if ch.isalnum() or ch in " ._-" else "_" for ch in title)
    target = Path(download_dir) / (safe_title + ".%(ext)s")

    if yt_dlp is None:
        raise RuntimeError("yt-dlp is not installed. Install it with: pip install yt-dlp")

    ydl_opts = {
        "outtmpl": str(target),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return str(target).replace("%(ext)s", "mp3")


def poll_queue(base_url):
    response = requests.get(f"{base_url}/api/pi/queue?limit=10", timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("songs", [])


def report_result(base_url, song_id, status, local_path=None, error=None):
    payload = {
        "song_id": song_id,
        "status": status,
    }
    if local_path:
        payload["local_path"] = local_path
    if error:
        payload["error"] = error

    response = requests.post(f"{base_url}/api/pi/report", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Download queued songs from Oracle and report back")
    parser.add_argument("--base-url", required=True, help="Base URL for the Oracle service; e.g. http://server:5000")
    parser.add_argument("--download-dir", required=True, help="Folder where songs should be saved")
    parser.add_argument("--upload-host", help="Oracle Cloud host name or IP")
    parser.add_argument("--upload-user", help="SSH user on Oracle Cloud host")
    parser.add_argument("--upload-key", help="SSH private key path")
    parser.add_argument("--upload-path", default="/home/ubuntu/media/music", help="Remote directory on Oracle Cloud host")
    args = parser.parse_args()

    os.makedirs(args.download_dir, exist_ok=True)

    while True:
        try:
            for song in poll_queue(args.base_url):
                try:
                    result_path = download_song(song, args.base_url, args.download_dir)
                    if args.upload_host and args.upload_user and args.upload_key:
                        upload_to_oracle(result_path, args.upload_host, args.upload_user, args.upload_key, args.upload_path)
                        print(f"Uploaded {result_path} to {args.upload_host}:{args.upload_path}")
                    report_result(args.base_url, song["id"], "downloaded", local_path=result_path)
                    print(f"Downloaded {song['title']} -> {result_path}")
                except Exception as exc:  # pragma: no cover - runtime failure path
                    report_result(args.base_url, song["id"], "failed", error=str(exc))
                    print(f"Failed {song['title']}: {exc}", file=sys.stderr)
        except requests.RequestException as exc:  # pragma: no cover - runtime failure path
            print(f"Queue poll failed: {exc}", file=sys.stderr)

        time.sleep(10)


if __name__ == "__main__":
    main()
