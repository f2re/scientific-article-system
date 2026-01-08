#!/usr/bin/env python3
"""
Unified article search tool
Command-line interface for searching and downloading academic papers
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from article_search import (
    search_semantic_scholar,
    search_arxiv,
    fetch_arxiv_by_id,
    normalize_paper_s2,
    normalize_paper_arxiv,
    batch_download_pdfs,
    filter_by_relevance,
    score_atmospheric_profile_paper,
    score_ml_weather_paper,
    build_catalog,
    create_links_file,
    generate_search_report,
    generate_summary_report
)


def search_papers(
    queries: List[str],
    subtopic: str = "general",
    year_from: int = 2021,
    max_per_query: int = 20,
    sources: List[str] = ['arxiv', 'semantic_scholar'],
    scorer_type: str = "atmospheric"
) -> List[Dict]:
    """
    Search for papers across multiple sources

    Args:
        queries: List of search query strings
        subtopic: Subtopic category for organization
        year_from: Minimum publication year
        max_per_query: Maximum results per query
        sources: Which sources to search ('arxiv', 'semantic_scholar')
        scorer_type: Relevance scoring type ('atmospheric', 'ml_weather', 'general')

    Returns:
        List of normalized paper dictionaries
    """
    all_papers = []
    seen_ids = set()

    for query in queries:
        print(f"\n[Query: {query}]")

        # Semantic Scholar
        if 'semantic_scholar' in sources:
            print("  Searching Semantic Scholar...")
            s2_results = search_semantic_scholar(query, year_from=year_from, limit=max_per_query)
            for paper in s2_results:
                normalized = normalize_paper_s2(paper, subtopic)
                if normalized['id'] not in seen_ids:
                    seen_ids.add(normalized['id'])
                    all_papers.append(normalized)

        # arXiv
        if 'arxiv' in sources:
            print("  Searching arXiv...")
            arxiv_results = search_arxiv(query, max_results=max_per_query, year_from=year_from)
            for paper in arxiv_results:
                normalized = normalize_paper_arxiv(paper, subtopic)
                if normalized['id'] not in seen_ids:
                    seen_ids.add(normalized['id'])
                    all_papers.append(normalized)

    # Score papers
    if scorer_type == "atmospheric":
        scorer = score_atmospheric_profile_paper
    elif scorer_type == "ml_weather":
        scorer = score_ml_weather_paper
    else:
        scorer = None

    scored_papers = filter_by_relevance(all_papers, min_score=5.0, scorer_func=scorer)

    print(f"\n  Total papers found: {len(all_papers)}")
    print(f"  After relevance filtering (≥5.0): {len(scored_papers)}")

    return scored_papers


def main():
    parser = argparse.ArgumentParser(description='Search and download academic papers')

    parser.add_argument('--query', type=str, help='Main search query')
    parser.add_argument('--queries-file', type=Path, help='File with multiple queries (one per line)')
    parser.add_argument('--subtopic', type=str, default='general', help='Subtopic category')
    parser.add_argument('--year-from', type=int, default=2021, help='Minimum publication year')
    parser.add_argument('--max-results', type=int, default=20, help='Max results per query')
    parser.add_argument('--sources', nargs='+', default=['arxiv', 'semantic_scholar'],
                        choices=['arxiv', 'semantic_scholar'], help='Search sources')
    parser.add_argument('--scorer', type=str, default='atmospheric',
                        choices=['atmospheric', 'ml_weather', 'general'], help='Relevance scoring type')

    parser.add_argument('--download', action='store_true', help='Download PDFs')
    parser.add_argument('--max-downloads', type=int, default=50, help='Maximum PDFs to download')
    parser.add_argument('--output-dir', type=Path, default=Path('papers'), help='Output directory')

    parser.add_argument('--catalog', type=Path, help='Output catalog JSON file')
    parser.add_argument('--report', type=Path, help='Output report markdown file')
    parser.add_argument('--summary', type=Path, help='Output summary markdown file')
    parser.add_argument('--links', type=Path, help='Output links text file')

    args = parser.parse_args()

    # Get queries
    queries = []
    if args.query:
        queries = [args.query]
    elif args.queries_file:
        with open(args.queries_file, 'r') as f:
            queries = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        parser.error("Must provide either --query or --queries-file")

    # Search
    print("=" * 80)
    print("ACADEMIC PAPER SEARCH")
    print("=" * 80)

    papers = search_papers(
        queries=queries,
        subtopic=args.subtopic,
        year_from=args.year_from,
        max_per_query=args.max_results,
        sources=args.sources,
        scorer_type=args.scorer
    )

    if not papers:
        print("\n❌ No papers found matching criteria")
        return 1

    # Download PDFs
    if args.download:
        print(f"\n{'=' * 80}")
        print("DOWNLOADING PDFS")
        print("=" * 80)

        download_dir = args.output_dir / "downloaded"
        stats = batch_download_pdfs(papers, download_dir, max_downloads=args.max_downloads)

        print(f"\nDownload Statistics:")
        print(f"  Downloaded: {stats['downloaded']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats['skipped']}")

    # Generate outputs
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Catalog
    catalog_file = args.catalog or (args.output_dir / "papers_catalog.json")
    catalog = build_catalog(papers, query=' | '.join(queries), output_file=catalog_file)
    print(f"\n✓ Catalog: {catalog_file}")

    # Report
    if args.report:
        generate_search_report(papers, ' | '.join(queries), args.report)
        print(f"✓ Report: {args.report}")

    # Summary
    if args.summary:
        generate_summary_report(catalog, args.summary)
        print(f"✓ Summary: {args.summary}")

    # Links
    if args.links:
        links_dir = args.output_dir / "links_only"
        links_dir.mkdir(exist_ok=True)
        links_file = args.links or (links_dir / "paper_links.txt")
        create_links_file(papers, links_file, group_by='subtopic')
        print(f"✓ Links: {links_file}")

    print(f"\n{'=' * 80}")
    print("SEARCH COMPLETE")
    print("=" * 80)\n")
    print(f"Total: {len(papers)} papers")
    print(f"Catalog: {catalog_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
