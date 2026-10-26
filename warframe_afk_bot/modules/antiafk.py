#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
antiafk.py — анти-афк хранитель сессии.

Warframe кикает за бездействие и предупреждает/наказывает за «идеально
мертвый» афк. Модуль периодически выполняет мини-ротацию «живых» действий
из конфига: лёгкие нажатия Shift/Ctrl, микро-движения мыши туда-обратно,
случайные стрейфы. Интервал рандомизирован, чтобы паттерн не был периодическим.

Действия полностью безвредны для позиционирования персонажа.
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule


class AntiAFKKeeper(FarmModule):
    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.enabled = bool(cfg.get("enabled", True))
        lo, hi = cfg.get("interval_sec", [45, 95])
        self.interval = (float(lo), float(hi))
        self.actions = cfg.get("actions", [])
        self.tick_interval = 1.0
        self._next_action = time.time() + random.uniform(*self.interval)
        self._mouse_anchor = None

    def _do(self, act: dict):
        t = act.get("type")
        inp = self.bot.input
        if t == "key":
            inp.press_key(act.get("key", "shift"), hold=float(act.get("hold", 0.05)))
        elif t == "move_mouse_rel":
            dx, dy = int(act.get("dx", 3)), int(act.get("dy", 2))
            self._mouse_anchor = inp.position()
            inp.move_rel(dx, dy)
        elif t == "move_mouse_back":
            if self._mouse_anchor:
                x, y = inp.position()
                ax, ay = self._mouse_anchor
                inp.move_rel(ax - x, ay - y)
                self._mouse_anchor = None
        elif t == "strafe":
            key = random.choice("wasd")
            inp.strafe(key, duration=random.uniform(0.08, 0.2))

    def on_tick(self, frame):
        if not self.enabled:
            return
        if time.time() < self._next_action:
            return
        self._next_action = time.time() + random.uniform(*self.interval)
        if not self.actions:
            return
        act = random.choice(self.actions)
        self._do(act)
        # иногда делаем связку из 2-3 действий подряд, как живой человек
        for _ in range(random.randint(0, 2)):
            time.sleep(random.uniform(0.2, 0.7))
            self._do(random.choice(self.actions))
        self.log.debug("Anti-AFK действие выполнено: %s", act.get("type"))
