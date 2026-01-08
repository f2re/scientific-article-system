#!/usr/bin/env python3
"""
Report generator for literature search results
Creates comprehensive markdown reports
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


def generate_search_report(
    papers: List[Dict],
    query: str,
    output_file: Path,
    top_n: int = 20,
    include_abstracts: bool = True
) -> str:
    """
    Generate comprehensive markdown report

    Args:
        papers: List of paper dictionaries (should be pre-sorted by relevance)
        query: Search query description
        output_file: Path to save markdown report
        top_n: Number of top papers to highlight
        include_abstracts: Include paper abstracts in report

    Returns:
        Report markdown string
    """
    # Statistics
    total_papers = len(papers)
    downloaded = sum(1 for p in papers if p.get('local_path'))
    avg_relevance = sum(p.get('relevance_score', 0) for p in papers) / total_papers if total_papers > 0 else 0
    year_range = f"{min(p['year'] for p in papers if p.get('year'))}-{max(p['year'] for p in papers if p.get('year'))}" if papers else "N/A"

    # Count by subtopic
    subtopics = {}
    for paper in papers:
        subtopic = paper.get('subtopic', 'general')
        if subtopic not in subtopics:
            subtopics[subtopic] = []
        subtopics[subtopic].append(paper)

    # Build report
    report = f"""# Literature Search Report

**Query**: {query}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

- **Total Papers Found**: {total_papers}
- **PDFs Downloaded**: {downloaded}
- **Links Only**: {total_papers - downloaded}
- **Year Range**: {year_range}
- **Average Relevance**: {avg_relevance:.1f}/10

---

## Papers by Subtopic

"""

    # Subtopic summaries
    for subtopic, subtopic_papers in sorted(subtopics.items()):
        report += f"### {subtopic.replace('_', ' ').title()}\n\n"
        report += f"**Count**: {len(subtopic_papers)} papers\n"
        report += f"**Avg Relevance**: {sum(p.get('relevance_score', 0) for p in subtopic_papers) / len(subtopic_papers):.1f}/10\n\n"

        # Top 3 in subtopic
        top_in_subtopic = sorted(subtopic_papers, key=lambda x: -x.get('relevance_score', 0))[:3]
        for paper in top_in_subtopic:
            status = "📄 PDF" if paper.get('local_path') else "🔗 Link"
            report += f"- **[{status}]** {paper['title']} ({paper.get('year', 'N/A')}) - Relevance: {paper.get('relevance_score', 0)}/10\n"
        report += "\n"

    # Top papers section
    report += f"\n---\n\n## Top {top_n} Papers by Relevance\n\n"

    for i, paper in enumerate(papers[:top_n], 1):
        # Status indicators
        pdf_status = "📄 PDF Downloaded" if paper.get('local_path') else "🔗 Link Only"

        if paper.get('source') == 'arxiv':
            source_badge = "🟢 arXiv (Open Access)"
        elif paper.get('pdf_available'):
            source_badge = "🟡 Open Access"
        else:
            source_badge = "🔴 Restricted Access"

        report += f"### {i}. [{source_badge}] {paper['title']}\n\n"
        report += f"**Status**: {pdf_status}\n\n"

        # Authors
        authors = paper.get('authors', [])
        if len(authors) <= 3:
            report += f"**Authors**: {', '.join(authors)}\n\n"
        else:
            report += f"**Authors**: {', '.join(authors[:3])} *et al.*\n\n"

        # Metadata
        report += f"**Year**: {paper.get('year', 'N/A')} | "
        report += f"**Venue**: {paper.get('venue', 'N/A')} | "
        report += f"**Relevance**: {paper.get('relevance_score', 0)}/10\n\n"

        if paper.get('citations'):
            report += f"**Citations**: {paper['citations']}\n\n"

        # Abstract
        if include_abstracts and paper.get('abstract'):
            abstract = paper['abstract'][:300]
            if len(paper['abstract']) > 300:
                abstract += "..."
            report += f"**Abstract**: {abstract}\n\n"

        # Links
        if paper.get('local_path'):
            report += f"**Local PDF**: `{paper['local_path']}`\n\n"

        if paper.get('url'):
            report += f"**URL**: {paper['url']}\n\n"

        if paper.get('pdf_url') and not paper.get('local_path'):
            report += f"**PDF URL**: {paper['pdf_url']}\n\n"

        report += "---\n\n"

    # Access guidance
    report += """
## How to Access Papers

### Open Access Papers (arXiv, Open Access Journals)
- Download directly from provided links
- Available immediately

### Restricted Access Papers
- Use institutional library access
- Contact authors via ResearchGate or email for preprints
- Use interlibrary loan services

### Recommended Databases
- **arXiv**: https://arxiv.org
- **Semantic Scholar**: https://www.semanticscholar.org
- **Google Scholar**: https://scholar.google.com
- **ResearchGate**: https://www.researchgate.net

---

## Next Steps

1. ✅ Literature search completed
2. ⏭️ Review top papers and download accessible PDFs
3. ⏭️ Request restricted papers via institutional access
4. ⏭️ Run analysis on collected PDFs
5. ⏭️ Extract methodologies and key findings

---

*Report generated by article-searcher agent*
"""

    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return report


def generate_summary_report(catalog: Dict, output_file: Path) -> str:
    """
    Generate concise summary report from catalog

    Quick overview for rapid assessment
    """
    metadata = catalog.get('search_metadata', {})
    papers = catalog.get('papers', [])

    summary = f"""# Literature Search Summary

**Query**: {metadata.get('query', 'N/A')}

**Date**: {metadata.get('date', datetime.now().isoformat())[:10]}

## Quick Stats

- **Papers**: {metadata.get('total_papers', 0)}
- **Downloaded**: {metadata.get('downloaded_pdfs', 0)} PDFs
- **Year Range**: {metadata.get('year_range', 'N/A')}
- **Avg Relevance**: {metadata.get('avg_relevance', 0)}/10

## Top 5 Must-Read Papers

"""

    # Top 5
    for i, paper in enumerate(papers[:5], 1):
        status = "✅ PDF" if paper.get('local_path') else "🔗"
        summary += f"{i}. **{status} {paper['title']}** ({paper.get('year', 'N/A')})\n"
        summary += f"   - Relevance: {paper.get('relevance_score', 0)}/10\n"
        if paper.get('citations'):
            summary += f"   - Citations: {paper['citations']}\n"
        summary += f"   - {paper.get('url', 'N/A')}\n\n"

    summary += """
## Status

✅ Search complete. Review detailed report for full paper list and access instructions.
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    return summary
