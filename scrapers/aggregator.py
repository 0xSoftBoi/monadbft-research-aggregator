"""Research aggregator that combines all scrapers."""

import logging
from typing import List, Dict, Optional
import json
from pathlib import Path
from datetime import datetime

from .arxiv_scraper import ArxivScraper
from .category_labs_scraper import CategoryLabsScraper
from .monad_docs_scraper import MonadDocsScraper
from .github_scraper import GitHubScraper

logger = logging.getLogger(__name__)


class ResearchAggregator:
    """Aggregate research from all sources."""
    
    def __init__(
        self, 
        github_token: Optional[str] = None,
        data_dir: str = "data"
    ):
        """Initialize research aggregator.
        
        Args:
            github_token: GitHub personal access token
            data_dir: Base directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.arxiv_scraper = ArxivScraper(data_dir=str(self.data_dir / "papers"))
        self.category_scraper = CategoryLabsScraper(data_dir=str(self.data_dir / "category_labs"))
        self.monad_scraper = MonadDocsScraper(data_dir=str(self.data_dir / "monad_docs"))
        self.github_scraper = GitHubScraper(github_token=github_token, data_dir=str(self.data_dir / "github"))
        
        self.aggregated_data = {
            'papers': [],
            'blog_posts': [],
            'documentation': [],
            'repositories': [],
            'aggregated_at': None,
        }
    
    def scrape_all(self, max_results_per_source: int = 50) -> Dict:
        """Scrape from all sources.
        
        Args:
            max_results_per_source: Max results to fetch from each source
            
        Returns:
            Aggregated data dictionary
        """
        logger.info("Starting full research aggregation")
        
        # Scrape arXiv papers
        logger.info("Scraping arXiv...")
        try:
            monadbft_paper = self.arxiv_scraper.get_monadbft_paper()
            self.aggregated_data['papers'].append(monadbft_paper)
            
            related_papers = self.arxiv_scraper.search_monadbft_papers(
                max_results=max_results_per_source
            )
            self.aggregated_data['papers'].extend(related_papers)
        except Exception as e:
            logger.error(f"Error scraping arXiv: {e}")
        
        # Scrape Category Labs blog
        logger.info("Scraping Category Labs blog...")
        try:
            blog_posts = self.category_scraper.scrape_blog_posts(
                max_posts=max_results_per_source
            )
            self.aggregated_data['blog_posts'].extend(blog_posts)
            
            technical_docs = self.category_scraper.get_technical_docs()
            self.aggregated_data['documentation'].extend(technical_docs)
        except Exception as e:
            logger.error(f"Error scraping Category Labs: {e}")
        
        # Scrape Monad documentation
        logger.info("Scraping Monad documentation...")
        try:
            monad_docs = self.monad_scraper.scrape_all_docs()
            self.aggregated_data['documentation'].extend(monad_docs)
            
            monadbft_specs = self.monad_scraper.scrape_monadbft_specs()
            if monadbft_specs:
                self.aggregated_data['documentation'].append(monadbft_specs)
        except Exception as e:
            logger.error(f"Error scraping Monad docs: {e}")
        
        # Scrape GitHub repositories
        logger.info("Scraping GitHub repositories...")
        try:
            monadbft_repo = self.github_scraper.scrape_monadbft_repo()
            if monadbft_repo:
                self.aggregated_data['repositories'].append(monadbft_repo)
            
            related_repos = self.github_scraper.search_monadbft_repos()
            self.aggregated_data['repositories'].extend(related_repos)
        except Exception as e:
            logger.error(f"Error scraping GitHub: {e}")
        
        self.aggregated_data['aggregated_at'] = datetime.now().isoformat()
        
        logger.info(f"Aggregation complete: "
                   f"{len(self.aggregated_data['papers'])} papers, "
                   f"{len(self.aggregated_data['blog_posts'])} blog posts, "
                   f"{len(self.aggregated_data['documentation'])} docs, "
                   f"{len(self.aggregated_data['repositories'])} repos")
        
        return self.aggregated_data
    
    def scrape_arxiv(self, query: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Scrape only arXiv papers."""
        if query:
            # Custom query
            pass  # Implement custom search
        else:
            return self.arxiv_scraper.search_monadbft_papers(max_results=max_results)
    
    def scrape_category_labs_blog(self) -> List[Dict]:
        """Scrape only Category Labs blog."""
        return self.category_scraper.scrape_blog_posts()
    
    def scrape_monad_docs(self) -> List[Dict]:
        """Scrape only Monad documentation."""
        return self.monad_scraper.scrape_all_docs()
    
    def scrape_github_repos(self) -> List[Dict]:
        """Scrape only GitHub repositories."""
        repos = self.github_scraper.search_monadbft_repos()
        monadbft_repo = self.github_scraper.scrape_monadbft_repo()
        if monadbft_repo:
            repos.insert(0, monadbft_repo)
        return repos
    
    def export_to_json(self, filename: str = "aggregated_research.json"):
        """Export aggregated data to JSON file."""
        output_path = self.data_dir / filename
        with open(output_path, 'w') as f:
            json.dump(self.aggregated_data, f, indent=2)
        logger.info(f"Exported aggregated data to {output_path}")
    
    def generate_summary_report(self, output_file: str = "research_summary.md") -> str:
        """Generate a markdown summary report.
        
        Returns:
            Markdown summary text
        """
        report_lines = [
            "# MonadBFT Research Summary",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Overview\n",
        ]
        
        # Papers summary
        report_lines.append(f"### Academic Papers ({len(self.aggregated_data['papers'])})\n")
        for paper in self.aggregated_data['papers'][:10]:  # Top 10
            report_lines.append(f"- **{paper.get('title', 'Unknown')}**")
            report_lines.append(f"  - Authors: {', '.join(paper.get('authors', [])[:3])}")
            report_lines.append(f"  - arXiv: {paper.get('arxiv_id', 'N/A')}")
            report_lines.append("")
        
        # Blog posts summary
        report_lines.append(f"\n### Blog Posts ({len(self.aggregated_data['blog_posts'])})\n")
        for post in self.aggregated_data['blog_posts'][:10]:
            report_lines.append(f"- [{post.get('title', 'Unknown')}]({post.get('url', '#')})")
            if post.get('published_date'):
                report_lines.append(f"  - Published: {post['published_date']}")
            report_lines.append("")
        
        # Documentation summary
        report_lines.append(f"\n### Documentation ({len(self.aggregated_data['documentation'])})\n")
        for doc in self.aggregated_data['documentation'][:10]:
            report_lines.append(f"- [{doc.get('title', 'Unknown')}]({doc.get('url', '#')})")
            report_lines.append("")
        
        # Repositories summary
        report_lines.append(f"\n### Repositories ({len(self.aggregated_data['repositories'])})\n")
        for repo in self.aggregated_data['repositories'][:10]:
            report_lines.append(f"- **{repo.get('full_name', repo.get('name', 'Unknown'))}**")
            report_lines.append(f"  - Description: {repo.get('description', 'N/A')}")
            report_lines.append(f"  - Stars: {repo.get('stars', 0)} | Language: {repo.get('language', 'N/A')}")
            report_lines.append(f"  - URL: {repo.get('url', '#')}")
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        # Save to file
        output_path = self.data_dir / output_file
        with open(output_path, 'w') as f:
            f.write(report)
        logger.info(f"Generated summary report: {output_path}")
        
        return report
    
    def get_statistics(self) -> Dict:
        """Get statistics about aggregated data."""
        return {
            'total_papers': len(self.aggregated_data['papers']),
            'total_blog_posts': len(self.aggregated_data['blog_posts']),
            'total_documentation': len(self.aggregated_data['documentation']),
            'total_repositories': len(self.aggregated_data['repositories']),
            'aggregated_at': self.aggregated_data['aggregated_at'],
        }
