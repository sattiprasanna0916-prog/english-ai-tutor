from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from backend.routes.question_routes import router as question_routes
from backend.routes.user_routes import router as user_routes
from backend.routes.attempt_routes import router as attempt_routes
from backend.routes.progress_routes import router as progress_routes

app = FastAPI(title="English AI Tutor API")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",   # ✅ ADD THIS
        "http://127.0.0.1:5500",   # ✅ ADD THIS (important)
        "https://english-ai-tutor-three.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.options("/{rest_of_path:path}")
async def preflight_handler():
    return Response(status_code=200)
# -----------------------------
# ROUTES
# -----------------------------
app.include_router(user_routes)
app.include_router(attempt_routes)
app.include_router(progress_routes)
app.include_router(question_routes)

# -----------------------------
# ROOT
# -----------------------------
@app.get("/")
def root():
    return {"message": "English AI Tutor backend is running ✅"}


# -----------------------------
# FAVICON FIX
# -----------------------------
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)