#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
effusion_farm.py — AFK-ферма ЭФФОСОВ (Orokin Moon / Phobos).

Классика жанра: узел с бесконечным спавном врагов, персонаж стоит на точке,
оружие стреляет в упор. Модуль:
  • удерживает огонь (ЛКМ) «залпами» или непрерывно;
  • авто-перезарядка по счётчику выстрелов (reload_every_shots);
  • ищет синий маркер ближайшего врага (HSV) и чуть доворачивает камеру мышью;
  • кликает по оранжевым маркерам выпавшего лута/эффосов;
  • считает статистику в bot.stats.

Требуемые шаблоны: отсутствуют (работает только на HSV-маркерах) —
можно использовать сразу после калибровки цветов под своё разрешение.
"""
from __future__ import annotations

import math
import random
import time

from modules.base import FarmModule


class EffusionFarm(FarmModule):
    class State(FarmModule.State):
        SCANNING = 1
        FIRING = 2
        RELOADING = 3
        LOOTING = 4

    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.state = self.State.SCANNING
        self.aim_mode = cfg.get("aim", "nearest_enemy_marker")
        self.fire_key = {"mouse_left": "left", "mouse_right": "right"}.get(
            cfg.get("fire_key", "mouse_left"), "left")
        self.reload_key = cfg.get("reload_key", "r")
        self.reload_every = int(cfg.get("reload_every_shots", 21))
        self.shot_duration = 0.11          # сек между «выстрелами» при подсчёте
        self.burst = bool(cfg.get("burst_enabled", False))
        self.burst_on = int(cfg.get("burst_on_ms", 800)) / 1000
        self.burst_off = int(cfg.get("burst_off_ms", 2500)) / 1000
        self.pickup_loot = bool(cfg.get("pickup_loot", True))
        # --- v2: safety — следим за HP и умеем возрождаться ---
        self.health_watch = bool(cfg.get("health_watch", True))
        self.hp_roi = tuple(cfg.get("hp_bar_roi", [30, 940, 400, 25]))  # x,y,w,h в координатах кадра
        self.hp_min_ratio = float(cfg.get("hp_min_ratio", 0.18))
        self.revive_enabled = bool(cfg.get("revive_enabled", True))
        self.revive_key = cfg.get("revive_key", "x")   # стандартная клавиша revive в Warframe
        self._dead_since = 0.0
        self._low_hp_since = 0.0
        self._shots_in_mag = 0
        self._fire_started = 0.0

    # ------------------------------------------------------------------
    def _safety_tick(self, frame) -> bool:
        """True — нужно пропустить обычный цикл (низкое HP / смерть)."""
        if not self.health_watch:
            return False
        try:
            ratio = self.bot.vision.health_bar_ratio(frame, self.hp_roi)
        except Exception:
            return False
        if ratio < self.hp_min_ratio:
            if self._low_hp_since == 0:
                self._low_hp_since = time.time()
            # при критическом HP перестаём стрелять и отходим назад (S)
            if time.time() - self._low_hp_since > 1.0:
                self.log.warning("HP критично (%.0f%%) — отход/ревайв", ratio * 100)
                if self.revive_enabled and ratio < 0.03:
                    self.bot.input.press_key(self.revive_key)
                    self.bot.stats["revives"] = self.bot.stats.get("revives", 0) + 1
                    self._dead_since = time.time()
                self.bot.input.strafe("s", duration=0.6)
                self._low_hp_since = 0
                return True
        else:
            self._low_hp_since = 0
        # после ревайва даём время на загрузку/возрождение
        if self._dead_since and time.time() - self._dead_since < 20:
            return True
        self._dead_since = 0
        return False

    def _find_enemy(self, frame):
        """Ближайший к перекрестию синий маркер врага."""
        h, w = frame.shape[:2]
        blobs = self.bot.vision.find_color_blobs(
            frame, "enemy_marker", min_area=30,
            sort_by_distance_to=(w / 2, h / 2))
        return blobs[0] if blobs else None

    def _find_loot(self, frame):
        h, w = frame.shape[:2]
        return self.bot.vision.find_color_blobs(
            frame, "loot_marker", min_area=40,
            sort_by_distance_to=(w / 2, h / 2))

    def _soft_aim(self, det):
        """Мягкая коррекция прицела движением мыши (pyautogui rel-move)."""
        pg = getattr(self.bot.input, "_pg", None)
        if not pg:
            return
        h, w = self.bot.last_frame.shape[:2] if self.bot.last_frame is not None else (1080, 1920)
        dx = int((det.cx - w / 2) * 0.08)      # пропорциональная ПИД-подобная подстройка
        dy = int((det.cy - h / 2) * 0.08)
        dx = max(-60, min(60, dx + random.randint(-2, 2)))
        dy = max(-40, min(40, dy + random.randint(-2, 2)))
        try:
            pg.moveRel(dx, dy, duration=0.05)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def on_tick(self, frame):
        # 0. Безопасность: HP / смерть — приоритет всего остального
        if self._safety_tick(frame):
            return
        # 1. Лут всегда приоритетнее стрельбы (пока горит маркер — подобрать)
        if self.pickup_loot:
            loot = self._find_loot(frame)
            if loot:
                for d in loot[:3]:
                    self.click_detection(d)
                    self.bot.stats["loot_picked"] += 1
                    self.log.info("Подобран лут (%d, %d)", d.cx, d.cy)
                    time.sleep(random.uniform(0.15, 0.35))

        enemy = self._find_enemy(frame) if self.aim_mode == "nearest_enemy_marker" else None

        # 2. Перезарядка по счётчику
        if self._shots_in_mag >= self.reload_every:
            self.set_state(self.State.RELOADING)
            self.bot.input.press_key(self.reload_key)
            self.log.info("Перезарядка (после %d выстрелов)", self._shots_in_mag)
            self._shots_in_mag = 0
            time.sleep(1.6)   # время анимации перезарядки
            self.set_state(self.State.SCANNING)
            return

        # 3. Стрельба
        if enemy or self.aim_mode == "center":
            if enemy:
                self._soft_aim(enemy)
            self.set_state(self.State.FIRING)
            if self.burst:
                on = random.uniform(self.burst_on * 0.8, self.burst_on * 1.2)
                self.bot.input.fire_held(on, button=self.fire_key)
                self._shots_in_mag += int(on / self.shot_duration)
                self.bot.stats["shots_fired"] += int(on / self.shot_duration)
                time.sleep(random.uniform(self.burst_off * 0.8, self.burst_off * 1.2))
            else:
                tap = random.uniform(0.35, 0.7)
                self.bot.input.fire_held(tap, button=self.fire_key)
                n = max(1, int(tap / self.shot_duration))
                self._shots_in_mag += n
                self.bot.stats["shots_fired"] += n
        else:
            # Врагов нет — микро-разведка: лёгкий стрейф взглядом, чтобы поймать спавн
            self.set_state(self.State.SCANNING)
            self.bot.input.move_rel(random.randint(-30, 30), 0)
