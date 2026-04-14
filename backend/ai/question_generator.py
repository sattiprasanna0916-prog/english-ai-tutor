import os
import httpx
from groq import Groq

MODEL_NAME = "llama-3.1-8b-instant"

api_key = os.getenv("GROQ_API_KEY")

# ✅ Proper HTTP client with timeout
http_client = httpx.Client(timeout=20.0)

# ✅ Reuse client (important)
client = Groq(
    api_key=api_key,
    http_client=http_client
)


def generate_question(level: str, category: str, role: str):
    if not api_key:
        raise Exception("GROQ_API_KEY not set")

    prompt = f"""
Generate ONE interview question.

Level: {level}
Role: {role}
Category: {category}

Rules:
- Short and clear
- Real interview style
- No explanation
"""

    res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You generate interview questions."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=50,
    )

    return (res.choices[0].message.content or "").strip()
def generate_followup_question(previous_question: str, user_answer: str, role: str, hint: str = ""):
    if not api_key:
        raise Exception("GROQ_API_KEY not set")

    prompt = f"""
You are a technical interviewer.

Previous question:
{previous_question}

Candidate answer:
{user_answer}
Hint:
{hint}

Ask ONE relevant follow-up interview question to go deeper.

Rules:
- Should relate to the answer
- Should feel like a real interviewer
- No explanation
- Keep it concise
"""

    res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are an experienced interviewer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=60,
    )

    return (res.choices[0].message.content or "").strip()