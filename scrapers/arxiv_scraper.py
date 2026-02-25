"""ArXiv paper scraper for MonadBFT and related consensus research."""

import arxiv
import logging
from typing import List, Dict, Optional
from datetime import datetime
import PyPDF2
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class ArxivScraper:
    """Scraper for MonadBFT papers from arXiv."""
    
    MONADBFT_ARXIV_ID = "2502.20692"
    
    RELATED_QUERIES = [
        "MonadBFT",
        "HotStuff consensus",
        "Fast-HotStuff",
        "Byzantine Fault Tolerance",
        "streamlined consensus",
        "responsive consensus",
        "blockchain consensus latency",
    ]
    
    def __init__(self, data_dir: str = "data/papers"):
        """Initialize ArXiv scraper.
        
        Args:
            data_dir: Directory to save downloaded papers
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_monadbft_paper(self) -> Dict:
        """Fetch the main MonadBFT paper.
        
        Returns:
            Dictionary with paper metadata and content
        """
        logger.info(f"Fetching MonadBFT paper: {self.MONADBFT_ARXIV_ID}")
        
        search = arxiv.Search(id_list=[self.MONADBFT_ARXIV_ID])
        paper = next(search.results())
        
        paper_data = self._extract_paper_metadata(paper)
        
        # Download PDF
        pdf_path = self.data_dir / f"monadbft_{self.MONADBFT_ARXIV_ID}.pdf"
        paper.download_pdf(filename=str(pdf_path))
        paper_data['local_path'] = str(pdf_path)
        
        # Extract text
        paper_data['text'] = self._extract_pdf_text(pdf_path)
        
        logger.info(f"Successfully fetched MonadBFT paper")
        return paper_data
    
    def search_monadbft_papers(
        self, 
        max_results: int = 50,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """Search for MonadBFT and related consensus papers.
        
        Args:
            max_results: Maximum number of results per query
            categories: arXiv categories to search (default: cs.DC, cs.CR)
            
        Returns:
            List of paper metadata dictionaries
        """
        if categories is None:
            categories = ["cs.DC", "cs.CR"]  # Distributed Computing, Cryptography
        
        all_papers = []
        seen_ids = set()
        
        for query in self.RELATED_QUERIES:
            logger.info(f"Searching arXiv for: {query}")
            
            # Build search query with categories
            cat_filter = " OR ".join([f"cat:{cat}" for cat in categories])
            full_query = f"({query}) AND ({cat_filter})"
            
            search = arxiv.Search(
                query=full_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            for paper in search.results():
                if paper.entry_id not in seen_ids:
                    paper_data = self._extract_paper_metadata(paper)
                    all_papers.append(paper_data)
                    seen_ids.add(paper.entry_id)
        
        logger.info(f"Found {len(all_papers)} unique papers")
        return all_papers
    
    def search_by_authors(self, authors: List[str], max_results: int = 20) -> List[Dict]:
        """Search papers by specific authors.
        
        Args:
            authors: List of author names
            max_results: Maximum results per author
            
        Returns:
            List of paper metadata dictionaries
        """
        all_papers = []
        seen_ids = set()
        
        for author in authors:
            logger.info(f"Searching papers by: {author}")
            
            search = arxiv.Search(
                query=f"au:{author}",
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            for paper in search.results():
                if paper.entry_id not in seen_ids:
                    paper_data = self._extract_paper_metadata(paper)
                    all_papers.append(paper_data)
                    seen_ids.add(paper.entry_id)
        
        return all_papers
    
    def download_paper(self, arxiv_id: str, extract_text: bool = True) -> Dict:
        """Download a specific paper by arXiv ID.
        
        Args:
            arxiv_id: arXiv paper ID
            extract_text: Whether to extract text from PDF
            
        Returns:
            Paper metadata and content
        """
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        
        paper_data = self._extract_paper_metadata(paper)
        
        # Download PDF
        pdf_path = self.data_dir / f"{arxiv_id.replace('/', '_')}.pdf"
        paper.download_pdf(filename=str(pdf_path))
        paper_data['local_path'] = str(pdf_path)
        
        if extract_text:
            paper_data['text'] = self._extract_pdf_text(pdf_path)
        
        return paper_data
    
    def _extract_paper_metadata(self, paper) -> Dict:
        """Extract metadata from arXiv paper object."""
        return {
            'arxiv_id': paper.entry_id.split('/')[-1],
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'abstract': paper.summary,
            'published': paper.published.isoformat(),
            'updated': paper.updated.isoformat() if paper.updated else None,
            'categories': paper.categories,
            'primary_category': paper.primary_category,
            'pdf_url': paper.pdf_url,
            'doi': paper.doi,
            'journal_ref': paper.journal_ref,
            'source': 'arxiv',
            'scraped_at': datetime.now().isoformat(),
        }
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text content from PDF."""
        try:
            text_parts = []
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def get_citations(self, arxiv_id: str) -> List[str]:
        """Get citations from a paper (using references section).
        
        Args:
            arxiv_id: arXiv paper ID
            
        Returns:
            List of cited arXiv IDs found in references
        """
        paper_data = self.download_paper(arxiv_id, extract_text=True)
        text = paper_data.get('text', '')
        
        # Simple regex to find arXiv IDs in text
        import re
        arxiv_pattern = r'arXiv:(\d{4}\.\d{4,5})'
        cited_ids = re.findall(arxiv_pattern, text)
        
        return list(set(cited_ids))
