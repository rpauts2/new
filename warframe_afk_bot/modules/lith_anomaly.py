#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lith_anomaly.py — AFK-фарм ЛИТ-аномалий (Intact/Buggy Anomalies, Земля и др.).

Сценарий: аномалии появляются на карте мира раз в час окном ~10 минут.
Бот на экране карты крутится/сканирует, ждёт появления иконки аномалии
(PNG-шаблон anomaly_icon.png), кликает по ней, затем на экране миссии
кликает «Начать», а после завершения сам забирает награду (карточка мода —
через эвристику синего фона pick_reward_card).

Машина состояний:
    WAIT_WINDOW -> SCAN_MAP -> CLICK_ANOMALY -> START_MISSION
    -> IN_MISSION (считаем время) -> COLLECT_REWARD -> WAIT_WINDOW

Требуемые шаблоны: anomaly_icon.png, mission_start_button.png
(нарезаются из скриншотов утилитой tools/make_templates.py).
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule


class LithAnomalyFarm(FarmModule):
    class State(FarmModule.State):
        SCAN_MAP = 1
        CLICK_ANOMALY = 2
        START_MISSION = 3
        IN_MISSION = 4
        COLLECT_REWARD = 5

    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.state = self.State.SCAN_MAP
        self.scan_templates = cfg.get("scan_templates", ["anomaly_icon.png"])
        self.click_template = cfg.get("click_template", "anomaly_icon.png")
        self.reward_templates = cfg.get("reward_templates",
                                        ["mod_card.png", "claim_button.png"])
        self.loop_delay = float(cfg.get("loop_delay_sec", 60))
        self.tick_interval = 1.0
        self._next_scan = 0.0
        self._mission_deadline = 0.0

    def _pan_camera(self):
        """Плавное «вращение» картой для обзора всех секторов."""
        pg = getattr(self.bot.input, "_pg", None)
        if not pg:
            return
        for _ in range(random.randint(2, 4)):
            try:
                pg.moveRel(random.randint(150, 400), random.randint(-80, 80),
                           duration=0.2)
            except Exception:
                break
            time.sleep(0.15)

    def on_tick(self, frame):
        s = self.state

        if s == self.State.SCAN_MAP:
            if time.time() < self._next_scan:
                return
            self._next_scan = time.time() + self.loop_delay
            for tpl in self.scan_templates:
                dets = self.bot.vision.match_template(frame, tpl, threshold=0.75)
                if dets:
                    self.log.info("Аномалия найдена! (%s, conf=%.2f)",
                                  tpl, dets[0].confidence)
                    self._target = dets[0]
                    self.set_state(self.State.CLICK_ANOMALY)
                    return
            # не нашли — осмотрелись
            self._pan_camera()

        elif s == self.State.CLICK_ANOMALY:
            dets = self.bot.vision.match_template(frame, self.click_template,
                                                  threshold=0.75)
            if dets:
                self.click_detection(dets[0])
                self.log.info("Клик по аномалии")
                self.set_state(self.State.START_MISSION)
            else:
                self.set_state(self.State.SCAN_MAP)

        elif s == self.State.START_MISSION:
            dets = self.bot.vision.match_template(frame, "mission_start_button.png")
            if dets:
                self.click_detection(dets[0])
                self.log.info("Миссия запущена — ждём завершения (~90 c)")
                self._mission_deadline = time.time() + 90
                self.set_state(self.State.IN_MISSION)
                self.bot.stats["cycles_done"] += 1
            elif self.state_age() > 15:
                self.set_state(self.State.SCAN_MAP)

        elif s == self.State.IN_MISSION:
            # Аномалия «ловится» сама по таймеру миссии; мониторим экран реварда
            card = self.bot.vision.pick_reward_card(frame)
            claim = self.bot.vision.match_template(frame, "claim_button.png")
            if card or claim:
                self.set_state(self.State.COLLECT_REWARD)
            elif time.time() > self._mission_deadline + 120:
                self.log.warning("Миссия зависла >207 c — возврат к скану")
                self.set_state(self.State.SCAN_MAP)

        elif s == self.State.COLLECT_REWARD:
            card = self.bot.vision.pick_reward_card(frame)
            if card:
                self.click_detection(card)
                self.log.info("Выбрана карточка награды (мод)")
                time.sleep(0.6)
            for tpl in ("claim_button.png", "ok_button.png"):
                dets = self.bot.vision.match_template(frame, tpl)
                if dets:
                    self.click_detection(dets[0])
                    self.log.info("Награда забрана (%s)", tpl)
                    break
            if self.state_age() > 10:
                self.set_state(self.State.SCAN_MAP)
