#!/usr/bin/env python3
"""
LinkAce to Hugo Weekly Digest Generator
Fetches latest links from LinkAce, processes with LLM, and generates Hugo content
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from dotenv import load_dotenv
from datetime import timezone

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Link:
    """Represents a LinkAce link"""
    id: int
    url: str
    title: str
    description: str
    created_at: str
    tags: List[str]
    
class LinkAceClient:
    """Client for LinkAce API"""
    
    def __init__(self):
        self.base_url = os.getenv('LINKACE_BASE_URL').rstrip('/')
        self.api_key = os.getenv('LINKACE_API_KEY')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_weekly_links(self, list_id: int) -> List[Link]:
        """Fetch links from specified list from the past week"""
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        url = f"{self.base_url}/api/v2/lists/{list_id}/links"
        params = {
            'per_page': 100,  # Adjust based on your needs
            'order_by': 'created_at',
            'order_dir': 'desc'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            links = []
            for link_data in data.get('data', []):
                # Parse LinkAce datetime with timezone awareness
                created_at = datetime.fromisoformat(link_data['created_at'].replace('Z', '+00:00')).replace(tzinfo=timezone.utc)

                # Filter for links from the past week
                if created_at >= one_week_ago:
                    tags = [tag['name'] for tag in link_data.get('tags', [])]
                    links.append(Link(
                        id=link_data['id'],
                        url=link_data['url'],
                        title=link_data['title'],
                        description=link_data.get('description', ''),
                        created_at=link_data['created_at'],
                        tags=tags
                    ))
            
            logger.info(f"Found {len(links)} links from the past week in list {list_id}")
            return links
            
        except requests.RequestException as e:
            logger.error(f"Error fetching links from LinkAce: {e}")
            return []

class OpenRouterClient:
    """Client for OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        self.model = os.getenv('OPENROUTER_MODEL')

    def call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Call OpenRouter LLM with comprehensive error handling"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert content curator and technical writer."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 2048,
            "top_p": 0.95
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            # Added response structure validation
            result = response.json()
            if 'choices' not in result or len(result['choices']) == 0:
                raise ValueError("Empty choices in API response")

            # Fixed nested structure access
            content = result['choices'][0]['message']['content']
            if not content.strip():
                raise ValueError("Empty content in LLM response")

            return content

        except requests.RequestException as e:
            logger.error(f"API Request failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"HTTP {e.response.status_code} Response: {e.response.text[:200]}")
            return ""

        except KeyError as e:
            logger.error(f"Malformed API response - missing key: {str(e)}")
            logger.debug(f"Full response: {json.dumps(result, indent=2)}")
            return ""

        except ValueError as e:
            logger.error(f"Content validation error: {str(e)}")
            return ""

        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__} - {str(e)}")
            logger.debug("Traceback:", exc_info=True)
            return ""


class ContentProcessor:
    """Processes links and generates structured content"""
    
    def __init__(self):
        self.openrouter = OpenRouterClient()
    
    def structure_links(self, links: List[Link]) -> str:
        """Structure links using LLM with optimization techniques"""
        
        # Prepare structured input for the LLM
        links_text = "\n".join([
            f"**{link.title}**\n"
            f"URL: {link.url}\n"
            f"Description: {link.description}\n"
            f"Tags: {', '.join(link.tags)}\n"
            f"Date: {link.created_at}\n---\n"
            for link in links
        ])
        
        # Optimized prompt based on best practices from search results
        prompt = f"""
        Create a well-structured weekly digest from these {len(links)} links I've saved this week.

        LINKS DATA:
        {links_text}

        REQUIREMENTS:
        1. Restructure the links as a easy to read list
        2. write a general 300 words description of the week activity
        3. Provide brief, insightful summaries inside the general description
        4. each link must come from from LINKS_DATA
        5. Use proper markdown formatting with headers, lists, and emphasis
        6. Make it SEO-friendly with good structure
        7. Keep tone professional but engaging, you have 20+ years experience of url link curation
        8. Suggest relevant tags for the post
        9. DO NOT create links not available in LINKS_DATA

        FORMAT:
        - Use bullet points or numbered lists for links
        - Footer includes following links:
          - shared.girard-davila.net linkace instance with stored links
          - github.com/alx/weekly_news github repository of the code used to generate this newsletter

        Make this content publication-ready for a technical blog.
        """
        llm_response = self.openrouter.call_llm(prompt, temperature=0.7)
        return llm_response
    
    def get_editor_feedback(self, content: str) -> str:
        """Simulate editor review process"""
        print("\n" + "="*80)
        print("EDITOR REVIEW PHASE")
        print("="*80)
        print("\nGenerated content:")
        print("-"*40)
        print(content)
        print("-"*40)
        
        feedback = input("\nEditor feedback (press Enter for no changes, or provide feedback): ").strip()
        return feedback if feedback else "Content approved as-is"
    
    def polish_content(self, content: str, feedback: str) -> str:
        """Polish content based on editor feedback"""
        if feedback == "Content approved as-is":
            return content
            
        polish_prompt = f"""
        Original content:
        {content}

        Editor feedback:
        {feedback}

        Please revise the content based on the editor's feedback while maintaining:
        - Proper markdown formatting
        - SEO-friendly structure  
        - Engaging tone
        - Technical accuracy
        - 20+ years of link curation experience
        - Best source of insightful links in multiple social circles
        - People look for value, give them best value

        Return the polished version.
        """
        
        return self.openrouter.call_llm(polish_prompt, temperature=0.5)

class HugoContentGenerator:
    """Generates Hugo-compatible markdown files"""
    
    def __init__(self):
        self.content_path = Path(os.getenv('HUGO_CONTENT_PATH', './content/posts'))
        self.content_path.mkdir(parents=True, exist_ok=True)
        
    def generate_frontmatter(self, title: str, tags: List[str]) -> str:
        """Generate Hugo front matter"""
        now = datetime.now()
        
        frontmatter = f"""---
title: "{title}"
date: {now.strftime('%Y-%m-%dT%H:%M:%S%z')}
draft: false
description: "Weekly curated links and insights from my reading list"
categories: ["Weekly Digest", "Curated Links"]
tags: {json.dumps(tags)}
author: "{os.getenv('EDITOR_NAME', 'Editor')}"
---

"""
        return frontmatter
    
    def save_content(self, content: str, links_count: int) -> str:
        """Save content as Hugo markdown file"""
        # Extract title and tags from content if possible
        lines = content.split('\n')
        title = f"Weekly Links Digest - Week of {datetime.now().strftime('%B %d, %Y')}"
        
        # Try to extract tags from content
        tags = ["weekly-digest", "curated-links", "reading-list"]
        
        # Generate filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename_prefix = os.getenv('OUTPUT_FILENAME_PREFIX', 'weekly-links')
        filename = f"{date_str}-{filename_prefix}.md"
        filepath = self.content_path / filename
        
        # Combine frontmatter and content
        frontmatter = self.generate_frontmatter(title, tags)
        
        # Add metadata at the top of content
        meta_content = f"""
*This week I discovered {links_count} interesting links. Here's what caught my attention:*

{content}

---
*This digest was automatically generated from my [LinkAce](https://linkace.org) bookmark collection and curated with AI assistance.*
"""
        
        full_content = frontmatter + meta_content
        
        # Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        logger.info(f"Hugo content saved to: {filepath}")
        return str(filepath)

def main():
    """Main workflow execution"""
    try:
        # Initialize clients
        linkace = LinkAceClient()
        processor = ContentProcessor()
        hugo_generator = HugoContentGenerator()
        
        # Get target list ID
        list_id = int(os.getenv('TARGET_LIST_ID', '1'))
        
        print(f"🔗 Fetching weekly links from LinkAce list {list_id}...")
        links = linkace.get_weekly_links(list_id)
        
        if not links:
            print("❌ No links found for this week")
            return
            
        print(f"✅ Found {len(links)} links from this week")
        
        print("🤖 Structuring content with AI...")
        structured_content = processor.structure_links(links)
        
        if not structured_content:
            print("❌ Failed to generate structured content")
            return
            
        print("✏️ Starting editor review...")
        feedback = processor.get_editor_feedback(structured_content)
        
        print("✨ Polishing content...")
        final_content = processor.polish_content(structured_content, feedback)
        
        print("📝 Generating Hugo markdown file...")
        output_file = hugo_generator.save_content(final_content, len(links))
        
        print(f"🎉 Complete! Hugo content ready at: {output_file}")
        print(f"💡 Run 'hugo server' in your Hugo directory to preview")
        
    except Exception as e:
        logger.error(f"Error in main workflow: {e}")
        raise

if __name__ == "__main__":
    main()

