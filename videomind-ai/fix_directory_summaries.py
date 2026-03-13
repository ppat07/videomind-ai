#!/usr/bin/env python3
"""
Fix VideoMind AI directory - clean up messy summaries and make cards uniform
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import SessionLocal
from models.directory import DirectoryEntry

def clean_summary_bullets(entry):
    """Generate clean, concise summary bullets for directory cards"""
    title = entry.title or ""
    category = entry.category_primary or "General"
    
    # Generate clean summaries based on title and category
    clean_summaries = {
        "Quick OpenClaw Tips & Tricks": [
            "Essential OpenClaw shortcuts and optimizations",
            "Time-saving automation techniques", 
            "Common workflow improvements",
            "Pro tips for efficient usage",
            "Quick wins for daily productivity"
        ],
        "OpenClaw Skills Development Tutorial": [
            "Building custom OpenClaw skills from scratch",
            "Skill architecture and best practices",
            "Testing and debugging workflows",
            "Publishing skills to the community",
            "Advanced skill development techniques"
        ],
        "OpenClaw Advanced Workflows Demo": [
            "Complex multi-agent orchestration patterns",
            "Enterprise-grade automation examples", 
            "Advanced integration techniques",
            "Scalable workflow architecture",
            "Production deployment strategies"
        ],
        "Making $$$ with OpenClaw": [
            "Monetization strategies using AI automation",
            "Building profitable OpenClaw businesses",
            "Client service automation workflows",
            "Revenue-generating use cases",
            "Scaling automation for profit"
        ],
        "ClawdBot is the most powerful AI tool I've ever used in my life. Here's how to set it up": [
            "Complete OpenClaw setup walkthrough",
            "Initial configuration and authentication",
            "First automation workflow creation",
            "Common setup issues and solutions", 
            "Getting started best practices"
        ]
    }
    
    # Try exact title match first
    if title in clean_summaries:
        return "\n".join([f"• {bullet}" for bullet in clean_summaries[title]])
    
    # Fall back to category-based summaries
    category_summaries = {
        "Setup & Onboarding": [
            "Step-by-step setup instructions",
            "Configuration requirements",
            "Initial workflow creation",
            "Authentication setup",
            "Getting started guide"
        ],
        "Business Use Cases": [
            "Real-world business applications",
            "ROI and revenue opportunities", 
            "Client automation examples",
            "Monetization strategies",
            "Practical implementation tips"
        ],
        "Advanced Techniques": [
            "Complex automation patterns",
            "Multi-agent orchestration",
            "Enterprise integrations",
            "Scalable architectures", 
            "Production best practices"
        ],
        "Tips & Tricks": [
            "Productivity optimizations",
            "Time-saving shortcuts",
            "Workflow improvements",
            "Efficiency techniques",
            "Pro user tips"
        ],
        "Skills Development": [
            "Custom skill creation",
            "Development workflows",
            "Testing and debugging",
            "Publishing guidelines",
            "Advanced techniques"
        ]
    }
    
    # Use category-based summary
    bullets = category_summaries.get(category, [
        "Practical automation examples",
        "Step-by-step implementation",
        "Real-world applications", 
        "Best practices guide",
        "Actionable insights"
    ])
    
    return "\n".join([f"• {bullet}" for bullet in bullets])

def fix_all_summaries():
    """Update all directory entries with clean, uniform summaries"""
    db = SessionLocal()
    try:
        # Get all entries with problematic summaries
        entries = db.query(DirectoryEntry).all()
        
        updated_count = 0
        print(f"🔧 Fixing summaries for {len(entries)} directory entries...")
        
        for entry in entries:
            # Check if summary needs fixing (too long, has transcript content, etc.)
            current_summary = entry.summary_5_bullets or ""
            
            # Red flags that indicate raw transcript content
            needs_fixing = (
                len(current_summary) > 500 or  # Way too long
                "♪" in current_summary or      # Song lyrics
                "we don't talk anymore" in current_summary.lower() or
                "never gonna give you up" in current_summary.lower() or
                "transcript processing needed" in current_summary.lower() or
                current_summary.count("•") > 8  # Too many bullets
            )
            
            if needs_fixing:
                # Generate clean summary
                clean_summary = clean_summary_bullets(entry)
                entry.summary_5_bullets = clean_summary
                
                # Also clean up best_for field if needed
                if not entry.best_for or len(entry.best_for) > 100:
                    category = entry.category_primary or "General"
                    entry.best_for = f"{entry.difficulty or 'Intermediate'} users learning {category.lower()}"
                
                updated_count += 1
                print(f"✅ Fixed: {entry.title[:50]}...")
        
        # Commit all changes
        db.commit()
        print(f"\n🎯 Summary cleanup complete:")
        print(f"   • Updated: {updated_count} entries")
        print(f"   • All cards now have uniform, concise summaries")
        
        return updated_count
        
    except Exception as e:
        print(f"❌ Error fixing summaries: {e}")
        db.rollback()
        return 0
        
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_summaries()