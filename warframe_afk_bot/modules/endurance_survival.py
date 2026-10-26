#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
endurance_survival.py — авто-выживание в эндлесс-режимах (_survival-bot.ahk rpauts2,
Nekros/Valkyr «stand in corner» из YagamiKlait Warframe).

Что делает бот на миссии Survival / Endless / Void Armageddon:
 1) Держит HP над порогом: как только полоса здоровья проседает ниже
    hp_panic_pct — кастует выживательную способность фрейма (Valkyr Scourge,
    Rhino Iron Skin, Revenant Mesmer Skin...). Список берётся из frames_db.
 2) Крутит sustain-ротацию фрейма по кулдаунам (туман Necro, Mesmer и т.п.),
    чтобы не стоять без урона.
 3) Собирает ресурсы/сферы: если в кадре виден оранжевый лут-маркер — подходит
    (клик по центру экрана с микро-движением мыши к цели) и жмёт F.
 4) Анти-залипание: каждые N секунд чуть крутит камеру и дёргает WASD, чтобы
    игра не подумала что игрок афк, и враги не столпились вплотную.
 5) Считает время миссии; при достижении max_wave_time_sec — выход (Esc→Exit),
    чтобы не фармить дольше чем нужно (защита от банов за подозрительно долгие сессии).

Конфиг (afk_zones.endurance_survival):
    enabled: true
    frame: "valkyr"           # фрейм из базы (для survival/sustain списков)
    hp_panic_pct: 40          # порог паники выше обычного (эндлесс = больно)
    heal_cast_cooldown_sec: 20 # как часто можно спамить спасалку
    loot_pickup: true         # собирать оранжевые маркеры
    interact_key: "f"
    wander_every_sec: [60, 120]   # анти-залипание движениями
    max_wave_time_sec: 1800       # авто-выход через 30 мин (0 = никогда)
    exit_keys: ["esc", "enter"]   # Esc -> подтверждение выхода
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule, _StateVal
from data.frames_db import get_frame


class EnduranceSurvival(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        HOLD_POSITION = _StateVal("HOLD_POSITION")
        PANIC_HEAL = _StateVal("PANIC_HEAL")
        LOOT_RUN = _StateVal("LOOT_RUN")
        EXIT_MISSION = _StateVal("EXIT_MISSION")

    def __init__(self, bot, cfg, name="endurance_survival"):
        super().__init__(bot, cfg, name)
        self.frame_name = str(cfg.get("frame", "valkyr"))
        self.frame = get_frame(self.frame_name)
        self.hp_panic = float(cfg.get("hp_panic_pct", 40))
        self.heal_cd = float(cfg.get("heal_cast_cooldown_sec", 20))
        self.loot_pickup = bool(cfg.get("loot_pickup", True))
        self.interact_key = cfg.get("interact_key", "f")
        lo, hi = cfg.get("wander_every_sec", [60, 120])
        self.wander = [float(lo), float(hi)]
        self.max_time = float(cfg.get("max_wave_time_sec", 1800))
        self.exit_keys = cfg.get("exit_keys", ["esc", "enter"])
        self.tick_interval = float(cfg.get("check_interval_sec", 0.7))
        self._last_heal = 0.0
        self._next_wander = time.time() + random.uniform(*self.wander)
        self._mission_started = None
        self._loot_until = 0.0

    # ---------- хелперы ----------
    def _ability_key(self, slot: str) -> str:
        from data.frames_db import ABILITY_KEYS
        ab = self.frame["abilities"].get(slot, {})
        return ab.get("hotkey") or ABILITY_KEYS.get(slot, "q")

    def _survival_slots(self) -> list[str]:
        surv = list(self.frame.get("survival") or [])
        if surv:
            return surv
        return [s for s, ab in self.frame["abilities"].items()
                if any(k in (str(ab.get("notes", "")) + " " +
                             str(ab.get("name", ""))).lower()
                       for k in ("неуязв", "щит", "лечен", "стака",
                                 "scourge", "iron skin"))]

    def _read_hp(self, frame):
        try:
            vis = self.bot.vision
            roi_rel = self.bot.cfg.get("vision", {}).get(
                "hud_hp_roi", [0.02, 0.90, 0.20, 0.05])
            h, w = frame.shape[:2]
            roi = (int(roi_rel[0] * w), int(roi_rel[1] * h),
                   int(roi_rel[2] * w), int(roi_rel[3] * h))
            return vis.health_bar_ratio(frame, roi)
        except Exception:
            return None

    # ---------- ядро ----------
    def on_tick(self, frame):
        now = time.time()
        inp = self.bot.input

        if self._mission_started is None:
            self._mission_started = now
            self.log.info("Выживание стартовало (фрейм: %s)", self.frame_name)

        elapsed = now - self._mission_started
        if self.max_time and elapsed > self.max_time:
            self.set_state(self.State.EXIT_MISSION)

        hp = self._read_hp(frame)

        # --- приоритет 1: выход ---
        if self.in_state(self.State.EXIT_MISSION):
            for k in self.exit_keys:
                inp.press_key(k)
                time.sleep(random.uniform(0.4, 0.8))
            self.log.info("Авто-выход из миссии после %.0f сек", elapsed)
            self.bot.stats["survival_exits"] = \
                self.bot.stats.get("survival_exits", 0) + 1
            self._mission_started = None
            self.set_state(self.State.IDLE)
            return

        # --- приоритет 2: паническое лечение ---
        if hp is not None and hp * 100 < self.hp_panic and now - self._last_heal > self.heal_cd:
            self.set_state(self.State.PANIC_HEAL)
            casted = False
            for slot in self._survival_slots():
                inp.press_key(self._ability_key(slot))
                casted = True
                self.log.warning("HP %.0f%% — спасалка %s (слот %s)",
                                 hp * 100, self.frame["abilities"]
                                 .get(slot, {}).get("name", "?"), slot)
                break
            if not casted:
                inp.hold_key("s", 0.9)   # просто отходим назад
            self._last_heal = now
            return

        # --- приоритет 3: сбор лута ---
        if self.loot_pickup:
            try:
                loot = self.bot.vision.find_color_blobs(
                    frame, "loot_marker", min_area=50)
            except KeyError:
                loot = []
            if loot and not self.in_state(self.State.LOOT_RUN):
                self.set_state(self.State.LOOT_RUN)
                self._loot_until = now + 6.0
                # ведём курсор к маркеру и жмём взаимодействие
                det = loot[0]
                x, y = self.bot.capture.to_screen_coords(det.cx, det.cy)
                inp.click_at(x, y)
                inp.press_key(self.interact_key)
                self.bot.stats["survival_loot"] = \
                    self.bot.stats.get("survival_loot", 0) + 1
                return
            if self.in_state(self.State.LOOT_RUN) and now >= self._loot_until:
                self.set_state(self.State.HOLD_POSITION)
                return

        # --- приоритет 4: sustain-урон, чтобы волны не копились ---
        self.set_state(self.State.HOLD_POSITION)
        for slot in (self.frame.get("sustain") or []):
            cd = float(self.frame["abilities"].get(slot, {})
                       .get("cooldown", 30))
            last = self.bot.stats.get(f"_es_last_{slot}", 0.0)
            if now - last > cd * random.uniform(0.95, 1.15):
                inp.press_key(self._ability_key(slot))
                self.bot.stats[f"_es_last_{slot}"] = now
                break

        # --- приоритет 5: анти-залипание позиционирования ---
        if now >= self._next_wander:
            dx = random.randint(-40, 40)
            dy = random.randint(-15, 15)
            inp.move_rel(dx, dy)
            key = random.choice(["a", "d", "w"])
            inp.hold_key(key, random.uniform(0.25, 0.6))
            self._next_wander = now + random.uniform(*self.wander)
