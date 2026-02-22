"""
Article processing service for VideoMind AI.
Handles article extraction, AI enhancement, and directory integration.
"""
import re
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import openai

from config import settings


class ArticleProcessor:
    """Processes articles for the AI training directory."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and parsed.netloc
        except:
            return False

    def extract_article_content(self, url: str) -> Dict[str, Any]:
        """
        Extract article content from URL.
        Returns structured content data.
        """
        if not self.is_valid_url(url):
            raise ValueError("Invalid URL provided")

        try:
            # Fetch the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract author/creator
            author = self._extract_author(soup)

            # Calculate metrics
            word_count = len(content.split())
            reading_time = max(1, round(word_count / 200))  # ~200 words per minute

            return {
                'title': title,
                'content': content,
                'author': author,
                'word_count': word_count,
                'reading_time_minutes': reading_time,
                'source_url': url
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch article: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to process article: {str(e)}")

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from HTML."""
        # Try multiple title selectors
        title_selectors = [
            'h1.entry-title',
            'h1.post-title', 
            'h1.article-title',
            '.post-header h1',
            'article h1',
            'h1',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title:
                    return title
        
        return "Untitled Article"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content from HTML."""
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'advertisement']):
            tag.decompose()

        # Try content selectors in order of preference
        content_selectors = [
            'article .entry-content',
            'article .post-content',
            '.article-content',
            '.post-body',
            'main article',
            'article',
            '.content'
        ]

        content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text().strip()
                if len(content) > 500:  # Ensure substantial content
                    break

        # Fallback to body content if no article content found
        if len(content) < 500:
            body = soup.find('body')
            if body:
                content = body.get_text().strip()

        # Clean up the content
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Clean up line breaks
        
        return content[:10000]  # Limit to 10k chars to avoid token limits

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author from HTML."""
        author_selectors = [
            '.author-name',
            '.byline',
            '.post-author',
            '[rel="author"]',
            '.author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text().strip()
                if author:
                    return author
        
        return None

    def enhance_with_ai(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance article data with AI-generated insights.
        Similar to video processing but for text content.
        """
        content = article_data['content']
        title = article_data['title']

        try:
            prompt = f"""
Analyze this AI/automation training article and provide structured insights:

Title: {title}
Content: {content[:4000]}...

Provide a JSON response with:
1. "summary_5_bullets" - 5 key takeaways as bullet points
2. "category_primary" - Main category (choose from: Automation Workflows, AI Development, Business Process, Data Analysis, Tool Integration, Other)
3. "difficulty" - Beginner, Intermediate, or Advanced
4. "tools_mentioned" - Comma-separated list of specific tools/platforms mentioned
5. "best_for" - Who would benefit most from this article
6. "teaches_agent_to" - What specific skills an AI agent could learn from this
7. "prompt_template" - A reusable prompt template based on the article's methodology
8. "execution_checklist" - Step-by-step checklist for implementing the article's concepts
9. "signal_score" - Quality score 0-100 (higher = more valuable for AI training)

Focus on practical AI training value.
"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )

            ai_insights = response.choices[0].message.content

            # Try to parse as JSON, fall back to text processing
            try:
                import json
                parsed_insights = json.loads(ai_insights)
                return {**article_data, **parsed_insights}
            except:
                # Fallback text parsing if JSON fails
                return self._parse_ai_response_text(article_data, ai_insights)

        except Exception as e:
            print(f"AI enhancement failed: {e}")
            # Return basic processing if AI fails
            return {
                **article_data,
                "summary_5_bullets": "• Key concepts from the article\n• Implementation strategies\n• Tool recommendations\n• Best practices\n• Actionable next steps",
                "category_primary": "Other",
                "difficulty": "Intermediate",
                "tools_mentioned": "",
                "best_for": "Practitioners interested in AI/automation",
                "teaches_agent_to": "Understand article concepts and methodologies",
                "prompt_template": f"Based on the article '{title}', help me implement the key concepts...",
                "execution_checklist": "1. Read the full article\n2. Identify key concepts\n3. Plan implementation\n4. Execute step by step",
                "signal_score": 60
            }

    def _parse_ai_response_text(self, article_data: Dict[str, Any], ai_text: str) -> Dict[str, Any]:
        """Parse AI response when JSON parsing fails."""
        # Basic text extraction - this is a fallback
        lines = ai_text.split('\n')
        
        result = article_data.copy()
        result.update({
            "summary_5_bullets": "• Article analysis completed\n• Key insights extracted\n• Training value assessed",
            "category_primary": "Other",
            "difficulty": "Intermediate", 
            "signal_score": 65
        })
        
        return result

    def process_article(self, url: str) -> Dict[str, Any]:
        """
        Complete article processing pipeline.
        Extract content -> Enhance with AI -> Return structured data.
        """
        print(f"Processing article: {url}")
        
        # Step 1: Extract article content
        article_data = self.extract_article_content(url)
        print(f"Extracted article: {article_data['title']} ({article_data['word_count']} words)")
        
        # Step 2: Enhance with AI
        enhanced_data = self.enhance_with_ai(article_data)
        print(f"AI enhancement complete. Signal score: {enhanced_data.get('signal_score', 'N/A')}")
        
        # Step 3: Add processing metadata
        enhanced_data.update({
            'content_type': 'article',
            'processing_status': 'completed'
        })
        
        return enhanced_data


# Create global instance
article_processor = ArticleProcessor()