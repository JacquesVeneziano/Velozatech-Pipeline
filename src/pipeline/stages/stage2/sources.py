from __future__ import annotations

from pipeline.utils.search import SearchResult, search_with_staleness

PLAYER_TYPES: list[str] = [
    "national_distributor",
    "regional_distributor",
    "contractor",
    "service_company",
    "manufacturer",
    "wholesaler",
]

# 14 source types, in priority order
_SOURCE_PRIORITY: list[str] = [
    "rfp_portals",
    "business_registry",
    "linkedin_company_pages",
    "industry_forums",
    "youtube_reviews",
    "employer_review_sites",
    "distributor_locator_maps",
    "trade_publications",
    "press_releases",
    "job_postings",
    "customer_reviews",
    "trade_show_exhibitor_lists",
    "surplus_dealers",
    "secondary_marketplaces",
]


def fetch_signals_for_player_type(
    player_type: str,
    industry: str,
    region: str,
) -> list[str]:
    signals: list[str] = []
    for source_type in _SOURCE_PRIORITY:
        handler = _HANDLERS.get(source_type, _noop)
        results = handler(player_type, industry, region)
        signals.extend(_to_signals(results, source_type))
    return signals


def _to_signals(results: list[SearchResult], source_type: str) -> list[str]:
    return [
        f"[{source_type}] {r.title}: {r.snippet}"
        for r in results
        if not r.is_stale
    ]


def _noop(player_type: str, industry: str, region: str) -> list[SearchResult]:
    return []


def _rfp_portals(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"{i} RFP tender {p} {r}")

def _business_registry(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"site:registreentreprises.gouv.qc.ca {i} {p}")

def _linkedin(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"site:linkedin.com {i} {p} {r}")

def _forums(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(
        f"{i} {p} problems complaints forum site:reddit.com OR site:contractortalk.com"
    )

def _youtube(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"site:youtube.com {i} {p} review problems")

def _employer_reviews(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(
        f"{i} {p} {r} site:glassdoor.com OR site:indeed.com"
    )

def _distributor_maps(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"{i} distributor locator {r}")

def _trade_publications(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"{i} trade magazine article {p} {r}")

def _press_releases(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"{i} {p} press release acquisition partnership {r}")

def _job_postings(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(
        f"site:indeed.ca OR site:jobillico.com {i} {p} {r}"
    )

def _customer_reviews(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(
        f"{i} {p} {r} reviews site:google.com OR site:yelp.ca"
    )

def _trade_shows(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"{i} trade show exhibitors {r}")

def _surplus_dealers(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(f"{i} parts surplus dealer {r}")

def _secondary_markets(p: str, i: str, r: str) -> list[SearchResult]:
    return search_with_staleness(
        f"{i} parts site:ebay.ca OR site:kijiji.ca OR site:facebook.com/marketplace {r}"
    )


_HANDLERS: dict[str, object] = {
    "rfp_portals": _rfp_portals,
    "business_registry": _business_registry,
    "linkedin_company_pages": _linkedin,
    "industry_forums": _forums,
    "youtube_reviews": _youtube,
    "employer_review_sites": _employer_reviews,
    "distributor_locator_maps": _distributor_maps,
    "trade_publications": _trade_publications,
    "press_releases": _press_releases,
    "job_postings": _job_postings,
    "customer_reviews": _customer_reviews,
    "trade_show_exhibitor_lists": _trade_shows,
    "surplus_dealers": _surplus_dealers,
    "secondary_marketplaces": _secondary_markets,
}
