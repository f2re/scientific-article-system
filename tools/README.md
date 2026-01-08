# Article Search Tools

Unified toolkit for searching and managing academic literature.

## Overview

The article search tools provide a clean, modular interface for:
- Searching academic papers via Semantic Scholar and arXiv APIs
- Downloading PDFs with validation
- Scoring papers by relevance
- Building structured catalogs
- Generating comprehensive reports

## Structure

```
tools/
├── search_papers.py          # Main CLI tool
└── article_search/           # Python package
    ├── __init__.py
    ├── search_apis.py        # API wrappers
    ├── pdf_downloader.py     # PDF download utilities
    ├── relevance_scorer.py   # Relevance scoring algorithms
    ├── catalog_builder.py    # Catalog generation
    └── report_generator.py   # Report generation
```

## Quick Start

### Basic Search

```bash
python3 tools/search_papers.py \
  --query "machine learning weather forecasting" \
  --year-from 2021 \
  --download \
  --output-dir papers
```

### Multi-Query Search with File

```bash
# Create query file
cat > queries.txt << 'EOF'
transformer weather prediction
neural network atmospheric modeling
deep learning precipitation forecast
EOF

# Execute search
python3 tools/search_papers.py \
  --queries-file queries.txt \
  --scorer ml_weather \
  --download \
  --max-downloads 50
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--query` | Single search query | Required* |
| `--queries-file` | File with multiple queries | Required* |
| `--year-from` | Minimum publication year | 2021 |
| `--max-results` | Max results per query | 20 |
| `--sources` | Search sources (arxiv, semantic_scholar) | both |
| `--scorer` | Relevance scoring (atmospheric, ml_weather, general) | atmospheric |
| `--download` | Download PDFs automatically | False |
| `--max-downloads` | Maximum PDFs to download | 50 |
| `--output-dir` | Output directory | papers |
| `--catalog` | Output catalog JSON file | auto |
| `--report` | Output detailed report | optional |
| `--summary` | Output summary report | optional |
| `--links` | Output links file | optional |

*Either `--query` or `--queries-file` required

## Python API Usage

### Search APIs

```python
from article_search import search_semantic_scholar, search_arxiv

# Search Semantic Scholar
papers = search_semantic_scholar("transformers in weather", year_from=2022, limit=20)

# Search arXiv
papers = search_arxiv("neural network atmospheric", max_results=30, year_from=2021)
```

### Download PDFs

```python
from article_search import batch_download_pdfs
from pathlib import Path

stats = batch_download_pdfs(papers, Path("papers/downloaded"), max_downloads=50)
print(f"Downloaded: {stats['downloaded']}")
```

### Score Papers

```python
from article_search import filter_by_relevance, score_atmospheric_profile_paper

# Score and filter papers
scored_papers = filter_by_relevance(
    papers,
    min_score=7.0,
    scorer_func=score_atmospheric_profile_paper
)
```

### Build Catalog

```python
from article_search import build_catalog
from pathlib import Path

catalog = build_catalog(
    papers,
    query="Atmospheric vertical profiles",
    output_file=Path("papers/catalog.json")
)
```

### Generate Reports

```python
from article_search import generate_search_report

generate_search_report(
    papers,
    query="ML in meteorology",
    output_file=Path("papers/report.md"),
    top_n=20
)
```

## Scoring Algorithms

### Atmospheric Profile Scoring
```python
from article_search import score_atmospheric_profile_paper

score = score_atmospheric_profile_paper(paper)  # Returns 1.0-10.0
```

Optimized keywords:
- Core: radiosonde, stratosphere, vertical profile, upper atmosphere, sounding
- High: profile reconstruction, GPS-RO, temperature profile, reanalysis, ERA5
- Medium: interpolation, data assimilation, satellite, meteorological
- Context: machine learning, neural network, weather forecasting

### ML Weather Scoring
```python
from article_search import score_ml_weather_paper

score = score_ml_weather_paper(paper)
```

Optimized keywords:
- Core: weather forecasting, weather prediction, transformer weather
- High: machine learning, deep learning, neural network, GraphCast, Pangu
- Medium: meteorological, atmospheric, climate model, NWP
- Context: vertical profile, temperature, precipitation, benchmark

## Rate Limits

**Semantic Scholar**: 1 request/second (automatic delays)
**arXiv**: 3 seconds between requests (automatic delays)
**PDF Downloads**: 2 seconds between files

All delays are handled automatically by the tools.

## Output Format

### Catalog JSON Structure

```json
{
  "search_metadata": {
    "query": "search query",
    "date": "2026-01-08T...",
    "total_papers": 100,
    "downloaded_pdfs": 45,
    "year_range": "2021-2026",
    "avg_relevance": 8.3
  },
  "subtopic_counts": {
    "ml_methods": 30,
    "data_assimilation": 25
  },
  "papers": [
    {
      "id": "arxiv:2212.12794",
      "title": "...",
      "authors": [...],
      "year": 2023,
      "abstract": "...",
      "citations": 234,
      "venue": "Science",
      "url": "https://...",
      "pdf_url": "https://...",
      "local_path": "papers/downloaded/...",
      "subtopic": "ml_methods",
      "relevance_score": 9.5
    }
  ]
}
```

## Integration with article-searcher Agent

The article-searcher agent (.claude/agents/article-searcher.md) uses this unified tool:

```bash
# Agent workflow
1. Create search queries file
2. Run: python3 tools/search_papers.py --queries-file ...
3. Generate catalog and reports automatically
4. Pass catalog to downstream agents (analyzer, writers)
```

## Error Handling

**No papers found:**
- Broaden search terms
- Reduce year constraint
- Check API connectivity

**Download failures:**
- Many papers require institutional access
- Use author preprints or contact directly
- Check PDF URL validity

**API errors:**
- Verify internet connection
- Respect rate limits
- Reduce --max-results if timing out

## Best Practices

1. **Query formulation**: Use specific technical terms, include method names
2. **Year range**: Default 2021+ for current research, extend for comprehensive reviews
3. **Downloads**: Start with 50-100 PDFs, check quality before scaling
4. **Ethics**: Only download Open Access content, respect rate limits
5. **Verification**: Check catalog and report after completion

## Dependencies

```bash
pip install requests feedparser
```

Built-in Python libraries used:
- json, pathlib, datetime, urllib.parse, collections

---

**Version**: 1.0.0
**Last Updated**: 2026-01-08
