#!/usr/bin/env python3
"""Split a tau2-bench results file into one JSON file per simulation.

A results file contains a top-level ``simulations`` list; each entry is a
single trajectory tagged with ``task_id`` and ``trial``. This script writes
each simulation to its own file named ``task_<task_id>_trial_<trial>.json``
in the target directory.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def _safe(value) -> str:
    """Make a value safe to embed in a filename."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(value))


def split_trajectories(trajectory_file: Path, target_dir: Path) -> int:
    with trajectory_file.open() as f:
        data = json.load(f)

    simulations = data.get("simulations")
    if not isinstance(simulations, list):
        raise ValueError(
            f"{trajectory_file}: expected a top-level 'simulations' list, "
            f"got {type(simulations).__name__}"
        )

    target_dir.mkdir(parents=True, exist_ok=True)

    used: dict[str, int] = {}
    for sim in simulations:
        base = f"task_{_safe(sim.get('task_id'))}_trial_{_safe(sim.get('trial'))}"
        # Disambiguate if the same (task_id, trial) appears more than once.
        seen = used.get(base, 0)
        used[base] = seen + 1
        name = base if seen == 0 else f"{base}_{seen}"
        sim["system_prompt"] = data.get("info").get("environment_info").get("policy")
        out_path = target_dir / f"{name}.json"
        with out_path.open("w") as f:
            json.dump(sim, f, indent=2)

    return len(simulations)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trajectory_file", type=Path, help="Path to the results JSON file")
    parser.add_argument("target_dir", type=Path, help="Directory to write per-simulation files into")
    args = parser.parse_args()

    if not args.trajectory_file.is_file():
        parser.error(f"trajectory file not found: {args.trajectory_file}")

    count = split_trajectories(args.trajectory_file, args.target_dir)
    print(f"Wrote {count} trajectories to {args.target_dir}")


if __name__ == "__main__":
    main()
