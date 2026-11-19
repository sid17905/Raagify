"""Real DSP features, schema raagify-v1. No trained genre classifier is bundled."""

import io
from math import gcd
import numpy as np
import soundfile as sf
from scipy.fft import dct
from scipy.signal import resample_poly, find_peaks

SAMPLE_RATE = 22050
FEATURE_SCHEMA = "raagify-v1"
FEATURE_NAMES = (
    [f"mfcc_{i}" for i in range(13)]
    + ["spectral_centroid", "tempo"]
    + [f"chroma_{i}" for i in range(12)]
)


def extract(data: bytes) -> tuple[list[float], list[float], float]:
    # Decode at most 60 seconds, with a bounded read even for a malicious header.
    with sf.SoundFile(io.BytesIO(data)) as source:
        if source.samplerate <= 0 or source.samplerate > 192000 or source.channels > 8:
            raise ValueError("Unsupported sample rate or channel count")
        duration = source.frames / source.samplerate
        audio = source.read(
            min(source.frames, source.samplerate * 60), dtype="float32", always_2d=True
        ).mean(axis=1)
        source_rate = source.samplerate
    if (
        duration < 0.1
        or duration > 86400
        or audio.size < 128
        or not np.isfinite(audio).all()
    ):
        raise ValueError("Audio must have a valid duration and finite samples")
    factor = gcd(source_rate, SAMPLE_RATE)
    audio = resample_poly(audio, SAMPLE_RATE // factor, source_rate // factor)
    n_fft, hop = 2048, 512
    if audio.size < n_fft:
        audio = np.pad(audio, (0, n_fft - audio.size))
    frames = np.lib.stride_tricks.sliding_window_view(audio, n_fft)[::hop]
    power = np.abs(np.fft.rfft(frames * np.hanning(n_fft), axis=1)) ** 2
    frequencies = np.fft.rfftfreq(n_fft, 1 / SAMPLE_RATE)
    magnitude = np.sqrt(power)
    centroid = np.mean(
        (magnitude * frequencies).sum(axis=1) / np.maximum(magnitude.sum(axis=1), 1e-12)
    )
    # Triangular mel filters followed by log energy and orthonormal DCT.
    mel_max = 2595 * np.log10(1 + (SAMPLE_RATE / 2) / 700)
    mel_hz = 700 * (10 ** (np.linspace(0, mel_max, 42) / 2595) - 1)
    bank = np.zeros((40, frequencies.size))
    for i in range(40):
        left, center, right = mel_hz[i : i + 3]
        bank[i] = np.maximum(
            0,
            np.minimum(
                (frequencies - left) / (center - left),
                (right - frequencies) / (right - center),
            ),
        )
    mfcc = dct(np.log(np.maximum(power @ bank.T, 1e-10)), type=2, norm="ortho", axis=1)[
        :, :13
    ].mean(axis=0)
    # Spectral-flux onset envelope and autocorrelation tempo between 40 and 220 BPM.
    onset = np.maximum(np.diff(magnitude, axis=0), 0).sum(axis=1)
    tempo = 0.0
    if onset.size > 8 and onset.max(initial=0) > 1e-8:
        onset = onset - onset.mean()
        correlation = np.correlate(onset, onset, mode="full")[onset.size - 1 :]
        lo = max(1, int(60 * SAMPLE_RATE / (hop * 220)))
        hi = min(correlation.size - 1, int(60 * SAMPLE_RATE / (hop * 40)))
        if hi >= lo:
            peaks, _ = find_peaks(correlation[lo : hi + 1])
            lag = lo + (
                int(peaks[np.argmax(correlation[lo + peaks])])
                if peaks.size
                else int(np.argmax(correlation[lo : hi + 1]))
            )
            tempo = 60 * SAMPLE_RATE / (hop * lag)
    # Energy pooled by nearest equal-tempered pitch class.
    chroma = np.zeros(12)
    valid = frequencies >= 27.5
    pitch = np.rint(69 + 12 * np.log2(frequencies[valid] / 440)).astype(int) % 12
    np.add.at(chroma, pitch, power.mean(axis=0)[valid])
    chroma /= max(float(chroma.sum()), 1e-12)
    raw = np.concatenate([mfcc, [centroid, tempo], chroma])
    scaled = np.concatenate(
        [mfcc / 100, [centroid / (SAMPLE_RATE / 2), tempo / 240], chroma]
    )
    if not np.isfinite(scaled).all():
        raise ValueError("Feature extraction returned invalid values")
    return scaled.tolist(), raw.tolist(), duration
