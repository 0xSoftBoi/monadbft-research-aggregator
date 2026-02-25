#!/usr/bin/env python3
"""
arXiv Client for fetching research papers.
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET
from loguru import logger


class ArxivClient:
    """Client for interacting with arXiv API."""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self):
        self.session = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def fetch_paper(self, arxiv_id: str) -> Optional[Dict]:
        """Fetch a specific paper by arXiv ID."""
        await self._ensure_session()
        
        try:
            params = {
                "id_list": arxiv_id,
                "max_results": 1
            }
            
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"arXiv API error: {response.status}")
                    return None
                
                xml_data = await response.text()
                return self._parse_entry(xml_data)
        
        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
            return None
    
    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search arXiv for papers matching query."""
        await self._ensure_session()
        
        try:
            params = {
                "search_query": query,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"arXiv search error: {response.status}")
                    return []
                
                xml_data = await response.text()
                return self._parse_feed(xml_data)
        
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    def _parse_feed(self, xml_data: str) -> List[Dict]:
        """Parse arXiv API XML feed."""
        try:
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                paper = self._parse_entry_element(entry, ns)
                if paper:
                    papers.append(paper)
            
            return papers
        
        except Exception as e:
            logger.error(f"Error parsing arXiv XML: {e}")
            return []
    
    def _parse_entry(self, xml_data: str) -> Optional[Dict]:
        """Parse single arXiv entry."""
        try:
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entry = root.find('atom:entry', ns)
            if entry is None:
                return None
            
            return self._parse_entry_element(entry, ns)
        
        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return None
    
    def _parse_entry_element(self, entry, ns) -> Dict:
        """Parse arXiv entry element."""
        paper = {}
        
        # Extract ID
        id_elem = entry.find('atom:id', ns)
        if id_elem is not None:
            paper['id'] = id_elem.text.split('/')[-1]
        
        # Extract title
        title_elem = entry.find('atom:title', ns)
        if title_elem is not None:
            paper['title'] = title_elem.text.strip()
        
        # Extract abstract
        summary_elem = entry.find('atom:summary', ns)
        if summary_elem is not None:
            paper['abstract'] = summary_elem.text.strip()
        
        # Extract authors
        authors = []
        for author in entry.findall('atom:author', ns):
            name_elem = author.find('atom:name', ns)
            if name_elem is not None:
                authors.append(name_elem.text)
        paper['authors'] = authors
        
        # Extract published date
        published_elem = entry.find('atom:published', ns)
        if published_elem is not None:
            paper['published'] = published_elem.text
        
        # Extract updated date
        updated_elem = entry.find('atom:updated', ns)
        if updated_elem is not None:
            paper['updated'] = updated_elem.text
        
        return paper
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()