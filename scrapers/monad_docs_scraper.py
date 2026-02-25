"""Official Monad documentation scraper."""

import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class MonadDocsScraper:
    """Scraper for official Monad documentation."""
    
    BASE_URL = "https://docs.monad.xyz"
    
    SECTIONS = [
        "/consensus",
        "/architecture",
        "/monadbft",
        "/validators",
        "/performance",
        "/technical-specs",
    ]
    
    def __init__(self, data_dir: str = "data/monad_docs"):
        """Initialize Monad docs scraper."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MonadBFT-Research-Aggregator/1.0'
        })
        self.scraped_urls = set()
    
    def scrape_all_docs(self) -> List[Dict]:
        """Scrape all documentation sections.
        
        Returns:
            List of documentation page data
        """
        logger.info(f"Scraping Monad documentation: {self.BASE_URL}")
        
        all_docs = []
        
        # Scrape each section
        for section in self.SECTIONS:
            url = f"{self.BASE_URL}{section}"
            docs = self._scrape_section(url)
            all_docs.extend(docs)
        
        # Recursively scrape linked pages
        additional_docs = self._scrape_linked_pages(all_docs)
        all_docs.extend(additional_docs)
        
        logger.info(f"Scraped {len(all_docs)} documentation pages")
        return all_docs
    
    def scrape_consensus_docs(self) -> List[Dict]:
        """Scrape consensus-specific documentation.
        
        Returns:
            List of consensus documentation data
        """
        url = f"{self.BASE_URL}/consensus"
        return self._scrape_section(url)
    
    def scrape_monadbft_specs(self) -> Dict:
        """Scrape MonadBFT technical specifications.
        
        Returns:
            MonadBFT specification data
        """
        url = f"{self.BASE_URL}/monadbft"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract specification sections
            specs = {
                'url': url,
                'title': self._extract_title(soup),
                'overview': self._extract_section(soup, 'overview'),
                'protocol_details': self._extract_section(soup, 'protocol'),
                'message_types': self._extract_section(soup, 'messages'),
                'safety_guarantees': self._extract_section(soup, 'safety'),
                'liveness_guarantees': self._extract_section(soup, 'liveness'),
                'performance_characteristics': self._extract_section(soup, 'performance'),
                'comparison': self._extract_section(soup, 'comparison'),
                'scraped_at': datetime.now().isoformat(),
            }
            
            return specs
            
        except Exception as e:
            logger.error(f"Error scraping MonadBFT specs: {e}")
            return {}
    
    def _scrape_section(self, url: str) -> List[Dict]:
        """Scrape a documentation section."""
        if url in self.scraped_urls:
            return []
        
        self.scraped_urls.add(url)
        docs = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            doc_data = {
                'url': url,
                'title': self._extract_title(soup),
                'content': self._extract_content(soup),
                'sections': self._extract_sections(soup),
                'code_examples': self._extract_code_examples(soup),
                'links': self._extract_links(soup),
                'source': 'monad_docs',
                'scraped_at': datetime.now().isoformat(),
            }
            
            docs.append(doc_data)
            
        except Exception as e:
            logger.warning(f"Error scraping {url}: {e}")
        
        return docs
    
    def _scrape_linked_pages(self, docs: List[Dict], max_depth: int = 2) -> List[Dict]:
        """Recursively scrape linked documentation pages."""
        additional_docs = []
        
        for doc in docs:
            links = doc.get('links', [])
            
            for link in links:
                # Only scrape internal documentation links
                if link.startswith(self.BASE_URL) and link not in self.scraped_urls:
                    linked_docs = self._scrape_section(link)
                    additional_docs.extend(linked_docs)
        
        return additional_docs
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_elem = soup.find('h1')
        return title_elem.get_text(strip=True) if title_elem else "Unknown"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content text."""
        content_elem = soup.find('article') or soup.find('main') or soup.find('body')
        return content_elem.get_text(strip=True) if content_elem else ""
    
    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract document sections with headings."""
        sections = []
        
        for heading in soup.find_all(['h2', 'h3']):
            section = {
                'level': heading.name,
                'title': heading.get_text(strip=True),
                'content': ''
            }
            
            # Get content until next heading
            content_parts = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                content_parts.append(sibling.get_text(strip=True))
            
            section['content'] = '\n'.join(content_parts)
            sections.append(section)
        
        return sections
    
    def _extract_code_examples(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract code examples from the page."""
        examples = []
        
        for code_block in soup.find_all(['pre', 'code']):
            # Get language if specified
            language = None
            if 'class' in code_block.attrs:
                for cls in code_block['class']:
                    if cls.startswith('language-'):
                        language = cls.replace('language-', '')
            
            examples.append({
                'language': language,
                'code': code_block.get_text(strip=True)
            })
        
        return examples
    
    def _extract_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract all internal documentation links."""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(self.BASE_URL, href)
            
            # Only include internal docs links
            if urlparse(full_url).netloc == urlparse(self.BASE_URL).netloc:
                links.append(full_url)
        
        return list(set(links))
    
    def _extract_section(self, soup: BeautifulSoup, section_id: str) -> str:
        """Extract a specific section by ID or heading text."""
        # Try to find by ID
        section = soup.find(id=section_id)
        if section:
            return section.get_text(strip=True)
        
        # Try to find by heading text
        for heading in soup.find_all(['h2', 'h3']):
            if section_id.lower() in heading.get_text().lower():
                content_parts = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3']:
                        break
                    content_parts.append(sibling.get_text(strip=True))
                return '\n'.join(content_parts)
        
        return ""
    
    def save_docs(self, docs: List[Dict], filename: str = "monad_docs.json"):
        """Save scraped documentation to JSON file."""
        output_path = self.data_dir / filename
        with open(output_path, 'w') as f:
            json.dump(docs, f, indent=2)
        logger.info(f"Saved {len(docs)} docs to {output_path}")