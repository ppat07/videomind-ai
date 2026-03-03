#!/usr/bin/env python3
"""
Directory Quality Enhancement System
Improves existing entries with better categorization and metadata
"""

import requests
import json
import time

BASE_URL = "https://www.videomind-ai.com"

def get_all_directory_entries():
    """Fetch all directory entries to analyze and enhance."""
    try:
        url = f"{BASE_URL}/api/directory"
        response = requests.get(url, params={"limit": 100}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        else:
            print(f"Failed to fetch directory: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error fetching directory: {e}")
        return []

def analyze_content_quality(entries):
    """Analyze existing content for quality improvements."""
    print("📊 DIRECTORY QUALITY ANALYSIS")
    print("=" * 50)
    
    total = len(entries)
    categories = {}
    difficulties = {}
    tools = {}
    creators = {}
    
    for entry in entries:
        # Category analysis
        cat = entry.get("category_primary", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
        
        # Difficulty analysis
        diff = entry.get("difficulty", "Unknown")
        difficulties[diff] = difficulties.get(diff, 0) + 1
        
        # Creator analysis
        creator = entry.get("creator_name", "Unknown")
        creators[creator] = creators.get(creator, 0) + 1
        
        # Tools mentioned
        tools_str = entry.get("tools_mentioned", "")
        if tools_str:
            for tool in tools_str.split(", "):
                tool = tool.strip()
                if tool:
                    tools[tool] = tools.get(tool, 0) + 1
    
    print(f"📈 Total entries: {total}")
    print(f"\n📂 Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {cat}: {count}")
    
    print(f"\n🎯 Difficulty levels:")
    for diff, count in sorted(difficulties.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {diff}: {count}")
    
    print(f"\n👥 Top creators:")
    for creator, count in sorted(creators.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • {creator}: {count}")
    
    print(f"\n🛠️ Top tools mentioned:")
    for tool, count in sorted(tools.items(), key=lambda x: x[1], reverse=True)[:15]:
        if len(tool) > 3:  # Filter out very short tool names
            print(f"  • {tool}: {count}")
    
    return {
        "total": total,
        "categories": categories,
        "difficulties": difficulties,
        "tools": tools,
        "creators": creators
    }

def main():
    """Main analysis execution."""
    print("🔍 VideoMind AI - Directory Quality Enhancement")
    print("=" * 60)
    print("Analyzing current content for improvement opportunities...")
    
    # Fetch and analyze current directory
    entries = get_all_directory_entries()
    
    if not entries:
        print("❌ Could not fetch directory entries.")
        return
    
    analysis = analyze_content_quality(entries)
    
    # Generate recommendations
    print("\n💡 IMPROVEMENT RECOMMENDATIONS")
    print("=" * 50)
    
    # Category balance recommendations
    total = analysis["total"]
    categories = analysis["categories"]
    
    if categories.get("General Content", 0) / total > 0.3:
        print("🎯 HIGH PRIORITY: Reduce 'General Content' ratio")
        print("   • Add more specific technical/business content")
        print("   • Focus on practical automation workflows")
    
    if categories.get("Setup & Onboarding", 0) / total < 0.2:
        print("📚 MEDIUM PRIORITY: Add more setup/onboarding content")
        print("   • New user tutorials")
        print("   • Getting started guides")
    
    if categories.get("Business Use Cases", 0) / total < 0.3:
        print("💼 HIGH PRIORITY: Add more business-focused content")
        print("   • Revenue generation workflows")
        print("   • Lead generation automation")
        print("   • Sales process automation")
    
    # Content gap analysis
    gaps = []
    ideal_categories = [
        "OpenClaw Workflows", "Business Automation", "Content Creation",
        "Lead Generation", "Sales Automation", "API Integration",
        "Financial Automation", "Marketing Automation"
    ]
    
    for ideal_cat in ideal_categories:
        if ideal_cat not in categories:
            gaps.append(ideal_cat)
    
    if gaps:
        print(f"\n🔍 CONTENT GAPS IDENTIFIED:")
        for gap in gaps:
            print(f"   • Missing: {gap}")
    
    # Quality score calculation
    quality_score = 0
    quality_factors = []
    
    # Diversity bonus
    if len(categories) >= 8:
        quality_score += 25
        quality_factors.append("✅ Good category diversity")
    else:
        quality_factors.append("❌ Limited category diversity")
    
    # Business focus bonus
    business_ratio = (categories.get("Business Use Cases", 0) + 
                     categories.get("Business Automation", 0)) / total
    if business_ratio >= 0.3:
        quality_score += 25
        quality_factors.append("✅ Strong business focus")
    else:
        quality_factors.append("❌ Weak business focus")
    
    # Technical depth bonus
    tech_categories = ["API Integration", "Programming", "Development", "Advanced Workflows"]
    tech_count = sum(categories.get(cat, 0) for cat in tech_categories)
    if tech_count >= total * 0.2:
        quality_score += 25
        quality_factors.append("✅ Good technical depth")
    else:
        quality_factors.append("❌ Limited technical content")
    
    # Volume bonus
    if total >= 100:
        quality_score += 25
        quality_factors.append("✅ Excellent content volume")
    elif total >= 50:
        quality_score += 15
        quality_factors.append("⚠️ Good content volume")
    else:
        quality_factors.append("❌ Low content volume")
    
    print(f"\n📊 DIRECTORY QUALITY SCORE: {quality_score}/100")
    print("Quality factors:")
    for factor in quality_factors:
        print(f"  {factor}")
    
    # Action plan
    print(f"\n🚀 ACTIONABLE NEXT STEPS")
    print("=" * 50)
    
    if quality_score >= 75:
        print("🏆 EXCELLENT: Focus on content promotion and user acquisition")
        print("• Launch marketing campaigns")
        print("• Optimize SEO and discoverability") 
        print("• Add premium content tiers")
    elif quality_score >= 50:
        print("📈 GOOD: Continue content expansion with quality focus")
        print("• Fill identified content gaps")
        print("• Add more business-focused videos")
        print("• Improve categorization accuracy")
    else:
        print("⚠️ NEEDS IMPROVEMENT: Major content expansion required")
        print("• Scale to 100+ videos immediately")
        print("• Focus on business automation content")
        print("• Add comprehensive tutorial series")
    
    print(f"\n✅ Quality analysis complete!")
    print(f"📊 Directory ready for: {analysis['total']} video AI training workflows")

if __name__ == "__main__":
    main()