from backend.db import get_connection

def register_user(email, branch, current_level="Beginner"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    existing = cur.fetchone()

    if existing:
        conn.close()
        return dict(existing)

    cur.execute("""
        INSERT INTO users (email, branch, current_level)
        VALUES (?, ?, ?)
    """, (email, branch, current_level))

    conn.commit()

    user_id = cur.lastrowid

    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()

    conn.close()
    return dict(user)


def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()

    conn.close()
    return dict(user) if user else None


def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()

    conn.close()
    return dict(user) if user else None