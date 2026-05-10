from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

STALENESS_THRESHOLD_MONTHS = 24


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    fetched_content: Optional[str] = None
    publication_date: Optional[date] = None
    is_stale: bool = False
    fields: dict = field(default_factory=dict)


def search(query: str, base_url: str = "") -> list[SearchResult]:
    """
    Stub — Claude must execute the WebSearch call and pass results back.
    Prints the required query to stderr so Claude can see what to search.
    """
    print(f"[SEARCH NEEDED] query={query!r} base_url={base_url!r}", file=sys.stderr)
    return []


def fetch(url: str) -> Optional[str]:
    """
    Stub — Claude must execute the WebFetch call and pass content back.
    Prints the URL to stderr so Claude can see what to fetch.
    """
    print(f"[FETCH NEEDED] url={url!r}", file=sys.stderr)
    return None


_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

_DATE_PATTERNS = [
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),
    re.compile(r"(\d{2})/(\d{2})/(\d{4})"),
    re.compile(
        r"(January|February|March|April|May|June|July|August"
        r"|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
        re.IGNORECASE,
    ),
]


def extract_publication_date(content: str) -> Optional[date]:
    for pattern in _DATE_PATTERNS:
        match = pattern.search(content)
        if not match:
            continue
        groups = match.groups()
        try:
            if groups[0].isdigit() and len(groups[0]) == 4:
                return date(int(groups[0]), int(groups[1]), int(groups[2]))
            elif groups[2].isdigit() and len(groups[2]) == 4 and groups[0].isdigit():
                return date(int(groups[2]), int(groups[1]), int(groups[0]))
            else:
                month = _MONTH_MAP.get(groups[0].lower())
                if month:
                    return date(int(groups[2]), month, int(groups[1]))
        except (ValueError, IndexError):
            continue
    return None


def check_staleness(result: SearchResult) -> SearchResult:
    if result.publication_date is None and result.fetched_content:
        result.publication_date = extract_publication_date(result.fetched_content)
    if result.publication_date:
        cutoff = date.today() - timedelta(days=STALENESS_THRESHOLD_MONTHS * 30)
        result.is_stale = result.publication_date < cutoff
    return result


def search_with_staleness(query: str, base_url: str = "") -> list[SearchResult]:
    return [check_staleness(r) for r in search(query, base_url)]
