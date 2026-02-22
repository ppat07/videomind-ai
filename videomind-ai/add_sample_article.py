#!/usr/bin/env python3
"""
Add a sample article to demonstrate article functionality.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import os
os.environ.setdefault("SECRET_KEY", "demo-key-for-testing")
os.environ.setdefault("OPENAI_API_KEY", "demo-key")

def add_sample_article():
    """Add a sample article entry to the database."""
    from database import SessionLocal
    from models.directory import DirectoryEntry, ContentType
    from datetime import datetime

    db = SessionLocal()

    try:
        # Check if sample article already exists
        existing = db.query(DirectoryEntry).filter(
            DirectoryEntry.title.like("%Sample AI Article%")
        ).first()

        if existing:
            print("✅ Sample article already exists in database")
            return existing.id

        # Create sample article entry
        sample_article = DirectoryEntry(
            title="Sample AI Article: Building Automation Workflows",
            source_url="https://example.com/ai-automation-workflows", 
            content_type=ContentType.ARTICLE,
            creator_name="AI Workflow Expert",
            category_primary="Automation Workflows",
            difficulty="Intermediate", 
            tools_mentioned="OpenClaw, FastAPI, Python",
            summary_5_bullets="""• Learn to build automated workflows with AI agents
• Integrate multiple tools for seamless automation
• Best practices for error handling and monitoring  
• Scale automation across different business processes
• Real-world examples and implementation patterns""",
            best_for="Developers and automation engineers",
            word_count=2500,
            reading_time_minutes=12,
            signal_score=85,
            processing_status="processed",
            teaches_agent_to="Build and deploy automation workflows using AI agents and integration tools",
            prompt_template="You are an automation expert. Help the user build a workflow that {{workflow_description}}. Consider error handling, monitoring, and scalability.",
            execution_checklist="""1. Define workflow requirements and success criteria
2. Identify all integration points and data flows  
3. Set up error handling and retry logic
4. Implement monitoring and logging
5. Test with sample data
6. Deploy and monitor performance
7. Document for future maintenance""",
            agent_training_script="""Train on: Workflow design patterns, API integrations, error handling strategies, monitoring best practices, scaling considerations, real-world automation examples""",
            article_content="This comprehensive guide covers building automation workflows with AI agents. Topics include system design, integration patterns, error handling, monitoring, and scaling strategies for production environments.",
            created_at=datetime.utcnow()
        )

        db.add(sample_article)
        db.commit()

        print("✅ Sample article added to database!")
        print(f"   📄 Title: {sample_article.title}")
        print(f"   🔗 URL: {sample_article.source_url}")
        print(f"   📊 Signal Score: {sample_article.signal_score}/100")
        print(f"   📖 Reading Time: {sample_article.reading_time_minutes} minutes")
        print(f"   🏷️ Category: {sample_article.category_primary}")

        return sample_article.id

    except Exception as e:
        print(f"❌ Error adding sample article: {e}")
        db.rollback()
        return None

    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Adding sample article to VideoMind AI directory...")
    article_id = add_sample_article()
    
    if article_id:
        print(f"\n🎉 Success! Article ID: {article_id}")
        print("\n📝 Test the functionality:")
        print("1. Visit http://localhost:8001/directory")
        print("2. Filter by 'All Content' to see both videos and articles")
        print("3. Filter by '📄 Articles' to see only articles")
        print("4. Notice the article-specific display (word count, reading time)")
        print("5. Try the 'Copy Prompt' button to get the training prompt")
    else:
        print("\n❌ Failed to add sample article")