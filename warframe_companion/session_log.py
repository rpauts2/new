#!/usr/bin/env python3
"""Manual Warframe mission log. Does not read from or control the game."""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOG = Path.home() / ".warframe_companion" / "missions.jsonl"


def _validated_duration(value: Any, *, label: str = "duration_minutes") -> float:
    try:
        duration = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number greater than zero") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"{label} must be a finite number greater than zero")
    return duration


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
    duration = _validated_duration(duration_minutes)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mission": mission,
        "duration_minutes": round(duration, 2),
        "frame": frame.strip(),
        "relic": relic.strip(),
        "reward": reward.strip(),
        "notes": notes.strip(),
        "completed": bool(completed),
    }
    path = Path(log_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + "\n")
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


def backup_log(log_path: str | Path, backup_path: str | Path | None = None) -> Path:
    """Validate and copy the log before any destructive operation."""
    source = Path(log_path).expanduser()
    if not source.exists():
        raise ValueError(f"Log file does not exist: {source}")
    read_entries(source)
    if backup_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = source.with_name(f"{source.name}.{stamp}.backup")
        suffix = 1
        while destination.exists():
            destination = source.with_name(f"{source.name}.{stamp}.{suffix}.backup")
            suffix += 1
    else:
        destination = Path(backup_path).expanduser()
    if source.resolve() == destination.resolve():
        raise ValueError("Backup destination must differ from the log file.")
    if destination.exists():
        raise FileExistsError(f"Backup already exists; refusing to overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental overwrite if another backup races us.
    with destination.open("xb") as stream:
        with source.open("rb") as original:
            shutil.copyfileobj(original, stream)
    shutil.copystat(source, destination)
    return destination


def clear_log(log_path: str | Path, *, confirm: bool = False) -> Path:
    """Back up the valid log, then empty it. Explicit confirmation is mandatory."""
    if not confirm:
        raise ValueError("Clearing history requires explicit confirmation (--confirm).")
    source = Path(log_path).expanduser()
    backup = backup_log(source)
    # Only truncate after the backup exists and has been created successfully.
    with source.open("w", encoding="utf-8"):
        pass
    return backup


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    completed: list[dict[str, Any]] = []
    rewards: Counter[str] = Counter()
    missions: Counter[str] = Counter()
    frames: Counter[str] = Counter()
    mission_minutes: dict[str, float] = defaultdict(float)
    frame_minutes: dict[str, float] = defaultdict(float)
    mission_completed: Counter[str] = Counter()
    frame_completed: Counter[str] = Counter()
    total_minutes = 0.0

    for index, entry in enumerate(entries, 1):
        mission = str(entry.get("mission") or "Unknown").strip() or "Unknown"
        frame = str(entry.get("frame") or "").strip() or "Not recorded"
        missions[mission] += 1
        frames[frame] += 1
        is_completed = entry.get("completed", True)
        if not isinstance(is_completed, bool):
            raise ValueError(f"completed must be true or false in session entry {index}")
        if not is_completed:
            continue
        duration = _validated_duration(entry.get("duration_minutes", 0), label=f"duration_minutes in session entry {index}")
        completed.append(entry)
        total_minutes += duration
        mission_minutes[mission] += duration
        frame_minutes[frame] += duration
        mission_completed[mission] += 1
        frame_completed[frame] += 1
        reward = str(entry.get("reward", "")).strip()
        if reward:
            rewards[reward] += 1

    hours = total_minutes / 60
    reward_rates = {name: round(count / hours, 2) for name, count in rewards.items()} if hours > 0 else {}

    def grouped(counts: Counter[str], minutes: dict[str, float], done: Counter[str]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for name, count in sorted(counts.items()):
            completed_count = done[name]
            elapsed = minutes[name]
            result[name] = {
                "sessions": count,
                "completed_sessions": completed_count,
                "completed_minutes": round(elapsed, 2),
                "average_completed_minutes": round(elapsed / completed_count, 2) if completed_count else 0.0,
            }
        return result

    return {
        "sessions": len(entries),
        "completed_sessions": len(completed),
        "total_minutes": round(total_minutes, 2),
        "average_minutes": round(total_minutes / len(completed), 2) if completed else 0.0,
        "rewards": dict(sorted(rewards.items())),
        "reward_rates_per_hour": dict(sorted(reward_rates.items())),
        "missions": dict(sorted(missions.items())),
        "frames": dict(sorted(frames.items())),
        "by_mission": grouped(missions, mission_minutes, mission_completed),
        "by_frame": grouped(frames, frame_minutes, frame_completed),
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
    backup = subparsers.add_parser("backup", help="Create a validated backup of the log")
    backup.add_argument("--output", type=Path, help="Optional backup destination")
    clear = subparsers.add_parser("clear", help="Back up and clear the log")
    clear.add_argument("--confirm", action="store_true", help="Required confirmation; a backup is created first")

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
            print("By mission:")
            for name, row in stats["by_mission"].items():
                print(f"  {name}: {row['sessions']} runs, {row['completed_minutes']} completed min, average {row['average_completed_minutes']} min")
            print("By frame:")
            for name, row in stats["by_frame"].items():
                print(f"  {name}: {row['sessions']} runs, {row['completed_minutes']} completed min, average {row['average_completed_minutes']} min")
            print("Recorded rewards:")
            if stats["rewards"]:
                for name, count in stats["rewards"].items():
                    rate = stats["reward_rates_per_hour"].get(name, 0)
                    print(f"  {name}: {count} (observed logging rate: {rate}/hour)")
            else:
                print("  (none recorded)")
        elif args.command == "export-csv":
            export_csv(read_entries(args.log), args.output)
            print(f"Exported to {args.output}")
        elif args.command == "backup":
            path = backup_log(args.log, args.output)
            print(f"Backup created: {path}")
        elif args.command == "clear":
            path = clear_log(args.log, confirm=args.confirm)
            print(f"History cleared. Backup saved to: {path}")
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
