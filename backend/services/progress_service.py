# backend/services/progress_service.py

import pandas as pd
from pathlib import Path
from datetime import datetime,timedelta

USERS_PATH = Path(__file__).resolve().parents[2] / "datasets" / "users.csv"
ATTEMPTS_PATH = Path(__file__).resolve().parents[2] / "datasets" / "attempts.csv"


# -------------------------
# LEVEL NORMALIZATION
# -------------------------
def _normalize_level(level: str) -> str:
    s = str(level or "").strip().lower()
    if s in ["1", "beginner"]:
        return "Beginner"
    if s in ["2", "intermediate"]:
        return "Intermediate"
    if s in ["3", "advanced"]:
        return "Advanced"
    return "Beginner"


# -------------------------
# GET CURRENT LEVEL
# -------------------------
def get_current_level(user_id: int) -> str:
    if not USERS_PATH.exists():
        return "Beginner"

    df = pd.read_csv(USERS_PATH)
    if df.empty:
        return "Beginner"

    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    row = df[df["user_id"] == int(user_id)]

    if row.empty:
        return "Beginner"

    return _normalize_level(row.iloc[0].get("current_level", "Beginner"))


# -------------------------
# LOAD ATTEMPTS
# -------------------------
def _load_attempts(user_id: int):
    if not ATTEMPTS_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(ATTEMPTS_PATH)
    if df.empty:
        return df

    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    df = df[df["user_id"] == int(user_id)]

    return df


# -------------------------
# STREAK CALCULATION
# -------------------------
def _calc_streak_days(df: pd.DataFrame) -> int:
    if df.empty or "created_at" not in df.columns:
        return 0

    try:
        dates = pd.to_datetime(df["created_at"], errors="coerce").dt.date
        unique_dates = sorted(set(d for d in dates if d is not None))

        if not unique_dates:
            return 0

        today = datetime.now().date()
        streak = 0
        current = today

        for d in reversed(unique_dates):
            if d == current:
                streak += 1
                current = current - timedelta(days=1)
            elif d < current:
                break

        return streak

    except Exception as e:
        print("STREAK ERROR:", e)
        return 0
# -------------------------
# MAIN PROGRESS FUNCTION
# -------------------------
def compute_progress(user_id: int):
    current_level = get_current_level(user_id)
    df = _load_attempts(user_id)

    if df.empty:
        return {
            "current_level": current_level,
            "total_attempts": 0,
            "avg_fluency": 0,
            "avg_grammar": 0,
            "avg_accuracy": 0,
            "avg_final": 0,
            "weakest_skill": "-",
            "streak_days": 0,
            "history_labels": [],
            "history_scores": [],
        }

    # -------------------------
    # Convert numeric safely
    # -------------------------
    for col in ["fluency_score", "grammar_score", "accuracy_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # -------------------------
    # Averages
    # -------------------------
    avg_flu = df["fluency_score"].mean()
    avg_gra = df["grammar_score"].mean()
    avg_acc = df["accuracy_score"].mean()

    avg_final = (avg_flu + avg_gra + avg_acc) / 3

    # -------------------------
    # Weakest skill
    # -------------------------
    skills = {
        "Fluency": avg_flu,
        "Grammar": avg_gra,
        "Accuracy": avg_acc
    }

    weakest_skill = min(skills, key=lambda k: skills[k] if skills[k] > 0 else 999)

    # -------------------------
    # Streak
    # -------------------------
    streak_days = _calc_streak_days(df)

    # -------------------------
    # Chart data (last 5 attempts)
    # -------------------------
    if "created_at" in df.columns:
        df = df.sort_values("created_at")
        df = df.fillna(0)
        last = df.tail(10)

        history_labels = last["created_at"].astype(str).str.slice(5, 10).tolist()

        history_scores = (
            (last["fluency_score"] +
             last["grammar_score"] +
             last["accuracy_score"]) / 3
        ).round(2).tolist()
    else:
        history_labels = []
        history_scores = []

    # -------------------------
    # FINAL RESPONSE
    # -------------------------
    return {
        "current_level": current_level,
        "total_attempts": len(df),

        "avg_fluency": round(avg_flu, 2),
        "avg_grammar": round(avg_gra, 2),
        "avg_accuracy": round(avg_acc, 2),
        "avg_final": round(avg_final, 2),

        "weakest_skill": weakest_skill,
        "streak_days": streak_days,

        "history_labels": history_labels,
        "history_scores": history_scores,
    }