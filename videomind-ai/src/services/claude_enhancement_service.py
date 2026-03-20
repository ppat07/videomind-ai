"""
AI enhancement service for VideoMind AI — uses Anthropic Claude to generate rich training data.
"""
import os
import json
from typing import Dict, Tuple

import anthropic


class ClaudeEnhancementService:
    """AI enhancement service that generates rich agent training data from video transcripts."""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.available = bool(api_key)
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def enhance_transcript(self, transcript_text: str, tier: str = "basic") -> Tuple[bool, Dict]:
        """
        Enhance transcript using Anthropic Claude to produce rich, structured agent training data.

        Returns:
            Tuple of (success, enhanced_data or error_dict)
        """
        if not self.client:
            return False, {"error": "ANTHROPIC_API_KEY not set"}

        if tier == "detailed":
            qa_count, key_points_count = 10, 8
        else:
            qa_count, key_points_count = 6, 6

        # Use up to 6000 chars — enough context for rich summaries
        text_sample = transcript_text[:6000] + ("..." if len(transcript_text) > 6000 else "")

        prompt = f"""You are an expert AI training data engineer. Analyze this video transcript and produce structured data for LLM fine-tuning and RAG pipelines.

TRANSCRIPT:
{text_sample}

Return ONLY valid JSON with these fields:
{{
  "summary": "3-5 sentence overview covering: what the video teaches, why it matters, and who benefits most",
  "full_summary": "A detailed 150-200 word summary explaining the core concepts, key techniques, and practical takeaways. Write as if briefing an AI agent that will implement these patterns.",
  "key_points": ["array of {key_points_count} specific, actionable learning points — avoid vague bullets"],
  "qa_pairs": [
    {{"question": "specific question about a concept or technique", "answer": "detailed answer (2-4 sentences)"}}
    // {qa_count} pairs total — focus on implementation, gotchas, and best practices
  ],
  "topics": ["3-5 precise topic tags, e.g. 'RAG pipelines', 'fine-tuning', 'prompt engineering'"],
  "teaches_agent_to": "one sentence: what can an agent DO after studying this content",
  "prerequisites": ["2-3 things a learner should already know before this video"],
  "implementation_steps": ["3-5 concrete steps to apply the techniques shown"]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                system="You are an expert at analyzing video transcripts and creating structured training data for AI agents. Always respond with valid JSON only.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            raw = response.content[0].text.strip()

            # Strip markdown fences if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)

            result = {
                "success": True,
                "tier": tier,
                "summary": data.get("summary", ""),
                "full_summary": data.get("full_summary", data.get("summary", "")),
                "key_points": (data.get("key_points") or [])[:key_points_count],
                "qa_pairs": (data.get("qa_pairs") or [])[:qa_count],
                "topics": (data.get("topics") or [])[:5],
                "teaches_agent_to": data.get("teaches_agent_to", ""),
                "prerequisites": data.get("prerequisites", []),
                "implementation_steps": data.get("implementation_steps", []),
                "word_count": len(transcript_text.split()),
                "processing_model": "claude-haiku-4-5-20251001",
                "enhancement_method": "ai_enhanced",
            }
            return True, result

        except (json.JSONDecodeError, KeyError) as e:
            return False, {"error": f"JSON parse error: {str(e)}"}
        except Exception as e:
            return False, {"error": f"Enhancement failed: {str(e)}"}


# Global service instance
claude_enhancement_service = ClaudeEnhancementService()
