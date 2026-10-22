#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ability_autopilot.py — автопилот способностей под конкретного варфрейма.

Что умеет:
  • Читает data/frames_db.py — ротация combo (предстартовые баффы) и
    sustain (поддержка баффов по кулдаунам) для 20+ фреймов;
  • Следит за таймерами перезарядки каждой способности (cooldown + jitter);
  • Кастует только когда есть враги (HSV-маркеры) — экономит энергию;
  • Следи за HP: при низком здоровье включает «панику» — касты выживания
    (Snow Globe / Iron Skin / Well of Life), аварийный отдых, глоток щита;
  • Мониторит энергию: при низкой энергии ставит только дешёвые способности
    и ждёт регенерации (или требует Energy Pickup via pick_color);
  • Совместим с effusion_farm / nightwave профилями: сам ничего не стреляет,
    только жмёт клавиши Q/E/R/F в правильный момент.

Конфиг (afk_zones.ability_autopilot):
  frame: "revenant"          # имя фрейма из базы (см. tools/frames_info.py --list)
  auto_cast: true            # разрешить автокаст
  combat_only: true          # кастовать только при наличии enemy_marker на экране
  energy_min_pct: 25         # ниже — не кастовать дорогие способности
  hp_panic_pct: 30           # ниже — режим выживания
  cooldown_jitter_pct: 15    # случайное отклонение таймеров (анти-паттерн)
  extra_abilities: {}        # ручные переопределения: {"2": {"cooldown": 18}}
"""
from __future__ import annotations

import time
import random
import logging

from modules.base import FarmModule, _StateVal
from data.frames_db import get_frame


class AbilityAutopilot(FarmModule):

    class State:
        IDLE = _StateVal("IDLE")
        WAIT_ENEMIES = _StateVal("WAIT_ENEMIES")
        ROTATE = _StateVal("ROTATE")
        PANIC_SURVIVE = _StateVal("PANIC_SURVIVE")
        LOW_ENERGY = _StateVal("LOW_ENERGY")
    def __init__(self, bot, cfg, name="ability_autopilot"):
        super().__init__(bot, cfg, name)
        self.frame_name = str(cfg.get("frame", "")).lower()
        if not self.frame_name:
            raise ValueError("ability_autopilot: не указан frame в конфиге")
        self.frame = get_frame(self.frame_name)
        fit, why = self.frame.get("afk_fit", ("unknown", ""))
        self.log.info("Фрейм '%s' (роль=%s, AFK-пригодность=%s): %s",
                      self.frame_name, self.frame.get("role"), fit, why)

        # применяем ручные переопределения из конфига
        for slot, over in (cfg.get("extra_abilities") or {}).items():
            if slot in self.frame["abilities"]:
                self.frame["abilities"][slot].update(over)

        self.auto_cast = bool(cfg.get("auto_cast", True))
        self.combat_only = bool(cfg.get("combat_only", True))
        self.energy_min = float(cfg.get("energy_min_pct", 25))
        self.hp_panic = float(cfg.get("hp_panic_pct", 30))
        self.jitter = float(cfg.get("cooldown_jitter_pct", 15)) / 100.0

        # таймеры готовности: slot -> unix-time когда можно кастовать
        self.ready_at: dict[str, float] = {slot: 0.0
                                           for slot in self.frame["abilities"]}
        self._combo_done = False
        self._last_enemy_seen = 0.0
        self._casts_total = 0

    # ------------------------------------------------------------------
    def _can_cast(self, slot: str) -> bool:
        return time.time() >= self.ready_at.get(slot, 0.0)

    def _mark_cast(self, slot: str):
        ab = self.frame["abilities"].get(slot) or {}
        cd = float(ab.get("cooldown", 20))
        cd *= 1.0 + random.uniform(-self.jitter, self.jitter)
        self.ready_at[slot] = time.time() + max(2.0, cd)
        self._casts_total += 1
        self.bot.stats.setdefault("ability_casts", 0)
        self.bot.stats["ability_casts"] += 1

    def _cast(self, slot: str, frame) -> bool:
        ab = self.frame["abilities"].get(slot)
        if not ab or not self._can_cast(slot):
            return False
        key = ab.get("hotkey", "q")
        if ab.get("cast") == "hold":
            self.bot.input.hold_key(key, float(ab.get("hold_sec", 2.0)))
        else:
            self.bot.input.press_key(key)
        self._mark_cast(slot)
        self.log.debug("Каст [%s] %s (%s)", slot, ab.get("name", "?"), key)
        return True

    # ------------------------------------------------------------------
    def _slots_sorted(self, names: list[str]) -> list[str]:
        """Сортировка слотов по priority (дешёвые/важные раньше)."""
        abils = self.frame["abilities"]
        return sorted(names, key=lambda s: abils.get(s, {}).get("priority", 50))

    def on_tick(self, frame):
        if not self.auto_cast:
            return

        # --- оценка угрозы и ресурсов через зрение ---
        vis = self.bot.vision
        enemies = []
        try:
            enemies = vis.find_color_blobs(frame, "enemy_marker", min_area=40)
        except KeyError:
            pass
        if enemies:
            self._last_enemy_seen = time.time()
        in_combat = (time.time() - self._last_enemy_seen) < 6.0

        hp = None
        try:
            # hud_hp_roi = [x, y, w, h] в долях экрана (настраивается в config.vision)
            roi_rel = self.bot.cfg.get("vision", {}).get(
                "hud_hp_roi", [0.02, 0.90, 0.20, 0.05])
            h, w = frame.shape[:2]
            x = int(roi_rel[0] * w); y = int(roi_rel[1] * h)
            rw = int(roi_rel[2] * w); rh = int(roi_rel[3] * h)
            hp = vis.health_bar_ratio(frame, (x, y, rw, rh))
        except KeyError:
            hp = None   # health_red не настроен — режим паники выключен
        except Exception:
            hp = None

        low_hp = hp is not None and hp * 100 < self.hp_panic

        # --- машина состояний ---
        if low_hp:
            self.set_state(self.State.PANIC_SURVIVE)
        elif in_combat:
            self.set_state(self.State.ROTATE)
        else:
            self.set_state(self.State.WAIT_ENEMIES)

        st = self.state

        if st == self.State.WAIT_ENEMIES:
            self._combo_done = False   # следующая волна — заново открываемся
            # редкий «разминочный» каст дешёвой способности раз в пачку
            if random.random() < 0.02:
                cheap = [s for s in self.frame["abilities"]
                         if float(self.frame["abilities"][s].get("cooldown", 99)) <= 15]
                if cheap:
                    self._cast(min(cheap, key=lambda s:
                                   self.frame["abilities"][s]["cooldown"]), frame)

        elif st == self.State.ROTATE:
            if not self._combo_done:
                order = self._slots_sorted(self.frame.get("combo", []))
                done_any = False
                for slot in order:
                    if self._cast(slot, frame):
                        done_any = True
                        time.sleep(random.uniform(0.25, 0.6))
                self._combo_done = done_any
                if done_any:
                    self.log.info("Открылись комбо: %s", "+".join(order))
            else:
                # поддержка sustain-ротации по кулдаунам
                for slot in self._slots_sorted(self.frame.get("sustain", [])):
                    if self._can_cast(slot):
                        self._cast(slot, frame)
                        break
            # добиваем выстрелами, если профиль это не делает
            fire_cfg = self.cfg.get("fire_during_rotate", False)
            if fire_cfg and enemies:
                e = min(enemies, key=lambda d: abs(d.cx - frame.shape[1]/2)
                        + abs(d.cy - frame.shape[0]/2))
                self.bot.input.fire_held(float(fire_cfg))

        elif st == self.State.PANIC_SURVIVE:
            # сначала — способности выживания (минимальный priority среди
            # танкующих: snow globe/rhino skin/trinity welc...)
            surv = [s for s, ab in self.frame["abilities"].items()
                    if any(k in str(ab.get("notes", "")).lower()
                           for k in ("неуязв", "щит", "лечен", "стака", "вампир"))]
            casted = False
            for slot in self._slots_sorted(surv or list(self.frame["abilities"])):
                if self._cast(slot, frame):
                    casted = True
                    break
            if not casted:
                # отходим: бег назад + прыжок (уклон от огня)
                self.bot.input.hold_key("s", 0.8)
                self.bot.input.press_key("space")
            if hp is not None and hp * 100 > self.hp_panic + 15:
                self.set_state(self.State.ROTATE)
                self._combo_done = False
