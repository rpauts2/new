#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triggerbot.py — визуальный триггербот (идея PixelCheck-триггеров Cyte-09.ahk).

Не aimbot в классическом смысле (не водит мышью по врагам — это уже читерщина
и гарантированный бан). Вместо этого:
  • следит за узкой зоной HUD (цветовой пиксель-триггер, как у Yagami Cyte-09);
  • когда цель появляется ЦЕНТРО в прицеле (узкая крестовина в середине кадра
    окрашивается в цвет подсветки цели) — делает одиночный клик огнём.

Это легальный паттерн «reaction macro»: бот лишь ускоряет реакцию, целится
по-прежнему игрок. Интервалы и флаги deliberately консервативные.

Конфиг (afk_zones.triggerbot):
    enabled: false
    crosshair_roi_rel: [0.495, 0.49, 0.01, 0.02]  # узкая полоска по центру экрана
    target_hex: "ff3b30"      # цвет подсветки цели (подбери calibrate.py!)
    tolerance: 40
    fire_key: mouse_left
    min_interval_ms: [180, 420]   # рандомная задержка перед выстрелом (анти-паттерн)
    require_loot_or_enemy: enemy_marker  # стрелять только если где-то в кадре есть враг
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule, _StateVal


class TriggerBot(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        ARMED = _StateVal("ARMED")
        FIRED = _StateVal("FIRED")

    def __init__(self, bot, cfg, name="triggerbot"):
        super().__init__(bot, cfg, name)
        self.roi = cfg.get("crosshair_roi_rel", [0.495, 0.49, 0.01, 0.02])
        self.hex = cfg.get("target_hex", "ff3b30")
        self.tol = int(cfg.get("tolerance", 40))
        self.fire_key = cfg.get("fire_key", "mouse_left")
        lo, hi = cfg.get("min_interval_ms", [180, 420])
        self.interval_ms = (float(lo), float(hi))
        self.require = cfg.get("require_loot_or_enemy")
        self.tick_interval = 1.0 / float(bot.capture.fps)  # каждый кадр
        self._next_fire = 0.0

    def on_tick(self, frame):
        now = time.time()
        if now < self._next_fire:
            return
        vis = self.bot.vision
        try:
            on_target = vis.color_in_roi(frame, self.roi, self.hex, self.tol)
        except Exception:
            on_target = False
        if not on_target:
            self.set_state(self.State.IDLE)
            return

        if self.require:
            try:
                blobs = vis.find_color_blobs(frame, self.require, min_area=40)
                if not blobs:
                    return
            except KeyError:
                pass

        self.set_state(self.State.ARMED)
        delay = random.uniform(*self.interval_ms) / 1000.0
        time.sleep(delay)                       # человеческая реакция
        self.bot.input.press_key(self.fire_key)
        self.bot.stats.setdefault("trigger_shots", 0)
        self.bot.stats["trigger_shots"] += 1
        self._next_fire = time.time() + random.uniform(*self.interval_ms) / 500.0
        self.set_state(self.State.FIRED)
