# VideoMind AI - Foundation Blueprint 🏗️

## Complete Architecture Design

### Project Structure
```
videomind-ai/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings & environment vars
│   ├── database.py             # SQLite connection & models
│   ├── models/
│   │   ├── __init__.py
│   │   ├── video.py            # Video processing models
│   │   └── user.py             # User/session models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── youtube_service.py  # YouTube audio extraction
│   │   ├── transcription_service.py # Whisper API calls
│   │   └── ai_service.py       # GPT enhancement
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   └── process.py          # Main processing endpoints
│   └── utils/
│       ├── __init__.py
│       ├── validators.py       # URL validation, etc.
│       └── helpers.py          # Common utilities
├── static/                     # Frontend files (CSS, JS)
├── templates/                  # HTML templates
├── tests/                      # Unit tests
├── temp/                       # Temporary file storage
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── docker-compose.yml          # For easy deployment
```

## Core Data Models

### Video Processing Model
```python
class VideoJob:
    id: str (UUID)
    youtube_url: str
    status: str (pending, processing, completed, failed)
    email: str (for delivery)
    tier: str (basic, detailed)
    created_at: datetime
    completed_at: datetime
    transcript: str (JSON)
    ai_enhanced: str (JSON)
    download_links: str (JSON)
    cost: float
    error_message: str (optional)
```

## API Endpoints

### Core Endpoints
- **POST /api/process** - Submit YouTube URL for processing
- **GET /api/status/{job_id}** - Check processing status
- **GET /api/download/{job_id}/{format}** - Download results
- **GET /health** - Health check

## Processing Workflow
1. **Validate YouTube URL** → Extract video metadata
2. **Download Audio** → yt-dlp extraction to temp file
3. **Transcribe** → Whisper API call with timestamps
4. **AI Enhancement** → GPT-3.5 for summaries/Q&As
5. **Generate Outputs** → JSON + Q&A formats
6. **Email Results** → Send download links
7. **Cleanup** → Delete temp files after 7 days

## Environment Variables Needed
- OPENAI_API_KEY
- DATABASE_URL
- STRIPE_SECRET_KEY
- EMAIL_API_KEY (SendGrid/similar)
- TEMP_STORAGE_PATH

## MVP Features Priority
1. ✅ Basic FastAPI server with health check
2. ✅ YouTube URL validation
3. ✅ Audio extraction (yt-dlp)
4. ✅ Whisper transcription
5. ✅ Basic AI enhancement
6. ✅ Simple web interface
7. ✅ Payment integration (later phase)

---
**STATUS: FOUNDATION COMPLETE - READY FOR CLAUDE CODE! 🚀**