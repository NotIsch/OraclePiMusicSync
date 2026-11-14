async function loadPlaylists() {
  const response = await fetch('/api/playlists');
  const data = await response.json();
  const playlists = data.playlists || [];

  const container = document.getElementById('playlist-container');
  const playlistCount = document.getElementById('playlist-count');
  const queuedCount = document.getElementById('queued-count');
  const downloadedCount = document.getElementById('downloaded-count');

  playlistCount.textContent = String(playlists.length);

  let queued = 0;
  let downloaded = 0;

  if (!playlists.length) {
    container.innerHTML = '<p>No playlists yet.</p>';
    queuedCount.textContent = '0';
    downloadedCount.textContent = '0';
    return;
  }

  container.innerHTML = playlists.map((playlist) => {
    const songs = playlist.songs || [];
    queued += songs.filter((song) => song.status === 'queued' || song.status === 'retrying' || song.status === 'downloading').length;
    downloaded += songs.filter((song) => song.status === 'downloaded').length;

    const rows = songs.length
      ? songs.map((song) => {
          const badgeClass = (song.status || 'queued').toLowerCase();
          return `
            <tr>
              <td>${song.title || 'Unknown song'}</td>
              <td><a href="${song.url}" target="_blank" rel="noreferrer">Open</a></td>
              <td><span class="badge ${badgeClass}">${song.status || 'queued'}</span></td>
              <td>${song.local_path || '-'}</td>
            </tr>
          `;
        }).join('')
      : '<tr><td colspan="4">No songs yet.</td></tr>';

    return `
      <div class="playlist-card">
        <div class="playlist-head">
          <h3>${playlist.name}</h3>
          <span>${songs.length} songs</span>
        </div>
        <table class="song-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>URL</th>
              <th>Status</th>
              <th>Local path</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }).join('');

  queuedCount.textContent = String(queued);
  downloadedCount.textContent = String(downloaded);
}

async function handlePlaylistSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('playlist-name').value.trim();
  const rawText = document.getElementById('song-list').value;

  const entries = rawText
    .split(/[\r\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean);

  const songs = entries.map((url, index) => ({
    title: `Track ${index + 1}`,
    url,
  }));

  await fetch('/api/oracle/playlist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, songs }),
  });

  document.getElementById('playlist-form').reset();
  await loadPlaylists();
}

document.getElementById('playlist-form').addEventListener('submit', handlePlaylistSubmit);
loadPlaylists();
setInterval(loadPlaylists, 5000);
