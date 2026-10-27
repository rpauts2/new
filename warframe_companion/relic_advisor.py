#!/usr/bin/env python3
"""Search a local WFCD relic dataset for relics containing a requested reward.

This module never guesses probabilities: it displays only chance values present
in the selected data file and identifies the file as the source.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_DATA_URL = "https://raw.githubusercontent.com/WFCD/warframe-drop-data/main/data/relics.json"
USER_AGENT = "WarframeCompanion/0.1 (relic data downloader)"


def normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def _extract_relics(payload: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata: dict[str, Any] = {}
    if isinstance(payload, list):
        relics = payload
    elif isinstance(payload, dict):
        metadata = {key: payload[key] for key in ("timestamp", "modified", "hash", "version") if key in payload}
        relics = payload.get("relics")
        if relics is None and isinstance(payload.get("data"), dict):
            relics = payload["data"].get("relics")
    else:
        relics = None
    if not isinstance(relics, list):
        raise ValueError("Expected a relic list, or an object containing a 'relics' list.")
    valid = [entry for entry in relics if isinstance(entry, dict)]
    if not valid:
        raise ValueError("The dataset contains no valid relic records.")
    return valid, metadata


def load_dataset(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = Path(path).expanduser()
    try:
        with source.open("r", encoding="utf-8-sig") as stream:
            payload = json.load(stream)
    except OSError as exc:
        raise ValueError(f"Cannot read data file '{source}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{source}' at line {exc.lineno}, column {exc.colno}") from exc
    relics, metadata = _extract_relics(payload)
    sidecar = source.with_name(source.name + ".meta.json")
    if sidecar.exists():
        try:
            with sidecar.open("r", encoding="utf-8") as stream:
                local_metadata = json.load(stream)
            if isinstance(local_metadata, dict):
                metadata = {**metadata, **local_metadata}
        except (OSError, json.JSONDecodeError):
            # A damaged metadata sidecar must not make the valid relic data unusable.
            pass
    return relics, metadata


def download_dataset(
    destination: str | Path,
    *,
    url: str = DEFAULT_DATA_URL,
    timeout: float = 20.0,
) -> Path:
    """Download WFCD relic JSON and replace the cache only after validation."""
    target = Path(destination).expanduser()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    response_headers: dict[str, str] = {}
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            headers = getattr(response, "headers", {})
            response_headers = {
                key: headers.get(key, "")
                for key in ("ETag", "Last-Modified")
                if headers.get(key)
            }
    except (OSError, urllib.error.URLError) as exc:
        raise ValueError(f"Could not download relic data from {url}: {exc}") from exc

    try:
        payload = json.loads(raw.decode("utf-8-sig"))
        _extract_relics(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Downloaded data from {url} is not a valid relic dataset: {exc}") from exc

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".download.tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()

    sidecar = target.with_name(target.name + ".meta.json")
    sidecar_temp = sidecar.with_name(sidecar.name + ".tmp")
    source_metadata = {
        "source_url": url,
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **response_headers,
    }
    try:
        sidecar_temp.write_text(json.dumps(source_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sidecar_temp.replace(sidecar)
    finally:
        if sidecar_temp.exists():
            sidecar_temp.unlink()
    return target


def _reward_rows(relic: dict[str, Any]) -> list[tuple[str, Any, str]]:
    """Return (reward name, chance, state) rows from known WFCD-like shapes."""
    rewards = relic.get("rewards", [])
    rows: list[tuple[str, Any, str]] = []

    def append_reward(entry: Any, state: str = "") -> None:
        if not isinstance(entry, dict):
            return
        name = entry.get("itemName") or entry.get("name") or entry.get("item")
        if name:
            rows.append((str(name), entry.get("chance", entry.get("probability")), state or str(entry.get("state", ""))))

    if isinstance(rewards, list):
        for reward in rewards:
            append_reward(reward, str(reward.get("state", "")) if isinstance(reward, dict) else "")
    elif isinstance(rewards, dict):
        for state, state_rewards in rewards.items():
            if isinstance(state_rewards, list):
                for reward in state_rewards:
                    append_reward(reward, str(state))
            elif isinstance(state_rewards, dict):
                # Some formats wrap a list in a named property.
                nested = state_rewards.get("rewards")
                if isinstance(nested, list):
                    for reward in nested:
                        append_reward(reward, str(state))
    return rows


def find_relics(
    relics: list[dict[str, Any]],
    item_query: str,
    *,
    tier: str = "",
    state: str = "",
    exact: bool = False,
) -> list[dict[str, Any]]:
    query = normalize(item_query)
    if not query:
        raise ValueError("Item search must not be empty.")
    tier_query = normalize(tier)
    state_query = normalize(state)
    matches: list[dict[str, Any]] = []

    for relic in relics:
        relic_tier = str(relic.get("tier", ""))
        relic_name = str(relic.get("relicName") or relic.get("name") or "")
        relic_state = str(relic.get("state", ""))
        if tier_query and normalize(relic_tier) != tier_query:
            continue
        if state_query and relic_state and normalize(relic_state) != state_query:
            # If states are attached to individual rewards, filter below instead.
            if not isinstance(relic.get("rewards"), dict):
                continue

        for reward_name, chance, reward_state in _reward_rows(relic):
            normalized_name = normalize(reward_name)
            if (normalized_name != query if exact else query not in normalized_name):
                continue
            effective_state = reward_state or relic_state
            if state_query and normalize(effective_state) != state_query:
                continue
            matches.append({
                "tier": relic_tier,
                "relic": relic_name,
                "state": effective_state or "not specified",
                "item": reward_name,
                "chance": chance,
            })

    def chance_value(record: dict[str, Any]) -> float:
        try:
            return float(record["chance"])
        except (TypeError, ValueError):
            return -1.0

    matches.sort(key=lambda record: (-chance_value(record), str(record["tier"]), str(record["relic"])))
    return matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search WFCD relic data for reward chances.")
    parser.add_argument("--data", required=True, type=Path, help="Path to WFCD data/relics.json")
    parser.add_argument("--download", action="store_true", help="Download latest WFCD relic data to --data before searching")
    parser.add_argument("--data-url", default=DEFAULT_DATA_URL, help=argparse.SUPPRESS)
    parser.add_argument("--item", required=True, help="Reward item name or part of its name")
    parser.add_argument("--tier", default="", help="Optional relic tier: Lith, Meso, Neo, or Axi")
    parser.add_argument("--state", default="", help="Optional refinement state, e.g. Intact or Radiant")
    parser.add_argument("--exact", action="store_true", help="Require an exact normalized item name")
    args = parser.parse_args(argv)

    try:
        if args.download:
            download_dataset(args.data, url=args.data_url)
        relics, metadata = load_dataset(args.data)
        matches = find_relics(relics, args.item, tier=args.tier, state=args.state, exact=args.exact)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Source file: {args.data.expanduser()}")
    if metadata:
        print("Dataset metadata: " + json.dumps(metadata, ensure_ascii=False, sort_keys=True))
    print(f"Relic records scanned: {len(relics)}")
    if not matches:
        print(f"No matching rewards found for: {args.item}")
        return 0

    print(f"Matches: {len(matches)} (sorted by recorded chance, highest first)")
    for result in matches:
        chance = f"{result['chance']}%" if result["chance"] is not None else "chance not supplied"
        print(f"- {result['tier']} {result['relic']} | {result['state']} | {result['item']} | {chance}")
    print("\nChance values are copied from the selected dataset. Verify its date and the in-game refinement state before making a farming decision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
