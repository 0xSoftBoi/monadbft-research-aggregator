#!/usr/bin/env python3
"""
Web scraper for documentation and blog posts.
"""

import asyncio
import aiohttp
import ipaddress
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from loguru import logger

ALLOWED_DOMAINS = {'monad.xyz', 'github.com', 'arxiv.org', 'x.com', 'twitter.com', 'medium.com', 'docs.monad.xyz'}

def _validate_crawl_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ('https', 'http'):
        raise ValueError(f"Invalid scheme: {parsed.scheme}")
    host = parsed.hostname or ''
    try:
        addr = ipaddress.ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            raise ValueError(f"Private/internal IP not allowed: {host}")
    except ValueError as e:
        if 'Private' in str(e) or 'internal' in str(e):
            raise
        # It's a hostname — check against allowlist
        domain = '.'.join(host.split('.')[-2:])  # get base domain
        if domain not in ALLOWED_DOMAINS and host not in ALLOWED_DOMAINS:
            raise ValueError(f"Domain not in allowlist: {host}")
    return url


class WebScraper:
    """Web scraper for documentation and blog content."""
    
    def __init__(self):
        self.session = None
        self.visited_urls: Set[str] = set()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "MonadBFT-Research-Aggregator"}
            )
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content of a page."""
        await self._ensure_session()
        
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
                
                return await response.text()
        
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_text(self, html: str, selectors: Dict[str, str] = None) -> Dict:
        """Extract text content from HTML."""
        soup = BeautifulSoup(html, 'lxml')
        
        result = {}
        
        if selectors:
            for key, selector in selectors.items():
                element = soup.select_one(selector)
                if element:
                    result[key] = element.get_text(strip=True)
        else:
            # Default extraction
            title = soup.find('title')
            result['title'] = title.get_text(strip=True) if title else ""
            
            # Try to find main content
            main = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main:
                result['content'] = main.get_text(strip=True)
            else:
                result['content'] = soup.get_text(strip=True)
        
        return result
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML."""
        soup = BeautifulSoup(html, 'lxml')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(base_url, href)
            
            # Only include same-domain links
            if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                links.append(absolute_url)
        
        return links
    
    async def crawl(
        self,
        start_url: str,
        depth: int = 2,
        include_patterns: List[str] = None,
        max_pages: int = 100
    ) -> List[Dict]:
        """Crawl website starting from URL."""
        _validate_crawl_url(start_url)
        logger.info(f"Starting crawl from {start_url} with depth {depth}")
        
        pages = []
        to_visit = [(start_url, 0)]
        self.visited_urls = set()
        
        while to_visit and len(pages) < max_pages:
            url, current_depth = to_visit.pop(0)
            
            if url in self.visited_urls or current_depth > depth:
                continue
            
            # Check include patterns
            if include_patterns:
                if not any(pattern in url for pattern in include_patterns):
                    continue
            
            html = await self.fetch_page(url)
            if not html:
                continue
            
            self.visited_urls.add(url)
            
            # Extract content
            content = self.extract_text(html)
            pages.append({
                "url": url,
                "title": content.get("title", ""),
                "content": content.get("content", ""),
                "depth": current_depth
            })
            
            logger.info(f"Crawled: {url} (depth {current_depth})")
            
            # Extract links for next depth
            if current_depth < depth:
                links = self.extract_links(html, url)
                for link in links:
                    if link not in self.visited_urls:
                        to_visit.append((link, current_depth + 1))
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        logger.success(f"Crawl complete: {len(pages)} pages")
        return pages
    
    async def scrape_blog(
        self,
        blog_url: str,
        selectors: Dict[str, str] = None
    ) -> List[Dict]:
        """Scrape blog posts from a blog."""
        logger.info(f"Scraping blog: {blog_url}")
        
        html = await self.fetch_page(blog_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        posts = []
        
        # Find article links
        articles = soup.find_all('article') or soup.find_all('div', class_='post')
        
        for article in articles[:10]:  # Limit to first 10
            post = {}
            
            # Extract title
            title = article.find(['h1', 'h2', 'h3'])
            if title:
                post['title'] = title.get_text(strip=True)
                
                # Find link
                link = title.find('a')
                if link and link.get('href'):
                    post['url'] = urljoin(blog_url, link['href'])
            
            # Extract excerpt
            excerpt = article.find('p')
            if excerpt:
                post['excerpt'] = excerpt.get_text(strip=True)
            
            if post:
                posts.append(post)
        
        logger.info(f"Found {len(posts)} blog posts")
        return posts
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()