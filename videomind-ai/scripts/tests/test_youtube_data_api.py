#!/usr/bin/env python3
"""
Test YouTube Data API integration for VideoMind AI.
"""
import sys
from pathlib import Path
import os

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from services.youtube_data_service import youtube_data_service
from utils.validators import extract_video_id_from_url

def test_youtube_data_api():
    """Test YouTube Data API integration."""
    
    # Test video URL - use a popular tech video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    
    print("🧪 Testing YouTube Data API Integration")
    print(f"📺 Test URL: {test_url}")
    print()
    
    # Check if API is available
    if not youtube_data_service.is_available():
        print("❌ YouTube Data API not configured")
        print("💡 Add YOUTUBE_DATA_API_KEY to your .env file to enable metadata enrichment")
        return False
    
    print("✅ YouTube Data API is configured")
    print()
    
    # Test video ID extraction
    video_id = extract_video_id_from_url(test_url)
    print(f"🆔 Extracted Video ID: {video_id}")
    
    if not video_id:
        print("❌ Could not extract video ID")
        return False
    
    print()
    
    # Test video details
    print("📋 Testing video details retrieval...")
    success, video_data = youtube_data_service.get_video_details(video_id)
    
    if success:
        print("✅ Video details retrieved successfully!")
        print(f"   📺 Title: {video_data['title']}")
        print(f"   👀 Views: {video_data['view_count']:,}")
        print(f"   👍 Likes: {video_data['like_count']:,}")
        print(f"   💬 Comments: {video_data['comment_count']:,}")
        print(f"   ⏰ Duration: {video_data['duration_formatted']}")
        print(f"   📅 Published: {video_data['publish_date_formatted']}")
        print()
    else:
        print(f"❌ Failed to get video details: {video_data.get('error')}")
        return False
    
    # Test channel details if we have channel ID
    channel_id = video_data.get('channel_id')
    if channel_id:
        print("📢 Testing channel details retrieval...")
        success, channel_data = youtube_data_service.get_channel_details(channel_id)
        
        if success:
            print("✅ Channel details retrieved successfully!")
            print(f"   📢 Channel: {channel_data['title']}")
            print(f"   👥 Subscribers: {channel_data['subscriber_count']:,}")
            print(f"   📹 Videos: {channel_data['video_count']:,}")
            print(f"   👀 Channel Views: {channel_data['view_count']:,}")
            print()
        else:
            print(f"⚠️ Could not get channel details: {channel_data.get('error')}")
    
    # Test enriched data
    print("🚀 Testing full metadata enrichment...")
    success, enriched_data = youtube_data_service.get_enriched_video_data(test_url)
    
    if success:
        print("✅ Full metadata enrichment successful!")
        
        video = enriched_data['video']
        channel = enriched_data['channel']
        metrics = enriched_data['engagement_metrics']
        
        print(f"   📊 Engagement Score: {metrics['engagement_score']:.2f}%")
        print(f"   📈 Like Rate: {metrics['like_rate']:.2f}%")
        print(f"   💬 Comment Rate: {metrics['comment_rate']:.2f}%")
        
        if channel:
            print(f"   📺 Views per Subscriber: {metrics['views_per_subscriber']:.1f}")
        
        print(f"   📝 Summary: {enriched_data['formatted_summary']}")
        print()
        
        # Show how this would enhance directory entries
        print("🎯 Enhancement Impact for Directory:")
        print(f"   • Rich metadata: {len(video.get('tags', []))} tags")
        print(f"   • Engagement data: {metrics['engagement_score']:.1f}% score")
        print(f"   • Channel authority: {channel['subscriber_count']:,} subscribers" if channel else "   • Channel authority: Not available")
        print(f"   • Content freshness: {video['publish_date_formatted']}")
        print()
        
        return True
    else:
        print(f"❌ Full enrichment failed: {enriched_data.get('error')}")
        return False


def test_quota_handling():
    """Test quota exceeded handling."""
    print("🧪 Testing API quota handling...")
    
    # Try multiple rapid requests to test quota limits
    test_videos = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style
        "https://www.youtube.com/watch?v=L_jWHffIx5E",  # Smells Like Teen Spirit
    ]
    
    for url in test_videos:
        video_id = extract_video_id_from_url(url)
        if video_id:
            success, data = youtube_data_service.get_video_details(video_id)
            if success:
                print(f"✅ {data['title']} - {data['view_count']:,} views")
            else:
                error = data.get('error', 'Unknown error')
                if 'quota' in error.lower():
                    print(f"⚠️ Quota exceeded: {error}")
                    break
                else:
                    print(f"❌ Error: {error}")


if __name__ == "__main__":
    print("🚀 VideoMind AI - YouTube Data API Test Suite")
    print("=" * 50)
    print()
    
    # Test main functionality
    success = test_youtube_data_api()
    
    if success:
        print("🎉 All tests passed!")
        print("\n💡 YouTube Data API integration is working correctly!")
        print("📊 VideoMind AI will now enrich video metadata with:")
        print("   • Official video statistics")
        print("   • Channel information")
        print("   • Engagement metrics") 
        print("   • Enhanced categorization")
        print("   • Signal scoring improvements")
        print("\nThis will significantly improve the quality of AI training directory entries!")
        
        # Test quota handling
        print("\n" + "=" * 50)
        test_quota_handling()
    else:
        print("❌ Tests failed!")
        print("\n💡 To fix:")
        print("1. Get a YouTube Data API key from Google Cloud Console")
        print("2. Enable YouTube Data API v3")
        print("3. Add YOUTUBE_DATA_API_KEY to your .env file")
        print("4. Restart the application")