from __future__ import annotations

import sys
from pathlib import Path

from pipeline.schemas.stage3 import ARCHETYPES, AssemblyRecord
from pipeline.state import load_player_map, save_taxonomy
from pipeline.utils.search import fetch, search_with_staleness

PHASE_A_SOURCES: list[str] = [
    "regulatory_scope",
    "distributor_product_tree",
    "manufacturer_catalogue",
    "trade_association_standards",
    "maintenance_manuals",
    "training_materials",
    "competitor_product_listings",
]


def run_phase_a(industry: str, region: str, state_dir: Path) -> dict:
    player_map = load_player_map(state_dir)
    distributor_urls: list[tuple[str, str]] = []
    if player_map:
        for cat in [2, 3]:
            for org in player_map.categories.get(cat, []):
                if org.source_url and org.source_url != "UNVERIFIED":
                    distributor_urls.append((org.name, org.source_url))

    assemblies: list[AssemblyRecord] = []

    for source in PHASE_A_SOURCES:
        source_assemblies = _search_source(source, industry, region, distributor_urls)
        assemblies.extend(source_assemblies)

    assemblies = _deduplicate_assemblies(assemblies)
    _check_archetype_coverage(assemblies)
    save_taxonomy(state_dir, assemblies)

    return {
        "stage": 3,
        "phase": "a",
        "assembly_count": len(assemblies),
        "archetypes_covered": sorted({a.archetype for a in assemblies}),
        "assemblies": [a.model_dump() for a in assemblies],
    }


def _search_source(
    source: str,
    industry: str,
    region: str,
    distributor_urls: list[tuple[str, str]],
) -> list[AssemblyRecord]:
    results = []

    if source == "distributor_product_tree":
        for name, url in distributor_urls[:5]:  # depth-limit: top 5 distributors
            content = fetch(url)
            if content:
                results.extend(_parse_product_tree(content, name))
    else:
        query = f"{industry} {source.replace('_', ' ')} assemblies components {region}"
        for r in search_with_staleness(query):
            if not r.is_stale:
                results.append(AssemblyRecord(
                    assembly_name=r.title,
                    archetype=ARCHETYPES[0],  # Claude assigns correct archetype during synthesis
                    source=source,
                    description=r.snippet,
                ))

    return results


def _parse_product_tree(content: str, distributor_name: str) -> list[AssemblyRecord]:
    """Stub — Claude parses actual product tree HTML and maps to archetypes."""
    return []


def _deduplicate_assemblies(assemblies: list[AssemblyRecord]) -> list[AssemblyRecord]:
    seen: dict[str, AssemblyRecord] = {}
    for assembly in assemblies:
        key = assembly.assembly_name.lower().strip()
        if key not in seen:
            seen[key] = assembly
    return list(seen.values())


def _check_archetype_coverage(assemblies: list[AssemblyRecord]) -> None:
    covered = {a.archetype for a in assemblies}
    missing = set(ARCHETYPES) - covered
    if missing:
        print(f"[FLAG] Phase A: archetypes without coverage: {missing}", file=sys.stderr)
