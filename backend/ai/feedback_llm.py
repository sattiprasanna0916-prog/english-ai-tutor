import os
from groq import Groq
import re
MODEL_NAME = "llama-3.1-8b-instant"


def generate_feedback_groq(
    transcript: str,
    fluency: float,
    grammar: float,
    accuracy: float,
    question: str = "",
    expected_text: str = "",
    **kwargs  # 🔥 accepts extra unused params safely
):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise Exception("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)

    # -----------------------------
    # FEEDBACK PROMPT
    # -----------------------------
    feedback_prompt = f"""
You are an AI interview coach.

Evaluate the user's answer and give clear, practical feedback.

Question:
{question}

User Answer:
{transcript}

Scores (0–10):
- Fluency: {fluency}
- Grammar: {grammar}
- Accuracy: {accuracy}

Instructions:
- Give 3 clear improvement points
- Be specific (not generic)
- Focus on communication and interview performance
- Keep it under 80 words

Output format:
- Point 1
- Point 2
- Point 3
"""

    feedback_res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful interview coach."},
            {"role": "user", "content": feedback_prompt},
        ],
        temperature=0.7,
        max_tokens=150,
    )

    raw_feedback = (feedback_res.choices[0].message.content or "").strip()

# normalize into bullet points
    lines = raw_feedback.split("\n")
    clean_lines = []

    for line in lines:
        line = line.strip()

    # remove numbering or symbols
        line = re.sub(r"^[\-\*\d\.\)\s]+", "", line)

        if line:
            clean_lines.append(line)

    feedback_text = "\n".join(clean_lines[:3])  # max 3 points

    # -----------------------------
    # IMPROVED ANSWER
    # -----------------------------
    improve_prompt = f"""
Improve the following interview answer.

Question:
{question}

User Answer:
{transcript}

Rules:
- 3 to 4 sentences
- Clear structure
- Natural spoken English
- Relevant to question
- No labels, only answer
"""

    improve_res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You improve answers clearly."},
            {"role": "user", "content": improve_prompt},
        ],
        temperature=0.6,
        max_tokens=120,
    )

    improved_answer = (improve_res.choices[0].message.content or "").strip()

    return {
        "feedback": feedback_text,
        "improved_answer": improved_answer,
    }