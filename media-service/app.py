"""Raagify media processing: real DSP features, embedded tags and artwork."""

import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from features import extract, FEATURE_SCHEMA
from artwork import embedded_artwork
from metadata import embedded_metadata

app = FastAPI(title="Raagify media processor", version="1.0.0")
MAX_BYTES = int(os.getenv("AUDIO_MAX_BYTES", "26214400"))


@app.get("/health")
def health():
    return {
        "status": "UP",
        "featureSchema": FEATURE_SCHEMA,
        "processing": "audio-features-and-embedded-metadata",
    }


@app.post("/analyze-file")
def analyze_file(file: UploadFile = File(...)):
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Audio exceeds configured size limit")
    try:
        vector, _, duration = extract(data)
    except (ValueError, RuntimeError, OSError) as error:
        raise HTTPException(422, "Audio could not be decoded") from error
    tags = embedded_metadata(data)
    return {
        "vector": vector,
        "genre": tags["genre"] or "Unclassified",
        "genreSource": "METADATA" if tags["genre"] else "UNCLASSIFIED",
        "available": True,
        "durationSeconds": duration,
        "featureSchema": FEATURE_SCHEMA,
    }


@app.post("/artwork-file")
def artwork_file(file: UploadFile = File(...)):
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Audio exceeds configured size limit")
    return embedded_artwork(data) or {"coverContentType": None, "coverBase64": None}


@app.post("/metadata-file")
def metadata_file(file: UploadFile = File(...)):
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Audio exceeds configured size limit")
    return embedded_metadata(data)
