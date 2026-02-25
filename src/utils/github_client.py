#!/usr/bin/env python3
"""
GitHub Client for fetching repository information.
"""

import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional
from loguru import logger
import os


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "MonadBFT-Research-Aggregator"
            }
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def get_repository(self, repo_full_name: str) -> Optional[Dict]:
        """Get repository information."""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/repos/{repo_full_name}"
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"GitHub API error for {repo_full_name}: {response.status}")
                    return None
                
                return await response.json()
        
        except Exception as e:
            logger.error(f"Error fetching repository {repo_full_name}: {e}")
            return None
    
    async def get_readme(self, repo_full_name: str) -> Optional[str]:
        """Get repository README content."""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/repos/{repo_full_name}/readme"
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                content = base64.b64decode(data.get("content", "")).decode('utf-8')
                return content
        
        except Exception as e:
            logger.error(f"Error fetching README for {repo_full_name}: {e}")
            return None
    
    async def get_repo_structure(self, repo_full_name: str, path: str = "") -> Optional[List[Dict]]:
        """Get repository file structure."""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/repos/{repo_full_name}/contents/{path}"
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                return await response.json()
        
        except Exception as e:
            logger.error(f"Error fetching structure for {repo_full_name}: {e}")
            return None
    
    async def get_file_content(self, repo_full_name: str, file_path: str) -> Optional[str]:
        """Get content of a specific file."""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/repos/{repo_full_name}/contents/{file_path}"
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                if data.get("encoding") == "base64":
                    content = base64.b64decode(data.get("content", "")).decode('utf-8')
                    return content
                
                return None
        
        except Exception as e:
            logger.error(f"Error fetching file {file_path} from {repo_full_name}: {e}")
            return None
    
    async def search_repositories(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search GitHub repositories."""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/search/repositories"
            params = {
                "q": query,
                "per_page": max_results,
                "sort": "stars"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"GitHub search error: {response.status}")
                    return []
                
                data = await response.json()
                return data.get("items", [])
        
        except Exception as e:
            logger.error(f"Error searching GitHub: {e}")
            return []
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()