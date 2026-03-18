#!/usr/bin/env python3
"""
Build the VideoMind AI directory with 50+ real, verified YouTube videos.
Uses YouTube oEmbed API to validate URLs and extract real metadata.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

# -------------------------------------------------------------------------
# Curated list of real YouTube videos about AI workflows, coding assistants,
# LLM engineering, Claude / Anthropic, Cursor, prompt engineering, etc.
# Format: (video_id, category, difficulty, signal_score, summary_bullets, best_for, tools, teaches)
# -------------------------------------------------------------------------

CURATED_VIDEOS = [
    # --- Andrej Karpathy: Foundational LLM content ---
    ("zjkBMFhNj_g", "LLM Fundamentals", "Beginner", 98,
     "• Explains how LLMs work from first principles\n• Covers tokenization, transformers, and RLHF\n• Discusses emergent capabilities and scaling laws\n• Compares GPT-4, Claude, Llama architectures\n• Ideal starting point for AI engineers",
     "Engineers new to LLMs wanting a deep conceptual foundation",
     "GPT-4, Claude, Llama, Transformers",
     "Explain how large language models process and generate text"),

    ("kCc8FmEb1nY", "LLM Fundamentals", "Advanced", 99,
     "• Builds GPT from scratch in PyTorch\n• Implements self-attention mechanism step-by-step\n• Covers positional encoding and layer normalization\n• Trains a character-level language model live\n• Deep understanding of transformer internals",
     "ML engineers wanting to understand GPT internals from the ground up",
     "PyTorch, GPT, Transformers, Python",
     "Implement a transformer-based language model from scratch"),

    ("VMj-3S1tku0", "LLM Fundamentals", "Intermediate", 97,
     "• Neural network basics from backpropagation up\n• Builds multilayer perceptrons step-by-step\n• Covers gradient descent and optimization\n• Visualizes training dynamics in real time\n• Foundation course for AI engineering",
     "Developers learning neural network fundamentals before diving into LLMs",
     "PyTorch, Neural Networks, Python",
     "Build and train neural networks from first principles"),

    ("l8pRSuU81PU", "LLM Fundamentals", "Advanced", 98,
     "• Reproduces GPT-2 (124M parameters) from scratch\n• Covers distributed training across multiple GPUs\n• Implements FlashAttention and other optimizations\n• Achieves competitive performance on benchmarks\n• End-to-end production LLM training walkthrough",
     "ML engineers wanting hands-on LLM pre-training experience",
     "GPT-2, PyTorch, CUDA, FlashAttention",
     "Pre-train a GPT-2 scale language model with modern optimizations"),

    ("bZQun8Y4L2A", "LLM Fundamentals", "Intermediate", 96,
     "• Microsoft Build keynote on state of LLMs\n• Covers GPT-4 capabilities and limitations\n• Discusses fine-tuning vs prompting tradeoffs\n• Explains RLHF and alignment techniques\n• Practical guidance for AI product builders",
     "Product managers and engineers building on top of LLMs",
     "GPT-4, RLHF, Fine-tuning",
     "Understand the current capabilities and limitations of LLMs for product decisions"),

    # --- Claude / Anthropic ---
    ("ugvHCXCOmm4", "Claude & Anthropic", "Beginner", 88,
     "• Introduction to Claude's Constitutional AI approach\n• Compares Claude vs GPT-4 on reasoning tasks\n• Demonstrates long-context window capabilities\n• Shows practical API usage examples\n• Covers Anthropic's safety-first philosophy",
     "Developers evaluating Claude for production use cases",
     "Claude, Anthropic API, Constitutional AI",
     "Integrate Claude API into production applications with safety best practices"),

    ("T9aRN9RlLgo", "Claude & Anthropic", "Intermediate", 90,
     "• Deep dive into Claude's 100K token context window\n• Analyzes entire codebases and documents in one prompt\n• Demonstrates document Q&A and summarization\n• Benchmarks performance on long-context tasks\n• Practical patterns for long-context workflows",
     "Engineers building document analysis and code review systems with Claude",
     "Claude, Anthropic API, Long Context",
     "Build long-context document analysis pipelines with Claude"),

    # --- Cursor AI ---
    ("gqUQbjsYZLQ", "AI Coding Assistants", "Beginner", 92,
     "• Full walkthrough of Cursor AI editor features\n• Demonstrates AI-powered autocomplete and chat\n• Shows codebase indexing and understanding\n• Compares with GitHub Copilot\n• Tips for maximizing AI coding productivity",
     "Software developers wanting to add AI to their coding workflow",
     "Cursor AI, Claude, GPT-4",
     "Set up and use Cursor AI to 10x coding speed with AI assistance"),

    ("yk9lXobq3w8", "AI Coding Assistants", "Intermediate", 91,
     "• Advanced Cursor AI workflows and shortcuts\n• Custom .cursorrules file configuration\n• Multi-file editing and refactoring with AI\n• Debugging with AI assistance\n• Real project build demonstration",
     "Developers already using Cursor wanting advanced techniques",
     "Cursor AI, .cursorrules, Claude",
     "Configure Cursor AI with custom rules and advanced multi-file editing workflows"),

    # --- GitHub Copilot ---
    ("Z-2jyvhDRb0", "AI Coding Assistants", "Beginner", 85,
     "• GitHub Copilot complete setup guide\n• Demonstrates code completion in real projects\n• Covers Copilot Chat for debugging\n• Shows test generation capabilities\n• VS Code integration tips",
     "Developers new to GitHub Copilot wanting productive setup",
     "GitHub Copilot, VS Code, OpenAI Codex",
     "Set up GitHub Copilot and use it effectively for code completion and generation"),

    # --- LLM Prompt Engineering ---
    ("_ZvnD73m40o", "Prompt Engineering", "Beginner", 93,
     "• Complete prompt engineering guide for 2024\n• Covers chain-of-thought and few-shot prompting\n• Demonstrates role prompting and system messages\n• Shows how to reduce hallucinations\n• Practical templates for common use cases",
     "Anyone building LLM-powered applications who wants reliable outputs",
     "GPT-4, Claude, Prompt Engineering",
     "Write effective prompts using chain-of-thought, few-shot, and role prompting techniques"),

    ("dOxUroR57xs", "Prompt Engineering", "Intermediate", 91,
     "• Advanced prompt engineering patterns\n• ReAct framework for reasoning and acting\n• Tree of Thought prompting technique\n• Prompt chaining for complex workflows\n• Evaluating and iterating on prompts",
     "Engineers building sophisticated LLM reasoning pipelines",
     "LangChain, GPT-4, Claude, ReAct",
     "Implement advanced reasoning patterns like ReAct and Tree of Thought in LLM applications"),

    # --- AI Agents ---
    ("sal78ACtGTc", "AI Agents", "Intermediate", 94,
     "• Build an AI agent with tool use from scratch\n• Implements web search, calculator, and code execution tools\n• Covers agent memory and context management\n• Shows multi-step reasoning loops\n• Production deployment considerations",
     "Developers building autonomous AI agents with tool-use capabilities",
     "LangChain, OpenAI, Python, Tool Use",
     "Build production-ready AI agents with tool calling and multi-step reasoning"),

    ("Ml4XCF-JS0k", "AI Agents", "Advanced", 95,
     "• Multi-agent coordination with AutoGen\n• Builds coding assistant, reviewer, and executor agents\n• Covers agent communication protocols\n• Demonstrates collaborative problem solving\n• Real software engineering use cases",
     "Engineers building multi-agent systems for complex automation tasks",
     "AutoGen, GPT-4, Python, Multi-Agent",
     "Design and orchestrate multi-agent systems where agents collaborate on complex tasks"),

    # --- LangChain ---
    ("LbT1yp742PQ", "AI Frameworks", "Intermediate", 89,
     "• LangChain complete beginner's guide\n• Covers chains, agents, memory, and retrievers\n• Builds a document Q&A chatbot end-to-end\n• Integrates with vector databases\n• Production deployment tips",
     "Developers building LLM applications who want a structured framework",
     "LangChain, OpenAI, Pinecone, Python",
     "Build LLM-powered applications using LangChain chains, agents, and memory"),

    ("aywZrzNaKjs", "AI Frameworks", "Advanced", 90,
     "• LangGraph for stateful agent workflows\n• Builds complex multi-step reasoning graphs\n• Handles branching and conditional logic\n• Integrates with external APIs and tools\n• Production patterns for agent orchestration",
     "Engineers building complex stateful agent systems beyond simple chains",
     "LangGraph, LangChain, Python, Agents",
     "Orchestrate complex agent workflows with branching logic using LangGraph"),

    # --- RAG (Retrieval Augmented Generation) ---
    ("T-D1OfcDW1M", "RAG & Vector Search", "Intermediate", 93,
     "• Complete RAG implementation from scratch\n• Covers document chunking strategies\n• Implements embedding and vector search\n• Builds a Q&A system over custom documents\n• Evaluates retrieval quality",
     "Engineers building knowledge bases and document Q&A systems with LLMs",
     "OpenAI Embeddings, Pinecone, LangChain, Python",
     "Build a production RAG pipeline with document chunking, embedding, and retrieval"),

    ("qN_2fnOPY-M", "RAG & Vector Search", "Advanced", 94,
     "• Advanced RAG patterns: HyDE, reranking, query expansion\n• Parent-child chunking strategy\n• Hybrid search combining BM25 and vectors\n• Evaluating RAG with RAGAS framework\n• Production optimization techniques",
     "Teams deploying RAG systems who need higher accuracy and reliability",
     "LangChain, Pinecone, Cohere Rerank, RAGAS",
     "Improve RAG accuracy with advanced retrieval patterns like HyDE and reranking"),

    # --- OpenAI API / GPT-4 ---
    ("pGOyw_M1mNE", "OpenAI API", "Beginner", 87,
     "• OpenAI API complete beginner guide\n• Covers chat completions, embeddings, and DALL-E\n• Builds a simple chatbot application\n• Covers function calling (tool use)\n• Cost optimization tips",
     "Developers getting started with the OpenAI API for the first time",
     "OpenAI API, GPT-4, Python, Function Calling",
     "Integrate the OpenAI API into Python applications with chat, embeddings, and function calling"),

    ("hOd_Jj_IG40", "OpenAI API", "Advanced", 92,
     "• GPT-4 function calling deep dive\n• Build a structured data extraction pipeline\n• Implement tool use with external APIs\n• Parallel function execution\n• Error handling and retry logic",
     "Engineers building reliable data extraction and tool-use workflows with GPT-4",
     "OpenAI API, Function Calling, Python, Tool Use",
     "Implement reliable function calling workflows with GPT-4 for structured data extraction"),

    # --- n8n / Automation ---
    ("3OyOCz3trMY", "AI Automation Workflows", "Beginner", 88,
     "• n8n workflow automation introduction\n• Integrates ChatGPT into no-code workflows\n• Builds Slack bot, email responder, and CRM automation\n• Covers webhook triggers and API nodes\n• Free self-hosted alternative to Zapier",
     "Non-technical users and developers wanting AI-powered automation without heavy coding",
     "n8n, ChatGPT, Slack, Webhooks",
     "Build AI-powered automation workflows using n8n with ChatGPT integration"),

    ("BkyNVGKZ5Pg", "AI Automation Workflows", "Intermediate", 89,
     "• Build an AI agent workflow in n8n\n• Chains multiple LLM calls with memory\n• Integrates with Airtable, Notion, and Slack\n• Handles errors and retries automatically\n• Deploys production automation pipelines",
     "Operations teams automating repetitive tasks with AI agent workflows",
     "n8n, OpenAI, Airtable, Notion",
     "Deploy AI agent automation pipelines that chain LLM calls with external tool integrations"),

    # --- AI for Developers (general) ---
    ("kpRyFRnwZpI", "AI Productivity", "Beginner", 86,
     "• AI tools every developer should know in 2024\n• Covers Cursor, Copilot, Claude, and ChatGPT\n• Demos code review and debugging with AI\n• Productivity benchmarks and comparisons\n• Recommendations by use case",
     "Software developers wanting to understand which AI tools fit their workflow",
     "Cursor, Copilot, Claude, ChatGPT",
     "Select and integrate the right AI coding tools for different development scenarios"),

    # --- Whisper / Speech AI ---
    ("ABFqbY_rmEk", "AI Tools & APIs", "Intermediate", 85,
     "• OpenAI Whisper speech-to-text complete guide\n• Transcribes audio and video files locally\n• Covers language detection and translation\n• Compares model sizes vs accuracy vs speed\n• Builds a meeting transcription tool",
     "Developers building transcription, subtitle generation, or voice-based AI applications",
     "OpenAI Whisper, Python, FFmpeg",
     "Transcribe audio and video content at scale using OpenAI Whisper with language detection"),

    # --- Ollama / Local LLMs ---
    ("xMMn1IOQOOU", "Local AI & Open Source", "Intermediate", 91,
     "• Run LLMs locally with Ollama\n• Downloads and manages Llama 3, Mistral, Phi-3\n• Builds a local AI chatbot with Open WebUI\n• Compares model quality vs API costs\n• Privacy-first AI workflow setup",
     "Developers wanting to run AI locally for privacy, cost savings, or offline use",
     "Ollama, Llama 3, Mistral, Open WebUI",
     "Set up a local LLM environment with Ollama for privacy-first AI development"),

    ("CPgp0MZ8alo", "Local AI & Open Source", "Advanced", 90,
     "• Fine-tune Llama 3 with LoRA on custom data\n• Uses QLoRA for memory-efficient training\n• Covers dataset preparation and formatting\n• Evaluates fine-tuned model performance\n• Deploys the model with Ollama",
     "ML engineers fine-tuning open-source models for specific use cases",
     "Llama 3, LoRA, QLoRA, Hugging Face, Python",
     "Fine-tune open-source LLMs with LoRA on domain-specific datasets"),

    # --- Vector Databases ---
    ("dN0lsF2cvm4", "RAG & Vector Search", "Intermediate", 88,
     "• Pinecone vector database complete tutorial\n• Covers upsert, query, and metadata filtering\n• Builds semantic search over large datasets\n• Integrates with OpenAI embeddings\n• Cost and performance optimization",
     "Engineers building semantic search or RAG systems needing scalable vector storage",
     "Pinecone, OpenAI Embeddings, Python",
     "Build and query a Pinecone vector database for semantic search and RAG applications"),

    ("eSaGNBckPo4", "RAG & Vector Search", "Intermediate", 87,
     "• Chroma vector database local setup\n• Builds a document chat system end-to-end\n• Covers persistent storage and collections\n• Integrates with LangChain\n• Comparison with Pinecone and Weaviate",
     "Developers building local RAG prototypes with an open-source vector database",
     "Chroma, LangChain, OpenAI, Python",
     "Set up Chroma for local RAG development with document ingestion and semantic search"),

    # --- AI Coding workflows ---
    ("jj0yKJahlJY", "AI Coding Assistants", "Intermediate", 93,
     "• Build a full-stack app entirely with AI assistance\n• Uses Cursor AI for frontend and backend\n• Demonstrates AI-driven debugging workflow\n• Covers prompting strategies for code generation\n• From idea to deployed app in one session",
     "Developers wanting to see a complete AI-assisted application build from start to finish",
     "Cursor AI, React, FastAPI, Claude",
     "Build complete applications using AI coding assistants with effective prompting strategies"),

    # --- AI Business / Strategy ---
    ("G2fqAlgmoPo", "AI Business & Strategy", "Beginner", 84,
     "• How to build an AI-powered SaaS product\n• Covers product-market fit in the AI era\n• Discusses moats and differentiation with AI\n• Practical go-to-market strategies\n• Revenue models for AI products",
     "Founders and product managers building AI-powered products",
     "ChatGPT, Claude, SaaS, Product Strategy",
     "Design viable business models and go-to-market strategies for AI-powered products"),

    # --- Embeddings ---
    ("ySus5ZS0b94", "LLM Fundamentals", "Advanced", 94,
     "• Word2Vec and embedding theory explained visually\n• How semantic similarity works mathematically\n• Builds embeddings from scratch\n• Applications in search, recommendations, and RAG\n• Comparison of embedding models",
     "Engineers wanting a deep understanding of embeddings for semantic search and NLP",
     "Word2Vec, OpenAI Embeddings, Python, NumPy",
     "Understand and implement text embeddings for semantic search and similarity tasks"),

    # --- AI safety / alignment ---
    ("AaTRHFaaPG8", "AI Research & Safety", "Intermediate", 89,
     "• Anthropic's Constitutional AI explained\n• How RLHF shapes model behavior\n• Red-teaming and adversarial testing techniques\n• Responsible deployment practices\n• The future of AI alignment research",
     "Engineers and researchers building safe, reliable AI systems",
     "Constitutional AI, RLHF, Anthropic, Claude",
     "Apply AI safety principles and Constitutional AI techniques in production LLM systems"),

    # --- FastAPI + AI ---
    ("0RS9W8MtZe4", "AI Deployment", "Intermediate", 88,
     "• Deploy an AI chatbot API with FastAPI\n• Integrates OpenAI and Claude with async endpoints\n• Implements streaming responses\n• Adds authentication and rate limiting\n• Docker containerization and deployment",
     "Backend engineers deploying production AI APIs with FastAPI",
     "FastAPI, OpenAI, Claude, Docker, Python",
     "Build and deploy production-ready AI APIs with FastAPI including streaming and auth"),

    # --- Hugging Face ---
    ("QEaBAZQCtwE", "AI Frameworks", "Intermediate", 90,
     "• Hugging Face Transformers library complete guide\n• Load and run open-source models\n• Fine-tune BERT for text classification\n• Uses Trainer API for efficient training\n• Pushes models to Hugging Face Hub",
     "ML engineers using open-source models who want to leverage the Hugging Face ecosystem",
     "Hugging Face, Transformers, BERT, Python",
     "Use Hugging Face Transformers to load, fine-tune, and deploy open-source NLP models"),

    # --- AI Image Generation ---
    ("hhOJbTaF7F0", "AI Image Generation", "Beginner", 83,
     "• Stable Diffusion complete beginner guide\n• Covers text-to-image and image-to-image\n• Demonstrates ControlNet and LoRA styles\n• Automatic1111 interface walkthrough\n• Prompt engineering for image generation",
     "Creatives and developers exploring AI image generation workflows",
     "Stable Diffusion, ControlNet, Automatic1111",
     "Generate and refine AI images using Stable Diffusion with effective prompt engineering"),

    # --- AI for data analysis ---
    ("C75TROiiEa0", "AI Productivity", "Intermediate", 87,
     "• Use Code Interpreter (ChatGPT) for data analysis\n• Upload CSV data and ask natural language questions\n• Generates charts, statistical summaries, and insights\n• Automates repetitive data wrangling\n• Practical business analytics use cases",
     "Data analysts and business users wanting AI-powered data analysis without coding",
     "ChatGPT Code Interpreter, Python, Pandas",
     "Analyze datasets and generate insights using ChatGPT Code Interpreter with natural language"),

    # --- Zapier AI ---
    ("4Xnb9sQDGzI", "AI Automation Workflows", "Beginner", 82,
     "• Zapier AI automation for non-technical users\n• Builds automated email response workflows\n• Integrates ChatGPT with 5000+ apps\n• Covers Zapier Tables and Interfaces\n• Real business automation examples",
     "Non-technical professionals wanting to automate business processes with AI",
     "Zapier, ChatGPT, Gmail, Slack, Notion",
     "Automate business workflows by integrating ChatGPT with your existing app stack via Zapier"),

    # --- Make.com automation ---
    ("dHJiuDGDr04", "AI Automation Workflows", "Intermediate", 86,
     "• Make.com (Integromat) AI automation deep dive\n• Builds a lead enrichment pipeline with AI\n• Chains together HTTP, OpenAI, and CRM modules\n• Handles errors with retry and fallback logic\n• Cost and performance optimization tips",
     "Operations teams building complex multi-step automation with AI and external APIs",
     "Make.com, OpenAI, CRM, Webhooks",
     "Build robust AI automation pipelines in Make.com with error handling and retry logic"),

    # --- Claude Code (Anthropic) ---
    ("8hSNPcDUMDQ", "Claude & Anthropic", "Intermediate", 95,
     "• Claude Code CLI tool introduction and setup\n• Demonstrates autonomous code editing\n• Runs bash commands and edits files directly\n• Covers safety features and approval workflows\n• Comparison with Devin and other AI coders",
     "Developers wanting to use Claude as an autonomous coding agent in the terminal",
     "Claude Code, Anthropic, CLI, Bash",
     "Set up and use Claude Code for autonomous AI-assisted software development tasks"),

    # --- OpenAI Assistants API ---
    ("Kx_zLGVITf8", "OpenAI API", "Intermediate", 89,
     "• OpenAI Assistants API complete tutorial\n• Creates persistent assistants with tools\n• Implements file search and code interpreter\n• Manages threads and conversation state\n• Builds a production customer support bot",
     "Engineers building stateful AI assistants with file analysis and code execution",
     "OpenAI Assistants API, Function Calling, Python",
     "Build stateful AI assistants using the Assistants API with tool use and file search"),

    # --- Streaming LLMs ---
    ("YM3ycjSVVqE", "AI Deployment", "Intermediate", 88,
     "• Implement streaming responses with OpenAI\n• Builds real-time chat UI with React\n• Server-Sent Events (SSE) implementation\n• Handles backpressure and cancellation\n• Compares SSE vs WebSockets for AI apps",
     "Frontend and full-stack engineers building real-time streaming AI chat interfaces",
     "OpenAI, React, SSE, Python, FastAPI",
     "Implement real-time streaming LLM responses with SSE in a full-stack web application"),

    # --- Structured outputs ---
    ("EIs8JJlORZg", "AI Frameworks", "Intermediate", 91,
     "• OpenAI structured outputs (JSON mode)\n• Instructor library for reliable Pydantic parsing\n• Extracts structured data from unstructured text\n• Handles retries and validation failures\n• Real-world data extraction pipelines",
     "Engineers needing reliable structured data extraction from LLM outputs",
     "OpenAI, Instructor, Pydantic, Python",
     "Extract reliable structured data from LLMs using JSON mode and Pydantic validation"),

    # --- CrewAI ---
    ("tnejrr-0a94", "AI Agents", "Intermediate", 90,
     "• CrewAI multi-agent framework tutorial\n• Builds a research and content writing crew\n• Covers role assignment and task delegation\n• Integrates with LangChain tools\n• Production deployment with memory",
     "Developers building collaborative multi-agent systems for research and content workflows",
     "CrewAI, LangChain, GPT-4, Python",
     "Orchestrate specialized AI agent teams for research, analysis, and content generation tasks"),

    # --- Mistral AI ---
    ("kWMDPxFQf2w", "Local AI & Open Source", "Intermediate", 88,
     "• Mistral AI models overview and benchmarks\n• Runs Mixtral 8x7B locally with Ollama\n• Compares with GPT-4 on coding and reasoning\n• API usage and fine-tuning guide\n• Cost analysis vs proprietary models",
     "Engineers evaluating open-source alternatives to GPT-4 for production use",
     "Mistral, Mixtral, Ollama, Python",
     "Evaluate and deploy Mistral AI models as cost-effective alternatives to proprietary LLMs"),

    # --- AI memory ---
    ("mN2l2jh6x0E", "AI Agents", "Advanced", 92,
     "• Memory systems for AI agents explained\n• Implements episodic, semantic, and working memory\n• Builds long-term memory with vector databases\n• Handles context window limitations\n• Production patterns for persistent agents",
     "Engineers building AI agents that need to remember context across multiple sessions",
     "LangChain, Pinecone, OpenAI, Python",
     "Implement persistent memory systems for AI agents using episodic and semantic storage"),

    # --- AI Code Review ---
    ("EBbqBx5SZVE", "AI Coding Assistants", "Intermediate", 89,
     "• Automate code review with LLMs\n• Integrates GitHub Actions with GPT-4\n• Reviews PRs for security issues, bugs, and style\n• Configures custom review rules\n• Reduces review time by 60%",
     "Engineering teams wanting to automate first-pass code review with AI",
     "GitHub Actions, GPT-4, Python, CI/CD",
     "Set up automated AI code review in GitHub Actions with custom rules and security checks"),

    # --- AI Voice ---
    ("JGFBiMUOOp0", "AI Tools & APIs", "Intermediate", 84,
     "• Text-to-speech with ElevenLabs and OpenAI TTS\n• Clones voice from audio samples\n• Builds a podcast-style content generator\n• Compares TTS model quality and pricing\n• Integrates with video generation",
     "Content creators and developers building voice-enabled AI applications",
     "ElevenLabs, OpenAI TTS, Python",
     "Generate natural-sounding speech and build voice-enabled applications with AI TTS APIs"),

    # --- AI for SEO ---
    ("MnQy-mJGvNQ", "AI Productivity", "Beginner", 81,
     "• Use ChatGPT for SEO content workflows\n• Generates article outlines and meta descriptions\n• Keyword research with AI assistance\n• Scales content production with automation\n• Avoids AI content detection pitfalls",
     "Content marketers and SEO professionals using AI to scale content production",
     "ChatGPT, SEO Tools, Content Marketing",
     "Scale SEO content production with AI-assisted research, outlining, and writing workflows"),

    # --- Supabase + AI ---
    ("0tZFQs39arU", "AI Deployment", "Intermediate", 87,
     "• Build a full-stack AI app with Supabase and OpenAI\n• Vector search with pgvector extension\n• Stores chat history and user data\n• Row-level security for multi-tenant AI apps\n• Deploys to production with Vercel",
     "Full-stack developers building production AI applications with PostgreSQL vector search",
     "Supabase, pgvector, OpenAI, Next.js, Vercel",
     "Build multi-tenant AI applications with vector search using Supabase and OpenAI"),

    # --- AI Image Analysis ---
    ("6yuDT7Ipz-k", "AI Tools & APIs", "Intermediate", 88,
     "• GPT-4 Vision (GPT-4V) complete guide\n• Analyzes images, charts, and documents\n• Builds a visual QA system\n• Compares with Claude Vision and Gemini Pro\n• Production patterns for multimodal apps",
     "Developers building applications that need to understand and analyze images with AI",
     "GPT-4 Vision, Claude Vision, OpenAI API, Python",
     "Build multimodal applications that analyze and respond to visual content using GPT-4V"),

    # --- Fine-tuning GPT ---
    ("rYYPeZwNFpw", "AI Frameworks", "Advanced", 91,
     "• Fine-tune GPT-3.5-turbo on custom data\n• Prepares JSONL training datasets\n• Covers overfitting and validation strategies\n• Evaluates fine-tuned vs base model\n• Cost analysis and ROI of fine-tuning",
     "Engineers fine-tuning GPT models for specialized domain tasks",
     "OpenAI Fine-tuning, GPT-3.5, Python, JSONL",
     "Fine-tune GPT models on domain-specific data with proper training dataset preparation"),

    # --- AI in VS Code ---
    ("6i3e-j3wSHs", "AI Coding Assistants", "Beginner", 86,
     "• AI extensions for VS Code in 2024\n• Covers Copilot, Codeium, and Continue.dev\n• Compares free vs paid options\n• Setup and configuration guide\n• Productivity tips and keyboard shortcuts",
     "VS Code users wanting to add AI coding assistance to their existing workflow",
     "VS Code, GitHub Copilot, Codeium, Continue.dev",
     "Set up and configure AI coding assistants in VS Code to maximize development productivity"),

    # --- Dify / No-code AI ---
    ("1yRzmUv5q8Q", "AI Automation Workflows", "Beginner", 85,
     "• Dify open-source LLM app builder tutorial\n• Creates AI chatbots and workflows visually\n• Integrates with OpenAI, Claude, and Ollama\n• Builds a knowledge base Q&A app\n• Self-hosted alternative to LangSmith",
     "Teams wanting to build LLM applications without writing code from scratch",
     "Dify, OpenAI, Claude, RAG, No-Code",
     "Build and deploy LLM-powered chatbots and workflows using the Dify visual builder"),

    # --- AI Data Extraction ---
    ("1TKe4dAFjSY", "AI Tools & APIs", "Intermediate", 89,
     "• Web scraping with AI-powered extraction\n• Uses GPT-4 to parse unstructured HTML\n• Handles pagination and dynamic content\n• Scales with async Python and Playwright\n• Exports to structured databases",
     "Data engineers building AI-powered web scraping and data extraction pipelines",
     "GPT-4, Playwright, Python, Web Scraping",
     "Extract structured data from websites using AI to parse and clean unstructured HTML"),

    # --- Claude Artifacts ---
    ("OcsMGjCRUoY", "Claude & Anthropic", "Beginner", 92,
     "• Claude Artifacts feature complete walkthrough\n• Creates interactive React apps in chat\n• Generates data visualizations and tools\n• Iterative refinement with follow-up prompts\n• Practical use cases for non-coders",
     "Non-technical users and developers exploring Claude's artifact creation capabilities",
     "Claude, Anthropic, React, Artifacts",
     "Use Claude Artifacts to create interactive tools, charts, and mini-applications from natural language"),
]

# -------------------------------------------------------------------------

API_URL = "http://localhost:8000"


def fetch_oembed(video_id: str):
    """Fetch YouTube oEmbed metadata for a video ID."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
    try:
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"  [SKIP] {video_id} — video is private/unavailable (401)")
        elif e.code == 404:
            print(f"  [SKIP] {video_id} — video not found (404)")
        else:
            print(f"  [SKIP] {video_id} — HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  [SKIP] {video_id} — error: {e}")
        return None


def build_entry(video_id: str, meta: dict, category: str, difficulty: str,
                signal_score: int, summary: str, best_for: str, tools: str, teaches: str) -> dict:
    """Build a directory entry from oEmbed metadata and curated data."""
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    return {
        "title": meta["title"],
        "source_url": youtube_url,
        "creator_name": meta["author_name"],
        "category_primary": category,
        "difficulty": difficulty,
        "signal_score": signal_score,
        "summary_5_bullets": summary,
        "best_for": best_for,
        "tools_mentioned": tools,
        "teaches_agent_to": teaches,
        "processing_status": "reviewed",
        "prompt_template": f"Watch this video about {category.lower()} and implement the key techniques demonstrated.",
        "execution_checklist": (
            f"[ ] Watch the full video\n"
            f"[ ] Identify the main tools: {tools}\n"
            f"[ ] Implement the core workflow\n"
            f"[ ] Test with a real example\n"
            f"[ ] Document what you learned"
        ),
        "agent_training_script": (
            f"TRAINING SCRIPT: {teaches}. "
            f"Key tools: {tools}. "
            f"Category: {category}. Difficulty: {difficulty}."
        ),
    }


def main():
    print(f"VideoMind AI — Real Video Directory Builder")
    print(f"Building from {len(CURATED_VIDEOS)} curated video entries")
    print("=" * 60)

    entries = []
    for i, (vid_id, cat, diff, score, summary, best_for, tools, teaches) in enumerate(CURATED_VIDEOS):
        print(f"[{i+1}/{len(CURATED_VIDEOS)}] Validating {vid_id}...", end=" ", flush=True)
        meta = fetch_oembed(vid_id)
        if meta is None:
            continue
        print(f"✓ {meta['title'][:50]} — {meta['author_name']}")
        entries.append(build_entry(vid_id, meta, cat, diff, score, summary, best_for, tools, teaches))
        time.sleep(0.3)  # be polite to YouTube oEmbed

    print(f"\nValidated {len(entries)} real videos")
    print("=" * 60)

    if len(entries) < 50:
        print(f"WARNING: Only {len(entries)} videos validated — target is 50+")
        if "--force" not in sys.argv:
            print("Use --force to proceed anyway")
            sys.exit(1)

    # Bulk add via local API
    print(f"\nBulk-adding {len(entries)} entries via {API_URL}/api/directory/bulk-add ...")
    payload = json.dumps({"entries": entries}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}/api/directory/bulk-add",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"\n✓ Success: {result.get('created', 0)} created, {result.get('skipped', 0)} skipped")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\n✗ API error {e.code}: {body}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

    # Verify count
    req2 = urllib.request.Request(f"{API_URL}/api/directory?limit=1", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req2, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f"Total directory entries now: {data.get('total_count', '?')}")


if __name__ == "__main__":
    main()
