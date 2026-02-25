#!/usr/bin/env python3
"""
MonadBFT Research Scraper

Aggregates research papers, documentation, blog posts, and implementations
related to MonadBFT consensus protocol.

Usage:
    python research_scraper.py --sources all
    python research_scraper.py --sources arxiv,github
    python research_scraper.py --output data/research.json
"""

import argparse
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import yaml

from utils.arxiv_client import ArxivClient
from utils.github_client import GitHubClient
from utils.data_parser import DataParser
from utils.web_scraper import WebScraper
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class MonadBFTResearchAggregator:
    """Main research aggregation class for MonadBFT."""
    
    def __init__(self, config_path: str = "config/sources.yaml"):
        self.config = self._load_config(config_path)
        self.arxiv_client = ArxivClient()
        self.github_client = GitHubClient()
        self.web_scraper = WebScraper()
        self.data_parser = DataParser()
        self.results = {
            "papers": [],
            "documentation": [],
            "blog_posts": [],
            "implementations": [],
            "metadata": {
                "aggregation_date": datetime.utcnow().isoformat(),
                "sources": []
            }
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return self._default_config()
        
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "arxiv": {
                "papers": ["2502.20692"],
                "search_terms": ["MonadBFT", "streamlined consensus", "Byzantine fault tolerance"]
            },
            "github": {
                "repositories": ["category-labs/monad-bft", "category-labs/monad"],
                "organizations": ["category-labs"]
            },
            "blogs": [
                {
                    "url": "https://blog.monad.xyz",
                    "name": "Category Labs Blog"
                }
            ],
            "documentation": [
                {
                    "url": "https://docs.monad.xyz",
                    "crawl_depth": 3
                }
            ]
        }
    
    async def scrape_arxiv(self) -> List[Dict]:
        """Scrape arXiv papers related to MonadBFT."""
        logger.info("Scraping arXiv papers...")
        papers = []
        
        # Fetch specific paper
        arxiv_id = self.config["arxiv"]["papers"][0]
        logger.info(f"Fetching arXiv paper: {arxiv_id}")
        
        paper = await self.arxiv_client.fetch_paper(arxiv_id)
        if paper:
            papers.append({
                "id": arxiv_id,
                "title": paper.get("title", "MonadBFT: Fast, Responsive, Fork-Resistant Streamlined Consensus"),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "published": paper.get("published", ""),
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                "source": "arxiv"
            })
        
        # Search for related papers
        for term in self.config["arxiv"]["search_terms"]:
            logger.info(f"Searching arXiv for: {term}")
            search_results = await self.arxiv_client.search(term, max_results=10)
            papers.extend(search_results)
        
        logger.success(f"Found {len(papers)} arXiv papers")
        return papers
    
    async def scrape_github(self) -> List[Dict]:
        """Scrape GitHub repositories and implementations."""
        logger.info("Scraping GitHub repositories...")
        implementations = []
        
        for repo in self.config["github"]["repositories"]:
            logger.info(f"Analyzing repository: {repo}")
            
            repo_data = await self.github_client.get_repository(repo)
            if repo_data:
                implementations.append({
                    "repository": repo,
                    "name": repo_data.get("name"),
                    "description": repo_data.get("description"),
                    "url": repo_data.get("html_url"),
                    "stars": repo_data.get("stargazers_count"),
                    "language": repo_data.get("language"),
                    "last_updated": repo_data.get("updated_at"),
                    "topics": repo_data.get("topics", []),
                    "source": "github"
                })
                
                # Get README content
                readme = await self.github_client.get_readme(repo)
                if readme:
                    implementations[-1]["readme"] = readme
                
                # Get code structure
                structure = await self.github_client.get_repo_structure(repo)
                if structure:
                    implementations[-1]["structure"] = structure
        
        logger.success(f"Found {len(implementations)} GitHub implementations")
        return implementations
    
    async def scrape_documentation(self) -> List[Dict]:
        """Scrape official Monad documentation."""
        logger.info("Scraping official documentation...")
        docs = []
        
        for doc_config in self.config["documentation"]:
            url = doc_config["url"]
            logger.info(f"Scraping documentation from: {url}")
            
            doc_pages = await self.web_scraper.crawl(
                url,
                depth=doc_config.get("crawl_depth", 3),
                include_patterns=doc_config.get("include_patterns", [])
            )
            
            for page in doc_pages:
                docs.append({
                    "url": page["url"],
                    "title": page["title"],
                    "content": page["content"],
                    "last_updated": page.get("last_updated"),
                    "source": "documentation"
                })
        
        logger.success(f"Scraped {len(docs)} documentation pages")
        return docs
    
    async def scrape_blog_posts(self) -> List[Dict]:
        """Scrape Category Labs blog posts."""
        logger.info("Scraping blog posts...")
        posts = []
        
        for blog_config in self.config["blogs"]:
            url = blog_config["url"]
            logger.info(f"Scraping blog: {url}")
            
            blog_posts = await self.web_scraper.scrape_blog(
                url,
                selectors=blog_config.get("selectors", {})
            )
            
            for post in blog_posts:
                if self._is_monadbft_related(post):
                    posts.append({
                        "title": post["title"],
                        "url": post["url"],
                        "date": post.get("date"),
                        "author": post.get("author"),
                        "excerpt": post.get("excerpt"),
                        "content": post.get("content"),
                        "source": "blog"
                    })
        
        logger.success(f"Found {len(posts)} relevant blog posts")
        return posts
    
    def _is_monadbft_related(self, post: Dict) -> bool:
        """Check if a blog post is related to MonadBFT."""
        keywords = ["monadbft", "consensus", "bft", "byzantine", "hotstuff", "blockchain"]
        text = (post.get("title", "") + " " + post.get("content", "")).lower()
        return any(keyword in text for keyword in keywords)
    
    async def aggregate_all(self, sources: List[str] = None) -> Dict:
        """Aggregate all research sources."""
        if sources is None:
            sources = ["arxiv", "github", "documentation", "blog"]
        
        console.print("\n[bold cyan]MonadBFT Research Aggregator[/bold cyan]")
        console.print(f"Aggregating sources: {', '.join(sources)}\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            tasks = []
            
            if "arxiv" in sources:
                task = progress.add_task("Scraping arXiv papers...", total=None)
                papers = await self.scrape_arxiv()
                self.results["papers"] = papers
                progress.update(task, completed=True)
            
            if "github" in sources:
                task = progress.add_task("Scraping GitHub repositories...", total=None)
                implementations = await self.scrape_github()
                self.results["implementations"] = implementations
                progress.update(task, completed=True)
            
            if "documentation" in sources:
                task = progress.add_task("Scraping documentation...", total=None)
                docs = await self.scrape_documentation()
                self.results["documentation"] = docs
                progress.update(task, completed=True)
            
            if "blog" in sources:
                task = progress.add_task("Scraping blog posts...", total=None)
                posts = await self.scrape_blog_posts()
                self.results["blog_posts"] = posts
                progress.update(task, completed=True)
        
        self.results["metadata"]["sources"] = sources
        self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """Generate summary statistics."""
        console.print("\n[bold green]✓ Aggregation Complete[/bold green]")
        console.print(f"\n📄 Papers found: {len(self.results['papers'])}")
        console.print(f"💻 Implementations found: {len(self.results['implementations'])}")
        console.print(f"📚 Documentation pages: {len(self.results['documentation'])}")
        console.print(f"📝 Blog posts found: {len(self.results['blog_posts'])}")
    
    def save_results(self, output_path: str):
        """Save aggregated results to file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.success(f"Results saved to {output_path}")
        console.print(f"\n💾 Results saved to: [cyan]{output_path}[/cyan]")


def main():
    parser = argparse.ArgumentParser(
        description="MonadBFT Research Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--sources",
        default="all",
        help="Comma-separated list of sources to scrape (arxiv,github,documentation,blog) or 'all'"
    )
    parser.add_argument(
        "--output",
        default="data/research.json",
        help="Output file path for aggregated results"
    )
    parser.add_argument(
        "--config",
        default="config/sources.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Parse sources
    if args.sources == "all":
        sources = ["arxiv", "github", "documentation", "blog"]
    else:
        sources = [s.strip() for s in args.sources.split(",")]
    
    # Run aggregator
    aggregator = MonadBFTResearchAggregator(config_path=args.config)
    results = asyncio.run(aggregator.aggregate_all(sources))
    aggregator.save_results(args.output)


if __name__ == "__main__":
    main()