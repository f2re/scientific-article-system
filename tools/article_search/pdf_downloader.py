#!/usr/bin/env python3
"""
PDF download utilities with validation
"""

import requests
import time
from pathlib import Path
from typing import Optional

DOWNLOAD_DELAY = 2.0  # Delay between downloads
USER_AGENT = "Scientific-Research-Bot/1.0 (academic-research; contact@research.edu)"


def download_pdf(url: str, filename: Path, verify_pdf: bool = True) -> bool:
    """
    Download PDF file with validation

    Args:
        url: PDF URL to download
        filename: Target filename (Path object)
        verify_pdf: Verify PDF header after download

    Returns:
        True if download successful, False otherwise
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, stream=True, timeout=90)
        time.sleep(DOWNLOAD_DELAY)

        if response.status_code == 200:
            # Write file
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify it's a valid PDF
            if verify_pdf:
                with open(filename, 'rb') as f:
                    header = f.read(4)
                    if header == b'%PDF':
                        return True
                    else:
                        # Not a valid PDF, remove file
                        filename.unlink()
                        print(f"Invalid PDF: {filename.name}")
                        return False
            return True
        else:
            print(f"HTTP {response.status_code}: {url}")
            return False

    except Exception as e:
        print(f"Download error ({filename.name}): {e}")
        # Clean up partial file
        if filename.exists():
            filename.unlink()
        return False


def download_arxiv_pdf(arxiv_id: str, download_dir: Path) -> Optional[Path]:
    """
    Download arXiv PDF by ID

    Args:
        arxiv_id: arXiv identifier (e.g., "2212.12794")
        download_dir: Directory to save PDF

    Returns:
        Path to downloaded file or None if failed
    """
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    safe_id = arxiv_id.replace('/', '_').replace(':', '_')
    filename = download_dir / f"arxiv_{safe_id}.pdf"

    if filename.exists():
        return filename  # Already downloaded

    if download_pdf(url, filename):
        return filename
    return None


def batch_download_pdfs(papers: list, download_dir: Path, max_downloads: Optional[int] = None) -> dict:
    """
    Download multiple PDFs from paper list

    Args:
        papers: List of paper dictionaries with 'pdf_url' field
        download_dir: Directory to save PDFs
        max_downloads: Maximum number of PDFs to download (None = all)

    Returns:
        Dictionary with download statistics and updated paper list
    """
    download_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    failed = 0
    skipped = 0

    for i, paper in enumerate(papers):
        if max_downloads and downloaded >= max_downloads:
            skipped += len(papers) - i
            break

        if not paper.get('pdf_url'):
            skipped += 1
            continue

        # Generate safe filename
        paper_id = paper.get('id', f'paper_{i}').replace(':', '_').replace('/', '_')
        filename = download_dir / f"{paper_id}.pdf"

        if filename.exists():
            paper['local_path'] = str(filename)
            downloaded += 1
            continue

        print(f"[{i+1}/{len(papers)}] Downloading: {paper['title'][:60]}...")

        if download_pdf(paper['pdf_url'], filename):
            paper['local_path'] = str(filename)
            downloaded += 1
        else:
            failed += 1

    return {
        'downloaded': downloaded,
        'failed': failed,
        'skipped': skipped,
        'total': len(papers)
    }
