#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nightwave_farm.py — AFK-фарм ночной волны Nightwave (Orokin Moon) с Revenant.

Легендарная связка из гайдов комьюнити: Revenant (Mesmer Skin/Shadow) стоит
в углу карты Orokin Luna, враги сами умирают от Mesmer; Hydroid с аурой
добивает уцелевших. Модуль:
  • активирует способности по таймингам (E — Mesmer, Q — Regret, аура Hydroid);
  • удерживает пассивный огонь/стрейф-микродвижения для анти-афк;
  • подбирает лут по оранжевым маркерам (сферолиты/кредиты тоже ловятся);
  • считает «волны» по всплескам синих маркеров — статистика XP/циклов.

Конфиг (afk_zones.nightwave_farm):
    enabled: true
    abilities:                 # ротация способностей [клавиша, задержка_после]
      - {key: e, cooldown_sec: 45}   # Mesmer
      - {key: q, cooldown_sec: 60}   # Regret (если используется)
      - {key: 4, cooldown_sec: 80}   # аура Hydroid в 4-м слоте
    fire_while_idle: true      # стрелять когда нет маркеров (дальние спавны)
    pickup_loot: true
    check_interval_sec: 0.5
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule


class NightwaveFarm(FarmModule):
    class State(FarmModule.State):
        FARMING = 1
        ABILITY_ROTATION = 2
        LOOTING = 3

    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.state = self.State.FARMING
        self.abilities = cfg.get("abilities", [{"key": "e", "cooldown_sec": 45}])
        self.fire_idle = bool(cfg.get("fire_while_idle", True))
        self.pickup_loot = bool(cfg.get("pickup_loot", True))
        self._next_ability = {a["key"]: time.time() for a in self.abilities}
        self._prev_enemy_count = 0
        self._wave_started = 0.0

    def _count_enemies(self, frame) -> int:
        h, w = frame.shape[:2]
        return len(self.bot.vision.find_color_blobs(
            frame, "enemy_marker", min_area=30,
            sort_by_distance_to=(w / 2, h / 2)))

    def on_tick(self, frame):
        now = time.time()

        # 1. Ротация способностей по индивидуальным кулдаунам
        for ab in self.abilities:
            key = ab["key"]
            cd = float(ab.get("cooldown_sec", 45))
            if now >= self._next_ability.get(key, 0):
                self.bot.input.press_key(key, hold=0.05)
                self._next_ability[key] = now + cd * random.uniform(0.95, 1.08)
                self.log.info("Ability '%s' активирована", key)
                self.bot.stats["abilities_cast"] = \
                    self.bot.stats.get("abilities_cast", 0) + 1

        # 2. Учёт волн: резкий рост числа маркеров = новая волна
        cnt = self._count_enemies(frame)
        if cnt > max(3, self._prev_enemy_count + 3):
            if now - self._wave_started > 20:
                self._wave_started = now
                self.bot.stats["waves_seen"] = self.bot.stats.get("waves_seen", 0) + 1
                self.log.info("Волна #%d (~%d целей)",
                              self.bot.stats["waves_seen"], cnt)
        self._prev_enemy_count = cnt

        # 3. Лут
        if self.pickup_loot:
            h, w = frame.shape[:2]
            loot = self.bot.vision.find_color_blobs(
                frame, "loot_marker", min_area=40,
                sort_by_distance_to=(w / 2, h / 2))
            for d in loot[:2]:
                self.click_detection(d)
                self.bot.stats["loot_picked"] += 1
                time.sleep(random.uniform(0.15, 0.3))

        # 4. Анти-афк микродвижение камеры (Revenant всё равно стоит в углу)
        if random.random() < 0.15:
            self.bot.input.move_rel(random.randint(-15, 15),
                                    random.randint(-5, 5))
