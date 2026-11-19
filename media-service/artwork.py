"""Extract actual embedded front-cover artwork; never synthesize a cover."""

import base64
import io
import mutagen
from PIL import Image
from mutagen.flac import Picture

MAX_COVER_BYTES = 5 * 1024 * 1024


def embedded_artwork(data):
    try:
        audio = mutagen.File(io.BytesIO(data))
        if audio is None:
            return None
        pictures = []
        if audio.tags and hasattr(audio.tags, "getall"):
            pictures = list(audio.tags.getall("APIC"))
        elif getattr(audio, "pictures", None):
            pictures = list(audio.pictures)
        elif audio.tags:
            for encoded in audio.tags.get("metadata_block_picture", []):
                if len(encoded) <= (MAX_COVER_BYTES + 4096) * 4 // 3:
                    pictures.append(Picture(base64.b64decode(encoded, validate=True)))
        for picture in sorted(pictures, key=lambda picture: picture.type != 3):
            payload = picture.data
            if not payload or len(payload) > MAX_COVER_BYTES:
                continue
            if payload.startswith(b"\x89PNG\r\n\x1a\n"):
                content_type = "image/png"
            elif payload.startswith(b"\xff\xd8\xff"):
                content_type = "image/jpeg"
            elif payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
                content_type = "image/webp"
            else:
                continue
            with Image.open(io.BytesIO(payload)) as image:
                if image.width * image.height > 30000000:
                    continue
                image.verify()
            return {
                "coverContentType": content_type,
                "coverBase64": base64.b64encode(payload).decode("ascii"),
            }
    except (
        mutagen.MutagenError,
        ValueError,
        OSError,
        TypeError,
        Image.DecompressionBombError,
    ):
        pass
    return None
