#!/usr/bin/env python3
"""
Academic paper search APIs
Provides unified interface for Semantic Scholar and arXiv
"""

import requests
import time
import feedparser
from urllib.parse import quote_plus
from typing import List, Dict, Optional

# Rate limits
S2_DELAY = 1.0  # Semantic Scholar: 1 request/sec
ARXIV_DELAY = 3.0  # arXiv: 3 seconds between requests

USER_AGENT = "Scientific-Research-Bot/1.0 (academic-research; contact@research.edu)"


def search_semantic_scholar(
    query: str,
    year_from: int = 2021,
    limit: int = 20,
    fields: Optional[List[str]] = None
) -> List[Dict]:
    """
    Search Semantic Scholar API

    Args:
        query: Search query string
        year_from: Minimum publication year
        limit: Maximum results (max 100)
        fields: Custom fields to retrieve

    Returns:
        List of paper dictionaries
    """
    if fields is None:
        fields = [
            "paperId", "title", "authors", "year", "abstract",
            "citationCount", "publicationVenue", "openAccessPdf", "url"
        ]

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "year": f"{year_from}-",
        "fields": ",".join(fields),
        "limit": min(limit, 100)
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        time.sleep(S2_DELAY)

        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"Semantic Scholar API error: HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"Semantic Scholar search error: {e}")
        return []


def search_arxiv(
    query: str,
    max_results: int = 50,
    sort_by: str = "relevance",
    year_from: Optional[int] = None
) -> List[Dict]:
    """
    Search arXiv API

    Args:
        query: Search query string
        max_results: Maximum results
        sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate')
        year_from: Filter papers from this year onwards

    Returns:
        List of paper dictionaries with arXiv metadata
    """
    encoded_query = quote_plus(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&max_results={max_results}&sortBy={sort_by}"

    try:
        feed = feedparser.parse(url)
        time.sleep(ARXIV_DELAY)

        papers = []
        for entry in feed.entries:
            arxiv_id = entry.id.split('/abs/')[-1]
            year = int(entry.published[:4])

            # Filter by year if specified
            if year_from and year < year_from:
                continue

            papers.append({
                'arxiv_id': arxiv_id,
                'title': entry.title.replace('\n', ' ').strip(),
                'authors': [author.name for author in entry.authors],
                'year': year,
                'abstract': entry.summary.replace('\n', ' ').strip(),
                'published': entry.published,
                'url': entry.link,
                'pdf_url': entry.link.replace('/abs/', '/pdf/') + '.pdf',
                'categories': [tag['term'] for tag in entry.tags] if hasattr(entry, 'tags') else []
            })

        return papers
    except Exception as e:
        print(f"arXiv search error: {e}")
        return []


def fetch_arxiv_by_id(arxiv_id: str) -> Optional[Dict]:
    """
    Fetch specific arXiv paper by ID

    Args:
        arxiv_id: arXiv identifier (e.g., "2212.12794")

    Returns:
        Paper dictionary or None if not found
    """
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

    try:
        feed = feedparser.parse(url)
        time.sleep(ARXIV_DELAY)

        if feed.entries:
            entry = feed.entries[0]
            return {
                'arxiv_id': arxiv_id,
                'title': entry.title.replace('\n', ' ').strip(),
                'authors': [author.name for author in entry.authors],
                'year': int(entry.published[:4]),
                'abstract': entry.summary.replace('\n', ' ').strip(),
                'published': entry.published,
                'url': entry.link,
                'pdf_url': entry.link.replace('/abs/', '/pdf/') + '.pdf',
                'categories': [tag['term'] for tag in entry.tags] if hasattr(entry, 'tags') else []
            }
        return None
    except Exception as e:
        print(f"arXiv fetch error: {e}")
        return None


def normalize_paper_s2(paper: Dict, subtopic: str = "general") -> Dict:
    """Normalize Semantic Scholar paper to standard format"""
    authors_list = [a.get('name', 'Unknown') for a in paper.get('authors', [])]

    return {
        'id': f"s2:{paper.get('paperId', 'unknown')}",
        'source': 'semantic_scholar',
        'title': paper.get('title', 'Untitled'),
        'authors': authors_list,
        'year': paper.get('year'),
        'abstract': paper.get('abstract', ''),
        'citations': paper.get('citationCount', 0),
        'venue': paper.get('publicationVenue', {}).get('name') if paper.get('publicationVenue') else None,
        'url': paper.get('url', ''),
        'pdf_url': paper.get('openAccessPdf', {}).get('url') if paper.get('openAccessPdf') else None,
        'pdf_available': bool(paper.get('openAccessPdf')),
        'subtopic': subtopic
    }


def normalize_paper_arxiv(paper: Dict, subtopic: str = "general") -> Dict:
    """Normalize arXiv paper to standard format"""
    return {
        'id': f"arxiv:{paper['arxiv_id']}",
        'source': 'arxiv',
        'title': paper['title'],
        'authors': paper['authors'],
        'year': paper['year'],
        'abstract': paper['abstract'],
        'citations': 0,  # arXiv doesn't track citations
        'venue': 'arXiv preprint',
        'url': paper['url'],
        'pdf_url': paper['pdf_url'],
        'pdf_available': True,
        'subtopic': subtopic,
        'categories': paper.get('categories', [])
    }
