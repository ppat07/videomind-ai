#!/usr/bin/env python3
"""
Simple PDF creator for VideoMind AI Training Data Mastery guide
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import markdown

def create_pdf():
    # Read the markdown content
    with open('products/video-ai-training-data-mastery.md', 'r') as f:
        content = f.read()
    
    # Create PDF document
    pdf_path = 'products/video-ai-training-data-mastery.pdf'
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    
    # Build story
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor='darkblue'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', 
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor='darkblue'
    )
    
    # Split content into sections
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 12))
            continue
            
        if line.startswith('# '):
            # Main title
            story.append(Paragraph(line[2:], title_style))
        elif line.startswith('## '):
            # Subtitle
            story.append(Paragraph(line[3:], subtitle_style))
        elif line.startswith('### '):
            # Sub-subtitle
            story.append(Paragraph(line[4:], styles['Heading3']))
        elif line.startswith('**') and line.endswith('**'):
            # Bold text
            story.append(Paragraph(f"<b>{line[2:-2]}</b>", styles['Normal']))
        elif line.startswith('- ') or line.startswith('* '):
            # Bullet points
            story.append(Paragraph(f"• {line[2:]}", styles['Normal']))
        elif line.startswith('```'):
            # Skip code blocks for now
            continue
        elif line.startswith('---'):
            # Page break
            story.append(PageBreak())
        else:
            # Normal paragraph
            if line:
                story.append(Paragraph(line, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    return pdf_path

if __name__ == "__main__":
    try:
        pdf_path = create_pdf()
        print(f"✅ PDF created successfully: {pdf_path}")
        
        # Check file size
        import os
        size = os.path.getsize(pdf_path)
        print(f"📊 File size: {size:,} bytes ({size/1024:.1f} KB)")
        
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")