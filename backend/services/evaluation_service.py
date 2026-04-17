from backend.db import get_connection
from backend.services.progress_service import compute_progress, get_current_level

LEVEL_ORDER = ["Beginner", "Intermediate", "Advanced"]


def _next_level(level: str) -> str:
    try:
        i = LEVEL_ORDER.index(level)
        return LEVEL_ORDER[min(i + 1, len(LEVEL_ORDER) - 1)]
    except Exception:
        return "Beginner"


def evaluate_and_update_level(user_id: int):
    prog = compute_progress(user_id)

    current_level = str(
        prog.get("current_level", get_current_level(user_id))
    ).strip().title()

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

    # -----------------------------
    # CONDITIONS
    # -----------------------------
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

    # -----------------------------
    # LEVEL UPDATE (SQLITE)
    # -----------------------------
    new_level = _next_level(current_level)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET current_level = ?
        WHERE user_id = ?
    """, (new_level, user_id))

    conn.commit()
    conn.close()

    return {
        "message": f"Level Up! {current_level} → {new_level}",
        "current_level": new_level,
        "suggested_level": new_level,
        "total_attempts": total_attempts,
        "avg_score": round(avg_score, 2),
    }