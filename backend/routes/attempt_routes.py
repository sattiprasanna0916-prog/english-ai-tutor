from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
import tempfile
import os

from backend.services.auth_service import verify_token

# AI
from backend.ai.audio_convert import ensure_wav_16k_mono
from backend.ai.transformer_scorer import score_from_audio_transformer
from backend.ai.speech_to_text import transcribe_audio
from backend.ai.feedback_llm import generate_feedback_groq
from backend.ai.speech_metrics import compute_audio_metrics
from backend.ai.grammar_score import compute_grammar_score
from backend.ai.accuracy_score import compute_accuracy_details

# Services
from backend.services.attempt_service import save_attempt, get_user_attempts
from backend.services.user_service import get_user
from backend.services.evaluation_service import evaluate_and_update_level

router = APIRouter(prefix="/attempts", tags=["Attempts"])

# 🔧 CONFIG
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

FLUENCY_WEIGHT = 0.3
GRAMMAR_WEIGHT = 0.3
ACCURACY_WEIGHT = 0.4


@router.post("/submit")
async def submit_attempt(
    level: str = Form(...),
    question: str = Form(...),
    audio: UploadFile = File(...),
    token_data: dict = Depends(verify_token),
):
    tmp_path = None
    wav_path = None

    # 🔐 Secure user from JWT
    user_id = token_data.get("sub")
    if not user_id or not get_user(user_id):
        raise HTTPException(status_code=401, detail="Invalid user")

    try:
        # -----------------------------
        # 🔒 AUDIO VALIDATION
        # -----------------------------
        filename = (audio.filename or "").lower()
        ext = os.path.splitext(filename)[-1]

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported audio format")

        content = await audio.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # -----------------------------
        # 1️⃣ SAVE TEMP FILE
        # -----------------------------
        suffix = ext if ext else ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # -----------------------------
        # 2️⃣ CONVERT TO WAV
        # -----------------------------
        wav_path = ensure_wav_16k_mono(tmp_path)

        # -----------------------------
        # 3️⃣ SPEECH TO TEXT
        # -----------------------------
        transcript = (transcribe_audio(wav_path) or "").strip()

        if not transcript or transcript.lower() in ["no speech detected", "silence"]:
            raise HTTPException(
                status_code=400,
                detail="No clear speech detected. Please speak clearly."
            )

        # -----------------------------
        # 4️⃣ SCORING PIPELINE
        # -----------------------------
        try:
            fluency = float(score_from_audio_transformer(wav_path, transcript))
            grammar = float(compute_grammar_score(transcript))

            acc_details = compute_accuracy_details(transcript, question)
            accuracy = float(acc_details.get("score", 0))

            metrics = compute_audio_metrics(wav_path, transcript)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Processing error: {str(e)}"
            )

        # Reject too short audio
        if float(metrics.get("audio_duration", 0)) < 2.5:
            raise HTTPException(
                status_code=400,
                detail="Audio too short. Minimum 3 seconds required."
            )

        # -----------------------------
        # 5️⃣ FINAL SCORE
        # -----------------------------
        final_score = round(
            FLUENCY_WEIGHT * fluency +
            GRAMMAR_WEIGHT * grammar +
            ACCURACY_WEIGHT * accuracy,
            2
        )

        # -----------------------------
        # 6️⃣ FEEDBACK (LLM)
        # -----------------------------
        fb = generate_feedback_groq(
            transcript=transcript,
            fluency=fluency,
            grammar=grammar,
            accuracy=accuracy,
            question=question,
            expected_text=question
        )

        feedback = fb.get("feedback", "")
        improved_answer = fb.get("improved_answer", "")

        # -----------------------------
        # 7️⃣ IMPROVEMENT TRACKING
        # -----------------------------
        previous_attempts = get_user_attempts(user_id)

        previous_score = None
        if previous_attempts:
            previous_score = previous_attempts[0].get("final_score")

        improvement = 0
        if previous_score is not None:
            improvement = round(final_score - float(previous_score), 2)

        # -----------------------------
        # 8️⃣ SAVE ATTEMPT
        # -----------------------------
        save_attempt(
            user_id=user_id,
            level=level,
            question=question,
            answer_text=transcript,
            audio_duration=metrics.get("audio_duration", 0),
            pause_count=metrics.get("pause_count", 0),
            filler_count=metrics.get("filler_count", 0),
            speech_rate=metrics.get("speech_rate", 0),
            fluency_score=fluency,
            grammar_score=grammar,
            accuracy_score=accuracy,
            final_score=final_score,
            feedback=feedback,
            improved_answer=improved_answer,
        )

        # -----------------------------
        # 9️⃣ LEVEL UPDATE
        # -----------------------------
        level_update = evaluate_and_update_level(user_id)

        # -----------------------------
        # 🔟 RESPONSE
        # -----------------------------
        return {
            "transcript": transcript,
            "fluency": round(fluency, 2),
            "grammar": round(grammar, 2),
            "accuracy": round(accuracy, 2),
            "final_score": final_score,
            "improvement": improvement,
            "feedback": feedback,
            "improved_answer": improved_answer,
            "audio_metrics": metrics,
            "level_update": level_update,
        }

    finally:
        # -----------------------------
        # 🧹 CLEANUP
        # -----------------------------
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


@router.get("/user/{user_id}")
def get_attempts(user_id: int, token_data: dict = Depends(verify_token)):
    # 🔐 Optional: ensure user can only access own data
    token_user = token_data.get("sub")

    if str(user_id) != str(token_user):
        raise HTTPException(status_code=403, detail="Access denied")

    if not get_user(user_id):
        return []

    return get_user_attempts(user_id)