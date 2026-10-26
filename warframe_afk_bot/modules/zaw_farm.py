#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zaw_farm.py — фарм Zo-метателем (Окукор / Bo / Glaive) по мотивам AHK-скриптов
wf-macro/zaw_throw.ahk, wf-macro/pt.ahk (Profit-Taker Orb), Yagami Glaive.ahk.

Классическая AFK-связка сообщества:
  • Profit-Taker Orb: удержание ЛКМ ~0.55 c -> бросок Zo (прыжок-прыжок-прицел-удар);
  • Окукор/Bo: просто цикл прыжкового броска по таймеру;
  • Glaive: бросок + подрыв в полёте (LMB во время броска).

Конфиг (afk_zones.zaw_throw):
    enabled: true
    mode: profit_taker      # profit_taker | okukor | bo | glaive
    fire_key: mouse_left
    aim_key: "["            # ADS (в некоторых сборках не нужен)
    melee_key: e
    jump_key: space
    throw_every_sec: [6, 12]   # случайный интервал полного цикла
    shoot_hold_sec: 0.55       # сколько «стрелять» перед броском (PT orb)
    humanize_pct: 15           # разброс всех таймингов
"""
from __future__ import annotations

import random
import time

from modules.base import FarmModule, _StateVal


class ZawThrowFarm(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        SHOOT = _StateVal("SHOOT")
        THROW = _StateVal("THROW")
        COOLDOWN = _StateVal("COOLDOWN")

    def __init__(self, bot, cfg, name="zaw_throw"):
        super().__init__(bot, cfg, name)
        self.mode = str(cfg.get("mode", "okukor")).lower()
        self.fire_key = cfg.get("fire_key", "mouse_left")
        self.aim_key = cfg.get("aim_key", "[")
        self.melee_key = cfg.get("melee_key", "e")
        self.jump_key = cfg.get("jump_key", "space")
        lo, hi = cfg.get("throw_every_sec", [6, 12])
        self.every = (float(lo), float(hi))
        self.shoot_hold = float(cfg.get("shoot_hold_sec", 0.55))
        self.hum = 1.0 + random.uniform(-0.1, 0.1) * float(cfg.get("humanize_pct", 15)) / 15.0
        self.tick_interval = 0.2
        self._next_at = 0.0

    def _dt(self, base: float) -> float:
        """Тайминг с человеческим джиттером (AHK lSleep+fps-поправки)."""
        return max(0.02, base * random.uniform(0.9, 1.1) * self.hum)

    # ---------- бросок Zo: два прыжка, прицел, ближний удар ----------
    def _throw(self):
        inp = self.bot.input
        inp.press_key(self.jump_key)
        time.sleep(self._dt(0.03))
        inp.press_key(self.jump_key)
        time.sleep(self._dt(0.03))
        inp.hold_key(self.aim_key, self._dt(0.03))
        inp.press_key(self.melee_key)
        time.sleep(self._dt(0.5))
        if self.mode == "glaive":
            # подрыв глевы в полёте — клик огнём
            inp.press_key(self.fire_key)
            time.sleep(self._dt(0.2))

    def on_tick(self, frame):
        now = time.time()

        if self.in_state(self.State.COOLDOWN):
            if now >= self._next_at:
                self.set_state(self.State.IDLE)
            return

        # один тик = один полный цикл (удержание огня -> бросок), как в AHK-оригинале;
        # блокирующие sleep здесь допустимы — планировщик всё равно идёт кадр за кадром
        if self.in_state(self.State.IDLE):
            self.set_state(self.State.SHOOT)

        if self.in_state(self.State.SHOOT):
            if self.mode in ("profit_taker", "okukor") and self.cfg.get("auto_shoot", True):
                # удержание огня (PT orb требует непрерывного DPS)
                self.bot.input.hold_key(self.fire_key, self._dt(self.shoot_hold))
            self._throw()
            self.bot.stats.setdefault("zaw_throws", 0)
            self.bot.stats["zaw_throws"] += 1
            self._next_at = time.time() + self._dt(random.uniform(*self.every))
            self.set_state(self.State.COOLDOWN)
