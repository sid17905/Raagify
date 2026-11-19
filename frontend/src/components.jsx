import { useState } from "react";
import { Link } from "react-router-dom";
import { write, message } from "./api";
import { usePlayer, formatTime } from "./PlayerContext";
import useResource from "./useResource";
export function Notice({ error }) {
  return error ? (
    <div className="notice" role="alert">
      {error}
    </div>
  ) : null;
}
export function State({
  resource,
  children,
  empty = false,
  emptyTitle = "Nothing here yet",
  emptyText = "Your next discovery is a play away.",
}) {
  if (resource.loading)
    return (
      <div className="state" role="status">
        <div className="spinner" />
        Loading your music…
      </div>
    );
  if (resource.error)
    return (
      <div className="state">
        <Notice error={resource.error} />
        <button onClick={resource.refresh}>Try again</button>
      </div>
    );
  if (empty)
    return (
      <div className="state">
        <span className="empty-disc">♫</span>
        <h2>{emptyTitle}</h2>
        <p>{emptyText}</p>
      </div>
    );
  return children;
}
export function Cover({ song }) {
  return (
    <div className={`cover tone-${song.id % 5}`}>
      {song.coverUrl ? (
        <img
          src={song.coverUrl}
          alt={`${song.title} cover`}
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
      ) : (
        <span aria-hidden="true">♫</span>
      )}
    </div>
  );
}
export function SongList({ songs = [], refresh, onRemove, onMove }) {
  const player = usePlayer(),
    [busy, setBusy] = useState(null),
    [error, setError] = useState(""),
    [addSong, setAddSong] = useState(null);
  async function like(song) {
    setBusy(song.id);
    setError("");
    try {
      await write({
        method: song.liked ? "delete" : "post",
        url: `/likes/${song.id}`,
      });
      refresh?.();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(null);
    }
  }
  return (
    <>
      <Notice error={error} />
      <div className="song-list">
        <div className="song-header">
          <span>#</span>
          <span>TRACK / ARTIST</span>
          <span className="album">ALBUM</span>
          <span>TIME</span>
          <span />
        </div>
        {songs.map((song, i) => (
          <div
            className={`song-row ${player.current?.id === song.id ? "active" : ""}`}
            key={song.id}
          >
            <button
              className="row-play"
              aria-label={`Play ${song.title}`}
              onClick={() => player.play(song, songs)}
            >
              {player.current?.id === song.id && player.playing ? "Ⅱ" : i + 1}
              <span>▶</span>
            </button>
            <div className="track">
              <Cover song={song} />
              <div>
                <Link to={`/songs/${song.id}`}>{song.title}</Link>
                <span>
                  {song.artist} <small>{song.genre || "Unclassified"}</small>
                </span>
              </div>
            </div>
            <span className="album muted">{song.album || "Single"}</span>
            <span className="muted time">
              {formatTime(song.durationSeconds)}
            </span>
            <div className="row-actions">
              <button
                disabled={busy === song.id}
                className={song.liked ? "heart liked" : "heart"}
                aria-label={`${song.liked ? "Unlike" : "Like"} ${song.title}`}
                onClick={() => like(song)}
              >
                {song.liked ? "♥" : "♡"}
              </button>
              <button
                aria-label={`Add ${song.title} to playlist`}
                onClick={() => setAddSong(song)}
              >
                ＋
              </button>
              {onMove && (
                <>
                  <button
                    aria-label={`Move ${song.title} up`}
                    disabled={i === 0}
                    onClick={() => onMove(i, -1)}
                  >
                    ↑
                  </button>
                  <button
                    aria-label={`Move ${song.title} down`}
                    disabled={i === songs.length - 1}
                    onClick={() => onMove(i, 1)}
                  >
                    ↓
                  </button>
                </>
              )}
              {onRemove && (
                <button
                  aria-label={`Remove ${song.title}`}
                  onClick={() => onRemove(song)}
                >
                  ×
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      {addSong && (
        <AddToPlaylist song={addSong} onClose={() => setAddSong(null)} />
      )}
    </>
  );
}
export function Modal({
  title,
  children,
  onClose,
  className = "",
  closeDisabled = false,
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`modal ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-title">
          <h2>{title}</h2>
          <button
            aria-label="Close dialog"
            disabled={closeDisabled}
            onClick={onClose}
          >
            ×
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
function AddToPlaylist({ song, onClose }) {
  const resource = useResource("/playlists"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [selected, setSelected] = useState("");
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await write({
        method: "post",
        url: `/playlists/${selected}/songs/${song.id}`,
      });
      onClose();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Add to playlist" onClose={onClose}>
      <p className="muted">
        {song.title} · {song.artist}
      </p>
      <State
        resource={resource}
        empty={resource.data?.length === 0}
        emptyTitle="Create your first playlist"
        emptyText="Head to Your playlists to make a home for this song."
      >
        <form onSubmit={submit}>
          <label>
            Playlist
            <select
              aria-label="Playlist"
              required
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              <option value="">Choose a playlist</option>
              {resource.data?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <Notice error={error} />
          <button className="primary" disabled={busy || !selected}>
            {busy ? "Adding…" : "Add song"}
          </button>
        </form>
      </State>
    </Modal>
  );
}
