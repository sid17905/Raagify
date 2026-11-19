"""Raagify audio feature API. Unclassified is an explicit placeholder, not ML."""

import json
import os
from pathlib import Path
import joblib
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from features import extract, FEATURE_SCHEMA, FEATURE_NAMES

app = FastAPI(title="Raagify audio features", version="1.0.0")
MAX_BYTES = int(os.getenv("AUDIO_MAX_BYTES", "26214400"))
model_path = os.getenv("GENRE_MODEL_PATH", "")
model = None
if model_path:
    # Only trusted, privately provisioned pickle/joblib files may be loaded.
    manifest = json.loads(Path(model_path + ".json").read_text())
    if (
        manifest.get("featureSchema") != FEATURE_SCHEMA
        or manifest.get("featureNames") != FEATURE_NAMES
    ):
        raise RuntimeError(
            "Model manifest must match the raagify-v1 raw feature schema"
        )
    model = joblib.load(model_path)
    if not callable(getattr(model, "predict", None)):
        raise RuntimeError("Model must expose predict(raw_27_feature_matrix)")


@app.get("/health")
def health():
    return {
        "status": "UP",
        "featureSchema": FEATURE_SCHEMA,
        "genrePrediction": "MODEL" if model is not None else "PLACEHOLDER",
    }


@app.post("/analyze-file")
def analyze_file(file: UploadFile = File(...)):
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Audio exceeds configured size limit")
    try:
        vector, raw, duration = extract(data)
    except (ValueError, RuntimeError, OSError) as error:
        raise HTTPException(422, "Audio could not be decoded") from error
    predicted = (
        str(model.predict(np.asarray([raw]))[0])
        if model is not None
        else "Unclassified"
    )
    return {
        "vector": vector,
        "predictedGenre": predicted,
        "genreSource": "MODEL" if model is not None else "PLACEHOLDER",
        "placeholder": model is None,
        "available": True,
        "durationSeconds": duration,
        "featureSchema": FEATURE_SCHEMA,
    }
