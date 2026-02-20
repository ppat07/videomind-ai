"""
Helpers to map processed jobs into directory-ready metadata.
"""
from typing import Dict, Any, List


CATEGORIES = [
    "Setup & Onboarding",
    "Automation Workflows",
    "Tooling & Integrations",
    "Business Use Cases",
    "Debugging & Fixes",
    "Prompts & Templates",
]


def _contains_any(text: str, terms: List[str]) -> bool:
    t = (text or "").lower()
    return any(term in t for term in terms)


def infer_category(title: str, summary: str, topics: List[str] = None) -> str:
    corpus = " ".join([title or "", summary or "", " ".join(topics or [])]).lower()

    if _contains_any(corpus, ["setup", "install", "onboard", "getting started"]):
        return "Setup & Onboarding"
    if _contains_any(corpus, ["debug", "error", "fix", "troubleshoot"]):
        return "Debugging & Fixes"
    if _contains_any(corpus, ["prompt", "template"]):
        return "Prompts & Templates"
    if _contains_any(corpus, ["notion", "api", "mcp", "integration", "tool"]):
        return "Tooling & Integrations"
    if _contains_any(corpus, ["money", "revenue", "sales", "business", "make $"]):
        return "Business Use Cases"
    return "Automation Workflows"


def infer_difficulty(transcript_word_count: int) -> str:
    if transcript_word_count >= 3500:
        return "Advanced"
    if transcript_word_count >= 1600:
        return "Intermediate"
    return "Beginner"


def make_5_bullets(summary: str, key_points: List[str]) -> str:
    points = [p for p in (key_points or []) if p][:5]
    if len(points) < 5 and summary:
        points = points + [summary]
    points = points[:5]
    return "\n".join([f"• {p}" for p in points])


def infer_signal_score(ai_enhanced: Dict[str, Any], transcript: Dict[str, Any]) -> int:
    score = 65
    qa_pairs = ai_enhanced.get("qa_pairs") or []
    topics = ai_enhanced.get("topics") or []
    wc = (transcript or {}).get("word_count") or 0

    score += min(len(qa_pairs) * 2, 12)
    score += min(len(topics) * 2, 10)
    if wc > 1200:
        score += 8
    if wc > 2500:
        score += 5
    return max(1, min(100, score))
