from backend.db import get_connection

def save_attempt(**data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO attempts (
            user_id, level, question, answer_text,
            audio_duration, pause_count, filler_count, speech_rate,
            fluency_score, grammar_score, accuracy_score, final_score,
            feedback, improved_answer
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["user_id"],
        data["level"],
        data["question"],
        data["answer_text"],
        data["audio_duration"],
        data["pause_count"],
        data["filler_count"],
        data["speech_rate"],
        data["fluency_score"],
        data["grammar_score"],
        data["accuracy_score"],
        data["final_score"],
        data["feedback"],
        data["improved_answer"]
    ))

    conn.commit()
    conn.close()


def get_user_attempts(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM attempts
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]