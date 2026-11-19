import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Cover, State } from "./components";
import useResource from "./useResource";

export function ListeningChart({ points }) {
  const [selected, setSelected] = useState(points.length - 1);
  useEffect(() => setSelected(points.length - 1), [points]);
  if (!points.some((point) => point.plays > 0))
    return (
      <div className="analytics-empty">
        No listening activity in this period. Plays will appear as listeners use
        the player.
      </div>
    );
  const width = 800,
    height = 230,
    pad = 35,
    max = Math.max(1, ...points.map((point) => point.plays));
  const coordinates = points.map((point, index) => ({
    x: pad + (index * (width - pad * 2)) / Math.max(1, points.length - 1),
    y: height - pad - (point.plays / max) * (height - pad * 2),
  }));
  const focus = points[selected] || points[points.length - 1];
  return (
    <>
      <div className="chart-focus" aria-live="polite">
        {focus.date} <strong>{focus.plays.toLocaleString()} plays</strong>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="group"
        aria-label="Daily listening activity. Focus or hover a point for its date and play count."
      >
        {[0, 0.5, 1].map((fraction) => (
          <g key={fraction}>
            <line
              x1={pad}
              x2={width - pad}
              y1={height - pad - fraction * (height - pad * 2)}
              y2={height - pad - fraction * (height - pad * 2)}
              stroke="#393943"
            />
            <text
              x="0"
              y={height - pad - fraction * (height - pad * 2) + 4}
              fill="#93939f"
              fontSize="12"
            >
              {Math.round(max * fraction)}
            </text>
          </g>
        ))}
        <polyline
          points={coordinates.map((point) => `${point.x},${point.y}`).join(" ")}
          fill="none"
          stroke="#ffc8a5"
          strokeWidth="3"
        />
        {coordinates.map((point, index) => (
          <circle
            key={points[index].date}
            cx={point.x}
            cy={point.y}
            r={index === selected ? 6 : 4}
            fill={index === selected ? "#fff0e5" : "#ffc8a5"}
            tabIndex="0"
            role="button"
            aria-label={`${points[index].date}: ${points[index].plays} plays`}
            onMouseEnter={() => setSelected(index)}
            onFocus={() => setSelected(index)}
            onClick={() => setSelected(index)}
          />
        ))}
        {[
          ...new Set([
            0,
            Math.floor((points.length - 1) / 2),
            points.length - 1,
          ]),
        ].map((index) => (
          <text
            key={index}
            x={coordinates[index].x}
            y={height - 7}
            fill="#93939f"
            fontSize="12"
            textAnchor="middle"
          >
            {points[index].date.slice(5)}
          </text>
        ))}
      </svg>
      <details className="analytics-data">
        <summary>View daily counts</summary>
        <table>
          <thead>
            <tr>
              <th>Date (UTC)</th>
              <th>Plays</th>
            </tr>
          </thead>
          <tbody>
            {points.map((point) => (
              <tr key={point.date}>
                <td>{point.date}</td>
                <td>{point.plays}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  );
}

export default function AnalyticsDashboard() {
  const [days, setDays] = useState(30);
  const resource = useResource(`/admin/analytics?days=${days}`);
  const data = resource.data;
  return (
    <>
      <div className="heading">
        <div>
          <span className="eyebrow">ADMINISTRATOR INSIGHTS</span>
          <h1>The sound of your community.</h1>
          <p className="muted">
            Catalog and listening activity from saved records.
          </p>
        </div>
        <div className="analytics-controls">
          <label>
            Time period
            <select
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </label>
          <button onClick={resource.refresh}>Refresh</button>
        </div>
      </div>
      <State resource={resource}>
        {data && (
          <>
            <div className="stat-grid">
              {[
                ["Songs", data.totals.songs],
                ["Listeners", data.totals.listeners],
                ["Playlists", data.totals.playlists],
                ["Likes", data.totals.likes],
                ["All recorded plays", data.totals.plays],
                [`Plays · ${days} days`, data.period.plays],
              ].map(([label, value]) => (
                <article className="stat-card" key={label}>
                  <span>{label}</span>
                  <strong>{value.toLocaleString()}</strong>
                </article>
              ))}
            </div>
            <div className="analytics-engagement">
              <span>
                <strong>{data.period.activeListeners}</strong> active listeners
                this period
              </span>
              <span>
                <strong>{data.period.newListeners}</strong> new listeners this
                period
              </span>
              <span>
                All dates use <strong>{data.timezone}</strong>
              </span>
            </div>
            <div className="analytics-grid">
              <section className="analytics-panel">
                <div className="analytics-panel-title">
                  <h2>Listening over time</h2>
                  <span>PLAY EVENTS</span>
                </div>
                <ListeningChart points={data.dailyPlays} />
              </section>
              <section className="analytics-panel">
                <div className="analytics-panel-title">
                  <h2>Genre tags in the collection</h2>
                  <span>CATALOG</span>
                </div>
                {data.genres.length ? (
                  <div className="genre-distribution">
                    {data.genres.map((genre) => (
                      <div key={genre.name}>
                        <div>
                          <strong>{genre.name}</strong>
                          <span>
                            {genre.songs} songs · {genre.plays} plays
                          </span>
                        </div>
                        <progress
                          max={Math.max(1, data.totals.songs)}
                          value={genre.songs}
                          aria-label={`${genre.name}: ${genre.songs} songs`}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="analytics-empty">
                    Upload songs to see the genre distribution.
                  </div>
                )}
              </section>
            </div>
            <div className="analytics-grid">
              <section className="analytics-panel">
                <div className="analytics-panel-title">
                  <h2>Most played</h2>
                  <span>ALL TIME</span>
                </div>
                {data.popularSongs.length ? (
                  <div className="popular-list">
                    {data.popularSongs.map((song, index) => (
                      <div key={song.id}>
                        <span className="popular-rank">{index + 1}</span>
                        <Cover song={song} />
                        <div>
                          <Link to={`/songs/${song.id}`}>{song.title}</Link>
                          <small>{song.artist}</small>
                        </div>
                        <div className="popular-count">
                          <strong>{song.plays} plays</strong>
                          <small>{song.likes} likes</small>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="analytics-empty">
                    Your popular tracks will appear once the collection has
                    songs.
                  </div>
                )}
              </section>
              <section className="analytics-panel">
                <div className="analytics-panel-title">
                  <h2>Audio analysis</h2>
                  <span
                    className={
                      data.processor.status === "UP" ? "ready" : "pending"
                    }
                  >
                    {data.processor.status === "UP"
                      ? "MEDIA PROCESSOR ONLINE"
                      : "MEDIA PROCESSOR UNAVAILABLE"}
                  </span>
                </div>
                <div className="analysis-counts">
                  {[
                    ["Features ready", data.totals.readyFeatures],
                    ["Features pending", data.totals.pendingFeatures],
                    ["Curated genre tags", data.totals.curatedGenres],
                    ["Unclassified songs", data.totals.unclassifiedSongs],
                    ["Songs with covers", data.totals.covers],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </div>
                  ))}
                </div>
                <p className="form-help">
                  Curated and embedded genre tags guide recommendations
                  alongside audio similarity. Songs can have several genre tags,
                  so tag counts overlap. The media processor extracts audio
                  features, tags and artwork.
                </p>
                <Link className="text-link" to="/admin">
                  Manage music and retry analysis →
                </Link>
              </section>
            </div>
          </>
        )}
      </State>
    </>
  );
}
