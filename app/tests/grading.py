from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Optional, Dict, Any

def _collapse_ws(s: str) -> str:
    # strip, collapse multiple spaces/tabs/newlines to single space
    return re.sub(r"\s+", " ", s.strip())

def normalize_text(s: str) -> str:
    """
    Lowercase, trim, collapse whitespace, and remove surrounding punctuation.
    Good default for short answers.
    """
    s = _collapse_ws(s.lower())
    # strip common leading/trailing punctuation
    return s.strip(".,;:!?\"'()[]{}")

def similar(a: str, b: str) -> float:
    """
    Cheap similarity using difflib (no extra deps).
    Returns 0..1.
    """
    return SequenceMatcher(None, a, b).ratio()

def grade_short_answer(user_answer: str, correct_answer: str, *, threshold: float = 0.85) -> bool:
    """
    Returns True if answers are equal after normalization, or
    similar enough based on `threshold`.
    """
    ua = normalize_text(user_answer)
    ca = normalize_text(correct_answer)
    if not ua and not ca:
        return True
    if ua == ca:
        return True
    return similar(ua, ca) >= threshold

def grade_mcq(user_answer: str, correct_answer: str, options: Optional[Dict[str, Any]] = None) -> bool:
    """
    Accepts either the option key (e.g. 'B') or the option text.
    """
    if options and user_answer in options:
        normalized = str(options[user_answer])
    else:
        normalized = user_answer
    return normalize_text(normalized) == normalize_text(correct_answer)
