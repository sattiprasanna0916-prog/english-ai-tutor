import librosa
import numpy as np
import re

FILLER_WORDS = {"uh", "um", "er", "ah", "like"}

def compute_audio_metrics(audio_path: str, transcript: str):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)

    # 🎧 duration
    duration = len(y) / sr if sr > 0 else 0

    # 🧠 pauses (less aggressive)
    intervals = librosa.effects.split(y, top_db=35)
    pause_count = max(0, len(intervals) - 1)

    pause_count = min(pause_count, 15)

    # 🗣️ transcript
    words = re.findall(r"[a-z']+", (transcript or "").lower())
    word_count = len(words)

    filler_count = sum(1 for w in words if w in FILLER_WORDS)

    # ⚡ speech rate
    speech_rate = (word_count / duration) * 60 if duration > 0 else 0

    # =========================
    # 🔥 IMPROVED FLUENCY SCORE
    # =========================

    score = 6.0   # 🔥 better baseline

    # -------------------------
    # LENGTH (balanced)
    # -------------------------
    if word_count < 5:
        score -= 3
    elif word_count < 10:
        score -= 2
    elif word_count < 20:
        score -= 1
    elif word_count > 25:
        score += 1

    # -------------------------
    # PAUSES
    # -------------------------
    if pause_count > 10:
        score -= 2
    elif pause_count > 5:
        score -= 1

    # -------------------------
    # FILLERS
    # -------------------------
    if filler_count >= 6:
        score -= 2
    elif filler_count >= 3:
        score -= 1
    elif filler_count == 0 and word_count > 10:
        score += 0.5   # reward clean speech

    # -------------------------
    # SPEECH RATE (realistic range)
    # -------------------------
    if speech_rate < 80:
        score -= 1.5
    elif speech_rate < 100:
        score -= 0.5
    elif 110 <= speech_rate <= 160:
        score += 0.5   # ideal range
    elif speech_rate > 190:
        score -= 1

    # -------------------------
    # FINAL CLAMP
    # -------------------------
    score = max(0, min(10, round(score, 2)))

    return {
        "audio_duration": round(duration, 2),
        "pause_count": int(pause_count),
        "filler_count": int(filler_count),
        "speech_rate": round(speech_rate, 2),
        "fluency_score": score
    }