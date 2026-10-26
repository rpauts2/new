#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
duviri_loop.py — AFK-фарм НЕКРАЛОХА (Duviri / «Loop», Глубинный Шрам).

Некралох капает ~200 за цикл; многие игроки оставляют бота проходить
короткие циклы Duviri. Модуль работает как «кликер-навигатор»:
на каждом экране ищет знакомые кнопки по шаблонам и жмёт их,
проходя полный круг: выбор наград -> старт забега -> завершение целей ->
эвакуация -> «Продолжить» (новый луп) -> повтор.

Машина состояний строится вокруг табличного матчинга: какой шаблон сейчас
виден, то действие и выполняем. Требуемые шаблоны см. cfg["templates"]
(нарезаются tools/make_templates.py из ваших скриншотов).
"""
from __future__ import annotations

import time

from modules.base import FarmModule


class DuviriLoopFarm(FarmModule):
    class State(FarmModule.State):
        NAVIGATING = 1
        IN_RUN = 2
        EXTRACTING = 3
        REWARDS = 4

    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.state = self.State.NAVIGATING
        self.tpl = cfg.get("templates", {})
        self.tick_interval = float(cfg.get("poll_sec", 1.0))
        self._run_started_at = 0.0
        # Максимум «залипания» в забеге, сек; после — пробуем выбраться сами
        self.max_run_time = float(cfg.get("max_run_time_sec", 25 * 60))

    def _click_if_seen(self, frame, key: str, wait_after: float = 1.0) -> bool:
        name = self.tpl.get(key)
        if not name:
            return False
        dets = self.bot.vision.match_template(frame, name)
        if dets:
            self.click_detection(dets[0])
            self.log.info("Клик: %s (%s)", key, name)
            time.sleep(wait_after)
            return True
        return False

    def on_tick(self, frame):
        s = self.state

        # --- Экраны меню/выбора наград: просто жмём всё подряд узнаваемое ---
        if s == self.State.NAVIGATING:
            for key in ("gear_choice", "continue", "start_run"):
                if self._click_if_seen(frame, key, wait_after=1.5):
                    if key == "start_run":
                        self._run_started_at = time.time()
                        self.set_state(self.State.IN_RUN)
                    return
            # ничего не кликнули и долго стоим — возможно, мы уже внутри забега
            if self.state_age() > 30:
                self.set_state(self.State.IN_RUN)
                self._run_started_at = time.time()

        # --- Внутри забега: ждём завершения целей или таймаута ---
        elif s == self.State.IN_RUN:
            if self._click_if_seen(frame, "complete", wait_after=1.0):
                return  # подтвердили выполнение цели
            extraction_ready = self._click_if_seen(frame, "extract", wait_after=1.0)
            if extraction_ready:
                self.bot.stats["cycles_done"] += 1
                self.set_state(self.State.EXTRACTING)
                return
            if time.time() - self._run_started_at > self.max_run_time:
                self.log.warning("Забег дольше %.0f мин — принудительный выход"
                                 " (ESC -> выход из сессии)", self.max_run_time / 60)
                self.bot.input.press_key("esc")
                time.sleep(1.0)
                self.set_state(self.State.REWARDS)

        # --- Экран эвакуации/итогов ---
        elif s == self.State.EXTRACTING:
            clicked = False
            for key in ("extract", "continue", "ok"):
                if self._click_if_seen(frame, key, wait_after=1.2):
                    clicked = True
            if not clicked and self.state_age() > 20:
                self.set_state(self.State.REWARDS)
            elif not clicked:
                self.set_state(self.State.NAVIGATING)

        # --- Экран наград: выбираем синюю карточку (мод) либо жмём claim ---
        elif s == self.State.REWARDS:
            card = self.bot.vision.pick_reward_card(frame)
            if card:
                self.click_detection(card)
                self.log.info("Выбрана награда (карточка мода)")
                time.sleep(1.0)
            if self._click_if_seen(frame, "claim", wait_after=1.0):
                self.set_state(self.State.NAVIGATING)
                return
            if self._click_if_seen(frame, "continue", wait_after=1.0):
                self.set_state(self.State.NAVIGATING)
                return
            if self.state_age() > 25:
                self.set_state(self.State.NAVIGATING)
