#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
profile_runner.py — модуль-обёртка над ProfileEngine.

Позволяет запускать «профили-плейлисты» (YAML-скрипты полных фарма-циклов)
как обычный модуль бота, включая паузу при открытии меню и приоритет над
простыми фермами (если профиль активен — effusion/lith спят, чтобы не
мешать друг другу кликами; настраивается `exclusive: true`).

Конфиг (afk_zones.profile_runner):
    enabled: true
    exclusive: true                      # глушить другие боевые модули
    profile_file: profiles/example_mission_cycle.yaml
    check_interval_sec: 0.4
"""
from __future__ import annotations

from modules.base import FarmModule
from core.profile_engine import ProfileEngine


class ProfileRunner(FarmModule):
    def __init__(self, bot, cfg, name):
        super().__init__(bot, cfg, name)
        self.exclusive = bool(cfg.get("exclusive", True))
        self.engine = ProfileEngine(bot, cfg)
        self.tick_interval = self.engine.tick_interval

    @property
    def active(self) -> bool:
        return self.engine.profile is not None and self.bot.running

    def on_tick(self, frame):
        if self.engine.profile is None:
            return
        # в меню/loading профиль ждёт — движок сам проверит условия when
        self.engine.on_tick(frame)

    def pause_others(self):
        """Эксклюзив: поставить боевые модули на паузу, пока профиль у руля."""
        if not self.exclusive or not self.active:
            return []
        paused = []
        for m in self.bot.modules:
            if m is self:
                continue
            if m.name in ("effusion_farm", "lith_anomaly", "duviri_loop"):
                if getattr(m, "_paused_by_profile", False) is False:
                    m._paused_by_profile = True
                    paused.append(m.name)
        return paused
