#!/usr/bin/env python3
"""
Test script for article processing functionality.
Run this to verify article support is working.
"""
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set basic config
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

def test_article_processor():
    """Test article processor initialization."""
    print("🧪 Testing article processor...")
    
    try:
        from services.article_service import ArticleProcessor
        processor = ArticleProcessor()
        print("✅ ArticleProcessor initialized successfully")
        
        # Test URL validation
        assert processor.is_valid_url("https://example.com/article")
        assert not processor.is_valid_url("not-a-url")
        print("✅ URL validation working")
        
    except Exception as e:
        print(f"❌ ArticleProcessor test failed: {e}")
        return False
    
    return True

def test_directory_model():
    """Test DirectoryEntry model with article support."""
    print("\n🧪 Testing directory model...")
    
    try:
        from models.directory import DirectoryEntry, ContentType
        
        # Test model creation
        entry = DirectoryEntry(
            title="Test Article",
            source_url="https://example.com/test",
            content_type=ContentType.ARTICLE,
            word_count=500,
            reading_time_minutes=3
        )
        
        assert entry.is_article
        assert not entry.is_video
        assert entry.display_url == "https://example.com/test"
        
        print("✅ DirectoryEntry model with article support working")
        
    except Exception as e:
        print(f"❌ Directory model test failed: {e}")
        return False
    
    return True

def test_api_imports():
    """Test that updated API modules import correctly."""
    print("\n🧪 Testing API imports...")
    
    try:
        from api.process import ArticleJobCreate, BatchArticleJobCreate
        from api.directory import router
        
        # Test schema validation
        article_job = ArticleJobCreate(
            article_url="https://example.com/article",
            email="test@example.com"
        )
        assert str(article_job.article_url) == "https://example.com/article"
        
        print("✅ API imports and schemas working")
        
    except Exception as e:
        print(f"❌ API import test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Testing VideoMind AI article support...\n")
    
    tests = [
        test_directory_model,
        test_article_processor,
        test_api_imports
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Article support is ready to use.")
        print("\n📝 To use article support:")
        print("1. Run: pip3 install beautifulsoup4 lxml")
        print("2. Restart your VideoMind AI server")
        print("3. Submit articles via the new form on the homepage")
        print("4. Filter by content type in the directory")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)