#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
afk_anomaly.py — AFK-ферма аномалий (Миррор / Орокин-луна) по мотивам
Lazy-World nova_farm.ahk + Mag «Притяжение» из Yagami Nekros solo farm.

Две тактики из комьюнити-скриптов, объединённые в один модуль:

1) NOVA/EMBER ANOMALY LOOP (nova_farm.ahk):
   встать у точки входа аномалии -> Null Star (4) -> Molecular Prime (1) ->
   ждать кулдаун ability 4 (~50 c) -> зайти в аномалию -> собрать лут -> повтор.

2) MAG VACUUM CORNER (Nekros solo farm):
   занять тупик, куда стягиваются враги -> включить автострельбу (мод
   Continuous Aim / Octopod) -> периодически жать способность «Притяжение»,
   которая затягивает и убивает врагов; интервал подкручивается на лету.

Конфиг (afk_zones.afk_anomaly):
    enabled: true
    tactic: mag_vacuum        # nova_loop | mag_vacuum
    fire_key: mouse_left      # для mag_vacuum используется только как fallback
    vacuum_slot: "4"          # слот способности-вакуума (у Nova Mag = 4, у Mag = 4)
    cast_keys: {"1": q, "4": f}  # переопределение клавиш если нестандартно
    interval_ms: [90, 160]    # базовый интервал спама вакуума (как gPause в AHK)
    interval_hotkey_edit: true  # Alt+Up/Down крутят интервал live (AHK TimeManagement)
    loop_pause_sec: [45, 55]  # пауза цикла nova_loop (кулдаун Null Star)
    enter_key: f              # вход в аномалию / взаимодействие
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule, _StateVal


class AfkAnomalyFarm(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        CAST_COMBO = _StateVal("CAST_COMBO")
        WAIT_COOLDOWN = _StateVal("WAIT_COOLDOWN")
        ENTER_ANOMALY = _StateVal("ENTER_ANOMALY")
        LOOT_SWEEP = _StateVal("LOOT_SWEEP")
        VACUUM_SPAM = _StateVal("VACUUM_SPAM")

    def __init__(self, bot, cfg, name="afk_anomaly"):
        super().__init__(bot, cfg, name)
        self.tactic = str(cfg.get("tactic", "mag_vacuum")).lower()
        self.vacuum_slot = str(cfg.get("vacuum_slot", "4"))
        self.enter_key = cfg.get("enter_key", "f")
        lo, hi = cfg.get("interval_ms", [90, 160])
        self.interval_ms = [float(lo), float(hi)]
        self.loop_pause = cfg.get("loop_pause_sec", [45, 55])
        self.tick_interval = 0.1
        self._next_cast = 0.0
        self._next_cycle = 0.0
        self._last_enemy_seen = 0.0
        if cfg.get("interval_hotkey_edit", True):
            self._register_live_tuning()

    # ---------- live-тюнинг интервала (Alt + Up/Down), как в AHK ----------
    def _register_live_tuning(self):
        try:
            import keyboard

            def bump(delta_ms):
                lo = max(30.0, self.interval_ms[0] + delta_ms)
                hi = max(lo + 10, self.interval_ms[1] + delta_ms)
                self.interval_ms = [lo, hi]
                self.log.info("Интервал вакуума: %.0f-%.0f мс", lo, hi)

            keyboard.on_press_key("up", lambda _: (
                keyboard.is_pressed("alt") and bump(+10)), suppress=False)
            keyboard.on_press_key("down", lambda _: (
                keyboard.is_pressed("alt") and bump(-10)), suppress=False)
        except Exception as e:
            self.log.debug("Live-тюнинг недоступен: %s", e)

    def _ability_key(self, slot: str) -> str:
        from data.frames_db import ABILITY_KEYS
        over = (self.cfg.get("cast_keys") or {}).get(slot)
        return over or ABILITY_KEYS.get(slot, "q")

    # ------------------------------------------------------------------
    def on_tick(self, frame):
        now = time.time()
        inp = self.bot.input

        # есть ли враги рядом (HSV-маркеры) — без них не спамим
        enemies = []
        try:
            enemies = self.bot.vision.find_color_blobs(frame, "enemy_marker", min_area=40)
            if enemies:
                self._last_enemy_seen = now
        except KeyError:
            pass

        if self.tactic == "mag_vacuum":
            if now < self._next_cast:
                return
            if not enemies and (now - self._last_enemy_seen) > 8:
                return
            key = self._ability_key(self.vacuum_slot)
            inp.press_key(key)
            self.bot.stats.setdefault("vacuum_casts", 0)
            self.bot.stats["vacuum_casts"] += 1
            base = random.uniform(*self.interval_ms) / 1000.0
            self._next_cast = now + base * random.uniform(0.92, 1.08)
            self.set_state(self.State.VACUUM_SPAM)
            return

        # ------------------- nova_loop тактика -------------------
        st = self.state
        if st in (self.State.IDLE, self.State.LOOT_SWEEP):
            if now >= self._next_cycle:
                self.set_state(self.State.CAST_COMBO)

        if self.in_state(self.State.CAST_COMBO):
            # комбо Nova: Null Star (4) -> Molecular Prime (1)
            inp.press_key(self._ability_key("4"))
            time.sleep(random.uniform(0.7, 1.0))
            inp.press_key(self._ability_key("1"))
            lo, hi = self.loop_pause
            self._next_cycle = now + random.uniform(lo, hi)
            self._enter_at = now + random.uniform(3.0, 5.0)
            self.set_state(self.State.WAIT_COOLDOWN)
            return

        if self.in_state(self.State.WAIT_COOLDOWN):
            if now >= getattr(self, "_enter_at", now + 1e9):
                self.set_state(self.State.ENTER_ANOMALY)
            return

        if self.in_state(self.State.ENTER_ANOMALY):
            inp.press_key(self.enter_key)     # войти в аномалию
            self.set_state(self.State.LOOT_SWEEP)
            self._sweep_until = now + 12.0
            return

        if self.in_state(self.State.LOOT_SWEEP):
            # подбираем оранжевый лут кнопкой взаимодействия
            try:
                loot = self.bot.vision.find_color_blobs(frame, "loot_marker", min_area=50)
            except KeyError:
                loot = []
            if loot:
                self.click_detection(loot[0], button="left")
                self.bot.stats.setdefault("loot_picked", 0)
                self.bot.stats["loot_picked"] += 1
            if now >= getattr(self, "_sweep_until", 0):
                inp.press_key("esc")          # выход из аномалии
                self.set_state(self.State.IDLE)
