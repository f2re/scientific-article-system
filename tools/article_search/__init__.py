"""
Article Search Tools
Unified toolkit for searching and managing academic literature
"""

from .search_apis import (
    search_semantic_scholar,
    search_arxiv,
    fetch_arxiv_by_id,
    normalize_paper_s2,
    normalize_paper_arxiv
)

from .pdf_downloader import (
    download_pdf,
    download_arxiv_pdf,
    batch_download_pdfs
)

from .relevance_scorer import (
    calculate_relevance,
    score_atmospheric_profile_paper,
    score_ml_weather_paper,
    filter_by_relevance
)

from .catalog_builder import (
    build_catalog,
    load_catalog,
    merge_catalogs,
    export_to_bibtex,
    create_links_file
)

from .report_generator import (
    generate_search_report,
    generate_summary_report
)

__version__ = "1.0.0"
__all__ = [
    # Search APIs
    'search_semantic_scholar',
    'search_arxiv',
    'fetch_arxiv_by_id',
    'normalize_paper_s2',
    'normalize_paper_arxiv',

    # PDF Downloader
    'download_pdf',
    'download_arxiv_pdf',
    'batch_download_pdfs',

    # Relevance Scoring
    'calculate_relevance',
    'score_atmospheric_profile_paper',
    'score_ml_weather_paper',
    'filter_by_relevance',

    # Catalog Builder
    'build_catalog',
    'load_catalog',
    'merge_catalogs',
    'export_to_bibtex',
    'create_links_file',

    # Report Generator
    'generate_search_report',
    'generate_summary_report',
]
