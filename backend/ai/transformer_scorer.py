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

    # 🔥 LIGHTWEIGHT MODE
    if not USE_AI_MODEL:
        words = re.findall(r"[a-z']+", (transcript or "").lower())
        word_count = len(words)

        filler_count = sum(1 for w in words if w in FILLER_WORDS)

        # -------------------------
        # BASE SCORE (dynamic)
        # -------------------------
        score = 6.0

        # -------------------------
        # LENGTH IMPACT
        # -------------------------
        if word_count < 5:
            score -= 4
        elif word_count < 10:
            score -= 2
        elif word_count < 20:
            score -= 1
        else:
            score += 1   # reward good length

        # -------------------------
        # FILLER PENALTY (stronger)
        # -------------------------
        if filler_count > 6:
            score -= 3
        elif filler_count > 3:
            score -= 1.5
        elif filler_count == 0:
            score += 0.5  # reward clean speech

        # -------------------------
        # REPETITION (flow issue)
        # -------------------------
        unique_ratio = len(set(words)) / max(1, word_count)

        if unique_ratio < 0.5:
            score -= 2
        elif unique_ratio > 0.8:
            score += 0.5

        # -------------------------
        # BASIC FLOW CHECK
        # -------------------------
        if word_count > 10:
            connectors = {"and", "because", "so", "then", "but"}
            if any(c in words for c in connectors):
                score += 0.5
            else:
                score -= 0.5

        # -------------------------
        # CLAMP
        # -------------------------
        return max(0, min(10, round(score, 2)))