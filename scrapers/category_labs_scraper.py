"""Category Labs blog and content scraper."""

import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class CategoryLabsScraper:
    """Scraper for Category Labs blog posts and technical content."""
    
    BLOG_URL = "https://blog.category.xyz"
    MONAD_VIZ_REPO = "https://github.com/category-labs/monad-viz"
    
    def __init__(self, data_dir: str = "data/category_labs"):
        """Initialize Category Labs scraper."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MonadBFT-Research-Aggregator/1.0'
        })
    
    def scrape_blog_posts(
        self, 
        max_posts: int = 50,
        filter_keywords: Optional[List[str]] = None
    ) -> List[Dict]:
        """Scrape blog posts from Category Labs blog.
        
        Args:
            max_posts: Maximum number of posts to scrape
            filter_keywords: Keywords to filter posts (e.g., ['MonadBFT', 'consensus'])
            
        Returns:
            List of blog post data dictionaries
        """
        if filter_keywords is None:
            filter_keywords = ['monadbft', 'consensus', 'bft', 'blockchain']
        
        logger.info(f"Scraping Category Labs blog: {self.BLOG_URL}")
        
        posts = []
        
        try:
            response = self.session.get(self.BLOG_URL, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find blog post links (adjust selectors based on actual site structure)
            post_links = soup.find_all('article') or soup.find_all('div', class_=['post', 'article'])
            
            for post_elem in post_links[:max_posts]:
                post_data = self._extract_post_data(post_elem)
                
                # Filter by keywords
                if self._matches_keywords(post_data, filter_keywords):
                    posts.append(post_data)
            
            logger.info(f"Scraped {len(posts)} blog posts")
            
        except Exception as e:
            logger.error(f"Error scraping blog: {e}")
        
        return posts
    
    def scrape_monad_viz_demo(self) -> Dict:
        """Scrape monad-viz demo repository information.
        
        Returns:
            Repository metadata and demo information
        """
        logger.info("Scraping monad-viz demo repository")
        
        # Note: This would use GitHub API in production
        # For now, returns structure for integration
        return {
            'repo_url': self.MONAD_VIZ_REPO,
            'name': 'monad-viz',
            'description': 'Visual consensus explorer for MonadBFT',
            'features': [
                'Interactive consensus visualization',
                'Block propagation animation',
                'Validator network topology',
                'Real-time finality tracking'
            ],
            'scraped_at': datetime.now().isoformat(),
        }
    
    def get_technical_docs(self) -> List[Dict]:
        """Fetch technical documentation from Category Labs.
        
        Returns:
            List of technical document metadata
        """
        docs = []
        
        # Technical doc URLs (update based on actual structure)
        doc_urls = [
            f"{self.BLOG_URL}/monadbft-overview",
            f"{self.BLOG_URL}/consensus-architecture",
            f"{self.BLOG_URL}/performance-analysis",
        ]
        
        for url in doc_urls:
            try:
                doc_data = self._scrape_technical_doc(url)
                if doc_data:
                    docs.append(doc_data)
            except Exception as e:
                logger.warning(f"Could not fetch {url}: {e}")
        
        return docs
    
    def _extract_post_data(self, post_elem) -> Dict:
        """Extract data from a blog post element."""
        # Extract title
        title_elem = post_elem.find(['h1', 'h2', 'h3'])
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # Extract link
        link_elem = post_elem.find('a', href=True)
        link = link_elem['href'] if link_elem else None
        if link and not link.startswith('http'):
            link = f"{self.BLOG_URL}{link}"
        
        # Extract excerpt/summary
        excerpt_elem = post_elem.find('p')
        excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ""
        
        # Extract date
        date_elem = post_elem.find('time')
        published_date = date_elem.get('datetime') if date_elem else None
        
        return {
            'title': title,
            'url': link,
            'excerpt': excerpt,
            'published_date': published_date,
            'source': 'category_labs_blog',
            'scraped_at': datetime.now().isoformat(),
        }
    
    def _scrape_technical_doc(self, url: str) -> Optional[Dict]:
        """Scrape a technical documentation page."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content
            content_elem = soup.find('article') or soup.find('main')
            if not content_elem:
                return None
            
            return {
                'url': url,
                'title': soup.find('h1').get_text(strip=True) if soup.find('h1') else "Unknown",
                'content': content_elem.get_text(strip=True),
                'html': str(content_elem),
                'source': 'category_labs_docs',
                'scraped_at': datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error scraping technical doc {url}: {e}")
            return None
    
    def _matches_keywords(self, post_data: Dict, keywords: List[str]) -> bool:
        """Check if post matches any of the filter keywords."""
        text = f"{post_data.get('title', '')} {post_data.get('excerpt', '')}".lower()
        return any(keyword.lower() in text for keyword in keywords)
    
    def save_posts(self, posts: List[Dict], filename: str = "blog_posts.json"):
        """Save scraped posts to JSON file."""
        output_path = self.data_dir / filename
        with open(output_path, 'w') as f:
            json.dump(posts, f, indent=2)
        logger.info(f"Saved {len(posts)} posts to {output_path}")