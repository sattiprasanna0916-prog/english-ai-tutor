from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import os
from fastapi import Depends
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


@router.post("/submit")
async def submit_attempt(
    user_id: int = Form(...),
    level: str = Form(...),
    question: str = Form(...),
    audio: UploadFile = File(...),
    token_data: dict = Depends(verify_token),
):
    tmp_path = None
    wav_path = None
    if not get_user(user_id):
        return {"error": "Invalid user"}
    try:
        # -----------------------------
# 🔒 AUDIO VALIDATION
# -----------------------------
        allowed_ext = [".wav", ".mp3", ".m4a", ".webm"]

        filename = (audio.filename or "").lower()
        ext = os.path.splitext(filename)[-1]

        if ext not in allowed_ext:
            return {"error": "❌ Unsupported audio format"}

# size limit (e.g. 10MB)
        content = await audio.read()

        if len(content) > 10 * 1024 * 1024:
            return {"error": "❌ File too large (max 10MB)"}
        # -----------------------------
        # 1️⃣ SAVE TEMP FILE (ANY FORMAT)
        # -----------------------------
        suffix = os.path.splitext(audio.filename or "")[-1] or ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # -----------------------------
        # 2️⃣ CONVERT TO WAV (FIX ERROR)
        # -----------------------------
        wav_path = ensure_wav_16k_mono(tmp_path)

        # -----------------------------
        # 3️⃣ SPEECH TO TEXT
        # -----------------------------
        transcript = (transcribe_audio(wav_path) or "").strip()

        if not transcript or transcript.lower() in ["no speech detected", "silence"]:
            return {
                "error": "❌ No clear speech detected. Please speak clearly.",
                "transcript": "",
            }

        # -----------------------------
        # 4️⃣ SCORES
        # -----------------------------
        fluency = float(score_from_audio_transformer(wav_path, transcript))
        grammar = float(compute_grammar_score(transcript))

        acc_details = compute_accuracy_details(transcript, question)
        accuracy = float(acc_details.get("score", 0))

        metrics = compute_audio_metrics(wav_path, transcript)

        # Optional: reject too short audio
        if float(metrics.get("audio_duration", 0)) < 2.5:
            return {
                "error": "❌ Audio too short. Please speak at least 3 seconds.",
            }

        # -----------------------------
        # 5️⃣ FINAL SCORE
        # -----------------------------
        final_score = round(
    0.3 * fluency +
    0.3 * grammar +
    0.4 * accuracy,
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
        previous_attempts = get_user_attempts(user_id)

        previous_score = None
        if previous_attempts:
            previous_score = previous_attempts[0].get("final_score", None)
        improvement = 0
        if previous_score is not None:
            improvement = round(final_score - float(previous_score), 2)
        # -----------------------------
        # 7️⃣ SAVE ATTEMPT
        # -----------------------------
        saved = save_attempt(
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
        # 8️⃣ LEVEL UPDATE
        # -----------------------------
        level_update = evaluate_and_update_level(user_id)

        # -----------------------------
        # 9️⃣ RESPONSE
        # -----------------------------
        return {
    "transcript": transcript,

    # ✅ flatten structure (frontend expects this)
    "fluency": round(fluency, 2),
    "grammar": round(grammar, 2),
    "accuracy": round(accuracy, 2),
    "final_score": final_score,
    "improvement": improvement, 
    "feedback": feedback,
    "improved_answer": improved_answer,

    # optional extras
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
def get_attempts(user_id: int):
    if not get_user(user_id):
        return []
    return get_user_attempts(user_id)
