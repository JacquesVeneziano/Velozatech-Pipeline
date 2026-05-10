from __future__ import annotations

import sys
from pathlib import Path

from pipeline.config.minimums import (
    CATEGORIES,
    MINIMUMS,
    PE_CHECK_CATEGORIES,
    PE_EMPLOYEE_THRESHOLD,
)
from pipeline.config.sources import SOURCE_REGISTRY
from pipeline.schemas.stage1 import OrgRecord, PlayerMap
from pipeline.stages.stage1.categories import search_category
from pipeline.stages.stage1.output import format_stage1_output
from pipeline.stages.stage1.validations import (
    run_adjacent_trade_search,
    run_dominant_player_validation,
    run_pe_check,
)
from pipeline.state import load_player_map, save_player_map
from pipeline.utils.dedup import dedup_merge


def run_stage1(
    industry: str,
    region: str,
    state_dir: Path,
    resume: bool = False,
) -> dict:
    player_map = PlayerMap(industry=industry, region=region)

    if resume:
        existing = load_player_map(state_dir)
        if existing:
            player_map = existing
            print(
                f"[RESUME] Completed categories: {player_map.completed_categories}",
                file=sys.stderr,
            )

    for category in CATEGORIES:
        if category in player_map.completed_categories:
            print(f"[SKIP] Category {category} already complete", file=sys.stderr)
            continue

        print(f"[START] Category {category}", file=sys.stderr)
        results: list[OrgRecord] = []

        for source_config in SOURCE_REGISTRY.get(category, []):
            new_results = search_category(source_config, industry, region, category)
            results = dedup_merge(results, new_results)
            if len(results) >= MINIMUMS[category]:
                break

        if len(results) < MINIMUMS[category]:
            msg = (
                f"Category {category}: {len(results)} results "
                f"(minimum {MINIMUMS[category]}) — below minimum"
            )
            player_map.flag(msg)
            print(f"[FLAG] {msg}", file=sys.stderr)

        validation_results = run_dominant_player_validation(category, industry, region)
        results = dedup_merge(results, validation_results)

        if category == 4:
            adjacent_results = run_adjacent_trade_search(industry, region)
            results = dedup_merge(results, adjacent_results)

        if category in PE_CHECK_CATEGORIES:
            for org in results:
                if org.employee_count and org.employee_count >= PE_EMPLOYEE_THRESHOLD:
                    org.pe_backed, org.pe_owner = run_pe_check(org.name, region)

        player_map.add(category, results)
        player_map.mark_complete(category)
        save_player_map(state_dir, player_map)
        print(f"[DONE] Category {category}: {len(results)} orgs", file=sys.stderr)

    return format_stage1_output(player_map)
