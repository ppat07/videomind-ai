"""
Ollama-based AI enhancement service — free, fully local, no API keys required.
Uses phi4-mini (or any model available in the local Ollama instance).
"""
import json
import os
from typing import Dict, Tuple

try:
    import urllib.request
    import urllib.error
    _urllib_available = True
except ImportError:
    _urllib_available = False

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi4-mini")


class OllamaEnhancementService:
    """AI enhancement service using a local Ollama model."""

    def is_available(self) -> bool:
        """Check if Ollama is reachable and the target model is present."""
        try:
            req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                models = [m["name"].split(":")[0] for m in data.get("models", [])]
                return OLLAMA_MODEL.split(":")[0] in models
        except Exception:
            return False

    def enhance_transcript(self, transcript_text: str, tier: str = "basic") -> Tuple[bool, Dict]:
        """
        Enhance transcript using local Ollama model.

        Returns:
            Tuple of (success, enhanced_data or error_dict)
        """
        if tier == "detailed":
            qa_count, key_points_count = 10, 8
        else:
            qa_count, key_points_count = 6, 6

        text_sample = transcript_text[:6000] + ("..." if len(transcript_text) > 6000 else "")

        prompt = f"""You are an expert AI training data engineer. Analyze this video transcript and produce structured data for LLM fine-tuning and RAG pipelines.

TRANSCRIPT:
{text_sample}

Return ONLY valid JSON with these exact fields:
{{
  "summary": "3-5 sentence overview covering what the video teaches, why it matters, and who benefits most",
  "full_summary": "A detailed 150-200 word summary explaining core concepts, key techniques, and practical takeaways. Write as if briefing an AI agent that will implement these patterns.",
  "key_points": ["array of {key_points_count} specific, actionable learning points"],
  "qa_pairs": [{{"question": "specific question", "answer": "detailed answer 2-4 sentences"}}],
  "topics": ["3-5 precise topic tags"],
  "teaches_agent_to": "one sentence: what can an agent DO after studying this content",
  "prerequisites": ["2-3 things a learner should already know"],
  "implementation_steps": ["3-5 concrete steps to apply the techniques shown"]
}}

Return only the JSON object, no markdown fences, no extra text."""

        try:
            payload = json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                result_data = json.loads(resp.read())

            raw = result_data.get("response", "").strip()

            # Strip markdown fences if model included them
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)

            return True, {
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
                "processing_model": f"ollama/{OLLAMA_MODEL}",
                "enhancement_method": "ollama_local",
            }

        except (json.JSONDecodeError, KeyError) as e:
            return False, {"error": f"JSON parse error from Ollama: {str(e)}"}
        except Exception as e:
            return False, {"error": f"Ollama enhancement failed: {str(e)}"}


# Global service instance
ollama_enhancement_service = OllamaEnhancementService()
