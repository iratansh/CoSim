from typing import Set

def tokenize(text: str) -> Set[str]:
    return {t for t in text.lower().replace('\n',' ').split() if t}

def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def relevance_score(query: str, doc: str) -> float:
    return jaccard(tokenize(query), tokenize(doc))

__all__ = ["relevance_score"]
