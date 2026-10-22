#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repeat_macro.py — модуль-ферма «повторяющий макрос».

Проигрывает JSON-макрос, записанный tools/hotkey_recorder.py, по кругу —
универсальный инструмент под ЛЮБУЮ афк-локацию: запиши один раз свои действия
(встать на точку, включить автострельбу модом/оружием, периодические движения
против кика) и оставь бота крутить цикл на всю ночь.

Конфиг (afk_zones.repeat_macro в config.yaml — добавь секцию при желании):
    enabled: true
    macro_file: profiles/my_macro.json
    loop_pause_sec: [2, 6]     # случайная пауза между циклами
    tick_interval игнорируется — модуль сам управляет таймингами внутри цикла.
"""
from __future__ import annotations

import json
import random
import time
import threading

from modules.base import FarmModule


class RepeatMacro(FarmModule):
    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.macro_file = cfg.get("macro_file", "profiles/my_macro.json")
        lo, hi = cfg.get("loop_pause_sec", [2, 6])
        self.loop_pause = (float(lo), float(hi))
        self.tick_interval = 0.5
        self._thread = None
        self._stop = threading.Event()
        self._events = self._load()

    def _load(self):
        try:
            with open(self.macro_file, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.log.warning("Макрос %s не найден — модуль спит. "
                             "Запишите: python tools/hotkey_recorder.py record",
                             self.macro_file)
            return []

    # ------- исполнение через InputController (чтобы работал любой бэкенд) -------
    def _run_loop(self):
        inp = self.bot.input
        while not self._stop.is_set() and self.bot.running:
            prev = 0.0
            for ev in self._events:
                if self._stop.is_set() or not self.bot.running:
                    return
                dt = max(0.0, ev["t"] - prev)
                prev = ev["t"]
                if self._stop.wait(dt):
                    return
                key = ev["key"]
                if ev["type"] == "press":
                    inp._pg.keyDown(key) if inp._pg else inp._kb.press(key)
                else:
                    inp._pg.keyUp(key) if inp._pg else inp._kb.release(key)
            self.bot.stats["cycles_done"] += 1
            pause = random.uniform(*self.loop_pause)
            self._stop.wait(pause)

    def on_tick(self, frame):
        if not self._events:
            return
        if self._thread is None or not self._thread.is_alive():
            if self.bot.running:
                self._stop.clear()
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()
                self.log.info("Макрос запущен: %d событий из %s",
                              len(self._events), self.macro_file)
