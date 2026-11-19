import { useEffect, useRef, useState } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import { PlayerProvider, usePlayer, formatTime } from "./PlayerContext";
import { write, message } from "./api";
import useResource from "./useResource";
import { Cover, Modal, Notice, SongList, State } from "./components";
import BatchUpload from "./BatchUpload";
import AnalyticsDashboard from "./AnalyticsDashboard";
import { readTrackMetadata, audioType } from "./batchFiles";

export default function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  );
}
function Gate() {
  const auth = useAuth();
  if (auth.loading)
    return (
      <div className="boot" role="status">
        Restoring your session…
      </div>
    );
  if (auth.error)
    return (
      <div className="boot">
        <Notice error={auth.error} />
        <button onClick={auth.restore}>Retry connection</button>
      </div>
    );
  return auth.user ? (
    <PlayerProvider key={auth.user.id}>
      <Shell />
    </PlayerProvider>
  ) : (
    <AuthScreen />
  );
}
function AuthScreen() {
  const auth = useAuth(),
    [register, setRegister] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      register
        ? await auth.register(data)
        : await auth.login(data.email, data.password);
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-layout">
      <section className="auth-art">
        <Link to="/" className="brand">
          <span className="brand-mark">r</span>raagify
          <span className="brand-dot">.</span>
        </Link>
        <div className="vinyl">
          <div className="vinyl-label">
            r<span>RAAGIFY / SIDE A</span>
          </div>
        </div>
        <div className="auth-caption">
          <span className="eyebrow">A LITTLE RHYTHM. A LOT OF YOU.</span>
          <h1>
            Find your
            <br />
            kind of sound.
          </h1>
          <p>
            A place for the songs you love.
            <br />
            And the ones you haven’t met yet.
          </p>
        </div>
        <small>YOUR MUSIC. YOUR MOMENT.</small>
      </section>
      <section className="auth-form">
        <span className="eyebrow">WELCOME TO RAAGIFY</span>
        <h2>
          {register ? "Make yourself at home." : "Good to have you back."}
        </h2>
        <p className="muted">
          {register
            ? "Create an account and start your collection."
            : "Sign in to pick up where you left off."}
        </p>
        <form onSubmit={submit}>
          {register && (
            <label>
              Your name
              <input
                name="displayName"
                autoComplete="name"
                required
                maxLength={100}
                placeholder="What should we call you?"
              />
            </label>
          )}
          <label>
            Email address
            <input
              name="email"
              type="email"
              autoComplete="email"
              required
              maxLength={190}
              placeholder="you@example.com"
            />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={register ? 10 : 1}
              maxLength={72}
              placeholder={
                register ? "At least 10 characters" : "Your password"
              }
            />
          </label>
          <Notice error={error} />
          <button className="primary" disabled={busy}>
            {busy ? "One moment…" : register ? "Create account →" : "Sign in →"}
          </button>
        </form>
        <p className="auth-switch">
          {register ? "Already have an account?" : "New around here?"}{" "}
          <button
            onClick={() => {
              setRegister(!register);
              setError("");
            }}
          >
            {register ? "Sign in" : "Join Raagify"}
          </button>
        </p>
      </section>
    </div>
  );
}
function Shell() {
  const { user, logout } = useAuth(),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function signout() {
    setBusy(true);
    try {
      await logout();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" to="/">
          <span className="brand-mark">r</span>raagify
          <span className="brand-dot">.</span>
        </Link>
        <div className="nav-label">YOUR DAILY SOUNDTRACK</div>
        <nav>
          <NavLink end to="/">
            <span aria-hidden="true">◉</span>Discover
          </NavLink>
          <NavLink to="/browse">
            <span aria-hidden="true">⌕</span>Browse & search
          </NavLink>
          <div className="nav-label">YOUR COLLECTION</div>
          <NavLink to="/likes">
            <span aria-hidden="true">♡</span>Liked songs
          </NavLink>
          <NavLink to="/playlists">
            <span aria-hidden="true">▤</span>Your playlists
          </NavLink>
          <NavLink to="/recent">
            <span aria-hidden="true">◷</span>Recently played
          </NavLink>
          {user.role === "ADMIN" && (
            <>
              <NavLink to="/admin/analytics">
                <span aria-hidden="true">▥</span>Analytics
              </NavLink>
              <NavLink to="/admin" end>
                <span aria-hidden="true">↑</span>Manage music
              </NavLink>
            </>
          )}
        </nav>
        <div className="sidebar-note">
          <span>MADE FOR YOUR EARS</span>
          <p>
            Stay curious.
            <br />
            Keep listening.
          </p>
          <div className="mini-wave" aria-hidden="true">
            {[5, 12, 22, 9, 17, 26, 12, 5].map((height, index) => (
              <span key={index} style={{ height }} />
            ))}
          </div>
        </div>
        <div className="profile">
          <div className="avatar">
            {user.displayName.slice(0, 1).toUpperCase()}
          </div>
          <div>
            <strong>{user.displayName}</strong>
            <small>
              {user.role === "ADMIN" ? "Administrator" : "Listener"}
            </small>
          </div>
          <button disabled={busy} aria-label="Sign out" onClick={signout}>
            ↗
          </button>
        </div>
        <Notice error={error} />
      </aside>
      <main>
        <header className="topbar">
          <span>GOOD MUSIC FINDS A WAY.</span>
          <Link to="/browse" className="search-shortcut">
            ⌕ <span>Find your next favorite</span>
          </Link>
        </header>
        <div className="content">
          <Routes>
            <Route path="/" element={<Discover />} />
            <Route path="/browse" element={<Browse />} />
            <Route path="/likes" element={<Library type="likes" />} />
            <Route path="/recent" element={<Library type="recent" />} />
            <Route path="/playlists" element={<Playlists />} />
            <Route path="/playlists/:id" element={<Playlist />} />
            <Route path="/songs/:id" element={<Song />} />
            <Route
              path="/admin"
              element={
                user.role === "ADMIN" ? <Admin /> : <Navigate to="/" replace />
              }
            />
            <Route
              path="/admin/analytics"
              element={
                user.role === "ADMIN" ? (
                  <AnalyticsDashboard />
                ) : (
                  <Navigate to="/" replace />
                )
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
        <footer className="page-footer">
          RAAGIFY <span>A good day starts with a good song.</span>
        </footer>
      </main>
    </div>
  );
}
function Heading({ eyebrow, title, text, action }) {
  return (
    <div className="heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        {text && <p className="muted">{text}</p>}
      </div>
      {action}
    </div>
  );
}
function Discover() {
  const { user } = useAuth(),
    r = useResource("/recommendations"),
    player = usePlayer();
  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow">YOUR NEXT FAVORITE IS OUT THERE</span>
          <h1>
            Let the music
            <br />
            take you somewhere.
          </h1>
          <p>A fresh mix of familiar feelings and new discoveries.</p>
          <button
            className="primary"
            disabled={!r.data?.length}
            onClick={() => player.play(r.data[0], r.data)}
          >
            ▶ Play your mix
          </button>
        </div>
        <div className="hero-record" aria-hidden="true">
          <div>
            r<span>FEEL SOMETHING.</span>
          </div>
        </div>
        <span className="hero-number">VOL. 01 / DAILY DISCOVERIES</span>
      </section>
      <Heading
        eyebrow={`CURATED FOR ${user.displayName.toUpperCase()}`}
        title="Made for your mood"
        text="Recommendations shaped by your likes and listening. Start fresh with popular tracks."
        action={
          <Link className="text-link" to="/browse">
            Explore all music ↗
          </Link>
        }
      />
      <State
        resource={r}
        empty={!r.data?.length}
        emptyTitle="Your soundtrack starts here"
        emptyText="Songs uploaded by an administrator will appear here. Like and play them to shape your recommendations."
      >
        <div className="card-grid">
          {r.data?.slice(0, 5).map((song) => (
            <article className="song-card" key={song.id}>
              <div className="card-art">
                <Cover song={song} queue={r.data} />
                <button
                  aria-label={`Play ${song.title}`}
                  onClick={() => player.play(song, r.data)}
                >
                  ▶
                </button>
              </div>
              <Link to={`/songs/${song.id}`}>{song.title}</Link>
              <p>{song.artist}</p>
              <span>{song.genre || "Unclassified"}</span>
            </article>
          ))}
        </div>
        <SongList songs={r.data || []} refresh={r.refresh} />
      </State>
    </>
  );
}
function Browse() {
  const [q, setQ] = useState(""),
    [query, setQuery] = useState(""),
    [page, setPage] = useState(0);
  const r = useResource(
    `/songs?q=${encodeURIComponent(query)}&page=${page}&size=15`,
  );
  function search(e) {
    e.preventDefault();
    setPage(0);
    setQuery(q);
  }
  return (
    <>
      <Heading
        eyebrow="THE WHOLE COLLECTION"
        title="Follow your curiosity."
        text="Search by song, artist, or genre."
      />
      <form className="search-form" onSubmit={search}>
        <span aria-hidden="true">⌕</span>
        <input
          aria-label="Search music"
          placeholder="A song, an artist, a feeling…"
          value={q}
          maxLength={200}
          onChange={(e) => setQ(e.target.value)}
        />
        <button className="primary">Search</button>
      </form>
      <State
        resource={r}
        empty={!r.data?.content.length}
        emptyTitle={query ? "No matching tracks" : "The collection is waiting"}
        emptyText={
          query
            ? "Try another title, artist, or genre."
            : "An administrator can upload the first song from Manage music."
        }
      >
        <div className="section-label">
          {r.data?.totalElements} TRACKS {query && `/ “${query}”`}
        </div>
        <SongList songs={r.data?.content || []} refresh={r.refresh} />
      </State>
      <div className="pagination">
        <button
          disabled={page === 0 || r.loading}
          onClick={() => setPage((p) => p - 1)}
        >
          ← Previous
        </button>
        <span>
          Page {page + 1} of {Math.max(1, r.data?.totalPages || 0)}
        </span>
        <button
          disabled={r.loading || !r.data || page + 1 >= r.data.totalPages}
          onClick={() => setPage((p) => p + 1)}
        >
          Next →
        </button>
      </div>
    </>
  );
}
function Library({ type }) {
  const liked = type === "likes",
    r = useResource(liked ? "/likes" : "/history/recent");
  return (
    <>
      <Heading
        eyebrow="YOUR COLLECTION"
        title={liked ? "All your favorites." : "Back for another listen."}
        text={
          liked
            ? "The songs that hit a little different."
            : "Your 30 most recently played tracks."
        }
      />
      <State
        resource={r}
        empty={!r.data?.length}
        emptyTitle={
          liked ? "Make room for favorites" : "A little quiet in here"
        }
        emptyText={
          liked
            ? "Tap the heart next to any track to save it here."
            : "Play a song and it will appear here."
        }
      >
        <SongList songs={r.data || []} refresh={r.refresh} />
      </State>
    </>
  );
}
function Playlists() {
  const r = useResource("/playlists"),
    [name, setName] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function create(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await write({ method: "post", url: "/playlists", data: { name } });
      setName("");
      r.refresh();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="MIX IT YOUR WAY"
        title="A place for every mood."
        text="Make a playlist. Give it a name. Make it yours."
      />
      <form onSubmit={create} className="inline-form">
        <label>
          New playlist
          <input
            required
            maxLength={120}
            placeholder="Late nights, long drives…"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <button className="primary" disabled={busy}>
          {busy ? "Creating…" : "＋ Create playlist"}
        </button>
      </form>
      <Notice error={error} />
      <State
        resource={r}
        empty={!r.data?.length}
        emptyTitle="Your first mix awaits"
        emptyText="Create a playlist above, then add songs with the + button."
      >
        <div className="playlist-grid">
          {r.data?.map((p) => (
            <Link
              to={`/playlists/${p.id}`}
              className="playlist-card"
              key={p.id}
            >
              <div className={`playlist-art tone-${p.id % 5}`}>▤</div>
              <h2>{p.name}</h2>
              <p>
                {p.songs.length} songs ·{" "}
                {formatTime(p.songs.reduce((n, s) => n + s.durationSeconds, 0))}
              </p>
              <span>OPEN PLAYLIST ↗</span>
            </Link>
          ))}
        </div>
      </State>
    </>
  );
}
function Playlist() {
  const { id } = useParams(),
    r = useResource(`/playlists/${id}`),
    navigate = useNavigate(),
    player = usePlayer(),
    [name, setName] = useState(""),
    [renaming, setRenaming] = useState(false),
    [deleting, setDeleting] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function mutate(config) {
    setBusy(true);
    setError("");
    try {
      const result = await write(config);
      if (config.method === "delete" && config.url === `/playlists/${id}`)
        navigate("/playlists");
      else {
        r.setData(result.data);
        setRenaming(false);
      }
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  function move(i, delta) {
    if (busy) return;
    const ids = r.data.songs.map((s) => s.id);
    [ids[i], ids[i + delta]] = [ids[i + delta], ids[i]];
    mutate({
      method: "put",
      url: `/playlists/${id}/songs/order`,
      data: { songIds: ids },
    });
  }
  return (
    <State resource={r}>
      <Heading
        eyebrow="YOUR PERSONAL MIX"
        title={r.data?.name}
        text={`${r.data?.songs.length || 0} songs`}
        action={
          <div className="button-group">
            <button
              className="primary"
              disabled={!r.data?.songs.length}
              onClick={() => player.play(r.data.songs[0], r.data.songs)}
            >
              ▶ Play all
            </button>
            <button
              disabled={busy}
              onClick={() => {
                setName(r.data.name);
                setRenaming(true);
              }}
            >
              Rename
            </button>
            <button disabled={busy} onClick={() => setDeleting(true)}>
              Delete
            </button>
          </div>
        }
      />
      <Notice error={error} />
      {r.data?.songs.length ? (
        <SongList
          songs={r.data.songs}
          refresh={r.refresh}
          onMove={move}
          onRemove={(song) => {
            if (!busy)
              mutate({
                method: "delete",
                url: `/playlists/${id}/songs/${song.id}`,
              });
          }}
        />
      ) : (
        <div className="state">
          <h2>Give this mix a soundtrack.</h2>
          <p>Add songs with the + button in Browse & search.</p>
          <Link className="primary" to="/browse">
            Find music →
          </Link>
        </div>
      )}
      {renaming && (
        <Modal
          title="Rename playlist"
          onClose={() => !busy && setRenaming(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              mutate({
                method: "put",
                url: `/playlists/${id}`,
                data: { name },
              });
            }}
          >
            <label>
              Playlist name
              <input
                required
                maxLength={120}
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            <Notice error={error} />
            <button className="primary" disabled={busy}>
              Save name
            </button>
          </form>
        </Modal>
      )}
      {deleting && (
        <Modal
          title="Delete playlist?"
          onClose={() => !busy && setDeleting(false)}
        >
          <p>Delete “{r.data?.name}” from your collection?</p>
          <Notice error={error} />
          <button
            className="danger"
            disabled={busy}
            onClick={() =>
              mutate({ method: "delete", url: `/playlists/${id}` })
            }
          >
            Delete playlist
          </button>
        </Modal>
      )}
    </State>
  );
}
function Song() {
  const { id } = useParams(),
    r = useResource(`/songs/${id}`),
    similar = useResource(`/songs/${id}/similar`),
    player = usePlayer();
  return (
    <>
      <State resource={r}>
        <div className="song-detail">
          <Cover
            song={r.data || { id: 0 }}
            queue={r.data ? [r.data, ...(similar.data || [])] : undefined}
          />
          <div>
            <span className="eyebrow">
              TRACK / {r.data?.genre || "Unclassified"}
            </span>
            <h1>{r.data?.title}</h1>
            <p>
              {r.data?.artist} · {r.data?.album || "Single"} ·{" "}
              {formatTime(r.data?.durationSeconds)}
            </p>
            <button
              className="primary"
              onClick={() =>
                player.play(r.data, [r.data, ...(similar.data || [])])
              }
            >
              ▶ Play track
            </button>
          </div>
        </div>
        <SongList songs={r.data ? [r.data] : []} refresh={r.refresh} />
      </State>
      <Heading
        eyebrow="KEEP THE FEELING GOING"
        title="More like this"
        text="Similar audio features, with genre-based suggestions when features are pending."
      />
      <State
        resource={similar}
        empty={!similar.data?.length}
        emptyTitle="More music is on the way"
        emptyText="Similar tracks will appear as the collection grows."
      >
        <SongList songs={similar.data || []} refresh={similar.refresh} />
      </State>
    </>
  );
}
function Admin() {
  const [page, setPage] = useState(0),
    r = useResource(`/songs?size=50&page=${page}`),
    [uploading, setUploading] = useState(false),
    [batching, setBatching] = useState(false),
    [editing, setEditing] = useState(null),
    [deleting, setDeleting] = useState(null),
    [error, setError] = useState(""),
    [artworkMessage, setArtworkMessage] = useState(""),
    [busy, setBusy] = useState(false);
  async function remove() {
    setBusy(true);
    setError("");
    try {
      await write({ method: "delete", url: `/admin/songs/${deleting.id}` });
      setDeleting(null);
      r.refresh();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function retry(song) {
    setBusy(true);
    setError("");
    try {
      await write({
        method: "post",
        url: `/admin/songs/${song.id}/features/retry`,
      });
      r.refresh();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function restoreCovers() {
    setBusy(true);
    setError("");
    setArtworkMessage("");
    try {
      const { data } = await write({
        method: "post",
        url: "/admin/songs/artwork/restore",
      });
      setArtworkMessage(
        `${data.restored} covers restored · ${data.unchanged} unchanged · ${data.failed} failed`,
      );
      r.refresh();
    } catch (error) {
      setError(message(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="ADMINISTRATOR STUDIO"
        title="Keep the collection growing."
        text="Upload audio, add artwork, and make every track easy to find."
        action={
          <div className="button-group">
            <button onClick={() => setBatching(true)}>Batch upload</button>
            <button disabled={busy} onClick={restoreCovers}>
              Restore embedded covers
            </button>
            <button className="primary" onClick={() => setUploading(true)}>
              ↑ Upload a song
            </button>
          </div>
        }
      />
      <Notice error={error} />
      {artworkMessage && (
        <p className="artwork-result" role="status">
          {artworkMessage}
        </p>
      )}
      <State
        resource={r}
        empty={!r.data?.content.length}
        emptyTitle="Upload your first track"
        emptyText="WAV, MP3, or OGG audio with optional PNG, JPEG, or WebP artwork."
      >
        {r.data?.content.map((song) => (
          <div className="admin-row" key={song.id}>
            <Cover song={song} />
            <div>
              <strong>{song.title}</strong>
              <p>
                {song.artist} · {song.genre || "Unclassified"}
              </p>
              <small
                className={
                  song.featureStatus === "PENDING" ? "pending" : "ready"
                }
              >
                {song.featureStatus === "PENDING"
                  ? "Features pending — genre fallback"
                  : `Features ready · Genre: ${song.genreSource === "ADMIN_OVERRIDE" ? "curated" : song.genreSource === "METADATA" ? "embedded" : "unclassified"}`}
              </small>
            </div>
            <div className="button-group">
              {song.featureStatus === "PENDING" && (
                <button disabled={busy} onClick={() => retry(song)}>
                  Retry features
                </button>
              )}
              <button onClick={() => setEditing(song)}>Edit</button>
              {!song.coverUrl && (
                <button
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    setError("");
                    try {
                      await write({
                        method: "post",
                        url: `/admin/songs/${song.id}/artwork/restore`,
                      });
                      r.refresh();
                    } catch (error) {
                      setError(message(error));
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Restore cover
                </button>
              )}
              <button onClick={() => setDeleting(song)}>Delete</button>
            </div>
          </div>
        ))}
        <div className="pagination">
          <button
            disabled={page === 0 || r.loading}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </button>
          <span>
            Page {page + 1} of {Math.max(1, r.data?.totalPages || 0)}
          </span>
          <button
            disabled={r.loading || !r.data || page + 1 >= r.data.totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      </State>
      {batching && (
        <BatchUpload
          onClose={() => {
            setBatching(false);
            r.refresh();
          }}
          onChanged={r.refresh}
        />
      )}
      {(uploading || editing) && (
        <SongForm
          song={editing}
          onClose={() => {
            setUploading(false);
            setEditing(null);
          }}
          onSaved={() => {
            setUploading(false);
            setEditing(null);
            r.refresh();
          }}
        />
      )}
      {deleting && (
        <Modal title="Delete song?" onClose={() => !busy && setDeleting(null)}>
          <p>
            Delete “{deleting.title}” and its audio from the collection? This
            also removes its likes and playlist entries.
          </p>
          <Notice error={error} />
          <button className="danger" disabled={busy} onClick={remove}>
            Delete song
          </button>
        </Modal>
      )}
    </>
  );
}
function SongForm({ song, onClose, onSaved }) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [detecting, setDetecting] = useState(false),
    [embeddedCover, setEmbeddedCover] = useState(null);
  const formRef = useRef(null),
    metadataAbort = useRef(null),
    autofilled = useRef({});
  useEffect(() => () => metadataAbort.current?.abort(), []);
  async function detectMetadata(event) {
    const file = event.target.files?.[0];
    metadataAbort.current?.abort();
    setEmbeddedCover(null);
    if (!file) return;
    const controller = new AbortController();
    metadataAbort.current = controller;
    setDetecting(true);
    const metadata = await readTrackMetadata(file, controller.signal);
    if (controller.signal.aborted || !formRef.current) return;
    for (const key of [
      "title",
      "artist",
      "album",
      "genre",
      "durationSeconds",
    ]) {
      const input = formRef.current.elements.namedItem(key);
      if (
        input &&
        metadata[key] &&
        (!input.value || input.value === autofilled.current[key])
      ) {
        input.value = metadata[key];
        autofilled.current[key] = metadata[key];
      }
    }
    setEmbeddedCover(metadata.cover);
    setDetecting(false);
  }
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    if (!song) {
      const file = form.get("audio");
      if (file?.size)
        form.set(
          "audio",
          new File([file], file.name, { type: audioType(file) || file.type }),
        );
      if (!form.get("cover")?.size && embeddedCover)
        form.set("cover", embeddedCover);
    }
    try {
      await write({
        method: song ? "put" : "post",
        url: song ? `/admin/songs/${song.id}` : "/admin/songs",
        data: song
          ? {
              ...Object.fromEntries(form),
              durationSeconds: Number(form.get("durationSeconds")),
            }
          : form,
      });
      onSaved();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title={song ? "Edit song" : "Upload a song"}
      onClose={() => !busy && onClose()}
    >
      <form ref={formRef} onSubmit={submit}>
        <label>
          Title
          <input
            name="title"
            required
            maxLength={160}
            defaultValue={song?.title}
          />
        </label>
        <label>
          Artist
          <input
            name="artist"
            required
            maxLength={160}
            defaultValue={song?.artist}
          />
        </label>
        <div className="form-pair">
          <label>
            Album
            <input
              name="album"
              maxLength={160}
              defaultValue={song?.album || ""}
            />
          </label>
          <label>
            Duration (seconds)
            <input
              name="durationSeconds"
              type="number"
              required
              min="1"
              max="86400"
              defaultValue={song?.durationSeconds}
            />
          </label>
        </div>
        <label>
          Genre tags (optional)
          <input
            name="genre"
            maxLength={80}
            defaultValue={song?.genre || ""}
            placeholder={
              song
                ? "Leave blank for no genre"
                : "Leave blank to use embedded genre tags"
            }
          />
        </label>
        {!song && (
          <>
            <label>
              Audio · WAV, MP3, OGG · up to 25 MiB
              <input
                name="audio"
                type="file"
                accept="audio/wav,audio/x-wav,audio/mpeg,audio/ogg"
                required
                onChange={detectMetadata}
              />
            </label>
            <label>
              Cover · PNG, JPEG, WebP · up to 5 MiB
              <input
                name="cover"
                type="file"
                accept="image/png,image/jpeg,image/webp"
              />
            </label>
            <p className="form-help">
              {detecting
                ? "Reading embedded song details… "
                : embeddedCover
                  ? "Embedded cover found. A separate cover overrides it. "
                  : ""}
              Audio features and embedded tags are extracted on upload. Embedded
              artwork is used when no separate cover is chosen. If analysis is
              unavailable, the song is saved with features pending.
            </p>
          </>
        )}
        <Notice error={error} />
        <button className="primary" disabled={busy || detecting}>
          {detecting
            ? "Reading song details…"
            : busy
              ? "Saving and analyzing…"
              : song
                ? "Save changes"
                : "Upload song"}
        </button>
      </form>
    </Modal>
  );
}
