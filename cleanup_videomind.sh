#!/bin/bash
# VideoMind AI Codebase Cleanup Script
# Removes outdated files from other projects

cd ~/.openclaw/workspace

echo "🧹 Cleaning up VideoMind AI codebase..."

# Milwaukee Transport Directory (completed project)
echo "Removing Milwaukee Transport files..."
rm -f milwaukee-transport-directory.md
rm -f Milwaukee-Companies-Research.md
rm -f Milwaukee-Transport-Directory-Template.csv
rm -f Milwaukee-Transportation-Outreach-Email.md

# Hunting Directory (abandoned project)
echo "Removing Hunting Directory files..."
rm -f hunting_advertiser_contacts.md

# Notion integration scripts (outdated)
echo "Removing old Notion scripts..."
rm -f notion-directory-builder-fixed.py
rm -f notion-directory-builder.py
rm -f notion-directory-final.py
rm -f notion_insert.py
rm -f fix_notion.py

# Google Sheets scripts (not used)
echo "Removing unused Google Sheets files..."
rm -f google-sheets-builder.py
rm -f sheets-templates.md

# Lead tracking templates (not used)
echo "Removing unused templates..."
rm -f Lead-Tracking-Template.csv

# Old research and guides
echo "Removing old research files..."
rm -f research_report_2026-02-18.md
rm -f larry_skill_setup_guide.md
rm -f QUICK-SETUP-INSTRUCTIONS.md

# Completed OpenClaw tool routing work
echo "Removing completed OpenClaw routing files..."
rm -f GitHub-Issue-Tool-Routing.md
rm -f OpenClaw-Tool-Routing-Feature-Request.md
rm -f OpenClaw-Tool-Routing-Implementation-Plan.md
rm -f openclaw-tool-routing-solution.md

echo "✅ Cleanup complete! VideoMind AI codebase is now focused."

# Stage deletions for git
git add -A

echo "📝 Files staged for deletion. Run 'git commit -m \"cleanup: remove outdated files unrelated to VideoMind AI\"' to commit."