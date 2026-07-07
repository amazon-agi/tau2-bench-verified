#!/usr/bin/env python3
"""Scan simulation result JSON files in a folder and produce a CSV report."""

import argparse
import csv
import json
import sys
from collections import defaultdict
from math import comb
from pathlib import Path


def pass_hat_k_task(num_trials: int, num_successes: int, k: int) -> float:
    """Compute per-task pass^k: C(successes, k) / C(trials, k)."""
    if num_trials < k:
        return 0.0
    return comb(num_successes, k) / comb(num_trials, k)


def process_file(filepath):
    try:
        with open(filepath) as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Warning: skipping {filepath.name} (invalid JSON: {e})", file=sys.stderr)
        return None

    simulations = data.get("simulations", [])
    n = len(simulations)
    if n == 0:
        return None

    tasks = defaultdict(list)
    for s in simulations:
        reward = (s.get("reward_info") or {}).get("reward", 0.0)
        tasks[s.get("task_id")].append(reward)

    passed = sum(1 for s in simulations if (s.get("reward_info") or {}).get("reward") == 1.0)

    def avg_pass_k(k):
        scores = []
        for trials in tasks.values():
            n_t = len(trials)
            successes = sum(1 for r in trials if r == 1.0)
            scores.append(pass_hat_k_task(n_t, successes, k))
        return sum(scores) / len(scores) if scores else 0.0

    total_duration = 0
    total_cost = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_user_turns = 0
    total_knl_toolcalls = 0
    total_other_toolcalls = 0

    knowledge_tools = {"list_articles", "get_article"}

    for sim in simulations:
        total_duration += sim.get("duration", 0) or 0
        total_cost += sim.get("agent_cost", 0) or 0

        messages = sim.get("messages", [])
        total_user_turns += sum(1 for m in messages if m.get("role") == "user")

        for msg in messages:
            usage = msg.get("usage")
            if usage:
                total_prompt_tokens += usage.get("prompt_tokens", 0)
                total_completion_tokens += usage.get("completion_tokens", 0)

            tool_calls = msg.get("tool_calls") or []
            for tc in tool_calls:
                fn_name = tc.get("name") or ""
                if fn_name in knowledge_tools:
                    total_knl_toolcalls += 1
                else:
                    total_other_toolcalls += 1

    return {
        "file": filepath.name,
        "n": n,
        "passed": passed,
        "pass^1": round(avg_pass_k(1), 4),
        "pass^2": round(avg_pass_k(2), 4),
        "avg_duration": round(total_duration / n, 2),
        "avg_cost": round(total_cost / n, 6),
        "avg_prompt_tokens": round(total_prompt_tokens / n, 1),
        "avg_completion_tokens": round(total_completion_tokens / n, 1),
        "avg_total_tokens": round((total_prompt_tokens + total_completion_tokens) / n, 1),
        "avg_turns": round(total_user_turns / n, 2),
        "avg_knl_toolcalls": round(total_knl_toolcalls / n, 2),
        "avg_otoolcalls": round(total_other_toolcalls / n, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate CSV report from simulation results")
    parser.add_argument("folder", help="Folder containing simulation JSON files")
    parser.add_argument("-s", "--single", help="Process only this file within the folder")
    parser.add_argument("-o", "--output", help="Output CSV file (default: stdout)")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory", file=sys.stderr)
        sys.exit(1)

    if args.single:
        single = folder / args.single
        if not single.is_file():
            print(f"Error: {single} not found", file=sys.stderr)
            sys.exit(1)
        files = [single]
    else:
        files = sorted(folder.glob("*.json"))
        if not files:
            print(f"No JSON files found in {folder}", file=sys.stderr)
            sys.exit(1)

    fieldnames = [
        "file", "n", "passed", "pass^1", "pass^2",
        "avg_duration", "avg_cost",
        "avg_prompt_tokens", "avg_completion_tokens", "avg_total_tokens",
        "avg_turns", "avg_knl_toolcalls", "avg_otoolcalls",
    ]

    rows = []
    for filepath in files:
        row = process_file(filepath)
        if row:
            rows.append(row)

    out = open(args.output, "w", newline="") if args.output else sys.stdout
    writer = csv.DictWriter(out, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    if args.output:
        out.close()
        print(f"Report written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
