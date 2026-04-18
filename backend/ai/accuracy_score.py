import re


def compute_accuracy_details(transcript: str, question: str) -> dict:
    """
    Computes how relevant the user's answer is to the question.
    Designed for interview-style answers (no fixed expected answer).
    """

    t = (transcript or "").lower().strip()
    q = (question or "").lower().strip()

    words = re.findall(r"\w+", t)
    q_words = set(re.findall(r"\w+", q))

    word_count = len(words)

    if not t or not q:
        return {
            "score": 0.0,
            "matched_keywords": [],
            "missing_keywords": [],
            "keyword_coverage": 0.0,
            "similarity": 0.0,
        }

    # -------------------------
    # KEYWORD MATCH (QUESTION BASED)
    # -------------------------
    matched = []
    missing = []

    for kw in q_words:
        if kw in t:
            matched.append(kw)
        else:
            missing.append(kw)

    coverage = len(matched) / max(1, len(q_words))

    # -------------------------
    # SIMPLE SIMILARITY (WORD OVERLAP)
    # -------------------------
    overlap = len(set(words) & q_words)
    similarity = overlap / max(1, len(q_words))

    # -------------------------
    # BASE SCORE
    # -------------------------
    score = (0.7 * coverage + 0.3 * similarity) * 10

    # -------------------------
    # LENGTH ADJUSTMENT
    # -------------------------
    if word_count < 5:
        score -= 2
    elif word_count > 15:
        score += 1

    # -------------------------
    # CLAMP SCORE
    # -------------------------
    score = max(0.0, min(10.0, round(score, 2)))

    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "keyword_coverage": round(coverage, 3),
        "similarity": round(similarity, 3),
    }


def compute_accuracy_score(transcript: str, question: str) -> float:
    return float(compute_accuracy_details(transcript, question)["score"])