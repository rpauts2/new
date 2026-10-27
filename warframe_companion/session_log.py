#!/usr/bin/env python3
"""Manual Warframe mission log. Does not read from or control the game."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOG = Path.home() / ".warframe_companion" / "missions.jsonl"


def add_entry(
    log_path: str | Path,
    mission: str,
    duration_minutes: float,
    *,
    frame: str = "",
    relic: str = "",
    reward: str = "",
    notes: str = "",
    completed: bool = True,
) -> dict[str, Any]:
    mission = mission.strip()
    if not mission:
        raise ValueError("mission must not be empty")
    if duration_minutes <= 0:
        raise ValueError("duration_minutes must be greater than zero")
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mission": mission,
        "duration_minutes": round(float(duration_minutes), 2),
        "frame": frame.strip(),
        "relic": relic.strip(),
        "reward": reward.strip(),
        "notes": notes.strip(),
        "completed": bool(completed),
    }
    path = Path(log_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_entries(log_path: str | Path) -> list[dict[str, Any]]:
    path = Path(log_path).expanduser()
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}") from exc
            if not isinstance(entry, dict):
                raise ValueError(f"Expected an object on line {line_number} in {path}")
            entries.append(entry)
    return entries


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [entry for entry in entries if entry.get("completed", True)]
    total_minutes = sum(float(entry.get("duration_minutes", 0)) for entry in completed)
    rewards = Counter(
        str(entry.get("reward", "")).strip()
        for entry in completed
        if str(entry.get("reward", "")).strip()
    )
    missions = Counter(str(entry.get("mission", "Unknown")) for entry in entries)
    hours = total_minutes / 60
    reward_rates = {
        name: round(count / hours, 2)
        for name, count in rewards.items()
    } if hours > 0 else {}
    return {
        "sessions": len(entries),
        "completed_sessions": len(completed),
        "total_minutes": round(total_minutes, 2),
        "average_minutes": round(total_minutes / len(completed), 2) if completed else 0.0,
        "rewards": dict(sorted(rewards.items())),
        "reward_rates_per_hour": dict(sorted(reward_rates.items())),
        "missions": dict(sorted(missions.items())),
    }


def export_csv(entries: list[dict[str, Any]], output_path: str | Path) -> None:
    fields = ["timestamp", "mission", "duration_minutes", "frame", "relic", "reward", "notes", "completed"]
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manual Warframe mission log and personal farming statistics")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help=f"JSONL log path (default: {DEFAULT_LOG})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Record one mission result manually")
    add.add_argument("--mission", required=True)
    add.add_argument("--minutes", required=True, type=float)
    add.add_argument("--frame", default="")
    add.add_argument("--relic", default="")
    add.add_argument("--reward", default="")
    add.add_argument("--notes", default="")
    add.add_argument("--failed", action="store_true", help="Mark this session as not completed")

    subparsers.add_parser("summary", help="Show personal statistics")
    export = subparsers.add_parser("export-csv", help="Export entries to CSV")
    export.add_argument("--output", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "add":
            entry = add_entry(
                args.log, args.mission, args.minutes, frame=args.frame, relic=args.relic,
                reward=args.reward, notes=args.notes, completed=not args.failed,
            )
            print(f"Saved: {entry['mission']} | {entry['duration_minutes']} min")
        elif args.command == "summary":
            stats = summarize(read_entries(args.log))
            print(f"Sessions: {stats['sessions']} (completed: {stats['completed_sessions']})")
            print(f"Completed mission time: {stats['total_minutes']} min")
            print(f"Average completed session: {stats['average_minutes']} min")
            print("Missions:")
            for name, count in stats["missions"].items():
                print(f"  {name}: {count}")
            print("Recorded rewards:")
            if stats["rewards"]:
                for name, count in stats["rewards"].items():
                    print(f"  {name}: {count}")
            else:
                print("  (none recorded)")
        elif args.command == "export-csv":
            export_csv(read_entries(args.log), args.output)
            print(f"Exported to {args.output}")
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
