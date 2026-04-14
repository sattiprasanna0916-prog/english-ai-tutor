import re

def compute_grammar_score(transcript: str) -> float:
    t = (transcript or "").strip()

    if not t:
        return 0.0

    score = 10.0

    # -------------------------
    # 1. Basic checks (soft)
    # -------------------------
    if not t[0].isupper():
        score -= 0.5

    if not re.search(r"[.!?]$", t):
        score -= 0.5

    # -------------------------
    # 2. Sentence structure
    # -------------------------
    sentences = [s.strip() for s in re.split(r"[.!?]+", t) if s.strip()]

    

    # -------------------------
    # 3. Word analysis
    # -------------------------
    words = re.findall(r"[a-zA-Z']+", t.lower())
    wc = len(words)
    if len(sentences) == 1 and wc > 12:
        score -= 0.5  # softer penalty

    if wc == 0:
        return 0.0

    # -------------------------
    # 4. Length penalty (balanced)
    # -------------------------
    if wc < 5:
        score -= 2.5
    elif wc < 10:
        score -= 1.5
    elif wc < 20:
        score -= 0.5

    # -------------------------
    # 5. Repetition check
    # -------------------------
    unique_ratio = len(set(words)) / wc

    if unique_ratio < 0.5:
        score -= 1.5
    elif unique_ratio < 0.7:
        score -= 0.5

    # -------------------------
    # 6. Basic grammar patterns
    # -------------------------
    if re.search(r"\b(\w+)\s+\1\b", t.lower()):
        score -= 1.5

    # Improved verb detection (any word ending with ed / ing)
    # Connectors
    connectors = {"because", "and", "so", "but", "then"}
    if wc > 10 and not any(c in words for c in connectors):
        score -= 0.5

    # -------------------------
    # 7. Filler (light penalty only)
    # -------------------------
    fillers = ["uh", "um", "like", "you know"]
    filler_count = sum(t.lower().count(f) for f in fillers)

    if filler_count >= 4:
        score -= 1.5
    elif filler_count >= 2:
        score -= 0.5

    # -------------------------
    # 8. Clamp
    # -------------------------
    score = max(0.0, min(10.0, score))

    return round(score, 2)