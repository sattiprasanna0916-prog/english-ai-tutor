from backend.db import get_connection
from datetime import datetime, timedelta


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
# GET CURRENT LEVEL (SQL)
# -------------------------
def get_current_level(user_id: int) -> str:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT current_level FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()

    if not row:
        return "Beginner"

    return _normalize_level(row["current_level"])


# -------------------------
# LOAD ATTEMPTS (SQL)
# -------------------------
def _load_attempts(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM attempts
        WHERE user_id = ?
        ORDER BY created_at
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# -------------------------
# STREAK CALCULATION
# -------------------------
def _calc_streak_days(rows):
    if not rows:
        return 0

    try:
        dates = [
            datetime.fromisoformat(r["created_at"]).date()
            for r in rows if r.get("created_at")
        ]

        unique_dates = sorted(set(dates))
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
    rows = _load_attempts(user_id)

    if not rows:
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
    # Extract values
    # -------------------------
    flu = [r.get("fluency_score", 0) or 0 for r in rows]
    gra = [r.get("grammar_score", 0) or 0 for r in rows]
    acc = [r.get("accuracy_score", 0) or 0 for r in rows]

    avg_flu = sum(flu) / len(flu)
    avg_gra = sum(gra) / len(gra)
    avg_acc = sum(acc) / len(acc)

    avg_final = (avg_flu + avg_gra + avg_acc) / 3

    # -------------------------
    # Weakest skill
    # -------------------------
    skills = {
        "Fluency": avg_flu,
        "Grammar": avg_gra,
        "Accuracy": avg_acc
    }

    weakest_skill = min(skills, key=skills.get)

    # -------------------------
    # Streak
    # -------------------------
    streak_days = _calc_streak_days(rows)

    # -------------------------
    # Chart data (last 10)
    # -------------------------
    last = rows[-10:]

    history_labels = [
        r["created_at"][5:10] if r.get("created_at") else ""
        for r in last
    ]

    history_scores = [
        round(
            (r.get("fluency_score", 0) +
             r.get("grammar_score", 0) +
             r.get("accuracy_score", 0)) / 3,
            2
        )
        for r in last
    ]

    # -------------------------
    # FINAL RESPONSE
    # -------------------------
    return {
        "current_level": current_level,
        "total_attempts": len(rows),

        "avg_fluency": round(avg_flu, 2),
        "avg_grammar": round(avg_gra, 2),
        "avg_accuracy": round(avg_acc, 2),
        "avg_final": round(avg_final, 2),

        "weakest_skill": weakest_skill,
        "streak_days": streak_days,

        "history_labels": history_labels,
        "history_scores": history_scores,
    }