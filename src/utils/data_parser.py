#!/usr/bin/env python3
"""
Data parsing utilities.
"""

import re
import json
from typing import Dict, List, Any
from loguru import logger


class DataParser:
    """Utilities for parsing and processing research data."""
    
    @staticmethod
    def extract_citations(text: str) -> List[str]:
        """Extract citations from text."""
        # Match common citation formats
        patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\(\w+\s+\d{4}\)',  # (Author 2020)
            r'arXiv:\d{4}\.\d{5}',  # arXiv:2020.12345
        ]
        
        citations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return list(set(citations))
    
    @staticmethod
    def extract_arxiv_ids(text: str) -> List[str]:
        """Extract arXiv IDs from text."""
        pattern = r'arXiv:(\d{4}\.\d{4,5})'
        return re.findall(pattern, text)
    
    @staticmethod
    def extract_github_repos(text: str) -> List[str]:
        """Extract GitHub repository references from text."""
        pattern = r'github\.com/([\w-]+/[\w-]+)'
        return re.findall(pattern, text, re.IGNORECASE)
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extract potential keywords from text."""
        # Remove punctuation and lowercase
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter by length
        keywords = [w for w in words if len(w) >= min_length]
        
        # Count frequency
        freq = {}
        for word in keywords:
            freq[word] = freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        
        return [k for k, v in sorted_keywords[:20]]
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,;:!?-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[Dict[str, str]]:
        """Extract code blocks from markdown text."""
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        code_blocks = []
        for lang, code in matches:
            code_blocks.append({
                "language": lang or "unknown",
                "code": code.strip()
            })
        
        return code_blocks
    
    @staticmethod
    def summarize_text(text: str, max_sentences: int = 3) -> str:
        """Create a simple summary of text."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Take first N sentences
        summary = '. '.join(sentences[:max_sentences])
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary