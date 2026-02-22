# VideoMind AI 🎥🤖

Transform any YouTube video into AI-ready training data. Built by Paul Patlur with Claude Code.

## 🎯 What It Does

VideoMind AI takes YouTube videos and converts them into structured training data for AI models:

- **Clean Transcripts** with timestamps
- **AI-Enhanced Summaries** and key points  
- **Q&A Pairs** for fine-tuning
- **Multiple Output Formats** (JSON, CSV, custom)
- **Fast Processing** with Whisper + GPT

## 🚀 Market Opportunity

- AI Transcription Market: $4.5B → $19.2B by 2034 (15.6% CAGR)
- AI Training Dataset Market: $2.8B → $9.58B by 2029
- **Gap:** No solution specifically optimizes video content for AI training

## 🛠 Tech Stack

- **Backend:** FastAPI + Python 3.11+
- **Database:** SQLite (upgradeable to PostgreSQL)
- **AI APIs:** OpenAI Whisper + GPT-3.5
- **Video Processing:** yt-dlp + FFmpeg
- **Frontend:** HTML + Tailwind CSS + JavaScript
- **Payment:** Stripe (coming soon)

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- FFmpeg installed on your system
- OpenAI API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd videomind-ai
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Create required directories:**
   ```bash
   mkdir -p temp static templates
   ```

6. **Run the application:**
   ```bash
   cd src
   python main.py
   ```

7. **Open in browser:**
   ```
   http://localhost:8000
   ```

## 🔧 Configuration

Edit the `.env` file with your settings:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
SECRET_KEY=your-super-secret-key

# Optional (defaults provided)
DATABASE_URL=sqlite:///./videomind.db
TEMP_STORAGE_PATH=./temp/
MAX_VIDEO_DURATION_MINUTES=120
```

## 🎪 API Endpoints

### Core Endpoints

- `GET /` - Homepage interface
- `POST /api/process` - Submit video for processing
- `GET /api/status/{job_id}` - Check processing status
- `GET /api/download/{job_id}/{format}` - Download results
- `GET /health` - Health check

### Example API Usage

```javascript
// Submit video for processing
const response = await fetch('/api/process', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        youtube_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        email: 'user@example.com',
        tier: 'detailed'
    })
});

const result = await response.json();
console.log('Job ID:', result.job_id);
```

## 💰 Pricing Model

- **Basic Tier:** $3 per video (transcript + summary + 5 Q&As)
- **Detailed Tier:** $5 per video (everything + key concepts + 10 Q&As)
- **Bulk Discount:** $2 per video for 5+ videos

## 🔄 Processing Pipeline

1. **Validate YouTube URL** → Extract video metadata
2. **Download Audio** → yt-dlp extraction to temp file
3. **Transcribe** → Whisper API call with timestamps
4. **AI Enhancement** → GPT for summaries/Q&As
5. **Generate Outputs** → JSON + Q&A formats
6. **Email Results** → Send download links
7. **Cleanup** → Delete temp files after 7 days

## 📊 Output Formats

### Basic Transcript JSON
```json
{
    "video_id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "transcript": [
        {
            "start": 0.0,
            "end": 3.5,
            "text": "We're no strangers to love"
        }
    ],
    "summary": "Rick Astley's classic song about commitment...",
    "key_points": ["Love", "Commitment", "Trust"],
    "qa_pairs": [
        {
            "question": "What is the main theme of the song?",
            "answer": "Commitment and loyalty in relationships"
        }
    ]
}
```

## 🧪 Testing

```bash
# Run health check
curl http://localhost:8000/health

# Test video info extraction
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "email": "test@example.com",
    "tier": "basic"
  }'
```

## 🚧 Development Status

### ✅ Completed (MVP Foundation)
- [x] FastAPI application structure
- [x] Database models and configuration
- [x] YouTube URL validation
- [x] Basic web interface
- [x] Health check endpoints
- [x] File management utilities

### 🔄 In Progress
- [ ] YouTube audio downloading service
- [ ] Whisper transcription integration
- [ ] AI enhancement with GPT
- [ ] Processing pipeline orchestration

### 📋 Coming Soon
- [ ] Stripe payment integration
- [ ] Email notifications
- [ ] Background job processing
- [ ] Advanced output formats
- [ ] Enterprise features

## 🐛 Troubleshooting

### Common Issues

**FFmpeg not found:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/
```

**OpenAI API errors:**
- Verify your API key is valid
- Check your OpenAI account has credits
- Ensure API key has proper permissions

**Database issues:**
- Check file permissions in project directory
- Ensure SQLite is available
- Delete `videomind.db` to reset database

## 📈 Roadmap

### Phase 1: MVP (8-12 weeks) ✅
- Basic YouTube-to-transcript pipeline
- Simple web interface
- Pay-per-use model

### Phase 2: Features (12-16 weeks)
- Multiple video platforms
- Advanced AI processing
- User accounts and dashboards
- Subscription billing

### Phase 3: Enterprise (16-24 weeks)
- Custom processing pipelines
- White-label capabilities
- Advanced analytics
- Enterprise integrations

## 🤝 Contributing

Built by Paul Patlur using Claude Code. This project is part of a journey to create a $10K/month business from video-to-AI-training data.

## 📄 License

Private project. All rights reserved.

---

**🔥 Built with determination and Claude Code! Let's turn this into a game-changer! 🚀**