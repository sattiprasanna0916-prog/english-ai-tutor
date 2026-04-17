from db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    branch TEXT,
    current_level TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    level TEXT,
    question TEXT,
    answer_text TEXT,
    audio_duration REAL,
    pause_count INTEGER,
    filler_count INTEGER,
    speech_rate REAL,
    fluency_score REAL,
    grammar_score REAL,
    accuracy_score REAL,
    final_score REAL,
    feedback TEXT,
    improved_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ DB ready")