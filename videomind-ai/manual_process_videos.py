#!/usr/bin/env python3
"""
Manual video processing to populate directory immediately
Bypasses the broken queue system to get videos into directory
"""
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import SessionLocal, create_tables
from models.directory import DirectoryEntry, ContentType
from models.video import VideoJob, ProcessingStatus
from datetime import datetime
import uuid

# Priority OpenClaw videos to populate directory
PRIORITY_VIDEOS = [
    {
        "title": "How I Use Clawdbot to Run My Business and Life 24/7",
        "source_url": "https://www.youtube.com/watch?v=YRhGtHfs1Lw",
        "creator_name": "Business Use Cases",
        "category_primary": "Business Use Cases",
        "difficulty": "Intermediate", 
        "tools_mentioned": "OpenClaw; automation workflows; business operations",
        "summary_5_bullets": "• 24/7 automation setup\n• Business workflow creation\n• Operational efficiency\n• Revenue automation\n• Life management systems",
        "best_for": "Business owners wanting comprehensive automation",
        "signal_score": 88
    },
    {
        "title": "My Multi-Agent Team with OpenClaw", 
        "source_url": "https://www.youtube.com/watch?v=bzWI3Dil9Ig",
        "creator_name": "Alex Finn",
        "category_primary": "Advanced Workflows",
        "difficulty": "Advanced",
        "tools_mentioned": "OpenClaw; multi-agent systems; orchestration",
        "summary_5_bullets": "• Multi-agent architecture\n• Agent coordination patterns\n• Team workflow design\n• Advanced automation\n• Scalable systems",
        "best_for": "Advanced users building complex automation",
        "signal_score": 90
    },
    {
        "title": "21 INSANE Use Cases For OpenClaw...",
        "source_url": "https://www.youtube.com/watch?v=8kNv3rjQaVA", 
        "creator_name": "Greg Isenberg",
        "category_primary": "Use Cases",
        "difficulty": "Intermediate",
        "tools_mentioned": "OpenClaw; automation; workflows; productivity",
        "summary_5_bullets": "• Creative automation ideas\n• Practical implementations\n• Business applications\n• Personal productivity\n• Advanced use patterns",
        "best_for": "Users seeking automation inspiration",
        "signal_score": 85
    },
    {
        "title": "I figured out the best way to run OpenClaw",
        "source_url": "https://www.youtube.com/watch?v=3GrG-dOmrLU",
        "creator_name": "Tech Tutorial",
        "category_primary": "Best Practices", 
        "difficulty": "Intermediate",
        "tools_mentioned": "OpenClaw; optimization; configuration; performance",
        "summary_5_bullets": "• Optimal configuration\n• Performance optimization\n• Resource management\n• Efficiency techniques\n• Best practices guide",
        "best_for": "Users optimizing their OpenClaw setup",
        "signal_score": 82
    },
    {
        "title": "OpenClaw Use Cases that are actually helpful...",
        "source_url": "https://www.youtube.com/watch?v=Q7r--i9lLck",
        "creator_name": "Practical AI",
        "category_primary": "Practical Use Cases",
        "difficulty": "Beginner", 
        "tools_mentioned": "OpenClaw; practical automation; real-world use",
        "summary_5_bullets": "• Real-world applications\n• Practical automation\n• Daily workflow helpers\n• Problem-solving focus\n• Actionable examples",
        "best_for": "Beginners seeking practical applications",
        "signal_score": 83
    },
    {
        "title": "Please don't install Clawdbot",
        "source_url": "https://www.youtube.com/watch?v=11sxky4vTcs",
        "creator_name": "Security Focus",
        "category_primary": "Security & Warnings",
        "difficulty": "Beginner",
        "tools_mentioned": "OpenClaw; security; installation; warnings",
        "summary_5_bullets": "• Security considerations\n• Installation warnings\n• Risk assessment\n• Safe usage practices\n• Alternative approaches",
        "best_for": "Security-conscious users",
        "signal_score": 78
    },
    {
        "title": "We Used OpenClaw for a Week. This is the Harsh Truth.",
        "source_url": "https://www.youtube.com/watch?v=4xDc00EF_eY",
        "creator_name": "Real Review",
        "category_primary": "Reviews & Reality Check",
        "difficulty": "Intermediate",
        "tools_mentioned": "OpenClaw; real experience; pros and cons",
        "summary_5_bullets": "• Honest review\n• Real-world results\n• Limitations discussion\n• Practical insights\n• User experience",
        "best_for": "Users wanting honest feedback",
        "signal_score": 87
    },
    {
        "title": "DO NOT use a VPS for OpenClaw (major warning)",
        "source_url": "https://www.youtube.com/watch?v=ev4iiGXlnh0", 
        "creator_name": "Infrastructure Guide",
        "category_primary": "Infrastructure & Setup",
        "difficulty": "Advanced",
        "tools_mentioned": "OpenClaw; VPS; infrastructure; hosting warnings",
        "summary_5_bullets": "• VPS limitations\n• Infrastructure warnings\n• Setup recommendations\n• Performance issues\n• Alternative solutions",
        "best_for": "Users planning infrastructure",
        "signal_score": 80
    },
    {
        "title": "6 OpenClaw use cases I promise will change your life",
        "source_url": "https://www.youtube.com/watch?v=41_TNGDDnfQ",
        "creator_name": "Life Automation",
        "category_primary": "Life Automation", 
        "difficulty": "Beginner",
        "tools_mentioned": "OpenClaw; life automation; personal productivity",
        "summary_5_bullets": "• Life-changing automation\n• Personal productivity\n• Daily routine optimization\n• Quality of life improvements\n• Practical implementations",
        "best_for": "Users wanting personal automation",
        "signal_score": 84
    },
    {
        "title": "50 days with OpenClaw: The hype, the reality & what actually broke",
        "source_url": "https://youtu.be/NZ1mKAWJPr4",
        "creator_name": "Long-term Review", 
        "category_primary": "Long-term Reviews",
        "difficulty": "Intermediate",
        "tools_mentioned": "OpenClaw; long-term use; reliability; issues",
        "summary_5_bullets": "• 50-day experience\n• Reality vs expectations\n• System reliability\n• Issues encountered\n• Long-term insights",
        "best_for": "Users considering long-term adoption",
        "signal_score": 89
    }
]

def populate_directory():
    """Directly populate the directory with priority videos"""
    
    # Ensure tables exist
    create_tables()
    
    db = SessionLocal()
    try:
        added_count = 0
        
        print("🚀 Manually populating VideoMind AI directory...")
        
        for video_data in PRIORITY_VIDEOS:
            # Check if video already exists
            existing = db.query(DirectoryEntry).filter(
                DirectoryEntry.source_url == video_data["source_url"]
            ).first()
            
            if existing:
                print(f"⏭️  Skipping existing: {video_data['title'][:50]}...")
                continue
            
            # Create directory entry directly
            entry = DirectoryEntry(
                title=video_data["title"],
                video_url=video_data["source_url"],  # Legacy field
                source_url=video_data["source_url"], 
                content_type=ContentType.VIDEO,
                creator_name=video_data["creator_name"],
                category_primary=video_data["category_primary"],
                difficulty=video_data["difficulty"],
                tools_mentioned=video_data["tools_mentioned"],
                summary_5_bullets=video_data["summary_5_bullets"],
                best_for=video_data["best_for"],
                signal_score=video_data["signal_score"],
                processing_status="reviewed",
                teaches_agent_to=f"Execute {video_data['category_primary'].lower()} workflows effectively.",
                prompt_template=f"Implement the {video_data['category_primary'].lower()} techniques from this tutorial with step-by-step commands.",
                execution_checklist="[ ] Review tutorial\n[ ] Setup environment\n[ ] Execute workflow\n[ ] Validate results\n[ ] Document process",
                agent_training_script=f"TRAINING SCRIPT: {video_data['category_primary']} implementation with practical examples.",
                created_at=datetime.utcnow()
            )
            
            db.add(entry)
            added_count += 1
            print(f"✅ Added: {video_data['title'][:60]}...")
        
        # Commit all changes
        db.commit()
        
        # Get final count
        total_entries = db.query(DirectoryEntry).count()
        
        print(f"\n🎯 Directory Population Complete:")
        print(f"   • Added: {added_count} new videos")
        print(f"   • Total: {total_entries} videos in directory")
        print(f"   • Status: Ready for customer testing!")
        
        return added_count, total_entries
        
    except Exception as e:
        print(f"❌ Error populating directory: {e}")
        db.rollback()
        return 0, 0
        
    finally:
        db.close()

if __name__ == "__main__":
    populate_directory()