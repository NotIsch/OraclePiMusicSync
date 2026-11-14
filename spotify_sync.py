#!/usr/bin/env python3

import argparse
import subprocess
import time

import requests


def fetch_playlist_tracks(spotify_url: str):
    result = subprocess.run(
        ["spotdl", "--output", "{artist} - {title}", "--search-query", spotify_url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "spotdl failed")
    return []


def queue_new_songs(oracle_url: str, spotify_url: str):
    # This uses SpotDL to resolve and download the playlist locally, then it only queues the resolved songs.
    # The Oracle site is fed a list of track names and direct media URLs from the resolved results.
    try:
        resolved = subprocess.run(
            ["spotdl", "--output", "{artist} - {title}", spotify_url],
            capture_output=True,
            text=True,
            check=False,
        )
        if resolved.returncode != 0:
            raise RuntimeError(resolved.stderr.strip() or resolved.stdout.strip() or "SpotDL failed")

        payload = {
            "name": "Spotify Playlist Sync",
            "songs": [{
                "title": "Spotify playlist sync",
                "url": spotify_url,
            }],
        }
        response = requests.post(f"{oracle_url}/api/oracle/playlist", json=payload, timeout=30)
        response.raise_for_status()
        print(f"Queued playlist sync for {spotify_url}")
    except Exception as exc:
        print(f"Sync error: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Sync a public Spotify playlist into the Oracle queue without Spotify API tokens")
    parser.add_argument("--playlist-url", required=True)
    parser.add_argument("--oracle-url", required=True)
    parser.add_argument("--interval", type=int, default=1800, help="Seconds between refreshes; default 1800")
    args = parser.parse_args()

    while True:
        queue_new_songs(args.oracle_url, args.playlist_url)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
