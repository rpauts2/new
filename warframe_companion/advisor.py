#!/usr/bin/env python3
"""Manual-play Warframe mission/frame advisor. No game input or screen capture."""
from __future__ import annotations
import argparse
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class Frame:
    name: str
    roles: frozenset[str]
    notes: str

# Broad roles, not a live meta ranking. Verify patch-sensitive details in current references.
FRAMES = (
    Frame("Nova", frozenset({"crowd_control", "damage_amplification", "speed"}), "Molecular Prime can slow or speed enemies; choose the cast mode deliberately."),
    Frame("Frost", frozenset({"defense", "crowd_control", "survival"}), "Snow Globe protects a fixed objective; positioning and recasts matter."),
    Frame("Gara", frozenset({"defense", "damage", "survival"}), "Objective protection and damage potential reward a practiced setup."),
    Frame("Khora", frozenset({"crowd_control", "loot", "damage", "defense"}), "Ensnare and Strangledome offer control; loot benefits depend on setup."),
    Frame("Nekros", frozenset({"loot", "survival", "support"}), "Desecrate can add eligible corpse-based loot rolls, not every drop."),
    Frame("Saryn", frozenset({"area_damage", "damage", "sanctuary"}), "Strong room-clearing potential when spores are maintained."),
    Frame("Volt", frozenset({"speed", "area_damage", "support", "defense"}), "Speed and shield utility; role depends on build and mission."),
    Frame("Wisp", frozenset({"support", "survival", "damage"}), "Reservoirs provide squad utility; placement matters."),
    Frame("Revenant", frozenset({"survival", "damage"}), "Mesmer Skin supports personal survivability but does not complete objectives."),
    Frame("Rhino", frozenset({"survival", "damage", "support"}), "Iron Skin and Roar offer durability and squad damage support."),
    Frame("Octavia", frozenset({"survival", "area_damage", "support"}), "Scaling damage and team buffs reward good placement and rhythm."),
    Frame("Mesa", frozenset({"area_damage", "damage", "defense"}), "High ability damage; line of sight and energy management still matter."),
    Frame("Trinity", frozenset({"support", "survival", "energy"}), "Healing and energy support can stabilize a squad."),
    Frame("Protea", frozenset({"defense", "area_damage", "support", "energy"}), "Deployable damage and resource support work well around objectives."),
    Frame("Mag", frozenset({"crowd_control", "area_damage", "defense"}), "Grouping and damage interactions work well in suitable layouts."),
    Frame("Vauban", frozenset({"crowd_control", "defense", "area_damage"}), "Excellent area control; some special enemies resist control."),
    Frame("Ivara", frozenset({"stealth", "spy", "loot"}), "A careful stealth option; vault mechanics and movement still matter."),
    Frame("Loki", frozenset({"stealth", "spy", "speed"}), "Invisibility and utility support deliberate Spy routes."),
    Frame("Titania", frozenset({"speed", "damage"}), "Fast traversal for suitable missions; tileset geometry matters."),
    Frame("Zephyr", frozenset({"defense", "area_damage", "survival"}), "Airborne survivability and grouped damage can suit open layouts."),
    Frame("Hildryn", frozenset({"survival", "support", "area_damage"}), "Shield-focused durability and team utility; check mission interactions."),
    Frame("Citrine", frozenset({"support", "survival", "damage"}), "Team sustain and status support make her a flexible squad pick."),
    Frame("Dante", frozenset({"support", "survival", "area_damage"}), "Overguard and spell damage can support a team, subject to balance."),
    Frame("Gyre", frozenset({"area_damage", "damage"}), "Electric area damage excels when the build sustains its setup."),
    Frame("Xaku", frozenset({"area_damage", "damage", "survival"}), "Broad area damage and weapon control; ability uptime matters."),
    Frame("Nezha", frozenset({"speed", "survival", "support"}), "Mobile durability and status utility suit many general missions."),
    Frame("Nidus", frozenset({"survival", "damage", "crowd_control"}), "Scales through sustained combat; fast missions limit ramp-up."),
    Frame("Limbo", frozenset({"defense", "crowd_control"}), "Can protect some objectives but may disrupt allies and mission flow."),
)

MISSION_ROLES = {
    "survival": ("survival", "area_damage", "damage"),
    "defense": ("defense", "area_damage", "support"),
    "mobile defense": ("defense", "survival", "support"),
    "excavation": ("defense", "survival", "support"),
    "interception": ("crowd_control", "area_damage", "support"),
    "disruption": ("damage", "survival", "speed"),
    "sanctuary onslaught": ("sanctuary", "area_damage", "damage"),
    "elite sanctuary onslaught": ("sanctuary", "area_damage", "damage"),
    "spy": ("spy", "stealth", "speed"),
    "capture": ("speed", "damage"),
    "exterminate": ("speed", "area_damage", "damage"),
    "rescue": ("speed", "stealth", "survival"),
    "sabotage": ("speed", "damage"),
    "void cascade": ("damage", "survival", "area_damage"),
    "void flood": ("speed", "survival", "support"),
    "void armageddon": ("defense", "area_damage", "support"),
    "netracells": ("survival", "area_damage", "damage"),
    "arbitration": ("survival", "damage", "support"),
    "mirror defense": ("defense", "area_damage", "support"),
    "alchemy": ("area_damage", "survival", "support"),
    "defection": ("support", "survival", "speed"),
}
GOAL_ROLE = {
    "survive": ("survival", "support"), "kill": ("area_damage", "damage"),
    "defend": ("defense", "crowd_control"), "speed": ("speed", "damage"),
    "stealth": ("stealth", "spy"), "control": ("crowd_control", "defense"),
    "support": ("support", "energy"), "loot": ("loot", "survival"),
}

def normalize(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())

def recommend(mission: str, goal: str | None = None, limit: int = 5, exclude: tuple[str, ...] = ()) -> list[dict[str, object]]:
    mission_key = normalize(mission)
    if mission_key not in MISSION_ROLES:
        raise ValueError(f"Unknown mission '{mission}'. Supported missions: {', '.join(sorted(MISSION_ROLES))}")
    mission_roles = MISSION_ROLES[mission_key]
    target_roles = mission_roles
    if goal:
        goal_key = normalize(goal)
        if goal_key not in GOAL_ROLE:
            raise ValueError(f"Unknown goal '{goal}'. Supported goals: {', '.join(sorted(GOAL_ROLE))}")
        target_roles = tuple(dict.fromkeys((*mission_roles, *GOAL_ROLE[goal_key])))
    excluded = {normalize(name) for name in exclude if normalize(name)}
    ranked = []
    for frame in FRAMES:
        if normalize(frame.name) in excluded:
            continue
        matches = [role for role in target_roles if role in frame.roles]
        if matches:
            score = sum(3 if role in mission_roles else 1 for role in matches)
            ranked.append({"frame": frame.name, "score": score, "matched_roles": matches, "notes": frame.notes})
    ranked.sort(key=lambda item: (-int(item["score"]), str(item["frame"])))
    return ranked[:max(1, min(int(limit), 10))]

def main() -> int:
    parser = argparse.ArgumentParser(description="Manual-play Warframe mission/frame advisor")
    parser.add_argument("--mission", help="Mission type, e.g. Survival, Disruption, Spy")
    parser.add_argument("--goal", choices=sorted(GOAL_ROLE), help="Optional priority")
    parser.add_argument("--limit", type=int, default=5, help="Number of recommendations (1-10)")
    parser.add_argument("--exclude", default="", help="Comma-separated frame names to exclude, e.g. Nekros, Nova")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format for scripts or other tools")
    parser.add_argument("--list-missions", action="store_true", help="List supported mission types")
    args = parser.parse_args()
    if args.list_missions:
        print("\n".join(sorted(MISSION_ROLES)))
        return 0
    if not args.mission:
        parser.error("--mission is required unless --list-missions is used")
    try:
        results = recommend(args.mission, args.goal, args.limit, tuple(args.exclude.split(",")))
    except ValueError as exc:
        parser.error(str(exc))
    if args.format == "json":
        print(json.dumps({"mission": args.mission, "goal": args.goal, "recommendations": results}, ensure_ascii=False, indent=2))
        return 0
    print(f"Recommendations for {args.mission}" + (f" | goal: {args.goal}" if args.goal else ""))
    for index, item in enumerate(results, 1):
        roles = ", ".join(str(role).replace("_", " ") for role in item["matched_roles"])
        print(f"\n{index}. {item['frame']} (match score: {item['score']})")
        print(f"   Role match: {roles}\n   Why: {item['notes']}")
    print("\nThese are broad role suggestions, not a live meta ranking. Check current updates, mods, mission modifiers, and squad needs.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
