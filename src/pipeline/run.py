import argparse
import json
import sys
from pathlib import Path


def _project_root() -> Path:
    """Walk up from this file until we find pyproject.toml — that's the project root."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


_DEFAULT_STATE_DIR = _project_root() / "state"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="Part opportunity vetting pipeline",
    )
    parser.add_argument("--stage", type=int, choices=[1, 2, 3], required=True)
    parser.add_argument("--industry", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--resume", action="store_true", default=False)
    parser.add_argument("--state-dir", type=Path, default=_DEFAULT_STATE_DIR)
    parser.add_argument("--phase", choices=["a", "b", "c"])
    parser.add_argument("--assembly-id")
    parser.add_argument("--assembly-ids", nargs="+")

    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True)

    if args.stage == 1:
        from pipeline.stages.stage1.runner import run_stage1
        result = run_stage1(
            industry=args.industry,
            region=args.region,
            state_dir=args.state_dir,
            resume=args.resume,
        )
    elif args.stage == 2:
        from pipeline.stages.stage2.runner import run_stage2
        result = run_stage2(
            industry=args.industry,
            region=args.region,
            state_dir=args.state_dir,
        )
    elif args.stage == 3:
        if args.phase is None:
            parser.error("--phase is required for stage 3")
        result = _run_stage3(args)

    print(json.dumps(result, indent=2, default=str))


def _run_stage3(args) -> dict:
    from pipeline.stages.stage3.phase_a import run_phase_a
    from pipeline.stages.stage3.phase_b import run_phase_b
    from pipeline.stages.stage3.phase_c import run_phase_c

    if args.phase == "a":
        return run_phase_a(
            industry=args.industry,
            region=args.region,
            state_dir=args.state_dir,
        )
    elif args.phase == "b":
        if not args.assembly_id:
            raise SystemExit("--assembly-id is required for phase b")
        return run_phase_b(
            assembly_id=args.assembly_id,
            state_dir=args.state_dir,
        )
    elif args.phase == "c":
        ids = args.assembly_ids or []
        if not ids:
            raise SystemExit("--assembly-ids is required for phase c")
        return run_phase_c(
            assembly_ids=ids,
            state_dir=args.state_dir,
        )


if __name__ == "__main__":
    main()
