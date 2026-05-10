from __future__ import annotations

import sys

from pipeline.config.pe_firms import PE_FIRM_PORTFOLIO_URLS
from pipeline.config.sources import ADJACENT_TRADES
from pipeline.schemas.stage1 import OrgRecord
from pipeline.utils.search import fetch, search_with_staleness


def run_dominant_player_validation(
    category: int,
    industry: str,
    region: str,
) -> list[OrgRecord]:
    """Searches for dominant players that may have been missed in the main source loop."""
    query = f'"{industry}" dominant player market leader {region} category {category}'
    results = search_with_staleness(query)
    orgs = []
    for result in results:
        if not result.is_stale:
            orgs.append(OrgRecord(
                name=result.fields.get("name", result.title),
                source_url=result.url or "UNVERIFIED",
                category=category,
                notes="found via dominant player validation",
            ))
    return orgs


def run_adjacent_trade_search(industry: str, region: str) -> list[OrgRecord]:
    """Category 4 only: finds crossover manufacturers from adjacent trades."""
    adjacent = ADJACENT_TRADES.get(industry.lower(), [])
    orgs = []
    for trade in adjacent:
        query = f'"{trade}" manufacturer distributor crossover {region}'
        results = search_with_staleness(query)
        for result in results:
            if not result.is_stale:
                orgs.append(OrgRecord(
                    name=result.fields.get("name", result.title),
                    source_url=result.url or "UNVERIFIED",
                    category=4,
                    notes=f"found via adjacent trade: {trade}",
                ))
    return orgs


def run_pe_check(org_name: str, region: str) -> tuple[bool, str | None]:
    """
    Checks if org_name appears in any Quebec PE firm portfolio page.
    Returns (pe_backed, pe_owner_name).
    """
    for firm_name, urls in PE_FIRM_PORTFOLIO_URLS.items():
        for url in urls:
            content = fetch(url)
            if content and org_name.lower() in content.lower():
                print(
                    f"[PE CHECK] {org_name} found in {firm_name} portfolio",
                    file=sys.stderr,
                )
                return True, firm_name
    return False, None
