#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
focus_fire.py — «фокусный огонь» (community favorite из AHK/WFU макросов):

Мягкий aim-assist поверх любой фермы: находит НОВЫЕ вражеские маркеры,
плавной серией относительных движений доворачивает камеру к ближайшему и
даёт короткую очередь. Работает ТОЛЬКО по экранному HUD (синие маркеры
врагов над головами) — никаких данных игры/памяти.

Идеален как дополнение к effusion_farm/nightwave_farm: те стреляют в упор,
этот добивает дальние спавны.

Конфиг (afk_zones.focus_fire):
    enabled: false             # включать по желанию
    fire_key: mouse_left
    burst_shots: 4             # выстрелов в очереди
    max_targets_per_tick: 2
    turn_gain: 0.10            # сила доворота (меньше = плавнее)
    cooldown_sec: [1.2, 2.5]   # пауза между очередями (рандом)
    check_interval_sec: 0.3
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule


class FocusFire(FarmModule):
    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.fire_key = {"mouse_left": "left", "mouse_right": "right"}.get(
            cfg.get("fire_key", "mouse_left"), "left")
        self.burst_shots = int(cfg.get("burst_shots", 4))
        self.max_targets = int(cfg.get("max_targets_per_tick", 2))
        self.turn_gain = float(cfg.get("turn_gain", 0.10))
        lo, hi = cfg.get("cooldown_sec", [1.2, 2.5])
        self.cooldown = (float(lo), float(hi))
        self._next_burst = 0.0

    def _aim_and_fire(self, det, frame_shape):
        pg = getattr(self.bot.input, "_pg", None)
        h, w = frame_shape
        dx = int((det.cx - w / 2) * self.turn_gain * random.uniform(0.8, 1.2))
        dy = int((det.cy - h / 2) * self.turn_gain * random.uniform(0.8, 1.2))
        dx = max(-90, min(90, dx))
        dy = max(-60, min(60, dy))
        if pg and (abs(dx) > 2 or abs(dy) > 2):
            try:
                for _ in range(3):  # три плавных шажка вместо одного рывка
                    pg.moveRel(dx // 3, dy // 3, duration=0.03)
                    time.sleep(0.02)
            except Exception:
                pass
        tap = random.uniform(0.25, 0.5)
        self.bot.input.fire_held(tap, button=self.fire_key)
        self.bot.stats["shots_fired"] += self.burst_shots

    def on_tick(self, frame):
        now = time.time()
        if now < self._next_burst:
            return
        h, w = frame.shape[:2]
        blobs = self.bot.vision.find_color_blobs(
            frame, "enemy_marker", min_area=25,
            sort_by_distance_to=(w / 2, h / 2))
        if not blobs:
            return
        self.set_state(self.State.IDLE)
        for d in blobs[:self.max_targets]:
            self._aim_and_fire(d, frame.shape)
            time.sleep(random.uniform(0.1, 0.25))
        self._next_burst = now + random.uniform(*self.cooldown)
