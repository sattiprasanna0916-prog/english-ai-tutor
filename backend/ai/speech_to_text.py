_model = None

def transcribe_audio(audio_path: str) -> str:
    global _model

    if _model is None:
        try:
            import whisper   # ✅ moved here
            _model = whisper.load_model("small")
        except Exception:
            return ""

    try:
        result = _model.transcribe(audio_path, fp16=False)
        return (result.get("text") or "").strip()
    except Exception:
        return ""