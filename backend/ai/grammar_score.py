import re


def compute_grammar_score(transcript: str) -> float:
    t = (transcript or "").strip()

    if not t:
        return 0.0

    words = re.findall(r"[a-zA-Z']+", t.lower())
    wc = len(words)

    score = 8.0  # start lower (more realistic baseline)

    # -------------------------
    # 1. Sentence basics
    # -------------------------
    if not t[0].isupper():
        score -= 1

    if not re.search(r"[.!?]$", t):
        score -= 1

    # -------------------------
    # 2. Repetition errors
    # -------------------------
    if re.search(r"\b(\w+)\s+\1\b", t.lower()):
        score -= 2

    # -------------------------
    # 3. Very short or broken sentences
    # -------------------------
    if wc < 4:
        score -= 2
    elif wc < 8:
        score -= 1

    # -------------------------
    # 4. Word diversity (basic quality)
    # -------------------------
    unique_ratio = len(set(words)) / max(1, wc)

    if unique_ratio < 0.5:
        score -= 2
    elif unique_ratio < 0.7:
        score -= 1

    # -------------------------
    # 5. Simple grammar mistake patterns
    # -------------------------
    common_errors = [
        r"\bi is\b",
        r"\bhe go\b",
        r"\bshe go\b",
        r"\bthey is\b",
        r"\bi done\b",
        r"\bi did went\b"
    ]

    for pattern in common_errors:
        if re.search(pattern, t.lower()):
            score -= 2

    # -------------------------
    # 6. Sentence structure check
    # -------------------------
    sentences = [s.strip() for s in re.split(r"[.!?]+", t) if s.strip()]

    if len(sentences) == 1 and wc > 15:
        score -= 1  # long unstructured sentence

    # -------------------------
    # 7. Clamp score
    # -------------------------
    score = max(0.0, min(10.0, score))

    return round(score, 2)