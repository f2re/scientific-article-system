#!/usr/bin/env python3
"""
Catalog builder for scientific papers
Creates structured JSON catalogs with metadata
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter


def build_catalog(
    papers: List[Dict],
    query: str,
    output_file: Path,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Build structured catalog from paper list

    Args:
        papers: List of paper dictionaries
        query: Search query description
        output_file: Path to save catalog JSON
        metadata: Additional metadata to include

    Returns:
        Complete catalog dictionary
    """
    # Calculate statistics
    year_range = f"{min(p['year'] for p in papers if p.get('year'))}-{max(p['year'] for p in papers if p.get('year'))}" if papers else "N/A"
    downloaded_count = sum(1 for p in papers if p.get('local_path'))

    # Count by subtopic
    subtopic_counts = Counter(p.get('subtopic', 'general') for p in papers)

    # Count by source
    source_counts = Counter(p.get('source', 'unknown') for p in papers)

    # Build catalog
    catalog = {
        "search_metadata": {
            "query": query,
            "date": datetime.now().isoformat(),
            "total_papers": len(papers),
            "downloaded_pdfs": downloaded_count,
            "links_only": len(papers) - downloaded_count,
            "year_range": year_range,
            "sources": list(source_counts.keys()),
            "avg_relevance": round(sum(p.get('relevance_score', 0) for p in papers) / len(papers), 2) if papers else 0
        },
        "subtopic_counts": dict(subtopic_counts),
        "source_counts": dict(source_counts),
        "papers": sorted(papers, key=lambda x: (-x.get('relevance_score', 0), -x.get('year', 0)))
    }

    # Add custom metadata
    if metadata:
        catalog["search_metadata"].update(metadata)

    # Save catalog
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    return catalog


def load_catalog(catalog_file: Path) -> Optional[Dict]:
    """Load existing catalog from file"""
    try:
        with open(catalog_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading catalog: {e}")
        return None


def merge_catalogs(catalog1: Dict, catalog2: Dict, output_file: Path) -> Dict:
    """
    Merge two catalogs, removing duplicates

    Deduplication based on paper ID or normalized title
    """
    papers1 = catalog1.get('papers', [])
    papers2 = catalog2.get('papers', [])

    # Deduplicate
    seen_ids = set()
    merged_papers = []

    for paper in papers1 + papers2:
        paper_id = paper.get('id')
        if paper_id and paper_id not in seen_ids:
            seen_ids.add(paper_id)
            merged_papers.append(paper)
        elif not paper_id:
            # No ID, use normalized title
            title_norm = paper.get('title', '').lower().replace(' ', '')
            if title_norm not in seen_ids:
                seen_ids.add(title_norm)
                merged_papers.append(paper)

    # Rebuild catalog
    merged_query = f"{catalog1['search_metadata'].get('query', '')} + {catalog2['search_metadata'].get('query', '')}"
    return build_catalog(merged_papers, merged_query, output_file)


def export_to_bibtex(papers: List[Dict], output_file: Path):
    """
    Export papers to BibTeX format

    Basic implementation for common fields
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, paper in enumerate(papers, 1):
            # Generate citation key
            first_author = paper['authors'][0].split()[-1] if paper.get('authors') else 'Unknown'
            year = paper.get('year', 'NoDate')
            key = f"{first_author}{year}_{i}"

            # Determine entry type
            if paper.get('source') == 'arxiv':
                entry_type = 'article'
                journal = 'arXiv preprint'
                note = f"arXiv:{paper.get('arxiv_id', '')}"
            else:
                entry_type = 'article'
                journal = paper.get('venue', 'Unknown Journal')
                note = ''

            # Write entry
            f.write(f"@{entry_type}{{{key},\n")
            f.write(f"  title = {{{paper.get('title', 'Untitled')}}},\n")
            f.write(f"  author = {{{' and '.join(paper.get('authors', ['Unknown']))}}},\n")
            f.write(f"  year = {{{year}}},\n")
            f.write(f"  journal = {{{journal}}},\n")

            if note:
                f.write(f"  note = {{{note}}},\n")

            if paper.get('url'):
                f.write(f"  url = {{{paper['url']}}},\n")

            f.write("}\n\n")


def create_links_file(papers: List[Dict], output_file: Path, group_by: str = 'subtopic'):
    """
    Create text file with all paper links grouped by category

    Args:
        papers: List of papers
        output_file: Output text file path
        group_by: Field to group by ('subtopic', 'year', 'source')
    """
    # Group papers
    groups = {}
    for paper in papers:
        key = paper.get(group_by, 'other')
        if key not in groups:
            groups[key] = []
        groups[key].append(paper)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PAPER LINKS AND METADATA\n")
        f.write("=" * 80 + "\n\n")

        for group_name, group_papers in sorted(groups.items()):
            f.write(f"\n{'=' * 80}\n")
            f.write(f"{group_name.upper().replace('_', ' ')}\n")
            f.write(f"{'=' * 80}\n\n")

            for paper in sorted(group_papers, key=lambda x: -x.get('relevance_score', 0)):
                f.write(f"Title: {paper['title']}\n")
                f.write(f"Authors: {', '.join(paper.get('authors', [])[:5])}\n")
                if len(paper.get('authors', [])) > 5:
                    f.write(f"         (+ {len(paper['authors']) - 5} more)\n")
                f.write(f"Year: {paper.get('year', 'N/A')}\n")
                f.write(f"Venue: {paper.get('venue', 'N/A')}\n")

                if 'relevance_score' in paper:
                    f.write(f"Relevance: {paper['relevance_score']}/10\n")

                if paper.get('citations'):
                    f.write(f"Citations: {paper['citations']}\n")

                # URLs
                if paper.get('url'):
                    f.write(f"URL: {paper['url']}\n")

                if paper.get('pdf_url'):
                    f.write(f"PDF: {paper['pdf_url']}\n")

                if paper.get('local_path'):
                    f.write(f"Local: {paper['local_path']}\n")

                f.write("\n" + "-" * 80 + "\n\n")
