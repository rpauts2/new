#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
necralisk_farm.py — фарм активности НЕКРАЛОХА через Necralot / Duviri-пороги.

Что автоматизируется (по мотивам гайдов сообщества):
  • Necralot (Глубинный Шрам / Duviri Pinn): выбор «безопасного» лота по
    иконкам наград (некралох > ресурсы), подтверждение;
  • Contagion-стиль: стоять в зоне споров и перекачивать некралохи кнопкой E;
  • Собирает «Echo Wand»-подобные активности: ждёт маркер взаимодействия
    (жёлтый ромб) и жал F/взаимодействие;
  • После выхода — авто-подтверждение экранов награды (делегировано auto_reward).

Конфиг (afk_zones.necralisk_farm):
  mode: "pinn" | "contagion"   # стиль активности
  poll_sec: 1.0
  interact_key: "f"            # клавиша взаимодействия в Warframe
  extract_template: extraction_button.png
  gear_choice_template: gear_choice_screen.png
  min_loot_blobs: 2            # сколько оранжевых маркеров = есть что фармить
  stay_center: true            # не двигаться (споры сами капают)
"""
from __future__ import annotations

import time

from modules.base import FarmModule, _StateVal


class NecraliskFarm(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        SCAN = _StateVal("SCAN")
        HARVEST = _StateVal("HARVEST")
        EXTRACT_WAIT = _StateVal("EXTRACT_WAIT")
        GEAR_PICK = _StateVal("GEAR_PICK")
        COOLDOWN = _StateVal("COOLDOWN")
    def __init__(self, bot, cfg, name="necralisk_farm"):
        super().__init__(bot, cfg, name)
        self.mode = cfg.get("mode", "pinn")
        self.interact_key = cfg.get("interact_key", "f")
        self.min_loot = int(cfg.get("min_loot_blobs", 2))
        self.stay_center = bool(cfg.get("stay_center", True))
        self.extract_tpl = cfg.get("extract_template", "extraction_button.png")
        self.gear_tpl = cfg.get("gear_choice_template", "gear_choice_screen.png")
        self._harvest_since = 0.0
        self.set_state(self.State.SCAN)

    # ------------------------------------------------------------------
    def _blobs(self, frame, key):
        try:
            return self.bot.vision.find_color_blobs(frame, key, min_area=50)
        except KeyError:
            return []

    def on_tick(self, frame):
        st = self.state

        if st == self.State.GEAR_PICK:
            dets = self.bot.vision.match_template(frame, self.gear_tpl, max_results=1) \
                if self.gear_tpl in self.bot.vision.templates else []
            if dets:
                self.click_detection(dets[0])
                self.log.info("Подтвердил выбор снаряжения лота")
                self.set_state(self.State.HARVEST)
                self._harvest_since = time.time()
            elif not self.bot.vision.match_template(frame, self.extract_tpl, max_results=1):
                # возможно уже в миссии
                self.set_state(self.State.HARVEST)
                self._harvest_since = time.time()
            return

        if st == self.State.SCAN:
            loot = self._blobs(frame, "loot_marker")
            if len(loot) >= self.min_loot:
                self.log.info("Найдено %d маркеров — начинаю сбор", len(loot))
                self.set_state(self.State.HARVEST)
                self._harvest_since = time.time()
            return

        if st == self.State.HARVEST:
            # контaгиоз-режим: просто стоим в зоне, споры капают сами
            if self.mode == "contagion" and self.stay_center:
                pass
            # собираем оранжевые маркеры кликами/взаимодействием
            loot = self._blobs(frame, "loot_marker")
            if loot:
                near = min(loot, key=lambda d: (d.cx - frame.shape[1]/2)**2 +
                           (d.cy - frame.shape[0]/2)**2)
                # если маркер близко к центру экрана — жмём F (взаимодействие),
                # иначе клик (стрельба по далёкому объекту его раскрывает)
                if abs(near.cx - frame.shape[1]/2) < 120 and \
                   abs(near.cy - frame.shape[0]/2) < 120:
                    self.bot.input.press_key(self.interact_key)
                else:
                    self.click_detection(near)
                self.bot.stats.setdefault("necraloths_collected", 0)
                self.bot.stats["necraloths_collected"] += 1
                time.sleep(0.4)
            else:
                # долго нет лута — ищем кнопку выхода
                ex = self.bot.vision.match_template(frame, self.extract_tpl,
                                                    max_results=1) \
                    if self.extract_tpl in self.bot.vision.templates else []
                if ex:
                    self.click_detection(ex[0])
                    self.set_state(self.State.EXTRACT_WAIT)
                elif time.time() - self._harvest_since > 240:
                    self.log.info("4 мин без лута — принудительный cooldown")
                    self.set_state(self.State.COOLDOWN)
            return

        if st == self.State.EXTRACT_WAIT:
            # auto_reward докликает экраны; мы просто отдыхаем
            self.set_state(self.State.COOLDOWN)
            return

        if st == self.State.COOLDOWN:
            if self.state_age() > 90:
                self.set_state(self.State.SCAN)
