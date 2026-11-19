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


def test_actual_decode_features_and_placeholder():
    response = client.post(
        "/analyze-file", files={"file": ("tone.wav", wav(), "audio/wav")}
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result["vector"]) == 27 and np.isfinite(result["vector"]).all()
    assert result["durationSeconds"] == 3
    assert result["placeholder"] is True and result["genreSource"] == "PLACEHOLDER"


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


def test_health_reports_model_state():
    assert client.get("/health").json()["genrePrediction"] == "PLACEHOLDER"
