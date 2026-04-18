import os
import logging
import re

logger = logging.getLogger(__name__)

# 🔥 Toggle
USE_AI_MODEL = False   # keep False for Render

FILLER_WORDS = {"uh", "um", "er", "ah", "like"}

# -------------------------
# OPTIONAL AI IMPORTS
# -------------------------
if USE_AI_MODEL:
    try:
        import torch
        import librosa
        from transformers import Wav2Vec2Processor, Wav2Vec2Model

        _processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
        _model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h")
        _model.eval()

    except Exception as e:
        logger.error(f"AI model load failed: {e}")
        USE_AI_MODEL = False


# -------------------------
# RULE-BASED SCORING
# -------------------------
def _rule_based_fluency(transcript: str) -> float:
    words = re.findall(r"[a-z']+", (transcript or "").lower())
    word_count = len(words)

    filler_count = sum(1 for w in words if w in FILLER_WORDS)

    score = 5.0

    # length
    if word_count < 5:
        score -= 3
    elif word_count < 10:
        score -= 2
    elif word_count < 20:
        score -= 1
    elif word_count > 25:
        score += 1

    # fillers
    if filler_count >= 6:
        score -= 3
    elif filler_count >= 3:
        score -= 2
    elif filler_count >= 1:
        score -= 1

    # repetition
    unique_ratio = len(set(words)) / max(1, word_count)
    if unique_ratio < 0.5:
        score -= 2
    elif unique_ratio < 0.7:
        score -= 1

    # connectors
    connectors = {"and", "because", "so", "then", "but"}
    if word_count > 10:
        if any(c in words for c in connectors):
            score += 0.5
        else:
            score -= 1

    # short penalty
    if word_count < 6:
        score -= 1.5

    return max(0, min(10, round(score, 2)))


# -------------------------
# AI MODEL SCORING
# -------------------------
def _ai_fluency(audio_path: str) -> float:
    try:
        audio, sr = librosa.load(audio_path, sr=16000)

        inputs = _processor(audio, sampling_rate=16000, return_tensors="pt")

        with torch.no_grad():
            outputs = _model(**inputs)

        # simple proxy: mean embedding magnitude
        embedding = outputs.last_hidden_state.mean().item()

        # normalize to score
        score = max(0, min(10, abs(embedding)))

        return round(score, 2)

    except Exception as e:
        logger.error(f"AI scoring failed: {e}")
        return None


# -------------------------
# MAIN FUNCTION
# -------------------------
def score_from_audio_transformer(audio_path: str, transcript: str) -> float:

    # ✅ Try AI model first (if enabled)
    if USE_AI_MODEL:
        ai_score = _ai_fluency(audio_path)
        if ai_score is not None:
            return ai_score

    # ✅ Fallback (always safe)
    return _rule_based_fluency(transcript)