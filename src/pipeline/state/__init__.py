from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pipeline.schemas.stage1 import PlayerMap
from pipeline.schemas.stage2 import FrictionMap
from pipeline.schemas.stage3 import AssemblyRecord, PartRecord


def _path(state_dir: Path, filename: str) -> Path:
    return state_dir / filename


def save_json(state_dir: Path, filename: str, data: Any) -> None:
    path = _path(state_dir, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(state_dir: Path, filename: str) -> Optional[Any]:
    path = _path(state_dir, filename)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_player_map(state_dir: Path, player_map: PlayerMap) -> None:
    save_json(state_dir, "stage1_output.json", player_map.model_dump())


def load_player_map(state_dir: Path) -> Optional[PlayerMap]:
    data = load_json(state_dir, "stage1_output.json")
    if data is None:
        return None
    return PlayerMap.model_validate(data)


def save_friction_map(state_dir: Path, friction_map: FrictionMap) -> None:
    save_json(state_dir, "stage2_output.json", friction_map.model_dump())


def load_friction_map(state_dir: Path) -> Optional[FrictionMap]:
    data = load_json(state_dir, "stage2_output.json")
    if data is None:
        return None
    return FrictionMap.model_validate(data)


def save_taxonomy(state_dir: Path, assemblies: list[AssemblyRecord]) -> None:
    save_json(state_dir, "stage3_taxonomy.json", [a.model_dump() for a in assemblies])


def load_taxonomy(state_dir: Path) -> list[AssemblyRecord]:
    data = load_json(state_dir, "stage3_taxonomy.json")
    if data is None:
        return []
    return [AssemblyRecord.model_validate(a) for a in data]


def save_drilldown(state_dir: Path, assembly_id: str, parts: list[PartRecord]) -> None:
    drilldown_dir = state_dir / "stage3_drilldown"
    drilldown_dir.mkdir(parents=True, exist_ok=True)
    save_json(drilldown_dir, f"{assembly_id}.json", [p.model_dump() for p in parts])


def load_drilldown(state_dir: Path, assembly_id: str) -> Optional[list[PartRecord]]:
    path = state_dir / "stage3_drilldown" / f"{assembly_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return [PartRecord.model_validate(p) for p in data]
