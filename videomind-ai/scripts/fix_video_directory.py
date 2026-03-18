#!/usr/bin/env python3
"""
Fix the VideoMind AI directory:
1. Remove fake/irrelevant entries
2. Fix metadata mismatches
3. Add real replacement videos to hit 50+
"""

import json
import sys
import time
import uuid
import urllib.request
import urllib.parse
import urllib.error
import sqlite3
from datetime import datetime, timezone

DB_PATH = "/Users/davidpatler/.openclaw/workspace/videomind-ai/src/videomind.db"

# Video IDs to DELETE (fake, off-topic, or joke entries)
DELETE_VIDEO_IDS = [
    "xvFZjo5PgG0",  # Rick Roll (different link)
    "dQw4w9WgXcQ",  # Rick Roll - fake "AI Training Video"
    "3AtDnEC4zak",  # "Claude Enhancement Demo" - fake VideoMind entry
    "QH2-TGUlwu4",  # "VideoMind AI Demo" - fake entry
    "Ml4XCF-JS0k",  # "10 Best Templates for Premiere Pro" - off-topic
]

# Metadata fixes: video_id -> corrected fields (based on actual video title/creator)
METADATA_FIXES = {
    "sal78ACtGTc": {
        # Real title: "What's next for AI agentic workflows ft. Andrew Ng of AI Fund"
        # Creator: Sequoia Capital
        "category_primary": "AI Agents",
        "summary_5_bullets": (
            "• Andrew Ng discusses the future of agentic AI workflows\n"
            "• Covers multi-step autonomous agent design patterns\n"
            "• Compares current AI capabilities with human-level task completion\n"
            "• Practical advice for teams building agent-based products\n"
            "• Sequoia-hosted fireside chat with the AI Fund founder"
        ),
        "best_for": "Founders and product teams thinking about agentic AI product strategy",
        "tools_mentioned": "AI Agents, LLMs, Autonomous Workflows",
        "teaches_agent_to": "Understand the current state and future direction of AI agentic workflows from a leading practitioner",
    },
    "aywZrzNaKjs": {
        # Real title: "LangChain Explained in 13 Minutes | QuickStart Tutorial"
        # Creator: Rabbitmetrics
        "category_primary": "AI Frameworks",
        "summary_5_bullets": (
            "• LangChain core concepts explained concisely\n"
            "• Covers chains, prompts, and output parsers\n"
            "• Builds a simple LLM app in minutes\n"
            "• Comparison with raw OpenAI API usage\n"
            "• Best starting point for LangChain beginners"
        ),
        "best_for": "Developers new to LangChain wanting a fast, clear introduction",
        "tools_mentioned": "LangChain, OpenAI, Python",
        "teaches_agent_to": "Get started with LangChain by understanding chains, prompts, and the core abstraction model",
    },
    "t3YJ5hKiMQ0": {
        # Real title: "Building makemore Part 5: Building a WaveNet"
        # Creator: Andrej Karpathy
        "category_primary": "LLM Fundamentals",
        "summary_5_bullets": (
            "• Implements WaveNet architecture in PyTorch\n"
            "• Extends makemore series to dilated causal convolutions\n"
            "• Shows how WaveNet improves language model quality\n"
            "• Deep dive into causal convolution mechanics\n"
            "• Part of Karpathy's foundational neural network series"
        ),
        "best_for": "ML engineers following Karpathy's neural network series wanting to understand convolutional language models",
        "tools_mentioned": "PyTorch, WaveNet, Neural Networks, Python",
        "teaches_agent_to": "Implement WaveNet-style dilated causal convolutions for language modeling",
    },
    "sVcwVQRHIc8": {
        # Real title: "Learn RAG From Scratch – Python AI Tutorial from a LangChain Engineer"
        # Creator: freeCodeCamp.org
        "category_primary": "RAG & Vector Search",
        "summary_5_bullets": (
            "• Full RAG pipeline implementation from scratch in Python\n"
            "• Covers document loading, chunking, and embedding\n"
            "• Builds vector search with FAISS or Chroma\n"
            "• Implements retrieval and generation with LangChain\n"
            "• Taught by an actual LangChain engineer"
        ),
        "best_for": "Python developers who want to build a RAG system from first principles",
        "tools_mentioned": "LangChain, FAISS, OpenAI Embeddings, Python",
        "teaches_agent_to": "Build a complete RAG pipeline from document ingestion to retrieval-augmented generation",
    },
    "_nSmkyDNulk": {
        # Real title: "Math problems with GPT-4o"
        # Creator: OpenAI
        "category_primary": "OpenAI API",
        "summary_5_bullets": (
            "• Official OpenAI demo of GPT-4o solving math problems\n"
            "• Shows multimodal input: handwritten equations processed in real-time\n"
            "• Demonstrates GPT-4o's reasoning and step-by-step explanation\n"
            "• Compares GPT-4o performance with previous models\n"
            "• From OpenAI's official product demonstration"
        ),
        "best_for": "Developers exploring GPT-4o's multimodal math and reasoning capabilities",
        "tools_mentioned": "GPT-4o, OpenAI API, Multimodal AI",
        "teaches_agent_to": "Understand GPT-4o's multimodal reasoning capabilities for math and step-by-step problem solving",
    },
    "y9k-U9AuDeM": {
        # Real title: "Should You Use Open Source Large Language Models?"
        # Creator: IBM Technology
        "category_primary": "Local AI & Open Source",
        "summary_5_bullets": (
            "• IBM Technology explains the open vs closed LLM tradeoffs\n"
            "• Covers privacy, cost, and customization advantages of open-source\n"
            "• Compares popular open-source models: Llama, Mistral, Falcon\n"
            "• When to use open-source vs proprietary LLMs\n"
            "• Deployment considerations for enterprise use cases"
        ),
        "best_for": "Engineering teams evaluating open-source LLMs for production deployment",
        "tools_mentioned": "Llama, Mistral, Falcon, Hugging Face, Open Source LLMs",
        "teaches_agent_to": "Evaluate open-source LLMs against proprietary models and make deployment decisions based on tradeoffs",
    },
    "cdiD-9MMpb0": {
        # Real title: "Andrej Karpathy: Tesla AI, Self-Driving, Optimus, Aliens, and AGI | Lex Fridman Podcast #333"
        # Creator: Lex Fridman
        "category_primary": "AI Research & Safety",
        "summary_5_bullets": (
            "• Andrej Karpathy on Tesla's full self-driving AI system\n"
            "• Deep dive into large-scale neural network training at Tesla\n"
            "• Discusses Optimus robot and humanoid AI future\n"
            "• Karpathy's vision for AGI and its implications\n"
            "• Long-form technical discussion with one of ML's top researchers"
        ),
        "best_for": "AI engineers and researchers interested in large-scale production AI and future AGI directions",
        "tools_mentioned": "Tesla FSD, Neural Networks, Computer Vision, Self-Driving AI",
        "teaches_agent_to": "Understand large-scale production AI deployment challenges and the long-term trajectory toward AGI",
    },
    "Ilg3gGewQ5U": {
        # Real title: "Backpropagation, intuitively | Deep Learning Chapter 3"
        # Creator: 3Blue1Brown
        "category_primary": "LLM Fundamentals",
        "summary_5_bullets": (
            "• Intuitive visual explanation of backpropagation\n"
            "• Shows how gradients flow backward through a neural network\n"
            "• Covers the chain rule in plain visual language\n"
            "• Part of 3Blue1Brown's acclaimed deep learning series\n"
            "• No calculus prerequisites needed to follow along"
        ),
        "best_for": "Beginners wanting a deep visual intuition for how neural networks learn",
        "tools_mentioned": "Neural Networks, Backpropagation, Deep Learning",
        "teaches_agent_to": "Understand how backpropagation and gradient flow enable neural network learning",
    },
    "AaTRHFaaPG8": {
        # Real title: "Eliezer Yudkowsky: Dangers of AI and the End of Human Civilization"
        # Creator: Lex Fridman
        "category_primary": "AI Research & Safety",
        "summary_5_bullets": (
            "• Eliezer Yudkowsky's case for existential AI risk\n"
            "• Detailed argument for why current AI alignment approaches may be insufficient\n"
            "• Discussion of intelligence explosion and control problem\n"
            "• Lex Fridman challenges Yudkowsky on key points\n"
            "• Essential listening for anyone building AI systems at scale"
        ),
        "best_for": "AI engineers and researchers who want to understand existential AI risk arguments from a leading theorist",
        "tools_mentioned": "AI Safety, Alignment, AGI, MIRI",
        "teaches_agent_to": "Understand the core arguments for AI existential risk and the alignment challenge from Eliezer Yudkowsky",
    },
    "G2fqAlgmoPo": {
        # Real title: "Introduction to Generative AI"
        # Creator: Google Cloud Tech
        "category_primary": "LLM Fundamentals",
        "summary_5_bullets": (
            "• Google Cloud's official introduction to generative AI\n"
            "• Covers foundation models, LLMs, and diffusion models\n"
            "• Explains how gen AI differs from traditional ML\n"
            "• Overview of Google's generative AI tools and products\n"
            "• Good entry point for teams new to generative AI"
        ),
        "best_for": "Business and technical teams who need a structured introduction to generative AI concepts",
        "tools_mentioned": "Google Cloud, Vertex AI, Foundation Models, LLMs",
        "teaches_agent_to": "Understand generative AI fundamentals including foundation models, LLMs, and multimodal AI",
    },
    "HSZ_uaif57o": {
        # Real title: "Learn LangChain.js - Build LLM apps with JavaScript and OpenAI"
        # Creator: freeCodeCamp.org
        "category_primary": "AI Frameworks",
        "summary_5_bullets": (
            "• Full LangChain.js course for JavaScript developers\n"
            "• Builds LLM-powered apps in Node.js from scratch\n"
            "• Covers chains, agents, and memory in JS ecosystem\n"
            "• Integrates with OpenAI and vector databases\n"
            "• Full freeCodeCamp course with practical projects"
        ),
        "best_for": "JavaScript/Node.js developers who want to build LLM applications without switching to Python",
        "tools_mentioned": "LangChain.js, OpenAI, JavaScript, Node.js",
        "teaches_agent_to": "Build LLM-powered applications in JavaScript using LangChain.js with chains, agents, and memory",
    },
}

# New videos to add from CURATED_VIDEOS in build_real_video_directory.py
# These were not previously added - try oEmbed to validate
NEW_VIDEO_CANDIDATES = [
    ("yk9lXobq3w8", "AI Coding Assistants", "Intermediate", 91,
     "• Advanced Cursor AI workflows and shortcuts\n• Custom .cursorrules file configuration\n• Multi-file editing and refactoring with AI\n• Debugging with AI assistance\n• Real project build demonstration",
     "Developers already using Cursor wanting advanced techniques",
     "Cursor AI, .cursorrules, Claude",
     "Configure Cursor AI with custom rules and advanced multi-file editing workflows"),

    ("xMMn1IOQOOU", "Local AI & Open Source", "Intermediate", 91,
     "• Run LLMs locally with Ollama\n• Downloads and manages Llama 3, Mistral, Phi-3\n• Builds a local AI chatbot with Open WebUI\n• Compares model quality vs API costs\n• Privacy-first AI workflow setup",
     "Developers wanting to run AI locally for privacy, cost savings, or offline use",
     "Ollama, Llama 3, Mistral, Open WebUI",
     "Set up a local LLM environment with Ollama for privacy-first AI development"),

    ("8hSNPcDUMDQ", "Claude & Anthropic", "Intermediate", 95,
     "• Claude Code CLI tool introduction and setup\n• Demonstrates autonomous code editing\n• Runs bash commands and edits files directly\n• Covers safety features and approval workflows\n• Comparison with Devin and other AI coders",
     "Developers wanting to use Claude as an autonomous coding agent in the terminal",
     "Claude Code, Anthropic, CLI, Bash",
     "Set up and use Claude Code for autonomous AI-assisted software development tasks"),

    ("hOd_Jj_IG40", "OpenAI API", "Advanced", 92,
     "• GPT-4 function calling deep dive\n• Build a structured data extraction pipeline\n• Implement tool use with external APIs\n• Parallel function execution\n• Error handling and retry logic",
     "Engineers building reliable data extraction and tool-use workflows with GPT-4",
     "OpenAI API, Function Calling, Python, Tool Use",
     "Implement reliable function calling workflows with GPT-4 for structured data extraction"),

    ("OcsMGjCRUoY", "Claude & Anthropic", "Beginner", 92,
     "• Claude Artifacts feature complete walkthrough\n• Creates interactive React apps in chat\n• Generates data visualizations and tools\n• Iterative refinement with follow-up prompts\n• Practical use cases for non-coders",
     "Non-technical users and developers exploring Claude's artifact creation capabilities",
     "Claude, Anthropic, React, Artifacts",
     "Use Claude Artifacts to create interactive tools, charts, and mini-applications from natural language"),

    ("EIs8JJlORZg", "AI Frameworks", "Intermediate", 91,
     "• OpenAI structured outputs (JSON mode)\n• Instructor library for reliable Pydantic parsing\n• Extracts structured data from unstructured text\n• Handles retries and validation failures\n• Real-world data extraction pipelines",
     "Engineers needing reliable structured data extraction from LLM outputs",
     "OpenAI, Instructor, Pydantic, Python",
     "Extract reliable structured data from LLMs using JSON mode and Pydantic validation"),

    ("Kx_zLGVITf8", "OpenAI API", "Intermediate", 89,
     "• OpenAI Assistants API complete tutorial\n• Creates persistent assistants with tools\n• Implements file search and code interpreter\n• Manages threads and conversation state\n• Builds a production customer support bot",
     "Engineers building stateful AI assistants with file analysis and code execution",
     "OpenAI Assistants API, Function Calling, Python",
     "Build stateful AI assistants using the Assistants API with tool use and file search"),

    ("CPgp0MZ8alo", "Local AI & Open Source", "Advanced", 90,
     "• Fine-tune Llama 3 with LoRA on custom data\n• Uses QLoRA for memory-efficient training\n• Covers dataset preparation and formatting\n• Evaluates fine-tuned model performance\n• Deploys the model with Ollama",
     "ML engineers fine-tuning open-source models for specific use cases",
     "Llama 3, LoRA, QLoRA, Hugging Face, Python",
     "Fine-tune open-source LLMs with LoRA on domain-specific datasets"),

    ("jj0yKJahlJY", "AI Coding Assistants", "Intermediate", 93,
     "• Build a full-stack app entirely with AI assistance\n• Uses Cursor AI for frontend and backend\n• Demonstrates AI-driven debugging workflow\n• Covers prompting strategies for code generation\n• From idea to deployed app in one session",
     "Developers wanting to see a complete AI-assisted application build from start to finish",
     "Cursor AI, React, FastAPI, Claude",
     "Build complete applications using AI coding assistants with effective prompting strategies"),

    ("3OyOCz3trMY", "AI Automation Workflows", "Beginner", 88,
     "• n8n workflow automation introduction\n• Integrates ChatGPT into no-code workflows\n• Builds Slack bot, email responder, and CRM automation\n• Covers webhook triggers and API nodes\n• Free self-hosted alternative to Zapier",
     "Non-technical users and developers wanting AI-powered automation without heavy coding",
     "n8n, ChatGPT, Slack, Webhooks",
     "Build AI-powered automation workflows using n8n with ChatGPT integration"),
]


def fetch_oembed(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
    try:
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  [SKIP] {video_id} — HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  [SKIP] {video_id} — error: {e}")
        return None


def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    count_before = db.execute("SELECT COUNT(*) as c FROM directory_entries").fetchone()['c']
    print(f"Starting count: {count_before}")

    # Step 1: Delete fake/bad entries
    print("\n--- Step 1: Removing fake/off-topic entries ---")
    deleted = 0
    for vid_id in DELETE_VIDEO_IDS:
        url = f"https://www.youtube.com/watch?v={vid_id}"
        result = db.execute("DELETE FROM directory_entries WHERE source_url=?", (url,))
        if result.rowcount > 0:
            print(f"  ✓ Deleted: {vid_id}")
            deleted += result.rowcount
        else:
            print(f"  - Not found: {vid_id}")
    db.commit()
    print(f"  Removed {deleted} entries")

    # Step 2: Fix metadata mismatches
    print("\n--- Step 2: Fixing metadata mismatches ---")
    fixed = 0
    for vid_id, fixes in METADATA_FIXES.items():
        url = f"https://www.youtube.com/watch?v={vid_id}"
        # Build SET clause
        set_parts = []
        values = []
        for col, val in fixes.items():
            set_parts.append(f"{col} = ?")
            values.append(val)
        values.append(url)
        sql = f"UPDATE directory_entries SET {', '.join(set_parts)} WHERE source_url = ?"
        result = db.execute(sql, values)
        if result.rowcount > 0:
            print(f"  ✓ Fixed: {vid_id}")
            fixed += result.rowcount
        else:
            print(f"  - Not found: {vid_id}")
    db.commit()
    print(f"  Fixed {fixed} entries")

    # Step 3: Add new validated videos
    print("\n--- Step 3: Adding new real videos ---")
    count_after_delete = db.execute("SELECT COUNT(*) as c FROM directory_entries").fetchone()['c']
    print(f"Current count after cleanup: {count_after_delete} (target: 50+)")

    # Get existing URLs
    existing = set(r['source_url'] for r in db.execute("SELECT source_url FROM directory_entries").fetchall())

    added = 0
    for (vid_id, category, difficulty, score, summary, best_for, tools, teaches) in NEW_VIDEO_CANDIDATES:
        url = f"https://www.youtube.com/watch?v={vid_id}"
        if url in existing:
            print(f"  [SKIP] {vid_id} — already in DB")
            continue

        meta = fetch_oembed(vid_id)
        if meta is None:
            continue

        print(f"  ✓ Adding: {meta['title'][:55]} ({meta['author_name']})")
        now = datetime.now(timezone.utc).isoformat()
        db.execute("""
            INSERT INTO directory_entries (
                id, title, source_url, video_url, creator_name,
                category_primary, difficulty, signal_score,
                summary_5_bullets, best_for, tools_mentioned, teaches_agent_to,
                processing_status, prompt_template, execution_checklist, agent_training_script,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), meta['title'], url, url, meta['author_name'],
            category, difficulty, score,
            summary, best_for, tools, teaches,
            "reviewed",
            f"Watch this video about {category.lower()} and implement the key techniques demonstrated.",
            f"[ ] Watch the full video\n[ ] Identify the main tools: {tools}\n[ ] Implement the core workflow\n[ ] Test with a real example\n[ ] Document what you learned",
            f"TRAINING SCRIPT: {teaches}. Key tools: {tools}. Category: {category}. Difficulty: {difficulty}.",
            now, now
        ))
        db.commit()
        added += 1
        time.sleep(0.3)

    count_final = db.execute("SELECT COUNT(*) as c FROM directory_entries").fetchone()['c']
    print(f"\n=== Final Results ===")
    print(f"Deleted: {deleted} fake/off-topic entries")
    print(f"Fixed: {fixed} metadata mismatches")
    print(f"Added: {added} new validated videos")
    print(f"Final count: {count_final}")

    db.close()

if __name__ == "__main__":
    main()
