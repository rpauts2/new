#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_reward.py — универсальный «дожиматель» пост-миссионных экранов.

Работает поверх любой другой фермы: постоянно сканирует экран и кликает
узнаваемые кнопки (Продолжить / Забрать / OK / Повторить / Выход / Принять),
пока ни одна не найдена. Это заменяет ручное «просмотреть 3 реварда» после
каждой миссии — ключевая часть большинства AFK-сеттапов.

Также умеет выбирать карточку награды по эвристике цвета (синий = мод).
"""
from __future__ import annotations

import time

from modules.base import FarmModule


class AutoRewardClicker(FarmModule):
    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.templates = cfg.get("templates", ["continue_button.png",
                                               "claim_button.png",
                                               "ok_button.png"])
        self.first_delay = float(cfg.get("delay_first_sec", 3.0))
        self.max_clicks = int(cfg.get("max_clicks_per_screen", 12))
        self.tick_interval = 0.7
        self._idle_since = time.time()
        self._active = False

    def on_tick(self, frame):
        clicked_any = False
        # 1. Обычные кнопки по шаблонам
        for tpl in self.templates:
            dets = self.bot.vision.match_template(frame, tpl, max_results=1)
            if dets:
                self.click_detection(dets[0])
                self.bot.stats["screens_clicked"] += 1
                self.log.info("Auto-reward: клик %s", tpl)
                clicked_any = True
                time.sleep(0.5)
        # 2. Если кнопок нет, но рядом видна карточка-награда — выбрать синюю
        if not clicked_any:
            card = self.bot.vision.pick_reward_card(frame)
            if card and card.confidence > 0.5:
                self.click_detection(card)
                self.log.info("Auto-reward: выбрана карточка награды")
                clicked_any = True

        if clicked_any:
            self._active = True
            self._idle_since = time.time()
        else:
            # экран чист > first_delay -> режим ожидания (не мешаем другим модулям)
            if self._active and time.time() - self._idle_since > self.first_delay:
                self._active = False
