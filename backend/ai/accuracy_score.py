import re
from difflib import SequenceMatcher

def compute_accuracy_details(transcript: str, expected_text: str) -> dict:

    t = (transcript or "").lower().strip()
    words = re.findall(r"\w+", t)
    wc = len(words)

    if not expected_text:
        return {
            "score": 0.0,
            "matched_keywords": [],
            "missing_keywords": [],
            "keyword_coverage": 0.0,
            "similarity": 0.0,
        }

    exp_words = list(set(re.findall(r"\w+", expected_text.lower())))
    transcript_words = set(words)

    matched = []
    missing = []

    # -------------------------
    # STRICTER KEYWORD MATCH
    # -------------------------
    for kw in exp_words:
        found = False

        for w in transcript_words:
            # exact OR strong partial match only
            if kw == w or (len(kw) > 4 and kw in w):
                found = True
                break

        if found:
            matched.append(kw)
        else:
            missing.append(kw)

    coverage = len(matched) / max(1, len(exp_words))

    # -------------------------
    # SIMILARITY
    # -------------------------
    sim = SequenceMatcher(None, t, expected_text.lower()).ratio()

    # -------------------------
    # WEIGHTED SCORE (STRONGER)
    # -------------------------
    score = (0.7 * coverage + 0.3 * sim) * 10

    # -------------------------
    # HARD LENGTH PENALTY
    # -------------------------
    if wc < 5:
        score -= 4
    elif wc < 10:
        score -= 2
    elif wc < 20:
        score -= 1

    # -------------------------
    # LOW COVERAGE PENALTY
    # -------------------------
    if coverage < 0.2:
        score -= 3
    elif coverage < 0.4:
        score -= 1.5

    # -------------------------
    # VERY LOW SIMILARITY PENALTY
    # -------------------------
    if sim < 0.2:
        score -= 2

    # -------------------------
    # CLAMP
    # -------------------------
    score = max(0.0, min(10.0, round(score, 2)))

    return {
        "score": score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "keyword_coverage": round(coverage, 3),
        "similarity": round(sim, 3),
    }


def compute_accuracy_score(transcript: str, expected_text: str) -> float:
    return float(compute_accuracy_details(transcript, expected_text)["score"])