#!/usr/bin/env python3
"""
Debug the categorization logic to see why Entertainment category failed.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from utils.directory_mapper import infer_category, _contains_any

def debug_categorization():
    title = "Funny Cat Videos Compilation"
    summary = "Entertainment content"
    topics = []
    
    corpus = " ".join([title or "", summary or "", " ".join(topics or [])]).lower()
    print(f"Corpus: '{corpus}'")
    
    # Test individual checks
    checks = [
        (["setup", "install", "onboard", "getting started", "configuration"], "Setup & Onboarding"),
        (["debug", "error", "fix", "troubleshoot", "problem", "issue"], "Debugging & Fixes"),
        (["prompt", "template", "system prompt", "prompt engineering"], "Prompts & Templates"),
        (["notion", "api", "mcp", "integration", "tool", "webhook", "automation", "workflow", "ai agent", "openclaw"], "Tooling & Integrations"),
        (["money", "revenue", "sales", "business", "make $", "profit", "roi", "entrepreneur"], "Business Use Cases"),
        (["automation", "workflow", "agent", "ai", "artificial intelligence", "machine learning"], "Automation Workflows"),
        (["review", "opinion", "thoughts on", "reaction", "commentary", "analysis"], "Reviews & Opinions"),
        (["news", "update", "announcement", "release", "breaking"], "News & Updates"),
        (["tutorial", "how to", "learn", "course", "education", "explanation", "guide"], "Educational"),
        (["funny", "entertainment", "meme", "comedy", "fun", "gaming", "music", "movie", "cat", "dog", "compilation", "viral", "hilarious"], "Entertainment"),
    ]
    
    for terms, category in checks:
        matches = _contains_any(corpus, terms)
        matching_terms = [term for term in terms if term in corpus]
        print(f"  {category}: {matches} (matched: {matching_terms})")
        if matches:
            print(f"  -> WOULD RETURN: {category}")
            break
    
    final_result = infer_category(title, summary, topics)
    print(f"\nFinal result: {final_result}")

if __name__ == "__main__":
    debug_categorization()