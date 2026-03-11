#!/usr/bin/env python3
"""
Manual directory fix - bypass API issues
"""
import sys
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_database
from models.directory import DirectoryEntry, ContentType

def create_directory_entries():
    """Create directory entries manually."""

    # Get database session
    from database import SessionLocal
    db = SessionLocal()

    try:
        # Check if entries already exist
        existing_count = db.query(DirectoryEntry).count()
        print(f"Existing entries: {existing_count}")

        if existing_count > 0:
            print("Directory already has entries!")
            return True

        # Create sample entries
        entries = [
            DirectoryEntry(
                id=str(uuid.uuid4()),
                title="Rick Roll - Classic AI Training Video",
                source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                content_type=ContentType.VIDEO,
                creator_name="Rick Astley",
                category_primary="Music & Entertainment",
                difficulty="Beginner",
                tools_mentioned="YouTube, VideoMind AI, AI Training",
                summary_5_bullets="• Classic music video\n• Perfect for testing\n• Well-known content\n• Audio transcription ready\n• AI training gold standard",
                best_for="Testing video processing pipeline and AI enhancement",
                signal_score=95,
                processing_status="processed",
                teaches_agent_to="Execute basic video processing workflows",
                prompt_template="Process this classic video for AI training data extraction",
                execution_checklist="[ ] Download transcript\n[ ] Extract audio\n[ ] Generate Q&As\n[ ] Format output",
                agent_training_script="TRAINING: Basic video-to-text processing with Claude enhancement",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            DirectoryEntry(
                id=str(uuid.uuid4()),
                title="VideoMind AI Demo - System Capabilities",
                source_url="https://www.youtube.com/watch?v=QH2-TGUlwu4",
                video_url="https://www.youtube.com/watch?v=QH2-TGUlwu4",
                content_type=ContentType.VIDEO,
                creator_name="VideoMind AI", 
                category_primary="AI Tools & Automation",
                difficulty="Intermediate",
                tools_mentioned="VideoMind AI, Claude, YouTube API, Whisper",
                summary_5_bullets="• AI video processing\n• Automated transcription\n• Training data generation\n• Multiple output formats\n• Production-ready system",
                best_for="Understanding VideoMind AI capabilities and workflow",
                signal_score=88,
                processing_status="processed",
                teaches_agent_to="Implement video-to-AI-training workflows",
                prompt_template="Use VideoMind AI to transform videos into structured AI training datasets",
                execution_checklist="[ ] Upload video\n[ ] Select processing tier\n[ ] Review AI enhancement\n[ ] Export training data",
                agent_training_script="TRAINING: Advanced video processing with AI enhancement and structured output",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            DirectoryEntry(
                id=str(uuid.uuid4()),
                title="Claude Enhancement Demo - AI Processing",
                source_url="https://www.youtube.com/watch?v=3AtDnEC4zak",
                video_url="https://www.youtube.com/watch?v=3AtDnEC4zak",
                content_type=ContentType.VIDEO,
                creator_name="VideoMind AI",
                category_primary="Business Use Cases",
                difficulty="Advanced",
                tools_mentioned="Claude AI, OpenAI, Whisper, FastAPI",
                summary_5_bullets="• Claude-based enhancement\n• Zero API costs\n• Superior reliability\n• Production scalability\n• Competitive advantage",
                best_for="Businesses needing reliable video AI processing at scale",
                signal_score=92,
                processing_status="processed",
                teaches_agent_to="Deploy production-ready AI video processing systems",
                prompt_template="Build scalable video AI processing with Claude enhancement and fallback systems",
                execution_checklist="[ ] Configure Claude API\n[ ] Implement fallbacks\n[ ] Test reliability\n[ ] Scale processing\n[ ] Monitor success rates",
                agent_training_script="TRAINING: Production AI video processing with multi-provider reliability",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]

        # Add all entries
        for entry in entries:
            db.add(entry)

        # Commit to database
        db.commit()

        print(f"✅ Created {len(entries)} directory entries!")
        return True

    except Exception as e:
        print(f"❌ Error creating entries: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Manual Directory Population")
    print("="*40)

    success = create_directory_entries()

    if success:
        print("✅ Directory populated successfully!")
        print("🔍 Check http://localhost:8000/directory")
    else:
        print("❌ Directory population failed")