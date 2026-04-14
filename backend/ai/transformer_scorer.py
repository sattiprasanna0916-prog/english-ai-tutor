# backend/ai/transformer_scorer.py

import os
import numpy as np
import logging
import re

logger = logging.getLogger(__name__)

# 🔥 Toggle this
USE_AI_MODEL = False

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

WEIGHTS_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "english-ai-tutor-transformer",
    "fluency_regressor.pt"
)

# Only load heavy libs if enabled
if USE_AI_MODEL:
    import torch
    import torch.nn as nn
    import librosa
    from transformers import Wav2Vec2Processor, Wav2Vec2Model

    _processor = None
    _model = None

FILLER_WORDS = {"uh", "um", "er", "ah", "like"}


# -------------------------
# MODEL CLASS (ONLY IF ENABLED)
# -------------------------
if USE_AI_MODEL:
    class Wav2Vec2FluencyRegressor(nn.Module):
        def __init__(self, model_source):
            super().__init__()
            self.base = Wav2Vec2Model.from_pretrained(model_source)
            hidden = self.base.config.hidden_size

            self.dropout = nn.Dropout(0.1)
            self.head = nn.Linear(hidden, 1)

        def forward(self, input_values, attention_mask=None):
            out = self.base(input_values=input_values, attention_mask=attention_mask)
            pooled = out.last_hidden_state.mean(dim=1)
            pooled = self.dropout(pooled)
            return self.head(pooled).squeeze(-1)


# -------------------------
# SAFE FILE CHECK
# -------------------------
def _file_ok(path: str) -> bool:
    return os.path.exists(path) and os.path.getsize(path) > 0


# -------------------------
# MODEL LOADER
# -------------------------
def _lazy_load():
    if not USE_AI_MODEL:
        return

    global _processor, _model

    if _processor is not None and _model is not None:
        return

    try:
        model_source = "facebook/wav2vec2-base-960h"

        _processor = Wav2Vec2Processor.from_pretrained(model_source)
        _model = Wav2Vec2FluencyRegressor(model_source)

        if _file_ok(WEIGHTS_PATH):
            state = torch.load(WEIGHTS_PATH, map_location="cpu")
            _model.load_state_dict(state, strict=False)
            logger.info("Custom fluency regressor loaded")
        else:
            logger.warning("Custom weights not found")

        _model.eval()

    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        _processor = None
        _model = None


# -------------------------
# MAIN SCORING FUNCTION
# -------------------------
def score_from_audio_transformer(audio_path: str, transcript: str) -> float:

    # 🔥 LIGHTWEIGHT MODE (DEPLOYMENT)
    if not USE_AI_MODEL:
        words = re.findall(r"[a-z']+", (transcript or "").lower())
        word_count = len(words)

        filler_count = sum(1 for w in words if w in FILLER_WORDS)

        score =5.5

        # length penalty
        if word_count < 5:
            score -= 3
        elif word_count < 10:
            score -=1.5
        elif word_count < 20:
            score -= 0.5

        # filler penalty
        if filler_count > 5:
            score -=2
        elif filler_count > 2:
            score -=1

        return max(0, min(10, round(score, 2)))

    # 🔥 FULL AI MODE (LOCAL ONLY)
    try:
        _lazy_load()

        y, _ = librosa.load(audio_path, sr=16000, mono=True)

        if y is None or len(y) == 0:
            return 5.0

        duration = len(y) / 16000

        if _processor is None or _model is None:
            base_score = 5.5
        else:
            inputs = _processor(
                y,
                sampling_rate=16000,
                return_tensors="pt",
                padding=True
            )

            with torch.no_grad():
                raw_pred = _model(
                    input_values=inputs["input_values"],
                    attention_mask=inputs.get("attention_mask", None),
                ).item()

            base_score = float(np.clip(raw_pred, 3.0, 9.0))

        words = re.findall(r"[a-z']+", transcript.lower())
        word_count = len(words)
        filler_count = sum(1 for w in words if w in FILLER_WORDS)

        minutes = duration / 60 if duration > 0 else 1
        wpm = word_count / minutes if minutes > 0 else 0

        score = base_score

        if word_count < 5:
            score -= 2
        elif word_count < 10:
            score -= 1

        if filler_count > 6:
            score -= 2
        elif filler_count > 3:
            score -= 1

        if wpm < 80 or wpm > 170:
            score -= 1

        if duration < 2:
            score -= 1

        return max(0, min(10, round(score, 2)))

    except Exception as e:
        logger.warning(f"Transformer scoring failed: {e}")
        return 5.0