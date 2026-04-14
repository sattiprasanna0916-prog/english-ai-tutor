import pandas as pd
import threading
from pathlib import Path
from datetime import datetime
lock = threading.Lock()
DATA_PATH = Path(__file__).resolve().parents[2] / "datasets" / "attempts.csv"

COLUMNS = [
    "attempt_id",
    "user_id",
    "level",
    "question",
    "answer_text",
    "audio_duration",
    "pause_count",
    "filler_count",
    "speech_rate",
    "fluency_score",
    "grammar_score",
    "accuracy_score",
    "final_score",
    "feedback",
    "improved_answer",
    "created_at",
]


def _ensure_file():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_PATH.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_PATH, index=False)
        return
    with lock:
        df = pd.read_csv(DATA_PATH)

        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""

        df = df[COLUMNS]
        df.to_csv(DATA_PATH, index=False)


def _safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


def _safe_int(x):
    try:
        return int(x)
    except:
        return 0


def save_attempt(
    user_id,
    level,
    question,
    answer_text,
    audio_duration,
    pause_count,
    filler_count,
    speech_rate,
    fluency_score,
    grammar_score,
    accuracy_score,
    final_score,
    feedback,
    improved_answer,
):
    _ensure_file()
    df = pd.read_csv(DATA_PATH)

    attempt_id = 1 if df.empty else int(df["attempt_id"].max()) + 1

    row = {
        "attempt_id": attempt_id,
        "user_id": _safe_int(user_id),
        "level": str(level),
        "question": str(question),
        "answer_text": str(answer_text),

        "audio_duration": _safe_float(audio_duration),
        "pause_count": _safe_int(pause_count),
        "filler_count": _safe_int(filler_count),
        "speech_rate": _safe_float(speech_rate),

        "fluency_score": _safe_float(fluency_score),
        "grammar_score": _safe_float(grammar_score),
        "accuracy_score": _safe_float(accuracy_score),
        "final_score": _safe_float(final_score),

        "feedback": str(feedback),
        "improved_answer": str(improved_answer),

        "created_at": datetime.now().isoformat(),
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)

    return row


def get_user_attempts(user_id: int):
    _ensure_file()
    df = pd.read_csv(DATA_PATH)

    if df.empty:
        return []

    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    df = df[df["user_id"] == int(user_id)]

    if df.empty:
        return []

    df = df.sort_values("created_at", ascending=False)

    return df.to_dict(orient="records")