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
    "General Content",  # For non-AI/automation content
    "Entertainment",    # Videos, reviews, discussions
    "Educational",      # Tutorials, explanations
    "News & Updates",   # Industry news, product updates
    "Reviews & Opinions" # Product reviews, commentary
]


def _contains_any(text: str, terms: List[str]) -> bool:
    """Check if any terms appear as whole words in text to avoid substring false positives."""
    import re
    t = (text or "").lower()
    for term in terms:
        # Use word boundaries for short terms that could be substrings
        if len(term) <= 3:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, t):
                return True
        else:
            # For longer terms, simple substring match is fine
            if term in t:
                return True
    return False


def infer_category(title: str, summary: str, topics: List[str] = None) -> str:
    corpus = " ".join([title or "", summary or "", " ".join(topics or [])]).lower()

    # AI/Automation-specific categories (highest priority)
    if _contains_any(corpus, ["setup", "install", "onboard", "getting started", "configuration"]):
        return "Setup & Onboarding"
    if _contains_any(corpus, ["debug", "error", "fix", "troubleshoot", "problem", "issue"]):
        return "Debugging & Fixes"  
    if _contains_any(corpus, ["prompt", "template", "system prompt", "prompt engineering"]):
        return "Prompts & Templates"
    if _contains_any(corpus, ["notion", "api", "mcp", "integration", "tool", "webhook", "automation", "workflow", "ai agent", "openclaw"]):
        return "Tooling & Integrations"
    if _contains_any(corpus, ["money", "revenue", "sales", "business", "make $", "profit", "roi", "entrepreneur"]):
        return "Business Use Cases"
    if _contains_any(corpus, ["automation", "workflow", "agent", "ai", "artificial intelligence", "machine learning"]):
        return "Automation Workflows"
    
    # Non-AI/Automation categories (broader content)
    if _contains_any(corpus, ["review", "opinion", "thoughts on", "reaction", "commentary", "analysis"]):
        return "Reviews & Opinions"
    if _contains_any(corpus, ["news", "update", "announcement", "release", "breaking"]):
        return "News & Updates"
    if _contains_any(corpus, ["tutorial", "how to", "learn", "course", "education", "explanation", "guide"]):
        return "Educational"
    if _contains_any(corpus, ["funny", "entertainment", "meme", "comedy", "fun", "gaming", "music", "movie", "cat", "dog", "compilation", "viral", "hilarious"]):
        return "Entertainment"
    
    # Default for any content that doesn't fit specific categories
    return "General Content"


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


def build_teaches_agent_to(category: str) -> str:
    return f"Execute {category.lower()} workflows with reliable, repeatable steps."


def build_prompt_template(title: str, category: str, tools: str) -> str:
    return (
        f"You are implementing lessons from: {title}.\\n"
        f"Category: {category}.\\n"
        f"Tools: {tools or 'OpenClaw, VideoMind AI'}.\\n"
        "Goal: produce an actionable plan with commands, checkpoints, and output format.\\n"
        "Return: (1) step-by-step plan, (2) copy/paste commands, (3) validation checklist."
    )


def build_execution_checklist(category: str) -> str:
    return "\\n".join([
        f"[ ] Confirm objective for {category}",
        "[ ] Verify required tools/auth are available",
        "[ ] Run the workflow step-by-step",
        "[ ] Capture output artifacts (links/files/results)",
        "[ ] Validate results against success criteria",
    ])


def build_agent_training_script(title: str, summary_bullets: str, checklist: str) -> str:
    return (
        f"TRAINING SCRIPT: {title}\\n\\n"
        "What to learn:\\n"
        f"{summary_bullets or '- Review source video and transcript'}\\n\\n"
        "How to execute:\\n"
        f"{checklist}\\n\\n"
        "When done, report: objective, steps executed, outcome, blockers, and next action."
    )
