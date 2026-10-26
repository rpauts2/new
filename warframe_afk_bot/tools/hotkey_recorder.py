#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hotkey_recorder.py — «макрос-рекордер» для кастомных AFK-цепочек.

Позволяет записать последовательность клавиш/пауз один раз (например:
W -> 0.5с -> прыжок -> X -> 2с -> перезарядка) и сохранить как JSON-профиль,
который потом можно проигрывать по кругу модулем RepeatMacro (см. ниже) или
отдельно:

    Запись:   python tools/hotkey_recorder.py record --out profiles/my_macro.json
    Повтор:   python tools/hotkey_recorder.py play --in profiles/my_macro.json --loops 0

Запись останавливается клавишей F10, воспроизведение — F9.
Требует модуль `keyboard` (на Windows запускать от администратора не обязательно).
"""
from __future__ import annotations

import json
import time
import argparse
import os
import sys

try:
    import keyboard
except ImportError:
    print("pip install keyboard")
    sys.exit(1)


def record(out_path: str):
    events = []
    stop_flag = {"v": False}
    print("Пишу события... F10 — закончить запись.")

    def on_press(e):
        if e.name == "f10":
            stop_flag["v"] = True
            return
        events.append({"t": round(time.time(), 3), "type": "press", "key": e.name})

    def on_release(e):
        if e.name == "f10":
            return
        events.append({"t": round(time.time(), 3), "type": "release", "key": e.name})

    keyboard.on_press(on_press)
    keyboard.on_release(on_release)
    t0 = time.time()
    while not stop_flag["v"]:
        time.sleep(0.05)
    keyboard.unhook_all()
    for ev in events:
        ev["t"] = round(ev["t"] - t0, 3)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(events, f, indent=1)
    print(f"Сохранено {len(events)} событий -> {out_path}")


def play(in_path: str, loops: int, speed: float = 1.0):
    with open(in_path) as f:
        events = json.load(f)
    stop = {"v": False}
    keyboard.add_hotkey("f9", lambda: stop.update(v=True))
    n = 0
    while not stop["v"] and (loops == 0 or n < loops):
        n += 1
        prev = 0.0
        for ev in events:
            if stop["v"]:
                break
            dt = max(0, ev["t"] - prev) / speed
            prev = ev["t"]
            time.sleep(dt)
            if ev["type"] == "press":
                keyboard.press(ev["key"])
            else:
                keyboard.release(ev["key"])
        # гарантируем отпускание всех клавиш между циклами
        for ev in events:
            if ev["type"] == "release":
                try:
                    keyboard.release(ev["key"])
                except Exception:
                    pass
        print(f"\rцикл {n}" + (f"/{loops}" if loops else ""), end="")
    print("\nОстановлено (F9).")
    keyboard.unhook_all()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--out", default="profiles/my_macro.json")
    pl = sub.add_parser("play")
    pl.add_argument("--in", dest="inp", default="profiles/my_macro.json")
    pl.add_argument("--loops", type=int, default=0, help="0 = бесконечно")
    pl.add_argument("--speed", type=float, default=1.0)
    a = p.parse_args()
    if a.cmd == "record":
        record(a.out)
    else:
        play(a.inp, a.loops, a.speed)
