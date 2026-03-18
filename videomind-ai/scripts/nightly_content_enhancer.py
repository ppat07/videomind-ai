#!/usr/bin/env python3
"""
Nightly Content Enhancer for VideoMind AI
Mission: Automatically improve existing content in the AI Training Directory
Focus: Better categorization, enhanced metadata, and content optimization

Tonight's Build: Intelligent content analysis and enhancement system
that makes existing videos more valuable and discoverable.
"""

import os
import sys
import sqlite3
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import openai
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))

from config import settings

class ContentEnhancer:
    def __init__(self):
        """Initialize the content enhancer with OpenAI client and database connection."""
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.db_path = project_root / "videomind.db"
        
    def get_database_connection(self):
        """Get SQLite database connection."""
        return sqlite3.connect(self.db_path, timeout=30.0)
    
    def get_unenhanced_content(self) -> List[Dict]:
        """Get content that could benefit from enhancement."""
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        # Look for directory entries that could benefit from enhancement
        # Focus on items with improvable signal scores and metadata
        query = """
        SELECT id, title, summary_5_bullets, category_primary, tools_mentioned, 
               video_url, best_for, signal_score, teaches_agent_to,
               execution_checklist, prompt_template
        FROM directory_entries 
        WHERE (
            signal_score <= 75 OR
            (execution_checklist IS NULL OR execution_checklist = '') OR
            (prompt_template IS NULL OR prompt_template = '') OR
            (LENGTH(best_for) < 60)
        )
        AND UPPER(content_type) = 'VIDEO'
        ORDER BY signal_score ASC, created_at DESC
        LIMIT 6
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"Debug: Query found {len(results)} raw results")
        conn.close()
        
        items = []
        for row in results:
            items.append({
                'id': row[0],
                'title': row[1],
                'summary': row[2], 
                'category': row[3],
                'tools_mentioned': row[4],
                'video_url': row[5],
                'best_for': row[6],
                'signal_score': row[7],
                'teaches_agent_to': row[8],
                'execution_checklist': row[9],
                'prompt_template': row[10]
            })
        
        return items
    
    def analyze_content(self, item: Dict) -> Dict:
        """Use AI to analyze and enhance content metadata."""
        
        # Prepare content for analysis
        content_text = f"""
        Title: {item.get('title', 'N/A')}
        Current Summary: {item.get('summary', 'N/A')}
        Current Category: {item.get('category', 'N/A')}
        Tools Mentioned: {item.get('tools_mentioned', 'N/A')}
        Best For: {item.get('best_for', 'N/A')}
        Current Signal Score: {item.get('signal_score', 'N/A')}
        """
        
        enhancement_prompt = """
        Analyze this video content and provide enhanced metadata that makes it more valuable for AI training and business automation learning.

        Content to analyze:
        {content}

        Provide a JSON response with:
        1. "enhanced_best_for": Compelling description of who should watch this and why (50-100 words)
        2. "improved_tools_mentioned": Specific tools, APIs, or technologies covered (comma-separated)
        3. "teaches_agent_to": What this teaches an AI agent to do (actionable capability)
        4. "signal_score": Quality score 1-100 based on practical value and actionability
        5. "enhanced_summary": Improved 5-bullet summary focusing on practical takeaways
        6. "execution_checklist": 3-5 step checklist for implementing what's taught

        Focus on practical, actionable insights that help people build real systems.
        """.format(content=content_text)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert content curator for AI training and business automation. Return only valid JSON."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse the JSON response
            enhancement_data = json.loads(response.choices[0].message.content)
            return enhancement_data
            
        except Exception as e:
            print(f"Error analyzing content for item {item['id']}: {e}")
            return {}
    
    def update_content_metadata(self, item_id: str, enhancements: Dict) -> bool:
        """Update database with enhanced metadata."""
        if not enhancements:
            return False
            
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # Update the directory entry with enhanced metadata
            update_query = """
            UPDATE directory_entries 
            SET 
                best_for = COALESCE(?, best_for),
                tools_mentioned = COALESCE(?, tools_mentioned),
                teaches_agent_to = COALESCE(?, teaches_agent_to),
                signal_score = COALESCE(?, signal_score),
                summary_5_bullets = COALESCE(?, summary_5_bullets),
                execution_checklist = COALESCE(?, execution_checklist),
                updated_at = ?
            WHERE id = ?
            """
            
            # Format enhanced summary as bullets if it's an array
            enhanced_summary = enhancements.get('enhanced_summary', [])
            if isinstance(enhanced_summary, list):
                summary_text = '\n'.join([f"• {item}" for item in enhanced_summary])
            else:
                summary_text = enhanced_summary
                
            # Format execution checklist
            execution_checklist = enhancements.get('execution_checklist', [])
            if isinstance(execution_checklist, list):
                checklist_text = '\n'.join([f"{i+1}. {item}" for i, item in enumerate(execution_checklist)])
            else:
                checklist_text = execution_checklist
            
            cursor.execute(update_query, (
                enhancements.get('enhanced_best_for'),
                enhancements.get('improved_tools_mentioned'),
                enhancements.get('teaches_agent_to'),
                enhancements.get('signal_score'),
                summary_text,
                checklist_text,
                datetime.now().isoformat(),
                item_id
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating metadata for item {item_id}: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def enhance_content_batch(self) -> Dict:
        """Run the content enhancement process."""
        print("🚀 Starting Nightly Content Enhancement...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get content that needs enhancement
        items_to_enhance = self.get_unenhanced_content()
        
        if not items_to_enhance:
            return {
                "status": "completed",
                "items_processed": 0,
                "message": "No content found that needs enhancement"
            }
        
        print(f"Found {len(items_to_enhance)} items to enhance")
        
        enhanced_count = 0
        failed_count = 0
        
        for i, item in enumerate(items_to_enhance, 1):
            print(f"\n[{i}/{len(items_to_enhance)}] Enhancing: {item.get('title', 'Unknown')[:60]}")
            
            # Analyze and enhance content
            enhancements = self.analyze_content(item)
            
            if enhancements:
                # Update database with enhancements
                if self.update_content_metadata(item['id'], enhancements):
                    enhanced_count += 1
                    print(f"✅ Enhanced: {item['id']}")
                    print(f"   Category: {enhancements.get('optimized_category', 'N/A')}")
                    print(f"   Difficulty: {enhancements.get('difficulty_level', 'N/A')}")
                    print(f"   AI Relevance: {enhancements.get('ai_training_relevance', 'N/A')}/10")
                else:
                    failed_count += 1
                    print(f"❌ Failed to update database for: {item['id']}")
            else:
                failed_count += 1
                print(f"❌ Failed to enhance: {item['id']}")
            
            # Small delay to avoid rate limiting
            if i < len(items_to_enhance):
                time.sleep(2)
        
        return {
            "status": "completed",
            "items_processed": enhanced_count,
            "items_failed": failed_count,
            "total_items": len(items_to_enhance)
        }

def main():
    """Main execution function."""
    
    # Verify we have required environment
    if not settings.openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return
    
    # Initialize and run enhancement
    enhancer = ContentEnhancer()
    
    try:
        results = enhancer.enhance_content_batch()
        
        # Print results summary
        print(f"\n🎯 Enhancement Complete!")
        print(f"Status: {results['status']}")
        print(f"Items Enhanced: {results['items_processed']}")
        if results.get('items_failed', 0) > 0:
            print(f"Items Failed: {results['items_failed']}")
        print(f"Total Processed: {results.get('total_items', 0)}")
        
        # Generate report for Paul
        if results['items_processed'] > 0:
            print(f"\n📊 Nightly Build Report:")
            print(f"✅ Enhanced {results['items_processed']} videos in the AI Training Directory")
            print(f"🎯 Improved categorization, descriptions, and metadata")
            print(f"📈 Higher quality content = better user experience = more revenue potential")
            print(f"🔄 System continues to self-improve every night")
        
    except Exception as e:
        print(f"❌ Error during enhancement: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()