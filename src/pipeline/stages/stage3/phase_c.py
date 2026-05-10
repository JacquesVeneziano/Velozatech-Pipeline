from __future__ import annotations

from datetime import date
from pathlib import Path

from pipeline.stages.stage3.scripts.build_export import build_excel_export
from pipeline.state import load_drilldown


def run_phase_c(assembly_ids: list[str], state_dir: Path) -> dict:
    all_parts = []
    missing = []

    for assembly_id in assembly_ids:
        parts = load_drilldown(state_dir, assembly_id)
        if parts is None:
            missing.append(assembly_id)
            continue
        all_parts.extend(parts)

    if missing:
        return {
            "error": f"drilldown data missing for: {missing} — run phase B first"
        }

    slug = "-".join(assembly_ids)
    output_path = state_dir / f"stage3-drill-down-{slug}-{date.today()}.xlsx"
    build_excel_export(all_parts, output_path)

    return {
        "stage": 3,
        "phase": "c",
        "output_file": str(output_path),
        "part_count": len(all_parts),
        "assembly_ids": assembly_ids,
    }
