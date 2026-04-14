import librosa
import numpy as np
import re

FILLER_WORDS = {"uh", "um", "er", "ah", "like"}

def compute_audio_metrics(audio_path: str, transcript: str):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)

    # 🎧 duration
    duration = len(y) / sr if sr > 0 else 0

    # 🧠 pauses
    intervals = librosa.effects.split(y, top_db=40)
    pause_count = max(0, len(intervals) - 1)

# cap unrealistic pauses
    if pause_count > 15:
        pause_count = 15

    # 🗣️ transcript processing
    words = re.findall(r"[a-z']+", transcript.lower())
    word_count = len(words)

    # filler words
    filler_count = sum(1 for w in words if w in FILLER_WORDS)

    # ⚡ speech rate (words per minute)
    speech_rate = (word_count / duration) * 60 if duration > 0 else 0

    # =========================
    # 🔥 FLUENCY SCORE LOGIC
    # =========================

    score = 10.0

    # ❌ Too short answer
    if word_count < 15:
        score -= 3
    elif word_count < 30:
        score -= 1.5

    # ❌ Too many pauses
    if pause_count >8:
        score -= 2
    elif pause_count > 4:
        score -= 1

    # ❌ Filler words penalty
    if filler_count > 5:
        score -= 2
    elif filler_count > 2:
        score -= 1

    # ❌ Speech rate issues
    if speech_rate < 90:   # too slow
        score -= 1.5
    elif speech_rate > 180:  # too fast
        score -= 1

    # clamp score
    score = max(0, min(10, round(score, 2)))

    return {
        "audio_duration": round(duration, 2),
        "pause_count": int(pause_count),
        "filler_count": int(filler_count),
        "speech_rate": round(speech_rate, 2),
        "fluency_score": score
    }