#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arbitration_farm.py — фарм Арбитража (Arbitration / Annals / Veiled.
По мотивам YagamiKlait «Nekros solo farm» + rpauts2 survival-bot, адаптировано
под Arbitration-модификаторы: враги бьют больно, щиты регенерируют медленно.)

Стратегия (комьюнити-метка «corner tank & spank»):
 1) Занять угол/спинку (игрок руками), бот лишь держит спину к стене (S+назад).
 2) Танк-фрейм из frames_db (valkyr/rhino/chroma/nekros) — авто-ротация щитов
    строго по кулдаунам с jitter. Ключ: не жать Iron Skin на кулдауне.
 3) Притягивалки (Banshee Sonic Nexus slot2 / Mag Pull slot3 / Mutalist Nova
    Null Pull slot2) — кастуются только когда в кадре >= min_enemies маркеров,
    чтобы толпа стянулась под AoE.
 4) Mesmer/Defection Revenant — отдельный режим: после каста НЕ стреляем
    (враги сами перестреливают друг друга), только поддерживаем кулдаун.
 5) Death-guard: если HP < death_pct — экстренный выход миссии (Esc->Exit),
    лучше потерять миссию, чем умереть и сломать серию.
 6) Статистика волн: сколько кастов, сколько лута, аптайм.

Конфиг (afk_zones.arbitration_farm):
    enabled: true
    frame: "valkyr"          # танк-фрейм (см. tools/frames_info.py --best arbitration)
    mode: tank               # tank | mesmer (mesmer = Revenant, без стрельбы)
    min_enemies: 3           # порог для притягивалок
    pull_slots: ["2", "3"]   # какие слоты считать «притяжением» (из базы фрейма)
    hp_panic_pct: 45
    death_pct: 18            # ниже — аварийный выход
    fire_during_hold: false  # автострельба между кастами (не для mesmer!)
    check_interval_sec: 0.6
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule, _StateVal
from data.frames_db import get_frame


class ArbitrationFarm(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        HOLD = _StateVal("HOLD")
        PULL_COMBO = _StateVal("PULL_COMBO")
        SURVIVAL = _StateVal("SURVIVAL")
        EMERGENCY_EXIT = _StateVal("EMERGENCY_EXIT")

    def __init__(self, bot, cfg, name="arbitration_farm"):
        super().__init__(bot, cfg, name)
        self.frame_name = str(cfg.get("frame", "valkyr"))
        self.frame = get_frame(self.frame_name)
        self.mode = str(cfg.get("mode", "tank")).lower()
        self.min_enemies = int(cfg.get("min_enemies", 3))
        self.pull_slots = [str(s) for s in cfg.get("pull_slots", ["2", "3"])]
        self.hp_panic = float(cfg.get("hp_panic_pct", 45))
        self.death_pct = float(cfg.get("death_pct", 18))
        self.fire_hold = cfg.get("fire_during_hold", False)
        self.tick_interval = float(cfg.get("check_interval_sec", 0.6))
        self._last_cast = {}
        self._last_pull = 0.0
        self._last_hp_warn = 0.0

    # ---------- хелперы ----------
    def _key(self, slot: str) -> str:
        from data.frames_db import ABILITY_KEYS
        return self.frame["abilities"].get(slot, {}).get(
            "hotkey") or ABILITY_KEYS.get(slot, "q")

    def _ready(self, slot: str, now: float) -> bool:
        cd = float(self.frame["abilities"].get(slot, {}).get("cooldown", 30))
        cd *= random.uniform(0.93, 1.12)          # анти-паттерн
        return now - self._last_cast.get(slot, 0.0) > cd

    def _cast(self, slot: str):
        self.bot.input.press_key(self._key(slot))
        self._last_cast[slot] = time.time()
        self.bot.stats.setdefault("arb_casts", {})
        self.bot.stats["arb_casts"][slot] = \
            self.bot.stats["arb_casts"].get(slot, 0) + 1

    def _read_hp(self, frame):
        try:
            roi_rel = self.bot.cfg.get("vision", {}).get(
                "hud_hp_roi", [0.02, 0.90, 0.20, 0.05])
            h, w = frame.shape[:2]
            return self.bot.vision.health_bar_ratio(frame, (
                int(roi_rel[0] * w), int(roi_rel[1] * h),
                int(roi_rel[2] * w), int(roi_rel[3] * h)))
        except Exception:
            return None

    def _is_pull(self, slot: str) -> bool:
        ab = self.frame["abilities"].get(slot, {})
        text = (str(ab.get("notes", "")) + " " + str(ab.get("name", ""))).lower()
        return any(k in text for k in ("притяжен", "стягив", "pull", "nexus",
                                       "defection", "vacuum"))

    # ---------- ядро ----------
    def on_tick(self, frame):
        now = time.time()
        inp = self.bot.input

        enemies = []
        try:
            enemies = self.bot.vision.find_color_blobs(
                frame, "enemy_marker", min_area=40)
        except KeyError:
            pass

        hp = self._read_hp(frame)

        # --- аварийный выход при верной смерти ---
        if hp is not None and hp * 100 < self.death_pct:
            if not self.in_state(self.State.EMERGENCY_EXIT):
                self.log.error("HP %.0f%% < %.0f%% — аварийный выход из Арбитража!",
                               hp * 100, self.death_pct)
                self.set_state(self.State.EMERGENCY_EXIT)
            inp.press_key("esc")
            time.sleep(random.uniform(0.5, 0.9))
            inp.press_key("enter")
            self.bot.stats["arb_emergency_exits"] = \
                self.bot.stats.get("arb_emergency_exits", 0) + 1
            return

        # --- режим выживания выше паники ---
        if hp is not None and hp * 100 < self.hp_panic:
            self.set_state(self.State.SURVIVAL)
            surv = list(self.frame.get("survival") or [])
            for slot in surv:
                if self._ready(slot, now):
                    self._cast(slot)
                    self.log.warning("Спасалка %s при HP %.0f%%",
                                     self.frame["abilities"][slot]["name"],
                                     hp * 100)
                    return
            inp.hold_key("s", 0.7)     # нет готовых щитов — отходим
            return

        # --- основная ротация ---
        self.set_state(self.State.HOLD if enemies else self.State.IDLE)

        if self.mode == "mesmer":
            # Revenant Mesmer/Defection: каст по кулдауну, НЕ стреляем —
            # обращённые враги делают всю работу.
            for slot in (self.frame.get("sustain") or []):
                if self._ready(slot, now) and enemies:
                    self._cast(slot)
                    return
            return

        # tank-режим: сначала притягивалка при толпе, затем щиты/DPS по роте
        if len(enemies) >= self.min_enemies and now - self._last_pull > 8:
            for slot in self.pull_slots:
                if slot in self.frame["abilities"] and self._is_pull(slot) \
                        and self._ready(slot, now):
                    self._cast(slot)
                    self._last_pull = now
                    self.set_state(self.State.PULL_COMBO)
                    # добиваем комбо-слотом сразу после стягивания
                    combo = self.frame.get("combo") or []
                    follow = [s for s in combo if s != slot]
                    if follow and self._ready(follow[0], now):
                        time.sleep(random.uniform(0.4, 0.8))
                        self._cast(follow[0])
                    return

        for slot in (self.frame.get("sustain") or []):
            if self._ready(slot, now):
                self._cast(slot)
                break

        if self.fire_hold and enemies and self.mode != "mesmer":
            e = min(enemies, key=lambda d: abs(d.cx - frame.shape[1] / 2)
                    + abs(d.cy - frame.shape[0] / 2))
            x, y = self.bot.capture.to_screen_coords(e.cx, e.cy)
            inp.click_at(x, y)
            inp.fire_held(float(self.fire_hold))
