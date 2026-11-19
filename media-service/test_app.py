import io
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient
from app import app
from features import extract

client = TestClient(app)


def wav(frequency=440):
    out = io.BytesIO()
    t = np.arange(22050 * 3) / 22050
    sf.write(out, 0.4 * np.sin(2 * np.pi * frequency * t), 22050, format="WAV")
    return out.getvalue()


def test_actual_decode_features_without_genre_guessing():
    response = client.post(
        "/analyze-file", files={"file": ("tone.wav", wav(), "audio/wav")}
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["vector"]) == 27 and np.isfinite(result["vector"]).all()
    assert result["durationSeconds"] == 3
    assert result["genreSource"] == "UNCLASSIFIED" and result["genre"] == "Unclassified"
    assert "genreConfidence" not in result and "genreModel" not in result


def test_spectral_centroid_and_chroma_respond_to_audio():
    low, _, _ = extract(wav(220))
    high, _, _ = extract(wav(880))
    assert high[13] > low[13] * 3
    assert np.argmax(low[15:]) == 9  # A pitch class


def test_invalid_audio_is_rejected():
    assert (
        client.post(
            "/analyze-file", files={"file": ("fake.wav", b"RIFFfakeWAVE", "audio/wav")}
        ).status_code
        == 422
    )


def test_health_reports_media_processing():
    assert client.get("/health").json()["status"] == "UP"
    assert "modelId" not in client.get("/health").json()


def test_embedded_tags_and_actual_cover_are_read():
    import base64
    from PIL import Image
    from mutagen.wave import WAVE
    from mutagen.id3 import APIC, TIT2, TPE1, TALB, TCON

    image = io.BytesIO()
    Image.new("RGB", (8, 8), (12, 50, 90)).save(image, format="PNG")
    audio = io.BytesIO(wav())
    tagged = WAVE(audio)
    tagged.add_tags()
    tagged.tags.add(TIT2(encoding=3, text="53_505 SpotiDost"))
    tagged.tags.add(TPE1(encoding=3, text="Arctic Monkeys - Topic"))
    tagged.tags.add(TALB(encoding=3, text="AM"))
    tagged.tags.add(TCON(encoding=3, text="Music"))
    tagged.tags.add(APIC(encoding=3, mime="image/png", type=3, data=image.getvalue()))
    tagged.save(audio)
    response = client.post(
        "/metadata-file", files={"file": ("53_505.mp3", audio.getvalue(), "audio/wav")}
    )
    assert response.status_code == 200
    data = response.json()
    assert (
        data["title"] == "505"
        and data["artist"] == "Arctic Monkeys"
        and data["album"] == "AM"
        and data["genre"] is None
    )
    assert (
        data["durationSeconds"] == 3
        and base64.b64decode(data["coverBase64"]) == image.getvalue()
    )
