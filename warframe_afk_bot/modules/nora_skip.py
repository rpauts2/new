#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nora_skip.py — «Nora Skip» спидран-приём (перенос из Lazy-World/wf-macro nora_skip.ahk).

Суть: Esc -> пауза -> клик по кнопке выхода из миссии -> двойной Esc.
Используется для мгновенного выхода из катсцен/заставки миссии и быстрого
рестарта лупа (например Nova-ферма на Эффосах: заставка -> skip -> комбо).

В оригинале клик идёт по фиксированным координатам (74% ширины, 55% высоты).
Мы делаем надёжнее: сначала пробуем найти шаблон exit_button.png, иначе —
координаты-доли экрана (адаптивны к любому разрешению).

Конфиг (afk_zones.nora_skip):
    enabled: true
    trigger_hotkey: f6          # ручная кнопка «скипнуть» (press-and-release)
    auto_on_cutscene: false     # авто-скип когда detect_screen==loading/unknown катсцена
    exit_pos_rel: [0.74, 0.55]  # доли экрана (x,y) кнопки Quit (как в AHK)
    exit_template: null         # например exit_button.png — приоритет над координатами
"""
from __future__ import annotations

import threading
import time

from modules.base import FarmModule, _StateVal


class NoraSkip(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        SKIPPING = _StateVal("SKIPPING")

    def __init__(self, bot, cfg, name="nora_skip"):
        super().__init__(bot, cfg, name)
        self.exit_rel = list(cfg.get("exit_pos_rel", [0.74, 0.55]))
        self.exit_tpl = cfg.get("exit_template")
        self.auto_on_cutscene = bool(cfg.get("auto_on_cutscene", False))
        self.tick_interval = 0.5
        self._skip_lock = threading.Lock()
        self._last_skip = 0.0
        self._cooldown = float(cfg.get("cooldown_sec", 8))

        hk = str(cfg.get("trigger_hotkey", "f6")).lower()
        try:
            import keyboard
            keyboard.on_press_key(hk, lambda _: self.request_skip(), suppress=False)
            self.log.info("Nora-skip хоткей: %s", hk.upper())
        except Exception as e:
            self.log.debug("Горячая клавиша skip недоступна: %s", e)

    def request_skip(self):
        if not self.bot.running:
            return
        if time.time() - self._last_skip < self._cooldown:
            return
        if self._skip_lock.acquire(blocking=False):
            try:
                self._last_skip = time.time()
                threading.Thread(target=self._do_skip, daemon=True).start()
            finally:
                self._skip_lock.release()

    def _do_skip(self):
        """Esc -> клик Quit -> Esc Esc (точная последовательность AHK-оригинала
        с его же таймингами 350/200/300/150 мс)."""
        inp = self.bot.input
        self.set_state(self.State.SKIPPING)
        try:
            inp.press_key("esc")
            time.sleep(0.35)
            if self.exit_tpl:
                det = self.bot.vision.match_template(self.bot.get_frame(), self.exit_tpl)
                if det:
                    self.click_detection(det)
                else:
                    self._click_rel()
            else:
                self._click_rel()
            time.sleep(0.3)
            inp.press_key("esc")
            time.sleep(0.15)
            inp.press_key("esc")
            self.bot.stats.setdefault("nora_skips", 0)
            self.bot.stats["nora_skips"] += 1
            self.log.info("Nora-skip выполнен")
        finally:
            self.set_state(self.State.IDLE)

    def _click_rel(self):
        fr = self.bot.last_frame
        h, w = fr.shape[:2] if fr is not None else (1080, 1920)
        x, y = int(self.exit_rel[0] * w), int(self.exit_rel[1] * h)
        self.bot.input.click_at(x, y)

    def on_tick(self, frame):
        if not self.auto_on_cutscene or self.in_state(self.State.SKIPPING):
            return
        # грубая эвристика катсцены: чёрные полосы сверху/снизу кадра
        import numpy as np
        band = int(frame.shape[0] * 0.09)
        top = frame[:band].mean()
        bottom = frame[-band:].mean()
        if top < 12 and bottom < 12:
            self.log.debug("Похоже на катсцену (полосы %.1f/%.1f)", top, bottom)
            self.request_skip()
