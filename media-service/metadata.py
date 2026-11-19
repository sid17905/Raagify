"""Read embedded music tags without replacing user-authored metadata."""

import io
import math
import re
import mutagen
from artwork import embedded_artwork

BRAND = r"(?:spotidost|spotidown|spotimate|spotiflyer|spotdown)"


def clean_text(value, title=False):
    value = str(value or "")
    value = re.sub(
        r"https?://(?:www\.)?" + BRAND + r"\.[a-z]+\S*", "", value, flags=re.I
    )
    value = re.sub(r"\b(?:www\.)?" + BRAND + r"(?:\.[a-z]+)?\b", "", value, flags=re.I)
    if title:
        value = re.sub(r"^\s*\d{1,3}_+\s*", "", value)
    value = re.sub(r"[\[({]\s*[\])}]", "", value)
    return re.sub(r"\s+", " ", value).strip(" -_|\t\r\n")[:160]


def embedded_metadata(data):
    result = {
        "title": None,
        "artist": None,
        "album": None,
        "genre": None,
        "durationSeconds": None,
    }
    try:
        audio = mutagen.File(io.BytesIO(data))
        if audio is not None:
            tags = audio.tags or {}

            def text(id3, key):
                value = tags.get(id3) if hasattr(tags, "getall") else tags.get(key)
                if hasattr(value, "text"):
                    return " / ".join(map(str, value.text))
                if isinstance(value, list):
                    return " / ".join(map(str, value))
                return str(value or "")

            result["title"] = clean_text(text("TIT2", "title"), title=True) or None
            artist = re.sub(r"\s+-\s+Topic$", "", text("TPE1", "artist"), flags=re.I)
            result["artist"] = clean_text(artist) or None
            result["album"] = clean_text(text("TALB", "album")) or None
            genre = clean_text(text("TCON", "genre"))[:80]
            result["genre"] = (
                genre
                if genre.lower() not in ("", "music", "unknown", "unclassified")
                else None
            )
            duration = getattr(audio.info, "length", 0)
            if math.isfinite(duration) and 0 < duration <= 86400:
                result["durationSeconds"] = math.ceil(duration)
    except (mutagen.MutagenError, ValueError, OSError, TypeError):
        pass
    result.update(
        embedded_artwork(data) or {"coverContentType": None, "coverBase64": None}
    )
    return result
