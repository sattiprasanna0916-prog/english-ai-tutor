from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.db import get_connection
from backend.routes.user_routes import router as user_routes

app = FastAPI(title="English AI Tutor API")

# -----------------------------
# ✅ DATABASE INIT (CRITICAL)
# -----------------------------
def init_db():
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

    conn.commit()
    conn.close()

# 🚨 RUN ON START
init_db()


# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://english-ai-tutor-three.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# ROUTES
# -----------------------------
app.include_router(user_routes)

# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def root():
    return {"message": "Backend running ✅"}