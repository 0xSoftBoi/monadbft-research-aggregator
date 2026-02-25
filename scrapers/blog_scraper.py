"""Category Labs blog scraper for MonadBFT articles."""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
from pathlib import Path
from datetime import datetime
import re


class CategoryLabsScraper:
    """Scraper for Category Labs blog posts about MonadBFT."""
    
    def __init__(self, data_dir: str = "data/blog_posts"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://blog.monad.xyz"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'
        })
    
    def fetch_post(self, url: str) -> Optional[Dict]:
        """Fetch a single blog post.
        
        Args:
            url: URL of the blog post
            
        Returns:
            Dictionary with post content
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract post data (adapt selectors based on actual site structure)
            post_data = {
                "url": url,
                "title": self._extract_title(soup),
                "author": self._extract_author(soup),
                "date": self._extract_date(soup),
                "content": self._extract_content(soup),
                "tags": self._extract_tags(soup),
                "scraped_at": datetime.now().isoformat()
            }
            
            # Save to file
            filename = self._url_to_filename(url)
            filepath = self.data_dir / f"{filename}.json"
            with open(filepath, 'w') as f:
                json.dump(post_data, f, indent=2)
            
            print(f"✓ Scraped: {post_data['title']}")
            return post_data
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def fetch_all_posts(self, max_posts: int = 50) -> List[Dict]:
        """Fetch all blog posts.
        
        Args:
            max_posts: Maximum number of posts to fetch
            
        Returns:
            List of post dictionaries
        """
        print("Fetching blog post list...")
        
        # This is a template - adapt based on actual blog structure
        post_urls = self._get_post_urls(max_posts)
        
        posts = []
        for url in post_urls[:max_posts]:
            post = self.fetch_post(url)
            if post:
                posts.append(post)
        
        print(f"\n✓ Fetched {len(posts)} posts")
        return posts
    
    def search_posts(self, keyword: str) -> List[Dict]:
        """Search for posts containing a keyword.
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            List of matching posts
        """
        all_posts = self.fetch_all_posts()
        
        matching = []
        for post in all_posts:
            content = post.get('content', '').lower()
            title = post.get('title', '').lower()
            
            if keyword.lower() in content or keyword.lower() in title:
                matching.append(post)
        
        return matching
    
    def _get_post_urls(self, max_posts: int) -> List[str]:
        """Get list of blog post URLs.
        
        Args:
            max_posts: Maximum number of URLs to return
            
        Returns:
            List of post URLs
        """
        # Template implementation - adapt to actual blog structure
        # Common patterns for blogs:
        
        urls = []
        
        # Example: Fetch from main blog page or sitemap
        try:
            response = self.session.get(self.base_url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links (adapt selector)
            article_links = soup.find_all('a', class_=re.compile(r'post|article'))
            
            for link in article_links:
                href = link.get('href')
                if href and not href.startswith('http'):
                    href = self.base_url + href
                if href and href not in urls:
                    urls.append(href)
                    
        except Exception as e:
            print(f"Error fetching post list: {e}")
            # Fallback: return known MonadBFT-related URLs
            urls = self._get_known_monadbft_urls()
        
        return urls[:max_posts]
    
    def _get_known_monadbft_urls(self) -> List[str]:
        """Return known MonadBFT-related blog post URLs."""
        # These would be actual URLs to MonadBFT blog posts
        return [
            f"{self.base_url}/monadbft-introduction",
            f"{self.base_url}/consensus-performance",
            f"{self.base_url}/bft-protocols-comparison",
            # Add more as discovered
        ]
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract post title."""
        # Try common title selectors
        title_elem = (
            soup.find('h1') or 
            soup.find('title') or
            soup.find(class_=re.compile(r'title|heading'))
        )
        return title_elem.get_text().strip() if title_elem else "Unknown Title"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract post author."""
        author_elem = soup.find(class_=re.compile(r'author|byline'))
        return author_elem.get_text().strip() if author_elem else "Category Labs"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date."""
        date_elem = (
            soup.find('time') or
            soup.find(class_=re.compile(r'date|published'))
        )
        if date_elem:
            return date_elem.get('datetime', date_elem.get_text().strip())
        return datetime.now().isoformat()
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content."""
        # Try to find main content area
        content_elem = (
            soup.find('article') or
            soup.find(class_=re.compile(r'content|post-body|entry')) or
            soup.find('main')
        )
        
        if content_elem:
            # Remove script and style elements
            for script in content_elem(['script', 'style']):
                script.decompose()
            return content_elem.get_text(separator='\n').strip()
        
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract post tags."""
        tags = []
        tag_elems = soup.find_all(class_=re.compile(r'tag'))
        for elem in tag_elems:
            tags.append(elem.get_text().strip())
        return tags
    
    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename."""
        # Extract path and convert to filename
        filename = url.split('/')[-1]
        filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
        return filename or 'post'
    
    def generate_index(self) -> str:
        """Generate an index of all scraped posts.
        
        Returns:
            Markdown formatted index
        """
        posts = []
        for filepath in self.data_dir.glob('*.json'):
            with open(filepath, 'r') as f:
                posts.append(json.load(f))
        
        # Sort by date
        posts.sort(key=lambda p: p.get('date', ''), reverse=True)
        
        index = "# Category Labs Blog Posts\n\n"
        for post in posts:
            index += f"## [{post['title']}]({post['url']})\n\n"
            index += f"**Author:** {post['author']}  \n"
            index += f"**Date:** {post['date']}  \n"
            if post.get('tags'):
                index += f"**Tags:** {', '.join(post['tags'])}  \n"
            index += "\n---\n\n"
        
        # Save index
        index_path = self.data_dir / "INDEX.md"
        with open(index_path, 'w') as f:
            f.write(index)
        
        return index


class MonadVizScraper:
    """Scraper for monad-viz demo and visualizations."""
    
    def __init__(self, data_dir: str = "data/visualizations"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_demo_code(self, repo_url: str = "https://github.com/category-labs/monad-viz") -> Dict:
        """Fetch visualization demo code.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Dictionary with demo information
        """
        # This would integrate with GitHub API or clone repo
        print(f"Fetching monad-viz demo from {repo_url}...")
        
        demo_data = {
            "repo_url": repo_url,
            "description": "Interactive MonadBFT consensus visualization",
            "features": [
                "Real-time consensus rounds",
                "Node communication visualization",
                "Fork prevention demonstration",
                "Performance metrics display"
            ],
            "fetched_at": datetime.now().isoformat()
        }
        
        # Save metadata
        filepath = self.data_dir / "monad_viz_info.json"
        with open(filepath, 'w') as f:
            json.dump(demo_data, f, indent=2)
        
        return demo_data


if __name__ == "__main__":
    # Test blog scraper
    blog_scraper = CategoryLabsScraper()
    print("Testing blog scraper...\n")
    
    # Fetch posts
    posts = blog_scraper.fetch_all_posts(max_posts=10)
    
    # Generate index
    index = blog_scraper.generate_index()
    print("\nGenerated blog index")
    
    # Test viz scraper
    viz_scraper = MonadVizScraper()
    demo = viz_scraper.fetch_demo_code()
    print(f"\n✓ Fetched visualization demo info")