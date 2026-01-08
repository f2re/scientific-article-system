#!/usr/bin/env python3
"""
Relevance scoring for academic papers
Calculates relevance score based on keywords, citations, and context
"""

from typing import Dict, List, Optional


def calculate_relevance(
    paper: Dict,
    core_keywords: List[str],
    high_priority_keywords: Optional[List[str]] = None,
    medium_priority_keywords: Optional[List[str]] = None,
    context_keywords: Optional[List[str]] = None,
    boost_citations: bool = True
) -> float:
    """
    Calculate relevance score (1.0 to 10.0) for a paper

    Args:
        paper: Paper dictionary with 'title', 'abstract', 'citations' fields
        core_keywords: Core topic keywords (highest weight)
        high_priority_keywords: Important keywords (medium-high weight)
        medium_priority_keywords: Useful keywords (medium weight)
        context_keywords: Contextual keywords (low weight)
        boost_citations: Add citation-based boost

    Returns:
        Relevance score from 1.0 to 10.0
    """
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower()

    score = 5.0  # Base score

    # Core keywords (highest priority)
    if core_keywords:
        for keyword in core_keywords:
            if keyword.lower() in title:
                score += 2.0
            elif keyword.lower() in abstract:
                score += 1.0

    # High priority keywords
    if high_priority_keywords:
        for keyword in high_priority_keywords:
            if keyword.lower() in title:
                score += 1.5
            elif keyword.lower() in abstract:
                score += 0.5

    # Medium priority keywords
    if medium_priority_keywords:
        for keyword in medium_priority_keywords:
            if keyword.lower() in title:
                score += 1.0
            elif keyword.lower() in abstract:
                score += 0.3

    # Context keywords (domain-specific)
    if context_keywords:
        context_count = sum(1 for kw in context_keywords if kw.lower() in abstract)
        score += min(2.0, context_count * 0.3)

    # Citation boost (for high-impact papers)
    if boost_citations:
        citations = paper.get('citations', 0)
        if citations > 100:
            score += 1.5
        elif citations > 50:
            score += 1.0
        elif citations > 20:
            score += 0.5

    # Cap at 10.0
    return min(10.0, max(1.0, score))


def score_atmospheric_profile_paper(paper: Dict) -> float:
    """
    Score paper for atmospheric vertical profile reconstruction topic

    Pre-configured keyword sets for atmospheric profiling research
    """
    core_keywords = [
        'radiosonde', 'stratosphere', 'stratospheric',
        'vertical profile', 'atmospheric profile',
        'upper atmosphere', 'sounding', '0.1 hpa'
    ]

    high_priority_keywords = [
        'profile reconstruction', 'profile retrieval', 'extrapolation',
        'gps-ro', 'gps radio occultation', 'temperature profile',
        'humidity profile', 'reanalysis', 'era5', 'merra'
    ]

    medium_priority_keywords = [
        'interpolation', 'data assimilation', 'satellite',
        'upper air', 'meteorological', 'atmospheric model'
    ]

    context_keywords = [
        'machine learning', 'neural network', 'deep learning',
        'weather forecasting', 'climate model', 'numerical prediction'
    ]

    return calculate_relevance(
        paper,
        core_keywords=core_keywords,
        high_priority_keywords=high_priority_keywords,
        medium_priority_keywords=medium_priority_keywords,
        context_keywords=context_keywords,
        boost_citations=True
    )


def score_ml_weather_paper(paper: Dict) -> float:
    """
    Score paper for machine learning in weather forecasting

    Pre-configured for ML/DL weather prediction research
    """
    core_keywords = [
        'weather forecasting', 'weather prediction',
        'transformer weather', 'neural network weather'
    ]

    high_priority_keywords = [
        'machine learning', 'deep learning', 'neural network',
        'transformer', 'attention mechanism', 'graphcast', 'pangu'
    ]

    medium_priority_keywords = [
        'meteorological', 'atmospheric', 'climate model',
        'numerical weather prediction', 'data-driven'
    ]

    context_keywords = [
        'vertical profile', 'temperature', 'precipitation',
        'reanalysis', 'era5', 'benchmark'
    ]

    return calculate_relevance(
        paper,
        core_keywords=core_keywords,
        high_priority_keywords=high_priority_keywords,
        medium_priority_keywords=medium_priority_keywords,
        context_keywords=context_keywords,
        boost_citations=True
    )


def filter_by_relevance(papers: List[Dict], min_score: float = 5.0, scorer_func=None) -> List[Dict]:
    """
    Filter papers by relevance score

    Args:
        papers: List of paper dictionaries
        min_score: Minimum relevance score threshold
        scorer_func: Scoring function (uses atmospheric_profile by default)

    Returns:
        Filtered and scored list of papers
    """
    if scorer_func is None:
        scorer_func = score_atmospheric_profile_paper

    scored_papers = []
    for paper in papers:
        score = scorer_func(paper)
        if score >= min_score:
            paper['relevance_score'] = round(score, 1)
            scored_papers.append(paper)

    # Sort by relevance
    scored_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
    return scored_papers
