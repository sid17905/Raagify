import { write } from "./api";
export const MAX_BATCH_FILES = 25;
export const AUDIO_MAX_BYTES = 25 * 1024 * 1024;
export const COVER_MAX_BYTES = 5 * 1024 * 1024;
export const AUDIO_ACCEPT =
  ".wav,.mp3,.ogg,audio/wav,audio/x-wav,audio/mpeg,audio/ogg";
export const COVER_ACCEPT = "image/png,image/jpeg,image/webp";

const audioTypes = { wav: "audio/wav", mp3: "audio/mpeg", ogg: "audio/ogg" };
export function cleanMusicText(value, title = false) {
  let text = String(value || "")
    .replace(
      /https?:\/\/(?:www\.)?(?:spotidost|spotidown|spotimate|spotiflyer|spotdown)\.[a-z]+\S*/gi,
      "",
    )
    .replace(
      /\b(?:www\.)?(?:spotidost|spotidown|spotimate|spotiflyer|spotdown)(?:\.[a-z]+)?\b/gi,
      "",
    );
  if (title) text = text.replace(/^\s*\d{1,3}_+\s*/, "");
  return text
    .replace(/[\[({]\s*[\])}]/g, "")
    .replace(/\s+/g, " ")
    .replace(/^[\s_|-]+|[\s_|-]+$/g, "")
    .slice(0, 160);
}
export function titleFromFilename(name) {
  return cleanMusicText(
    name
      .replace(/\.[^.]+$/, "")
      .replace(/^\d{1,3}_+/, "")
      .replace(/_/g, " "),
    true,
  );
}

export function audioType(file) {
  return audioTypes[file.name.split(".").pop().toLowerCase()] || "";
}

export function audioProblem(file) {
  if (!audioType(file)) return "Choose WAV, MP3, or OGG audio.";
  if (!file.size) return "The audio file is empty.";
  if (file.size > AUDIO_MAX_BYTES) return "Audio must be at most 25 MiB.";
  return "";
}

export function newTrack(file) {
  return {
    id: crypto.randomUUID(),
    file,
    cover: null,
    title: titleFromFilename(file.name),
    artist: "",
    album: "",
    genre: "",
    durationSeconds: "",
    reading: !audioProblem(file),
    durationWarning: "",
    status: "draft",
    progress: 0,
    error: "",
    song: null,
  };
}

export function missingDetails(track) {
  const missing = [];
  if (!track.title.trim() || track.title.length > 160) missing.push("title");
  if (!track.artist.trim() || track.artist.length > 160) missing.push("artist");
  if (track.album.length > 160)
    missing.push("album must be at most 160 characters");
  if (track.genre.length > 80)
    missing.push("genre must be at most 80 characters");
  const duration = Number(track.durationSeconds);
  if (!Number.isInteger(duration) || duration < 1 || duration > 86400)
    missing.push("duration (1–86400 seconds)");
  return missing;
}

export function coverProblem(file) {
  if (!file) return "";
  if (!COVER_ACCEPT.split(",").includes(file.type))
    return "Choose PNG, JPEG, or WebP artwork.";
  if (!file.size || file.size > COVER_MAX_BYTES)
    return "Cover must be nonempty and at most 5 MiB.";
  return "";
}

export function readyToUpload(track) {
  return (
    ["draft", "failed"].includes(track.status) &&
    !audioProblem(track.file) &&
    !coverProblem(track.cover) &&
    !missingDetails(track).length
  );
}

export function uploadBody(track) {
  const form = new FormData();
  for (const key of ["title", "artist", "album", "genre", "durationSeconds"])
    form.append(key, String(track[key]).trim());
  // Browser MIME aliases differ; Spring still validates the actual signature.
  form.append(
    "audio",
    new File([track.file], track.file.name, { type: audioType(track.file) }),
  );
  if (track.cover) form.append("cover", track.cover);
  return form;
}

export async function readTrackMetadata(file, signal) {
  let metadata = {};
  try {
    const form = new FormData();
    form.append("file", new File([file], file.name, { type: audioType(file) }));
    metadata =
      (
        await write({
          method: "post",
          url: "/admin/songs/metadata",
          data: form,
          signal,
        })
      ).data || {};
  } catch {
    /* Native duration/filename remain usable if tag extraction is unavailable. */
  }
  const duration =
    metadata.durationSeconds > 0
      ? String(metadata.durationSeconds)
      : await readDuration(file, signal);
  let cover = null;
  if (
    metadata.coverBase64 &&
    metadata.coverBase64.length <= ((COVER_MAX_BYTES + 2) * 4) / 3 + 4 &&
    COVER_ACCEPT.split(",").includes(metadata.coverContentType)
  ) {
    try {
      const binary = atob(metadata.coverBase64);
      if (binary.length <= COVER_MAX_BYTES) {
        const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
        const ext = {
          "image/png": "png",
          "image/jpeg": "jpg",
          "image/webp": "webp",
        }[metadata.coverContentType];
        cover = new File([bytes], `embedded-cover.${ext}`, {
          type: metadata.coverContentType,
        });
      }
    } catch {
      /* Invalid embedded artwork is ignored. */
    }
  }
  return {
    title: cleanMusicText(metadata.title, true) || titleFromFilename(file.name),
    artist: cleanMusicText(metadata.artist).replace(/\s+-\s+Topic$/i, ""),
    album: cleanMusicText(metadata.album),
    genre:
      metadata.genre && !/^(music|unknown|unclassified)$/i.test(metadata.genre)
        ? cleanMusicText(metadata.genre).slice(0, 80)
        : "",
    durationSeconds: duration,
    cover,
  };
}
export function readDuration(file, signal) {
  return new Promise((resolve) => {
    if (signal?.aborted) {
      resolve("");
      return;
    }
    const audio = document.createElement("audio");
    const url = URL.createObjectURL(file);
    let settled = false;
    const finish = (duration = "") => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      signal?.removeEventListener("abort", aborted);
      audio.onloadedmetadata = null;
      audio.ondurationchange = null;
      audio.onerror = null;
      audio.removeAttribute("src");
      audio.load();
      URL.revokeObjectURL(url);
      resolve(duration);
    };
    const aborted = () => finish();
    const loaded = () => {
      if (
        Number.isFinite(audio.duration) &&
        audio.duration > 0 &&
        audio.duration <= 86400
      )
        finish(String(Math.ceil(audio.duration)));
    };
    const timer = setTimeout(() => finish(), 10000);
    signal?.addEventListener("abort", aborted, { once: true });
    audio.preload = "metadata";
    audio.onloadedmetadata = loaded;
    audio.ondurationchange = loaded;
    audio.onerror = () => finish();
    audio.src = url;
    audio.load();
  });
}
