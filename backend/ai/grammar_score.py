import re

def compute_grammar_score(transcript: str) -> float:
    t = (transcript or "").strip()

    if not t:
        return 0.0

    score = 10.0

    # -------------------------
    # 1. Basic checks (stronger)
    # -------------------------
    if not t[0].isupper():
        score -= 1

    if not re.search(r"[.!?]$", t):
        score -= 1

    # -------------------------
    # 2. Sentence structure
    # -------------------------
    sentences = [s.strip() for s in re.split(r"[.!?]+", t) if s.strip()]
    words = re.findall(r"[a-zA-Z']+", t.lower())
    wc = len(words)

    if wc == 0:
        return 0.0

    # Long single sentence → penalty
    if len(sentences) == 1 and wc > 12:
        score -= 1.5

    # Too many short sentences → penalty
    if len(sentences) > 5:
        score -= 1

    # -------------------------
    # 3. Length penalty (stronger)
    # -------------------------
    if wc < 5:
        score -= 3
    elif wc < 10:
        score -= 2
    elif wc < 20:
        score -= 1

    # -------------------------
    # 4. Repetition check
    # -------------------------
    unique_ratio = len(set(words)) / wc

    if unique_ratio < 0.5:
        score -= 2
    elif unique_ratio < 0.7:
        score -= 1

    # -------------------------
    # 5. Grammar pattern issues
    # -------------------------
    if re.search(r"\b(\w+)\s+\1\b", t.lower()):
        score -= 2  # repeated words

    # Missing connectors → stronger penalty
    connectors = {"because", "and", "so", "but", "then"}
    if wc > 10 and not any(c in words for c in connectors):
        score -= 1

    # -------------------------
    # 6. Filler penalty (stronger)
    # -------------------------
    fillers = ["uh", "um", "like", "you know"]
    filler_count = sum(t.lower().count(f) for f in fillers)

    if filler_count >= 4:
        score -= 2
    elif filler_count >= 2:
        score -= 1

    # -------------------------
    # 7. Missing punctuation inside long text
    # -------------------------
    if wc > 20 and t.count(",") == 0:
        score -= 1

    # -------------------------
    # 8. Clamp
    # -------------------------
    score = max(0.0, min(10.0, score))

    return round(score, 2)