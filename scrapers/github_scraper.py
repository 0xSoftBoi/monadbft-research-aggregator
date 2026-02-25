"""GitHub repository and implementation scraper."""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class GitHubScraper:
    """Scraper for MonadBFT GitHub repositories."""
    
    API_BASE = "https://api.github.com"
    MONADBFT_REPO = "category-labs/monad-bft"
    MONAD_VIZ_REPO = "category-labs/monad-viz"
    
    def __init__(self, github_token: Optional[str] = None, data_dir: str = "data/github"):
        """Initialize GitHub scraper.
        
        Args:
            github_token: GitHub personal access token (optional, for higher rate limits)
            data_dir: Directory to save data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        self.session.headers.update(headers)
    
    def scrape_monadbft_repo(self) -> Dict:
        """Scrape the main MonadBFT repository.
        
        Returns:
            Repository metadata and structure
        """
        return self.scrape_repository(self.MONADBFT_REPO)
    
    def scrape_repository(self, repo: str) -> Dict:
        """Scrape a GitHub repository.
        
        Args:
            repo: Repository in format 'owner/name'
            
        Returns:
            Repository data dictionary
        """
        logger.info(f"Scraping GitHub repository: {repo}")
        
        try:
            # Get repository metadata
            url = f"{self.API_BASE}/repos/{repo}"
            response = self.session.get(url)
            response.raise_for_status()
            repo_data = response.json()
            
            # Get repository contents
            contents = self._get_repo_contents(repo)
            
            # Get README
            readme = self._get_readme(repo)
            
            # Get recent commits
            commits = self._get_recent_commits(repo, count=50)
            
            # Get releases
            releases = self._get_releases(repo)
            
            # Get issues and discussions
            issues = self._get_issues(repo)
            
            return {
                'name': repo_data['name'],
                'full_name': repo_data['full_name'],
                'description': repo_data['description'],
                'url': repo_data['html_url'],
                'stars': repo_data['stargazers_count'],
                'forks': repo_data['forks_count'],
                'watchers': repo_data['watchers_count'],
                'language': repo_data['language'],
                'created_at': repo_data['created_at'],
                'updated_at': repo_data['updated_at'],
                'topics': repo_data.get('topics', []),
                'contents': contents,
                'readme': readme,
                'commits': commits,
                'releases': releases,
                'issues': issues,
                'scraped_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error scraping repository {repo}: {e}")
            return {}
    
    def search_monadbft_repos(self) -> List[Dict]:
        """Search for MonadBFT-related repositories.
        
        Returns:
            List of repository metadata
        """
        queries = [
            'monadbft',
            'hotstuff consensus',
            'fast-hotstuff',
            'bft consensus blockchain',
        ]
        
        all_repos = []
        seen_repos = set()
        
        for query in queries:
            try:
                url = f"{self.API_BASE}/search/repositories"
                params = {
                    'q': query,
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 30
                }
                
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for repo in data.get('items', []):
                    repo_full_name = repo['full_name']
                    if repo_full_name not in seen_repos:
                        all_repos.append(self._extract_repo_metadata(repo))
                        seen_repos.add(repo_full_name)
                        
            except Exception as e:
                logger.error(f"Error searching repos for '{query}': {e}")
        
        return all_repos
    
    def _get_repo_contents(self, repo: str, path: str = "") -> List[Dict]:
        """Get repository file structure."""
        try:
            url = f"{self.API_BASE}/repos/{repo}/contents/{path}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting repo contents: {e}")
            return []
    
    def _get_readme(self, repo: str) -> Optional[str]:
        """Get repository README content."""
        try:
            url = f"{self.API_BASE}/repos/{repo}/readme"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Decode base64 content
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        except Exception as e:
            logger.error(f"Error getting README: {e}")
            return None
    
    def _get_recent_commits(self, repo: str, count: int = 50) -> List[Dict]:
        """Get recent commits from repository."""
        try:
            url = f"{self.API_BASE}/repos/{repo}/commits"
            params = {'per_page': count}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            commits = response.json()
            
            return [{
                'sha': commit['sha'],
                'message': commit['commit']['message'],
                'author': commit['commit']['author']['name'],
                'date': commit['commit']['author']['date'],
                'url': commit['html_url'],
            } for commit in commits]
        except Exception as e:
            logger.error(f"Error getting commits: {e}")
            return []
    
    def _get_releases(self, repo: str) -> List[Dict]:
        """Get repository releases."""
        try:
            url = f"{self.API_BASE}/repos/{repo}/releases"
            response = self.session.get(url)
            response.raise_for_status()
            releases = response.json()
            
            return [{
                'tag': release['tag_name'],
                'name': release['name'],
                'body': release['body'],
                'published_at': release['published_at'],
                'url': release['html_url'],
            } for release in releases]
        except Exception as e:
            logger.error(f"Error getting releases: {e}")
            return []
    
    def _get_issues(self, repo: str, count: int = 50) -> List[Dict]:
        """Get repository issues."""
        try:
            url = f"{self.API_BASE}/repos/{repo}/issues"
            params = {'per_page': count, 'state': 'all'}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            issues = response.json()
            
            return [{
                'number': issue['number'],
                'title': issue['title'],
                'state': issue['state'],
                'created_at': issue['created_at'],
                'updated_at': issue['updated_at'],
                'url': issue['html_url'],
            } for issue in issues]
        except Exception as e:
            logger.error(f"Error getting issues: {e}")
            return []
    
    def _extract_repo_metadata(self, repo: Dict) -> Dict:
        """Extract basic metadata from repository object."""
        return {
            'name': repo['name'],
            'full_name': repo['full_name'],
            'description': repo.get('description', ''),
            'url': repo['html_url'],
            'stars': repo['stargazers_count'],
            'forks': repo['forks_count'],
            'language': repo.get('language'),
            'created_at': repo['created_at'],
            'updated_at': repo['updated_at'],
        }
    
    def save_repo_data(self, repo_data: Dict, filename: Optional[str] = None):
        """Save repository data to JSON file."""
        if filename is None:
            filename = f"{repo_data['name']}_data.json"
        
        output_path = self.data_dir / filename
        with open(output_path, 'w') as f:
            json.dump(repo_data, f, indent=2)
        logger.info(f"Saved repo data to {output_path}")