import { createContext, useContext, useEffect, useRef, useState } from "react";
import { write, message } from "./api";
const PlayerContext = createContext(null);
export const formatTime = (value) =>
  Number.isFinite(value) && value >= 0
    ? `${Math.floor(value / 60)}:${String(Math.floor(value % 60)).padStart(2, "0")}`
    : "0:00";
export function PlayerProvider({ children }) {
  const [queue, setQueue] = useState([]),
    [index, setIndex] = useState(-1),
    [playing, setPlaying] = useState(false),
    [time, setTime] = useState(0),
    [duration, setDuration] = useState(0),
    [volume, setVolumeState] = useState(0.8),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  const audio = useRef(null),
    recorded = useRef(null),
    wantPlay = useRef(false);
  const current = queue[index] || null;
  function start() {
    if (!audio.current) return;
    wantPlay.current = true;
    setError("");
    audio.current.play().catch(() => {
      setPlaying(false);
      setLoading(false);
      setError("Playback could not start. Press Play to retry.");
    });
  }
  useEffect(() => {
    if (audio.current) audio.current.volume = volume;
  }, [volume]);
  useEffect(() => {
    if (!current || !audio.current) return;
    setTime(0);
    setDuration(current.durationSeconds || 0);
    recorded.current = null;
    setError("");
    setLoading(true);
    audio.current.load();
    if (wantPlay.current) start();
  }, [current?.id]);
  const play = (song, list = [song]) => {
    const next = [...list];
    let i = next.findIndex((s) => s.id === song.id);
    if (i < 0) {
      next.push(song);
      i = next.length - 1;
    }
    wantPlay.current = true;
    setQueue(next);
    setIndex(i);
    if (current?.id === song.id) start();
  };
  const toggle = () => {
    if (!audio.current || !current) return;
    if (audio.current.paused) start();
    else {
      wantPlay.current = false;
      audio.current.pause();
    }
  };
  function change(delta) {
    if (!queue.length) return;
    wantPlay.current = true;
    const target = (index + delta + queue.length) % queue.length;
    if (target === index) {
      audio.current.currentTime = 0;
      start();
    } else setIndex(target);
  }
  const next = () => change(1),
    prev = () => change(-1);
  const seek = (value) => {
    if (audio.current && Number.isFinite(duration)) {
      audio.current.currentTime = Math.max(
        0,
        Math.min(duration, Number(value)),
      );
      setTime(audio.current.currentTime);
    }
  };
  const setVolume = (value) => setVolumeState(Number(value));
  const onPlay = () => {
    setPlaying(true);
    setLoading(false);
    if (current && recorded.current !== current.id) {
      recorded.current = current.id;
      write({ method: "post", url: `/songs/${current.id}/plays` }).catch((e) =>
        setError(`Listening history could not be saved: ${message(e)}`),
      );
    }
  };
  return (
    <PlayerContext.Provider
      value={{
        queue,
        current,
        playing,
        play,
        toggle,
        next,
        prev,
        time,
        duration,
        volume,
        seek,
        setVolume,
      }}
    >
      {children}
      <audio
        aria-label="Raagify audio"
        ref={audio}
        src={current?.streamUrl || undefined}
        preload="metadata"
        onPlay={onPlay}
        onPause={() => setPlaying(false)}
        onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
        onCanPlay={() => setLoading(false)}
        onWaiting={() => setLoading(true)}
        onPlaying={() => setLoading(false)}
        onError={() => {
          if (current) {
            setPlaying(false);
            setLoading(false);
            setError(
              "This track could not be loaded. Try another song or sign in again.",
            );
          }
        }}
        onEnded={next}
      />
      <div className="player" aria-label="Audio player">
        <div className="now">
          <div className="player-art">♫</div>
          <div>
            <small>{loading ? "BUFFERING..." : "NOW PLAYING"}</small>
            <strong>{current?.title || "Find something you love"}</strong>
            <span>
              {current?.artist || "Choose a track to start listening"}
            </span>
          </div>
        </div>
        <div className="transport">
          <div>
            <button disabled={!current} aria-label="Previous" onClick={prev}>
              ◀◀
            </button>
            <button
              disabled={!current}
              className="play"
              aria-label={playing ? "Pause" : "Play"}
              onClick={toggle}
            >
              {playing ? "Ⅱ" : "▶"}
            </button>
            <button disabled={!current} aria-label="Next" onClick={next}>
              ▶▶
            </button>
          </div>
          <div className="timeline">
            <span>{formatTime(time)}</span>
            <input
              disabled={!current}
              aria-label="Seek"
              type="range"
              min="0"
              max={Number.isFinite(duration) ? duration : 0}
              step=".1"
              value={Math.min(time, Number.isFinite(duration) ? duration : 0)}
              onChange={(e) => seek(e.target.value)}
            />
            <span>{formatTime(duration)}</span>
          </div>
        </div>
        <label className="volume">
          Volume
          <input
            aria-label="Volume"
            type="range"
            min="0"
            max="1"
            step=".05"
            value={volume}
            onChange={(e) => setVolume(e.target.value)}
          />
        </label>
        {error && (
          <div className="player-error" role="alert">
            {error}
            <button
              aria-label="Dismiss player error"
              onClick={() => setError("")}
            >
              ×
            </button>
          </div>
        )}
      </div>
    </PlayerContext.Provider>
  );
}
export const usePlayer = () => useContext(PlayerContext);
