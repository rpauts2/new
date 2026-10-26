#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest.py — автотест ядра без реального экрана/игры.
Гоняет VisionEngine на синтетическом «скриншоте» и прогоняет on_tick()
всех модулей с мок-вводом. Запуск:  python tools/selftest.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import numpy as np
import cv2
import yaml

img = np.full((1080, 1920, 3), (40, 35, 30), np.uint8)


def put_center(bgr, cx, cy, w, h):
    x, y = int(cx - w / 2), int(cy - h / 2)
    img[y:y + h, x:x + w] = bgr


put_center((0, 140, 255), 700, 500, 26, 26)     # оранжевый маркер лута
put_center((255, 180, 40), 1150, 420, 22, 22)   # синий маркер врага
put_center((200, 90, 20), 500, 800, 260, 340)   # синяя карточка награды

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
from core.vision import VisionEngine

vis = VisionEngine(cfg)
loot = vis.find_color_blobs(img, "loot_marker")
enemy = vis.find_color_blobs(img, "enemy_marker")
card = vis.pick_reward_card(img)
print("loot:", [(round(d.cx), round(d.cy)) for d in loot])
print("enemy:", [(round(d.cx), round(d.cy)) for d in enemy])
assert loot and abs(loot[0].cx - 700) < 20, "loot detect fail"
assert enemy and abs(enemy[0].cx - 1150) < 20, "enemy detect fail"
assert card, "reward card fail"

# Шаблонный матчинг: вырезаем кусок как PNG-шаблон и находим его
os.makedirs("templates", exist_ok=True)
tpl_path = "templates/_selftest_tpl.png"
cv2.imwrite(tpl_path, img[409:431, 1139:1161])
vis2 = VisionEngine(cfg)
dets = vis2.match_template(img, "_selftest_tpl.png", threshold=0.8)
print("template match:", [(round(d.cx), round(d.cy), round(d.confidence, 2)) for d in dets])
assert dets and abs(dets[0].cx - 1150) < 25, "template match fail"
os.remove(tpl_path)

# Модули: импорт из реестра + on_tick с моками вместо ввода/захвата
from core.bot import MODULE_REGISTRY, import_module_class


class RC:
    @staticmethod
    def to_screen_coords(x, y):
        return int(x), int(y)


class MockInput:
    _pg = None
    _kb = None

    def press_key(self, *a, **k): pass
    def fire_held(self, *a, **k): pass
    def click_at(self, x, y, button="left", double=False):
        print(f"   [mock-click] ({x},{y}) {button}")
    def move_rel(self, dx, dy): pass
    def strafe(self, *a, **k): pass
    def position(self): return (960, 540)


class FakeBot:
    vision = vis
    input = MockInput()
    capture = RC()
    stats = {"shots_fired": 0, "loot_picked": 0,
             "screens_clicked": 0, "cycles_done": 0}
    running = True
    last_frame = img


fb = FakeBot()
zones = cfg["afk_zones"]
for name in ["effusion_farm", "lith_anomaly", "duviri_loop",
             "auto_reward", "repeat_macro"]:
    mp, cls = MODULE_REGISTRY[name]
    inst = import_module_class(mp, cls)(bot=fb, cfg=zones.get(name, {}), name=name)
    inst.tick_interval = 0
    inst.on_tick(img)
    print("tick OK:", name, "| state:", inst.state.name)

inst = import_module_class(*MODULE_REGISTRY["antiafk"])(
    bot=fb, cfg=cfg["antiafk"], name="antiafk")
inst._next_action = 0
inst.actions = []
inst.tick_interval = 0
inst.on_tick(img)
print("tick OK: antiafk")

print("\n=== ALL SELFTESTS PASSED ===")
