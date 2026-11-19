# Pretrained genre options

**Observed:** Public pretrained genre models are available. The following model metadata was inspected on 2026-11-19; no weights were installed or inference executed for these models.

| Classification | Model | Declared output and input | Integration |
| --- | --- | --- | --- |
| Observed (publisher metadata) | [Essentia Genre Discogs400](https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json) | 400 genre/style scores; mono 16 kHz audio through Discogs EfficientNet embeddings | Needs its supplied embedding model and classifier head; not the existing 27-feature joblib loader |
| Observed (publisher metadata) | [Essentia MTG-Jamendo genre](https://essentia.upf.edu/models/classification-heads/mtg_jamendo_genre/mtg_jamendo_genre-discogs-effnet-1.json) | 87 genre scores; mono 16 kHz audio through Discogs EfficientNet embeddings | Needs the same matching embedding model and its Jamendo genre head |
| Observed (publisher metadata) | [Wav2Vec2 GTZAN](https://huggingface.co/m3hrdadfi/wav2vec2-base-100k-gtzan-music-genres) | Blues, classical, country, disco, hiphop, jazz, metal, pop, reggae, rock; normalized 16 kHz audio | Config declares a custom Wav2Vec2ForSpeechClassification architecture; requires that matching classification head and preprocessing |

**Recommendation:** For a broader music catalog, evaluate Discogs400, map its detailed tags into a manageable UI genre set, and keep administrator overrides. For a small college/demo project using the ten GTZAN categories, a GTZAN classifier is a narrower starting point. Assess the chosen model on representative songs before selecting it; publisher evaluation results do not establish Raagify accuracy.

**Observed (source):** The current service already extracts MFCC, spectral centroid, tempo and chroma for recommendations. Those features can remain unchanged while a pretrained classifier receives its own required waveform/embedding input and returns predictedGenre with genreSource=MODEL. The upload timeout/PENDING fallback and administrator genre overrides can be preserved.

**Observed:** GENRE_MODEL_PATH currently supports a compatible 27-feature joblib/sklearn predictor plus its schema manifest. It cannot directly load the linked TensorFlow or PyTorch weights.

**Recommendation:** Pin the selected model revision, reproduce its original preprocessing and label mapping, add an adapter, and exercise real model inference plus unavailable/timeout behavior. Resolve the selected distribution's stated use terms when choosing a model.

**Unverified:** These candidate models' loading, CPU latency, genre accuracy and compatibility with the local Windows/Python 3.14 runtime have not been tested. The running app still labels genre prediction as PLACEHOLDER.
