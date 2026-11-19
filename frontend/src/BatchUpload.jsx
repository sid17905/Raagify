import { useEffect, useRef, useState } from "react";
import { message, write } from "./api";
import { Modal, Notice } from "./components";
import {
  AUDIO_ACCEPT,
  COVER_ACCEPT,
  MAX_BATCH_FILES,
  audioProblem,
  coverProblem,
  missingDetails,
  newTrack,
  readyToUpload,
  readDuration,
  uploadBody,
} from "./batchFiles";

export default function BatchUpload({ onClose, onChanged }) {
  const [tracks, setTracks] = useState([]);
  const [common, setCommon] = useState({ artist: "", album: "", genre: "" });
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [finished, setFinished] = useState(false);
  const alive = useRef(true);
  const uploading = useRef(false);
  const metadataController = useRef(null);
  const metadataQueue = useRef([]);
  const readers = useRef(0);

  useEffect(() => {
    alive.current = true;
    metadataController.current = new AbortController();
    return () => {
      alive.current = false;
      metadataController.current.abort();
      metadataQueue.current = [];
    };
  }, []);

  function patch(id, values) {
    if (alive.current)
      setTracks((current) =>
        current.map((track) =>
          track.id === id ? { ...track, ...values } : track,
        ),
      );
  }

  function drainMetadata() {
    while (
      readers.current < 2 &&
      metadataQueue.current.length &&
      alive.current
    ) {
      const { id, file } = metadataQueue.current.shift();
      readers.current++;
      readDuration(file, metadataController.current.signal)
        .then((duration) => {
          if (alive.current)
            setTracks((current) =>
              current.map((track) =>
                track.id === id && track.file === file
                  ? {
                      ...track,
                      reading: false,
                      durationSeconds: track.durationSeconds || duration,
                      durationWarning: duration
                        ? ""
                        : "Duration could not be read. Enter it manually.",
                    }
                  : track,
              ),
            );
        })
        .finally(() => {
          readers.current--;
          drainMetadata();
        });
    }
  }

  function addFiles(event) {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    const identity = (file) => `${file.name}:${file.size}:${file.lastModified}`;
    const selected = new Set(tracks.map((track) => identity(track.file)));
    const added = [];
    let duplicates = 0;
    for (const file of files) {
      if (selected.has(identity(file))) {
        duplicates++;
        continue;
      }
      selected.add(identity(file));
      added.push(newTrack(file));
    }
    if (tracks.length + added.length > MAX_BATCH_FILES) {
      setNotice(`Choose at most ${MAX_BATCH_FILES} files per batch.`);
      return;
    }
    setNotice(
      duplicates ? `${duplicates} already-selected file(s) skipped.` : "",
    );
    setFinished(false);
    setTracks((current) => [...current, ...added]);
    metadataQueue.current.push(
      ...added
        .filter((track) => track.reading)
        .map(({ id, file }) => ({ id, file })),
    );
    drainMetadata();
  }

  function edit(id, key, value) {
    setTracks((current) =>
      current.map((track) =>
        track.id === id
          ? {
              ...track,
              [key]: value,
              ...(track.status === "failed"
                ? { status: "draft", error: "" }
                : {}),
            }
          : track,
      ),
    );
    setFinished(false);
  }

  function applyCommon() {
    const values = Object.fromEntries(
      Object.entries(common).filter(([, value]) => value.trim()),
    );
    setTracks((current) =>
      current.map((track) =>
        ["draft", "failed"].includes(track.status)
          ? {
              ...track,
              ...values,
              status: "draft",
              error: "",
            }
          : track,
      ),
    );
    setFinished(false);
  }

  function replaceAudio(track, event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    patch(track.id, {
      file,
      durationSeconds: "",
      reading: !audioProblem(file),
      durationWarning: "",
      status: "draft",
      error: "",
      progress: 0,
    });
    if (!audioProblem(file)) {
      metadataQueue.current.push({ id: track.id, file });
      drainMetadata();
    }
    setFinished(false);
  }

  async function uploadReady() {
    if (uploading.current) return;
    const selected = tracks.filter(readyToUpload);
    if (!selected.length) return;
    uploading.current = true;
    setBusy(true);
    setFinished(false);
    setNotice("");
    let saved = false;
    try {
      for (const track of selected) {
        if (!alive.current) break;
        patch(track.id, { status: "uploading", progress: 0, error: "" });
        try {
          const { data } = await write({
            method: "post",
            url: "/admin/songs",
            data: uploadBody(track),
            onUploadProgress: (event) => {
              if (event.total)
                patch(track.id, {
                  progress: Math.min(
                    100,
                    Math.round((event.loaded / event.total) * 100),
                  ),
                });
            },
          });
          saved = true;
          patch(track.id, { status: "uploaded", progress: 100, song: data });
        } catch (error) {
          const status = error.response?.status;
          const uncertain = !status || status >= 500;
          patch(track.id, {
            status: uncertain ? "uncertain" : "failed",
            progress: 0,
            error: uncertain
              ? "Upload could not be confirmed. Check Manage music before selecting this file again."
              : message(error),
          });
          if (status === 401 || status === 403) {
            setNotice(
              "Your administrator session is unavailable. Sign in again before continuing.",
            );
            break;
          }
        }
      }
    } finally {
      uploading.current = false;
      if (alive.current) {
        setBusy(false);
        setFinished(true);
      }
      if (saved) onChanged();
    }
  }

  const ready = tracks.filter(readyToUpload).length;
  const uploaded = tracks.filter((track) => track.status === "uploaded").length;
  const failed = tracks.filter((track) =>
    ["failed", "uncertain"].includes(track.status),
  ).length;

  return (
    <Modal
      title="Batch upload songs"
      className="batch-modal"
      closeDisabled={busy}
      onClose={() => {
        if (!uploading.current) onClose();
      }}
    >
      <p className="muted">
        Choose up to 25 audio files, review the details, then upload ready
        tracks. Titles come from filenames; durations are read automatically
        when supported.
      </p>
      <label className="batch-picker">
        Select audio files · WAV, MP3, OGG · up to 25 MiB each
        <input
          type="file"
          accept={AUDIO_ACCEPT}
          multiple
          disabled={busy}
          onChange={addFiles}
        />
      </label>
      <Notice error={notice} />
      {!tracks.length ? (
        <div className="state">
          <h3>Select your first batch</h3>
          <p>You can edit each track and apply shared details before saving.</p>
        </div>
      ) : (
        <>
          <section className="batch-common" aria-label="Shared track details">
            <h3>Shared details</h3>
            <div className="batch-fields">
              {[
                ["artist", "Artist for batch", 160],
                ["album", "Album for batch", 160],
                ["genre", "Genre for batch", 80],
              ].map(([key, label, max]) => (
                <label key={key}>
                  {label}
                  <input
                    value={common[key]}
                    maxLength={max}
                    disabled={busy}
                    onChange={(event) =>
                      setCommon({ ...common, [key]: event.target.value })
                    }
                  />
                </label>
              ))}
            </div>
            <div className="batch-common-footer">
              <small>Non-empty values apply to all unsaved tracks.</small>
              <button
                type="button"
                disabled={
                  busy || !Object.values(common).some((value) => value.trim())
                }
                onClick={applyCommon}
              >
                Apply shared details
              </button>
            </div>
          </section>
          <div className="batch-summary" role="status">
            {tracks.length} selected · {ready} ready · {uploaded} uploaded
            {failed > 0 ? ` · ${failed} need attention` : ""}
          </div>
          <div className="batch-tracks">
            {tracks.map((track, index) => {
              const locked =
                busy || ["uploaded", "uncertain"].includes(track.status);
              const missing = missingDetails(track);
              const fileError =
                audioProblem(track.file) || coverProblem(track.cover);
              return (
                <section
                  className={`batch-track ${track.status}`}
                  key={track.id}
                  aria-label={`Track ${index + 1}: ${track.file.name}`}
                >
                  <div className="batch-track-heading">
                    <div>
                      <strong>{track.file.name}</strong>
                      <small>
                        {(track.file.size / (1024 * 1024)).toFixed(2)} MiB
                      </small>
                    </div>
                    {!busy && track.status !== "uploaded" && (
                      <button
                        type="button"
                        aria-label={`Remove ${track.file.name} from batch`}
                        onClick={() =>
                          setTracks((current) =>
                            current.filter((item) => item.id !== track.id),
                          )
                        }
                      >
                        Remove
                      </button>
                    )}
                    {track.status === "uploaded" && (
                      <span className="ready">Uploaded</span>
                    )}
                  </div>
                  <div className="batch-fields">
                    {[
                      ["title", "Title", 160],
                      ["artist", "Artist", 160],
                      ["album", "Album", 160],
                      ["genre", "Genre override", 80],
                    ].map(([key, label, max]) => (
                      <label key={key}>
                        {label}
                        <input
                          value={track[key]}
                          required={key === "title" || key === "artist"}
                          maxLength={max}
                          disabled={locked}
                          onChange={(event) =>
                            edit(track.id, key, event.target.value)
                          }
                        />
                      </label>
                    ))}
                    <label>
                      Duration (seconds)
                      <input
                        type="number"
                        required
                        min="1"
                        max="86400"
                        step="1"
                        value={track.durationSeconds}
                        disabled={locked}
                        onChange={(event) =>
                          edit(track.id, "durationSeconds", event.target.value)
                        }
                      />
                    </label>
                    <label>
                      Cover (optional)
                      <input
                        type="file"
                        accept={COVER_ACCEPT}
                        disabled={locked}
                        onChange={(event) =>
                          edit(
                            track.id,
                            "cover",
                            event.target.files?.[0] || null,
                          )
                        }
                      />
                      {track.cover && (
                        <small>
                          {track.cover.name}{" "}
                          <button
                            type="button"
                            disabled={locked}
                            onClick={() => edit(track.id, "cover", null)}
                          >
                            Clear cover
                          </button>
                        </small>
                      )}
                    </label>
                  </div>
                  {track.status === "uploaded" ? (
                    <p className="batch-result">
                      Saved to Manage music. Use Edit there to change details.{" "}
                      {track.song?.featureStatus === "PENDING"
                        ? "Audio features are pending; genre fallback is active."
                        : track.song?.genreSource === "PLACEHOLDER"
                          ? "Audio features ready; genre prediction is a placeholder."
                          : "Audio features ready."}
                    </p>
                  ) : (
                    <>
                      {!busy && track.status !== "uncertain" && (
                        <label className="batch-replace">
                          Replace audio
                          <input
                            type="file"
                            accept={AUDIO_ACCEPT}
                            onChange={(event) => replaceAudio(track, event)}
                          />
                        </label>
                      )}
                      {track.reading && (
                        <p className="form-help" role="status">
                          Reading audio duration…
                        </p>
                      )}
                      {!track.reading &&
                        track.durationWarning &&
                        !track.durationSeconds && (
                          <p className="form-help">{track.durationWarning}</p>
                        )}
                      {fileError && <Notice error={fileError} />}
                      {missing.length > 0 && (
                        <p className="batch-missing">
                          Complete: {missing.join(", ")}.
                        </p>
                      )}
                      <Notice error={track.error} />
                      {track.status === "uploading" && (
                        <div className="batch-progress" role="status">
                          <progress
                            max="100"
                            value={track.progress}
                            aria-label={`Upload progress for ${track.file.name}`}
                          />
                          <span>
                            {track.progress < 100
                              ? `Uploading ${track.progress}%`
                              : "Analyzing and saving…"}
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </section>
              );
            })}
          </div>
          <div className="batch-actions">
            <div>
              <p>
                {busy
                  ? "Keep this tab open while files upload."
                  : finished
                    ? "Saved tracks will not be uploaded again. Fix any remaining tracks and retry."
                    : "Blank genre uses the current prediction. Files stay queued in this tab until saved."}
              </p>
              <small>
                Required: title, artist, duration. Album, genre and cover are
                optional.
              </small>
            </div>
            <div className="button-group">
              <button type="button" disabled={busy} onClick={onClose}>
                {uploaded ? "Done" : "Close"}
              </button>
              <button
                type="button"
                className="primary"
                disabled={busy || !ready}
                onClick={uploadReady}
              >
                {busy
                  ? "Uploading batch…"
                  : finished
                    ? `Upload remaining (${ready})`
                    : `Upload ready tracks (${ready})`}
              </button>
            </div>
          </div>
        </>
      )}
    </Modal>
  );
}
