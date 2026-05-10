from __future__ import annotations

import sys
from pathlib import Path

from pipeline.schemas.stage2 import FrictionMap
from pipeline.stages.stage2.sources import PLAYER_TYPES, fetch_signals_for_player_type
from pipeline.stages.stage2.synthesis import synthesise_buyer_profile
from pipeline.state import load_player_map, save_friction_map


def run_stage2(industry: str, region: str, state_dir: Path) -> dict:
    player_map = load_player_map(state_dir)
    if player_map is None:
        return {"error": "stage1_output.json not found — run stage 1 first"}

    friction_map = FrictionMap(industry=industry, region=region)

    for player_type in PLAYER_TYPES:
        print(f"[STAGE2] Processing player type: {player_type}", file=sys.stderr)
        signals = fetch_signals_for_player_type(player_type, industry, region)
        profile = synthesise_buyer_profile(player_type, signals)
        friction_map.add(profile)

    save_friction_map(state_dir, friction_map)
    return friction_map.model_dump()
