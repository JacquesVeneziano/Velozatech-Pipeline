from __future__ import annotations

from pipeline.schemas.stage1 import OrgRecord

UNVERIFIED = "UNVERIFIED"


def validate_citations(orgs: list[OrgRecord]) -> tuple[list[OrgRecord], list[str]]:
    """Returns (orgs, warnings). Orgs missing source_url are flagged but not dropped."""
    warnings: list[str] = []
    for org in orgs:
        if not org.source_url or org.source_url == UNVERIFIED:
            warnings.append(
                f"{org.name} (cat {org.category}): missing source_url — flagged UNVERIFIED"
            )
    return orgs, warnings
