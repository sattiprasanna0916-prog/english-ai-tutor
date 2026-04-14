import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(audio_path: str) -> str:
    try:
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3"
            )
        return response.text.strip()
    except Exception as e:
        print("Groq transcription error:", e)
        return ""