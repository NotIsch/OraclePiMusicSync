# Oracle Music Tracker

This project is a free, no-API music tracking system for a Raspberry Pi and an Oracle VM.

It is designed to:

1. show a simple web dashboard for playlists and song status,
2. sync a public Spotify playlist without using the Spotify API,
3. let a Pi download songs with free tools,
4. upload those songs to the Oracle VM, and
5. keep checking the playlist every 30 minutes for new tracks.

## Free setup, no Spotify API required

This version is intentionally free to run:

- no Spotify Developer app needed
- no paid services
- uses `spotdl` and `yt-dlp` via public playlist access and free download tools

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## API overview

- `GET /` — dashboard
- `POST /api/oracle/playlist` — add a playlist and queue songs
- `GET /api/playlists` — view stored playlists and song status
- `GET /api/pi/queue` — fetch songs for the Pi
- `POST /api/pi/report` — mark a song as downloaded or failed
- `GET /api/health` — service health check

## Public Spotify playlist sync

This project is set up to use public Spotify playlist links without a Spotify API key.

Run:

```bash
python spotify_sync.py \
  --playlist-url "https://open.spotify.com/playlist/3JCyTn0t8T0iw3UM8ZzHil?si=b530f93115504715" \
  --oracle-url http://your-oracle-host:5000 \
  --interval 1800
```

This checks the playlist every 30 minutes and adds any new songs to the Oracle queue.

## Pi worker

On the Pi, install the tools:

```bash
pip install -r requirements.txt
pip install spotdl yt-dlp
python3 pi_client.py \
  --base-url http://your-oracle-host:5000 \
  --download-dir /home/pi/music \
  --upload-host 123.45.67.89 \
  --upload-user ubuntu \
  --upload-key /home/pi/.ssh/id_ed25519 \
  --upload-path /home/ubuntu/media/music
```

Then it will:

- fetch queued songs,
- download each one with `yt-dlp`,
- upload it to the Oracle VM,
- mark it as downloaded in the Oracle dashboard.

## Oracle VM setup

On the VM:

```bash
mkdir -p /home/ubuntu/media/music
```

Then allow the Pi to SSH in:

```bash
ssh-keygen -t ed25519 -C "pi@home"
ssh-copy-id -i ~/.ssh/id_ed25519.pub ubuntu@123.45.67.89
```

## GitHub

I can’t push to your GitHub account from here without your credentials or repo URL, but this project is ready to be committed and pushed from your machine.

Use:

```bash
git init
git add .
git commit -m "Initial Oracle Music Tracker"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

That will upload it to your GitHub account.
