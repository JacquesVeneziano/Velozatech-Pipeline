from __future__ import annotations

import re
from pathlib import Path

from pipeline.schemas.stage3 import PartRecord
from pipeline.state import load_taxonomy, save_drilldown
from pipeline.utils.search import search_with_staleness


def run_phase_b(assembly_id: str, state_dir: Path) -> dict:
    taxonomy = load_taxonomy(state_dir)
    assembly = next(
        (a for a in taxonomy if _to_id(a.assembly_name) == assembly_id),
        None,
    )

    if assembly is None:
        return {
            "error": f"assembly_id {assembly_id!r} not found in taxonomy — run phase A first"
        }

    parts = _decompose_assembly(assembly_id, assembly.assembly_name)
    save_drilldown(state_dir, assembly_id, parts)

    return {
        "stage": 3,
        "phase": "b",
        "assembly_id": assembly_id,
        "part_count": len(parts),
        "parts": [p.model_dump() for p in parts],
    }


def _decompose_assembly(assembly_id: str, assembly_name: str) -> list[PartRecord]:
    queries = [
        f"{assembly_name} parts list bill of materials BOM",
        f"{assembly_name} OEM part numbers catalogue",
        f"{assembly_name} replacement parts distributor",
    ]
    parts: list[PartRecord] = []
    for query in queries:
        for result in search_with_staleness(query):
            if not result.is_stale:
                parts.append(PartRecord(
                    assembly_id=assembly_id,
                    part_name=result.fields.get("part_name", result.title),
                    oem_part_number=result.fields.get("oem_part_number", "UNVERIFIED"),
                    brand=result.fields.get("brand", "UNVERIFIED"),
                    description=result.snippet,
                    source_url=result.url or "UNVERIFIED",
                ))
    return parts


def _to_id(name: str) -> str:
    return re.sub(r"[^\w]+", "_", name.lower()).strip("_")
