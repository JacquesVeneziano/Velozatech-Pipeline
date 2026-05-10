from __future__ import annotations

from pipeline.config.sources import SourceConfig
from pipeline.schemas.stage1 import OrgRecord
from pipeline.utils.search import search_with_staleness


def search_category(
    source: SourceConfig,
    industry: str,
    region: str,
    category: int,
    adjacent_trade: str = "",
) -> list[OrgRecord]:
    query = source.query_template.format(
        industry=industry,
        region=region,
        adjacent_trade=adjacent_trade,
    )
    results = search_with_staleness(query, base_url=source.base_url)

    orgs = []
    for result in results:
        if result.is_stale:
            continue
        orgs.append(
            OrgRecord(
                name=result.fields.get("name", result.title),
                source_url=result.url or "UNVERIFIED",
                category=category,
                employee_count=result.fields.get("employee_count"),
                notes=result.snippet,
            )
        )
    return orgs
