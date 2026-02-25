"""ArXiv paper scraper for MonadBFT research papers."""

import arxiv
import requests
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime
import PyPDF2
import re


class ArxivScraper:
    """Scraper for MonadBFT and related BFT consensus papers from arXiv."""
    
    def __init__(self, data_dir: str = "data/papers"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.data_dir / "metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Load existing paper metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"papers": []}
    
    def save_metadata(self):
        """Save paper metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def fetch_paper(self, arxiv_id: str) -> Dict:
        """Fetch a specific paper by arXiv ID.
        
        Args:
            arxiv_id: ArXiv ID (e.g., '2502.20692')
            
        Returns:
            Dictionary with paper information
        """
        print(f"Fetching paper {arxiv_id}...")
        
        # Search for paper
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        
        # Download PDF
        pdf_path = self.data_dir / f"{arxiv_id.replace('.', '_')}.pdf"
        paper.download_pdf(filename=str(pdf_path))
        
        # Extract metadata
        paper_data = {
            "arxiv_id": arxiv_id,
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "abstract": paper.summary,
            "published": paper.published.isoformat(),
            "updated": paper.updated.isoformat(),
            "categories": paper.categories,
            "pdf_path": str(pdf_path),
            "pdf_url": paper.pdf_url,
            "downloaded_at": datetime.now().isoformat()
        }
        
        # Extract text content
        paper_data["content"] = self.extract_pdf_text(pdf_path)
        
        # Add to metadata
        self.metadata["papers"].append(paper_data)
        self.save_metadata()
        
        print(f"✓ Downloaded: {paper.title}")
        return paper_data
    
    def fetch_monadbft_paper(self) -> Dict:
        """Fetch the main MonadBFT paper."""
        return self.fetch_paper("2502.20692")
    
    def search_bft_papers(self, query: str = "BFT consensus", max_results: int = 50) -> List[Dict]:
        """Search for BFT consensus papers.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of paper dictionaries
        """
        print(f"Searching for: {query}...")
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for paper in search.results():
            paper_data = {
                "arxiv_id": paper.entry_id.split('/')[-1],
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "abstract": paper.summary,
                "published": paper.published.isoformat(),
                "categories": paper.categories,
                "pdf_url": paper.pdf_url
            }
            results.append(paper_data)
            print(f"  - {paper.title}")
        
        return results
    
    def search_related_papers(self) -> List[Dict]:
        """Search for papers related to MonadBFT."""
        queries = [
            "HotStuff consensus",
            "Fast-HotStuff",
            "BFT consensus blockchain",
            "streamlined consensus",
            "responsive BFT",
            "blockchain finality"
        ]
        
        all_results = []
        for query in queries:
            results = self.search_bft_papers(query, max_results=10)
            all_results.extend(results)
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for paper in all_results:
            if paper['arxiv_id'] not in seen:
                seen.add(paper['arxiv_id'])
                unique_results.append(paper)
        
        return unique_results
    
    def extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text content from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Warning: Could not extract text from {pdf_path}: {e}")
            return ""
    
    def extract_key_concepts(self, paper_data: Dict) -> Dict:
        """Extract key concepts from paper.
        
        Args:
            paper_data: Paper metadata with content
            
        Returns:
            Dictionary of extracted concepts
        """
        content = paper_data.get("content", "") + " " + paper_data.get("abstract", "")
        
        concepts = {
            "protocols": [],
            "algorithms": [],
            "metrics": [],
            "challenges": []
        }
        
        # Protocol patterns
        protocol_patterns = [
            r"\b(PBFT|HotStuff|Fast-HotStuff|MonadBFT|Tendermint|Raft)\b",
            r"\b(\w+BFT)\b"
        ]
        
        # Metric patterns
        metric_patterns = [
            r"(\d+\.?\d*)\s*(ms|milliseconds?|seconds?|TPS|transactions per second)",
            r"(latency|throughput|finality|communication complexity)"
        ]
        
        for pattern in protocol_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts["protocols"].extend(matches)
        
        for pattern in metric_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts["metrics"].extend(matches)
        
        # Remove duplicates
        for key in concepts:
            if isinstance(concepts[key], list):
                concepts[key] = list(set(concepts[key]))
        
        return concepts
    
    def generate_summary(self, paper_data: Dict) -> str:
        """Generate a summary of the paper.
        
        Args:
            paper_data: Paper metadata
            
        Returns:
            Formatted summary string
        """
        summary = f"""
# {paper_data['title']}

**Authors:** {', '.join(paper_data['authors'])}
**Published:** {paper_data['published'][:10]}
**arXiv ID:** {paper_data['arxiv_id']}

## Abstract

{paper_data['abstract']}

## Key Concepts

{json.dumps(self.extract_key_concepts(paper_data), indent=2)}

## Links

- [PDF]({paper_data['pdf_url']})
- [arXiv Page](https://arxiv.org/abs/{paper_data['arxiv_id']})
"""
        return summary


if __name__ == "__main__":
    scraper = ArxivScraper()
    
    # Fetch MonadBFT paper
    print("Fetching MonadBFT paper...")
    monadbft = scraper.fetch_monadbft_paper()
    
    print("\n" + "="*80)
    print(scraper.generate_summary(monadbft))
    
    # Search for related papers
    print("\n" + "="*80)
    print("\nSearching for related papers...")
    related = scraper.search_related_papers()
    print(f"\nFound {len(related)} related papers")