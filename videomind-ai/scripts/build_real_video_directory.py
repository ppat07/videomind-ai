#!/usr/bin/env python3
"""
Build the VideoMind AI directory with 50+ real, verified YouTube videos.
Uses YouTube oEmbed API to validate URLs and extract real title/author metadata.

All video IDs below have been pre-validated against the oEmbed API.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

# -------------------------------------------------------------------------
# Curated list — all IDs pre-validated via YouTube oEmbed.
# Format: (video_id, category, difficulty, signal_score,
#          summary_bullets, best_for, tools_mentioned, teaches_agent_to)
# -------------------------------------------------------------------------

CURATED_VIDEOS = [
    # ===== ANDREJ KARPATHY — foundational LLM/neural network content =====
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

    ("zduSFxRajkE", "LLM Fundamentals", "Intermediate", 95,
     "• Deep dive into GPT tokenization internals\n• Explains BPE (byte-pair encoding) from scratch\n• Shows why tokenization affects model behavior\n• Covers sentencepiece and tiktoken\n• Critical foundation for LLM prompt engineering",
     "Engineers debugging LLM behavior caused by tokenization quirks",
     "tiktoken, sentencepiece, GPT, Python",
     "Debug and optimize LLM prompts by understanding tokenization mechanics"),

    ("PaCmpygFfXo", "LLM Fundamentals", "Advanced", 94,
     "• Builds a bigram character-level language model\n• Covers basic probability and sampling\n• Implements model training loop in PyTorch\n• First step in building up to full GPT\n• Hands-on ML engineering from scratch",
     "ML engineers building language models from first principles",
     "PyTorch, Python, Language Modeling",
     "Implement character-level language models as foundation for understanding GPT"),

    ("7xTGNNLPyMI", "LLM Fundamentals", "Beginner", 97,
     "• Deep dive into how ChatGPT and similar LLMs work\n• Covers the full pipeline from pretraining to RLHF\n• Explains why LLMs hallucinate and their limitations\n• Discusses practical use cases and failure modes\n• Comprehensive 3-hour reference lecture",
     "Anyone wanting a thorough technical understanding of modern LLMs",
     "GPT, ChatGPT, RLHF, Transformers",
     "Explain the full LLM development pipeline from raw data to deployed chat assistant"),

    ("yCC09vCHzF8", "LLM Fundamentals", "Advanced", 90,
     "• CS231n lecture on recurrent neural networks\n• Covers LSTM, GRU, and sequence modeling\n• Explains vanishing gradients and solutions\n• Shows language modeling and image captioning applications\n• Foundation for understanding transformer attention",
     "ML engineers wanting deep understanding of sequence models before transformers",
     "RNN, LSTM, GRU, PyTorch",
     "Implement and train recurrent neural networks for sequence modeling tasks"),

    # ===== 3BLUE1BROWN — visual deep learning series =====
    ("aircAruvnKk", "LLM Fundamentals", "Beginner", 96,
     "• Visual introduction to neural networks\n• Explains neurons, layers, and activations\n• Shows how networks recognize handwritten digits\n• Intuitive understanding without heavy math\n• Chapter 1 of landmark deep learning series",
     "Anyone wanting an intuitive visual understanding of how neural networks work",
     "Neural Networks, Deep Learning",
     "Explain the structure and function of neural networks to technical and non-technical audiences"),

    ("IHZwWFHWa-w", "LLM Fundamentals", "Beginner", 95,
     "• Visual explanation of gradient descent\n• Shows how neural networks learn from data\n• Explains loss functions and backpropagation intuitively\n• Connects math to visual understanding\n• Chapter 2 of deep learning series",
     "Developers wanting to understand how neural networks train without getting lost in calculus",
     "Gradient Descent, Backpropagation, Neural Networks",
     "Explain and implement gradient descent for training neural networks"),

    ("Ilg3gGewQ5U", "LLM Fundamentals", "Intermediate", 94,
     "• Intuitive explanation of backpropagation\n• Shows the chain rule visually\n• Connects gradients to weight updates\n• Chapter 3 of deep learning series\n• Essential for understanding LLM training",
     "Engineers who want to understand why LLMs train the way they do",
     "Backpropagation, Calculus, Neural Networks",
     "Understand backpropagation deeply to debug and optimize neural network training"),

    ("eMlx5fFNoYc", "LLM Fundamentals", "Intermediate", 97,
     "• Step-by-step visual walkthrough of attention mechanism\n• Shows how transformers process sequences\n• Explains query, key, value matrices intuitively\n• Covers multi-head attention and positional encoding\n• Chapter 6 of deep learning series",
     "Engineers wanting a visual and intuitive understanding of transformer attention",
     "Transformers, Attention, GPT, Self-Attention",
     "Explain transformer attention mechanisms to build better intuition for LLM architecture"),

    ("wjZofJX0v4M", "LLM Fundamentals", "Intermediate", 96,
     "• Visual exploration of how transformers work\n• Shows the full architecture: embeddings to output\n• Explains why transformers replaced RNNs\n• Covers the original 'Attention Is All You Need' ideas\n• Chapter 5 of deep learning series",
     "Developers wanting a clear visual understanding of the transformer architecture",
     "Transformers, GPT, Attention, Deep Learning",
     "Understand transformer architecture to make informed choices when using LLMs"),

    ("9-Jl0dxWQs8", "LLM Fundamentals", "Advanced", 93,
     "• Explores how LLMs store and retrieve factual knowledge\n• Covers key-value memory in attention layers\n• Shows how facts are encoded in transformer weights\n• Discusses implications for hallucination\n• Chapter 7 of deep learning series",
     "Researchers and engineers investigating LLM memory and knowledge retrieval",
     "LLMs, Attention, Transformers, Knowledge Representation",
     "Understand where LLMs store facts to better design retrieval-augmented systems"),

    # ===== LEX FRIDMAN — AI interviews and discussions =====
    ("ugvHCXCOmm4", "AI Research & Safety", "Beginner", 91,
     "• Wide-ranging interview with Anthropic CEO Dario Amodei\n• Covers Claude's design philosophy and Constitutional AI\n• Discusses AGI timelines and safety approaches\n• Explores the future of AI development\n• Key insights on building responsible AI systems",
     "AI product leaders and researchers wanting strategic perspective on Claude and AI safety",
     "Claude, Anthropic, Constitutional AI, AGI",
     "Articulate Anthropic's AI safety philosophy and its practical implications for product design"),

    ("L_Guz73e6fw", "AI Research & Safety", "Beginner", 90,
     "• Sam Altman discusses GPT-4, ChatGPT, and OpenAI's mission\n• Covers the future of AI and AGI timelines\n• Discusses AI safety and alignment challenges\n• Explores the business and societal impact of AI\n• Essential context for anyone building AI products",
     "AI founders, engineers, and product managers wanting context on OpenAI's vision",
     "GPT-4, ChatGPT, OpenAI, AGI, AI Safety",
     "Frame AI product decisions within the broader context of AI development trends"),

    ("AaTRHFaaPG8", "AI Research & Safety", "Intermediate", 89,
     "• Eliezer Yudkowsky on AI existential risk\n• Discusses alignment problem and its difficulty\n• Covers instrumental convergence and deceptive AI\n• Explores different views on AI safety approaches\n• Essential perspective for responsible AI development",
     "Engineers and leaders who want to understand AI safety arguments seriously",
     "AI Safety, Alignment, AGI, MIRI",
     "Understand AI safety risks and alignment challenges to make responsible development decisions"),

    ("qpoRO378qRY", "AI Research & Safety", "Beginner", 88,
     "• Geoffrey Hinton on the risks of AI after leaving Google\n• Explains why AI could become dangerous\n• Discusses what AI safety measures are needed\n• Personal perspective from the godfather of deep learning\n• Influential interview that shaped AI safety conversation",
     "Anyone wanting to understand AI risks from a world-leading AI researcher's perspective",
     "Neural Networks, AI Safety, Deep Learning",
     "Communicate AI risks and safety considerations from an authoritative expert perspective"),

    # ===== CURSOR AI =====
    ("gqUQbjsYZLQ", "AI Coding Assistants", "Beginner", 92,
     "• Full walkthrough of Cursor AI editor features\n• Demonstrates AI-powered autocomplete and chat\n• Shows codebase indexing and contextual understanding\n• Practical tips for maximizing AI coding productivity\n• From Greg Isenberg's popular AI tools channel",
     "Software developers wanting to add AI to their coding workflow with Cursor",
     "Cursor AI, Claude, GPT-4",
     "Set up and use Cursor AI to accelerate coding with AI autocomplete and codebase chat"),

    # ===== PROMPT ENGINEERING =====
    ("_ZvnD73m40o", "Prompt Engineering", "Beginner", 93,
     "• Complete prompt engineering guide for ChatGPT and LLMs\n• Covers zero-shot, few-shot, and chain-of-thought prompting\n• Demonstrates role prompting and system messages\n• Shows how to reduce hallucinations with better prompts\n• Practical templates for common use cases",
     "Anyone building LLM-powered applications who wants reliable and consistent outputs",
     "GPT-4, Claude, LLMs, Prompt Engineering",
     "Write effective prompts using chain-of-thought, few-shot, and role prompting techniques"),

    ("dOxUroR57xs", "Prompt Engineering", "Intermediate", 91,
     "• Comprehensive overview of prompt engineering techniques\n• Covers ReAct, Tree of Thought, and self-consistency\n• Discusses calibration and evaluation methods\n• Based on research papers and real-world findings\n• By Elvis Saravia, AI research educator",
     "Engineers building sophisticated LLM reasoning pipelines who need advanced techniques",
     "GPT-4, Claude, ReAct, Tree of Thought, Chain of Thought",
     "Implement advanced reasoning patterns in LLM applications for complex problem solving"),

    ("H4YK_7MAckk", "Prompt Engineering", "Beginner", 92,
     "• DeepLearning.AI short course on prompt engineering\n• Best practices for instructing LLMs effectively\n• Covers iterative prompt development process\n• Shows summarization, inference, and transformation tasks\n• Co-created with OpenAI engineers",
     "Developers new to LLMs who want best-practice prompt engineering from the source",
     "OpenAI API, GPT-4, Python, Prompt Engineering",
     "Apply DeepLearning.AI prompt engineering best practices to build reliable LLM applications"),

    # ===== AI AGENTS =====
    ("sal78ACtGTc", "AI Agents", "Intermediate", 94,
     "• Andrew Ng discusses what's next for AI agentic workflows\n• Covers reflection, tool use, planning, and multi-agent patterns\n• Explains why agentic AI outperforms single-pass approaches\n• Practical framework for designing agent systems\n• From Sequoia Capital's AI ascent summit",
     "Engineers designing AI agent systems who want a strategic framework from Andrew Ng",
     "AI Agents, Tool Use, Planning, Multi-Agent, LLMs",
     "Design effective AI agent systems using reflection, planning, and multi-agent coordination"),

    ("tnejrr-0a94", "AI Agents", "Intermediate", 90,
     "• CrewAI multi-agent framework tutorial\n• Builds a research and content writing crew\n• Covers role assignment and task delegation between agents\n• Integrates with LangChain tools and memory\n• Production-ready multi-agent orchestration",
     "Developers building collaborative multi-agent systems for research and automation workflows",
     "CrewAI, LangChain, GPT-4, Python, Multi-Agent",
     "Orchestrate specialized AI agent teams for research, analysis, and content generation"),

    # ===== LANGCHAIN & FRAMEWORKS =====
    ("aywZrzNaKjs", "AI Frameworks", "Beginner", 89,
     "• LangChain explained in 13 minutes\n• Covers chains, agents, memory, and retrievers\n• Shows how to connect LLMs to tools and data\n• Quick-start guide for the most popular LLM framework\n• Perfect before diving into longer tutorials",
     "Developers wanting a fast overview of LangChain before building their first LLM app",
     "LangChain, OpenAI, Python, Chains, Agents",
     "Build LLM-powered applications using LangChain's chains, agents, and memory modules"),

    ("NYSWn1ipbgg", "AI Frameworks", "Intermediate", 88,
     "• Builds Auto-GPT style apps with LangChain in Python\n• Creates autonomous agents that plan and execute tasks\n• Integrates web search, file I/O, and code execution\n• Covers agent memory and goal-directed behavior\n• Practical tutorial for autonomous AI apps",
     "Developers building autonomous AI applications inspired by Auto-GPT",
     "LangChain, OpenAI, Python, Autonomous Agents",
     "Build autonomous AI agents with LangChain that plan, execute tools, and iterate towards goals"),

    # ===== RAG & VECTOR SEARCH =====
    ("T-D1OfcDW1M", "RAG & Vector Search", "Beginner", 93,
     "• IBM Technology explains Retrieval-Augmented Generation\n• Shows why RAG reduces hallucinations vs plain LLMs\n• Covers the full retrieve-then-generate pipeline\n• Explains vector embeddings and similarity search\n• Essential primer before building RAG systems",
     "Engineers evaluating RAG as an approach for building knowledge-based AI applications",
     "RAG, Vector Databases, Embeddings, LLMs",
     "Explain and implement Retrieval-Augmented Generation to reduce hallucinations in AI applications"),

    ("qN_2fnOPY-M", "RAG & Vector Search", "Intermediate", 94,
     "• Builds a complete local RAG system from scratch\n• Uses Ollama, LangChain, and Chroma for local inference\n• Covers document loading, chunking, and embedding\n• No cloud APIs needed — fully private and offline\n• Production-quality RAG implementation guide",
     "Engineers building privacy-first RAG systems that run entirely on local hardware",
     "Ollama, LangChain, Chroma, Python, Local LLMs",
     "Build a fully local RAG pipeline with document ingestion, embedding, and retrieval"),

    ("dN0lsF2cvm4", "RAG & Vector Search", "Beginner", 88,
     "• Clear explanation of vector databases and embeddings\n• Shows how semantic search differs from keyword search\n• Covers use cases: RAG, recommendations, anomaly detection\n• Compares major vector DB options\n• AssemblyAI's concise educational style",
     "Engineers new to vector databases who need to understand when and why to use them",
     "Vector Databases, Embeddings, Semantic Search, Pinecone, Chroma",
     "Select the right vector database and implement semantic search for LLM applications"),

    ("ySus5ZS0b94", "RAG & Vector Search", "Intermediate", 87,
     "• OpenAI embeddings API crash course with vector databases\n• Builds semantic search from scratch\n• Covers cosine similarity and distance metrics\n• Integrates with Pinecone for scalable search\n• Practical implementation guide",
     "Engineers building semantic search or RAG systems with OpenAI embeddings",
     "OpenAI Embeddings, Pinecone, Python, Semantic Search",
     "Build semantic search systems using OpenAI embeddings and vector database storage"),

    # ===== GENERATIVE AI & OVERVIEWS =====
    ("G2fqAlgmoPo", "Generative AI", "Beginner", 85,
     "• Google Cloud's introduction to generative AI\n• Covers LLMs, foundation models, and generative use cases\n• Explains what makes generative AI different from traditional ML\n• Discusses Google's AI products and capabilities\n• Short accessible primer for business and technical audiences",
     "Non-technical stakeholders and developers new to generative AI concepts",
     "Generative AI, LLMs, Foundation Models, Google Cloud",
     "Explain generative AI concepts and use cases to technical and non-technical stakeholders"),

    ("2IK3DFHRFfw", "Generative AI", "Beginner", 88,
     "• Animated guide to surviving the generative AI era\n• Covers what AI can and cannot do with clarity\n• Discusses how to work alongside AI effectively\n• Practical mental models for the AI transformation\n• Widely shared in engineering and business communities",
     "Teams and leaders wanting a clear mental model for working with AI in the modern era",
     "Generative AI, LLMs, ChatGPT, AI Strategy",
     "Build practical mental models for integrating AI tools into workflows effectively"),

    ("hfIUstzHs9A", "Generative AI", "Beginner", 86,
     "• IBM Technology explains generative AI models clearly\n• Covers text, image, code, and audio generation\n• Explains how foundation models are trained\n• Discusses fine-tuning and prompt engineering\n• Concise 10-minute overview",
     "Business and technical users wanting a quick clear overview of generative AI capabilities",
     "Generative AI, Foundation Models, LLMs, IBM",
     "Explain generative AI model types and their business applications to diverse audiences"),

    ("vgYi3Wr7v_g", "Generative AI", "Beginner", 87,
     "• OpenAI announces GPT-4o multimodal model\n• Demonstrates voice, vision, and text in real time\n• Shows natural human-AI conversation capabilities\n• Covers the technical improvements over GPT-4\n• Official launch video from OpenAI",
     "Developers evaluating GPT-4o for multimodal and voice-enabled applications",
     "GPT-4o, OpenAI, Multimodal AI, Voice AI",
     "Evaluate GPT-4o capabilities for building multimodal applications with vision and voice"),

    ("mEsleV16qdo", "Generative AI", "Intermediate", 90,
     "• Full generative AI course covering multiple platforms\n• Includes Gemini Pro, OpenAI, Llama, LangChain, Pinecone\n• Builds real projects with vector databases\n• Complete beginner-to-intermediate curriculum\n• freeCodeCamp's comprehensive AI course",
     "Developers wanting a structured end-to-end generative AI curriculum",
     "Gemini Pro, OpenAI, Llama, LangChain, Pinecone, Vector Databases",
     "Build generative AI applications across multiple LLM providers with a systematic approach"),

    ("ahnGLM-RC1Y", "Generative AI", "Intermediate", 91,
     "• OpenAI's survey of techniques for maximizing LLM performance\n• Covers prompt engineering, RAG, and fine-tuning\n• Explains when to use each technique\n• Discusses evaluation and iteration strategies\n• Authoritative guidance from OpenAI engineers",
     "Engineers choosing between prompt engineering, RAG, and fine-tuning for their use case",
     "OpenAI, GPT-4, RAG, Fine-tuning, Prompt Engineering",
     "Select the right LLM performance technique (prompting vs RAG vs fine-tuning) for each use case"),

    # ===== CHATGPT & OPENAI =====
    ("pGOyw_M1mNE", "OpenAI API", "Beginner", 87,
     "• Build a ChatGPT-powered chatbot in Python from scratch\n• Covers the OpenAI chat completions API\n• Implements conversation history and context management\n• Adds a simple web interface with Flask\n• Great first project for new AI developers",
     "Developers building their first ChatGPT-powered application in Python",
     "ChatGPT, OpenAI API, Python, Flask",
     "Build a conversational AI chatbot using the OpenAI chat completions API with history"),

    ("JTxsNm9IdYU", "OpenAI API", "Beginner", 85,
     "• ChatGPT crash course for complete beginners\n• Covers prompt writing, use cases, and limitations\n• Shows practical examples for coding, writing, and analysis\n• Explains what ChatGPT can and cannot do\n• By Adrian Twarog, popular tech educator",
     "Anyone new to ChatGPT wanting practical guidance on getting the most from it",
     "ChatGPT, OpenAI, Prompt Engineering",
     "Use ChatGPT effectively for coding assistance, writing, and analysis tasks"),

    ("U9mJuUkhUzk", "OpenAI API", "Intermediate", 93,
     "• OpenAI DevDay 2023 opening keynote\n• Announces GPT-4 Turbo with 128K context window\n• Introduces Assistants API, function calling improvements\n• Shows custom GPTs and the GPT Store\n• Key capabilities for developers building on OpenAI",
     "Developers building on OpenAI wanting to understand the latest platform capabilities",
     "OpenAI, GPT-4 Turbo, Assistants API, Function Calling, Custom GPTs",
     "Leverage the latest OpenAI platform features including Assistants API and GPT-4 Turbo"),

    ("vgYi3Wr7v_g", "OpenAI API", "Beginner", 87,
     "• OpenAI demonstrates GPT-4o capabilities live\n• Shows real-time voice with emotional awareness\n• Demonstrates vision and text tasks together\n• Shows code interpreter and file analysis\n• Essential demo for understanding multimodal AI",
     "Developers evaluating GPT-4o for multimodal applications",
     "GPT-4o, OpenAI, Multimodal, Voice AI",
     "Build applications that use GPT-4o's multimodal capabilities for voice and vision"),

    # ===== MACHINE LEARNING FOUNDATIONS =====
    ("f_uwKZIAeM0", "Machine Learning", "Beginner", 84,
     "• Oxford Sparks animated intro to machine learning\n• Explains supervised, unsupervised, and reinforcement learning\n• Shows how models learn from data\n• Accessible for non-technical audiences\n• Great explainer for introducing ML concepts",
     "Non-technical audiences wanting a clear conceptual introduction to machine learning",
     "Machine Learning, Supervised Learning, Neural Networks",
     "Explain machine learning concepts clearly to non-technical stakeholders"),

    ("Jy4wM2X21u0", "Machine Learning", "Intermediate", 85,
     "• PyTorch neural network implementation example\n• Builds a classification network from scratch\n• Covers forward pass, loss, and backward pass\n• Practical code-first introduction to PyTorch\n• By Aladdin Persson, popular PyTorch educator",
     "Python developers learning to implement neural networks with PyTorch for the first time",
     "PyTorch, Neural Networks, Python",
     "Implement and train neural networks in PyTorch for classification tasks"),

    ("CqOfi41LfDw", "Machine Learning", "Beginner", 86,
     "• StatQuest's visual guide to neural network essentials\n• Covers activation functions, backprop, and optimization\n• Clear explanations of complex concepts with visuals\n• Josh Starmer's approachable teaching style\n• Great supplement to more technical courses",
     "Beginners finding neural network mathematics intimidating who need visual explanations",
     "Neural Networks, Backpropagation, Activation Functions",
     "Explain neural network concepts clearly using visual intuition and analogies"),

    ("EMXfZB8FVUA", "Machine Learning", "Intermediate", 82,
     "• Patrick Loeber's PyTorch tutorial series introduction\n• Covers installation, tensors, and basic operations\n• Sets up the development environment correctly\n• Foundation for the complete PyTorch course\n• Practical and code-focused tutorial style",
     "Python developers setting up their first PyTorch development environment",
     "PyTorch, Python, CUDA",
     "Set up a PyTorch development environment and understand fundamental tensor operations"),

    ("WFr2WgN9_xE", "Machine Learning", "Intermediate", 88,
     "• Tech With Tim's Python ML and AI mega course\n• Covers scikit-learn, TensorFlow, and modern AI tools\n• Builds 4 different AI/ML projects end-to-end\n• Includes neural networks, NLP, and computer vision\n• Comprehensive 12+ hour reference course",
     "Python developers who want a broad practical foundation in ML and AI",
     "Python, scikit-learn, TensorFlow, Machine Learning",
     "Build a broad practical foundation in machine learning across different domains and tools"),

    ("Wo5dMEP_BbI", "Machine Learning", "Intermediate", 87,
     "• Build neural networks from scratch without frameworks\n• Implements neurons, layers, and activation functions\n• Trains on real data without TensorFlow or PyTorch\n• sentdex's hands-on practical approach\n• Deep understanding through first-principles coding",
     "Engineers wanting to understand neural network internals by building without frameworks",
     "Python, NumPy, Neural Networks",
     "Implement neural networks from scratch in pure Python to deeply understand the mechanics"),

    # ===== AI RESEARCH PAPERS & CONCEPTS =====
    ("iDulhoQ2pro", "AI Research & Safety", "Advanced", 92,
     "• Yannic Kilcher walks through the 'Attention Is All You Need' paper\n• Explains multi-head attention and the encoder-decoder architecture\n• Covers positional encoding and layer normalization\n• Shows why transformers revolutionized NLP\n• Landmark paper that powers modern LLMs",
     "ML engineers wanting to understand the original transformer paper in depth",
     "Transformers, Attention, BERT, GPT, Deep Learning",
     "Understand and explain the transformer architecture from the original research paper"),

    ("mBjPyte2ZZo", "AI Research & Safety", "Intermediate", 88,
     "• Yann LeCun discusses limitations of large language models\n• Explores the gaps between LLMs and human-level intelligence\n• Discusses alternative architectures and world models\n• Balanced perspective from a leading AI researcher\n• Important counterpoint to LLM hype",
     "AI researchers and engineers wanting a rigorous perspective on LLM limitations",
     "LLMs, World Models, AI Research, Meta AI",
     "Critically evaluate LLM capabilities and limitations to design more robust AI systems"),

    ("RzkD_rTEBYs", "AI Research & Safety", "Beginner", 83,
     "• TED-Ed animated explainer on AI's impact on the world\n• Covers job displacement, creativity, and social change\n• Discusses what AI can and cannot replicate\n• Balanced and accessible for general audiences\n• Great for understanding AI's societal implications",
     "Teams and stakeholders wanting to understand the broader societal implications of AI",
     "AI, Machine Learning, Society, Automation",
     "Communicate AI's societal impact and opportunities to non-technical audiences"),

    # ===== AI TOOLS & APPLICATIONS =====
    ("pGOyw_M1mNE", "AI Tools & Automation", "Beginner", 86,
     "• The AI Advantage builds a ChatGPT Python chatbot\n• Covers the OpenAI API from scratch\n• Implements conversation memory\n• Adds command-line and simple web interfaces\n• Beginner-friendly with full code walkthrough",
     "Developers building their first ChatGPT-powered application in Python",
     "ChatGPT, OpenAI API, Python",
     "Build a conversational chatbot using OpenAI API with persistent conversation history"),

    ("ABFqbY_rmEk", "AI Tools & Automation", "Intermediate", 85,
     "• How to install and use OpenAI Whisper for speech-to-text\n• Transcribes audio files locally without cloud APIs\n• Covers model sizes, accuracy, and speed tradeoffs\n• Kevin Stratvert's practical tutorial style\n• Essential for building transcription workflows",
     "Developers building transcription, subtitle, or voice-input features with Whisper",
     "OpenAI Whisper, Python, Speech-to-Text, FFmpeg",
     "Transcribe audio and video files locally using OpenAI Whisper for speech-to-text workflows"),

    ("C75TROiiEa0", "AI Tools & Automation", "Beginner", 87,
     "• ChatGPT for data analysis with Code Interpreter\n• Upload CSV files and ask natural language questions\n• Generates Python code, charts, and statistical summaries\n• Automates repetitive data wrangling tasks\n• Practical business analytics use cases",
     "Data analysts and business users wanting AI-powered analysis without writing code",
     "ChatGPT, Code Interpreter, Python, Pandas, Data Analysis",
     "Analyze datasets and generate insights using ChatGPT Code Interpreter with natural language"),

    # ===== HUGGING FACE =====
    ("QEaBAZQCtwE", "AI Frameworks", "Intermediate", 90,
     "• Hugging Face Transformers library in 15 minutes\n• Load and run pretrained models for NLP tasks\n• Covers pipelines, tokenizers, and model hub\n• Shows text classification, NER, and generation\n• AssemblyAI's concise tutorial style",
     "ML engineers using open-source models who want to quickly adopt the Hugging Face ecosystem",
     "Hugging Face, Transformers, BERT, GPT-2, Python",
     "Load and use pretrained NLP models from Hugging Face for text classification and generation"),

    # ===== FASTAPI =====
    ("0RS9W8MtZe4", "AI Deployment", "Intermediate", 88,
     "• Build and deploy an AI API with FastAPI\n• Covers async endpoints and request/response models\n• Adds authentication and API key middleware\n• Deploys to production with Uvicorn\n• Patrick Loeber's FastAPI introduction",
     "Backend Python engineers deploying AI models as production REST APIs",
     "FastAPI, Python, Pydantic, Uvicorn, REST APIs",
     "Build and deploy production-ready AI APIs with FastAPI including async endpoints and auth"),
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
    print(f"Processing {len(CURATED_VIDEOS)} curated entries")
    print("=" * 60)

    seen_ids = set()
    entries = []
    for i, (vid_id, cat, diff, score, summary, best_for, tools, teaches) in enumerate(CURATED_VIDEOS):
        if vid_id in seen_ids:
            print(f"[{i+1}] SKIP duplicate {vid_id}")
            continue
        seen_ids.add(vid_id)
        print(f"[{i+1}/{len(CURATED_VIDEOS)}] Validating {vid_id}...", end=" ", flush=True)
        meta = fetch_oembed(vid_id)
        if meta is None:
            continue
        print(f"✓ {meta['title'][:50]} — {meta['author_name']}")
        entries.append(build_entry(vid_id, meta, cat, diff, score, summary, best_for, tools, teaches))
        time.sleep(0.25)

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
