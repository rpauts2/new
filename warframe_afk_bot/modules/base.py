#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base.py — базовый класс модуля-фермы (конечный автомат с частотой тиков).
"""
from __future__ import annotations

import time
import logging


class _StateVal:
    """Простое значение состояния с именем (для логов)."""
    __slots__ = ("name",)
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name


class FarmModule:
    """Общий каркас: throttle по tick_interval + машина состояний."""

    class State:
        IDLE = _StateVal("IDLE")

    def __init__(self, bot, cfg: dict, name: str):
        self.bot = bot                 # доступ к capture/vision/input/stats
        self.cfg = cfg or {}
        self.name = name
        self.log = logging.getLogger(f"wf.{name}")
        self.tick_interval = float(cfg.get("check_interval_sec",
                                           cfg.get("poll_sec", 0.5)))
        self._last_tick = 0.0
        self.state = FarmModule.State.IDLE
        self._state_since = time.time()

    # -------- служебное --------
    def set_state(self, s):
        if s != self.state:
            self.log.debug("%s: %s -> %s", self.name, self.state.name, s.name)
            self.state = s
            self._state_since = time.time()

    def in_state(self, s) -> bool:
        return self.state == s

    def state_age(self) -> float:
        return time.time() - self._state_since

    def click_detection(self, det, button: str = "left"):
        """Клик по объекту из кадра (преобразует координаты кадра в экран)."""
        x, y = self.bot.capture.to_screen_coords(det.cx, det.cy)
        self.bot.input.click_at(x, y, button=button)

    # -------- интерфейс --------
    def tick(self, frame):
        """Вызывается планировщиком не чаще tick_interval."""
        now = time.time()
        if now - self._last_tick < self.tick_interval:
            return
        self._last_tick = now
        try:
            self.on_tick(frame)
        except NotImplementedError:
            raise
        except Exception:
            self.log.exception("Ошибка в %s", self.name)

    def on_tick(self, frame):
        raise NotImplementedError
