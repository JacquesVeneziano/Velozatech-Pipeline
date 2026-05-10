from __future__ import annotations

from pipeline.config.minimums import MINIMUMS
from pipeline.config.sources import CATEGORY_NAMES
from pipeline.schemas.stage1 import PlayerMap


def format_stage1_output(player_map: PlayerMap) -> dict:
    categories_out = {}
    for cat_num, orgs in player_map.categories.items():
        minimum = MINIMUMS.get(cat_num, 0)
        categories_out[str(cat_num)] = {
            "name": CATEGORY_NAMES.get(cat_num, f"Category {cat_num}"),
            "count": len(orgs),
            "minimum": minimum,
            "met_minimum": len(orgs) >= minimum,
            "orgs": [o.model_dump() for o in orgs],
        }

    return {
        "stage": 1,
        "industry": player_map.industry,
        "region": player_map.region,
        "status": "complete" if len(player_map.completed_categories) == 8 else "partial",
        "completed_categories": player_map.completed_categories,
        "flags": player_map.flags,
        "categories": categories_out,
    }
