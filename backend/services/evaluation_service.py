# backend/services/evaluation_service.py
import pandas as pd
from pathlib import Path
from backend.services.progress_service import compute_progress, get_current_level
USERS_PATH = Path(__file__).resolve().parents[2] / "datasets" / "users.csv"
LEVEL_ORDER = ["Beginner", "Intermediate", "Advanced"]
def _ensure_users_file():
    if not USERS_PATH.exists():
        USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["user_id", "email", "branch", "current_level", "created_at"]).to_csv(USERS_PATH, index=False)
def _next_level(level: str) -> str:
    try:
        i = LEVEL_ORDER.index(level)
        return LEVEL_ORDER[min(i + 1, len(LEVEL_ORDER) - 1)]
    except Exception:
        return "Beginner"
def evaluate_and_update_level(user_id: int):
    _ensure_users_file()
    prog = compute_progress(user_id)
    current_level = str(prog.get("current_level", get_current_level(user_id))).strip().title()
    total_attempts = prog.get("total_attempts", 0)
    if total_attempts == 0:
        return {
            "message": "No attempts yet",
            "current_level": current_level,
            "suggested_level": current_level,
            "total_attempts": 0,
            "avg_score": 0,
        }
    avg_flu = prog.get("avg_fluency", 0)
    avg_gra = prog.get("avg_grammar", 0)
    avg_acc = prog.get("avg_accuracy", 0)
    scores = [avg_flu, avg_gra, avg_acc]
    valid_scores = [s for s in scores if s > 0]

    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    # Condition to level up
    if total_attempts < 5:
        return {
            "message": f"Need at least {5 - total_attempts} more attempt(s) to level up.",
            "current_level": current_level,
            "suggested_level": current_level,
            "total_attempts": total_attempts,
            "avg_score": round(avg_score, 2),
        }

    if avg_score < 8:
        return {
            "message": "Improve your performance. Average score should be ≥ 8 to level up.",
            "current_level": current_level,
            "suggested_level": current_level,
            "total_attempts": total_attempts,
            "avg_score": round(avg_score, 2),
        }
    if current_level.lower() == "advanced":
        return {
            "message": "You are already at the highest level.",
            "current_level": current_level,
            "suggested_level": current_level,
            "total_attempts": total_attempts,
            "avg_score": round(avg_score, 2),
        }

    # Level up
    users_df = pd.read_csv(USERS_PATH)
    users_df["user_id"] = pd.to_numeric(users_df["user_id"], errors="coerce")

    idx_list = users_df.index[users_df["user_id"] == int(user_id)].tolist()
    if not idx_list:
        return {
            "message": "User not found",
            "current_level": "",
            "suggested_level": ""
        }
    idx = idx_list[0]
    new_level = _next_level(current_level)
    users_df.at[idx, "current_level"] = new_level
    users_df.to_csv(USERS_PATH, index=False)
    return {
        "message": f"Level Up! {current_level} → {new_level}",
        "current_level": new_level,
        "suggested_level": new_level,
        "total_attempts": total_attempts,
        "avg_score": round(avg_score, 2),
    }