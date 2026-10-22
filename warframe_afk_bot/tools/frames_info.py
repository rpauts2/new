#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
frames_info.py — просмотр и подбор базы варфреймов.

    python tools/frames_info.py --list                 # все фреймы
    python tools/frames_info.py revenant               # детали ротации
    python tools/frames_info.py --best duviri          # топ AFK-фреймов
    python tools/frames_info.py --profile revenant     # готовый YAML-профиль!
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.frames_db import FRAMES_DB, get_frame, list_frames  # noqa: E402


def show(name: str):
    fr = get_frame(name)
    fit, why = fr["afk_fit"]
    print(f"\n=== {name} ===")
    print(f"Роль: {fr['role']}   AFK-пригодность: {fit}")
    print(f"Вердикт: {why}")
    if not fr["abilities"]:
        print("Способности не описаны в базе.")
        return
    print("\nСпособности:")
    for slot in sorted(fr["abilities"]):
        ab = fr["abilities"][slot]
        cd = ab.get("cooldown", "?")
        cast = f"hold {ab.get('hold_sec', 2)}s" if ab.get("cast") == "hold" else "press"
        note = f"  // {ab.get('notes')}" if ab.get("notes") else ""
        print(f"  [{slot}] ({ab['hotkey'].upper()}) {ab['name']:<28} "
              f"CD={cd:<4} {cast:<10}{note}")
    print(f"\nКомбо открытия: {' -> '.join(fr.get('combo', [])) or '—'}")
    print(f"Sustain-ротация: {' -> '.join(fr.get('sustain', [])) or '—'}")


def best(zone_hint: str = ""):
    rank = {"excellent": 0, "good": 1, "weak": 2, "unknown": 3}
    rows = []
    for name, fr in FRAMES_DB.items():
        fit, why = fr.get("afk_fit", ("unknown", ""))
        score = rank.get(fit, 3)
        hint = zone_hint.lower()
        if hint and (hint in why.lower() or hint in name):
            score -= 1
        rows.append((score, fit, name, why))
    rows.sort()
    print(f"{'ФРЕЙМ':<16} {'AFK':<10} ПОЧЕМУ")
    print("-" * 72)
    for _, fit, name, why in rows:
        print(f"{name:<16} {fit:<10} {why}")


def gen_profile(name: str):
    """Генерирует YAML-профиль автокаста для frames_db — можно класть в profiles/."""
    fr = get_frame(name)
    if not fr["abilities"]:
        print(f"Нет данных по '{name}'"); return
    lines = [
        f"# Автокаст «{name}» — сгенерировано tools/frames_info.py",
        f"name: \"{name} autopilot\"",
        f"vars: {{casts: 0}}",
        "start: rotate",
        "",
        "steps:",
        "  - name: rotate",
        '    when: "screen == mission"',
        "    actions:",
    ]
    order = fr.get("combo") or fr.get("sustain") or sorted(fr["abilities"])
    for slot in order:
        ab = fr["abilities"].get(slot, {})
        cd = float(ab.get("cooldown", 20))
        key = ab.get("hotkey", "q")
        if ab.get("cast") == "hold":
            hs = ab.get("hold_sec", 2.0)
            lines.append(f"      - down: {key}")
            lines.append(f"      - wait: {hs}")
            lines.append(f"      - up: {key}")
        else:
            lines.append(f"      - press: {key}")
        lines.append(f"      - inc: {{casts: 1}}")
        lo, hi = int(cd * 0.85), int(cd * 1.15)
        lines.append(f"      - wait: [{lo}, {hi}]")
    lines += ["      - click_color: loot_marker",
              "      - move_rel: [3, 0]", "      - move_rel: [-3, 0]",
              "    next: rotate"]
    text = "\n".join(lines) + "\n"
    out = os.path.join("profiles", f"{name}_autopilot.yaml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"Сохранено: {out}\n"
          f"Подключи в config.yaml: afk_zones.profile_runner.profile_file: {out}")


def main():
    args = sys.argv[1:]
    if not args or args[0] == "--list":
        print("Доступные фреймы:")
        for n in list_frames():
            fr = FRAMES_DB[n]
            fit = fr["afk_fit"][0]
            print(f"  {n:<18} [{fr['role']:<8}] AFK: {fit}")
        print(f"\nВсего: {len(FRAMES_DB)}. Детали: frames_info.py <имя>")
        return
    if args[0] == "--best":
        best(args[1] if len(args) > 1 else "")
        return
    if args[0] == "--profile":
        gen_profile(args[1] if len(args) > 1 else "revenant")
        return
    show(args[0])


if __name__ == "__main__":
    main()
