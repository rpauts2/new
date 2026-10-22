#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
profile_engine.py — движок «профилей фарма» (плейлистов), как у топовых
ботов из комьюнити Warframe (WFU-макросы, AHK-скрипты, AutoHotFarming),
но реализованный честно: только экран + ввод, никаких инъекций.

Профиль = YAML с последовательностью ШАГОВ. Каждый шаг имеет:
  name:    идентификатор
  when:    условие запуска (опционально)
  actions: список действий
  next:    переход (goto / on_success / on_fail) — можно строить конечные
           автоматы любой сложности: «зайти в миссию → фармить → выйти →
           реварды → повторить»

Синтаксис условия `when` (берётся из последнего кадра vision-стэка):
  screen == mission          — классификатор detect_screen()
  template "x.png" > 0.85    — найден шаблон с порогом
  color loot_marker exists   — HSV-маркер присутствует
  color enemy_marker count > 3
  always                     — без условий

Действия (actions):
  press: {key, hold}         down/up: key        wait: sec (или [min,max])
  click_template: "x.png"    click_color: "loot_marker"   click_point: [x,y]
  move_rel: [dx,dy]          scroll: n            strafe: {dir,sec}
  fire: {sec, button}        reload: true (press reload_key)
  set: {var: value}          log: "текст"         goto: step_name
  repeat_until: {template|color|screen, max_sec}  — ждать условие в цикле

Переменные профиля (${var}) подставляются в числа/строки действий —
например счётчик циклов для статистики.

Пример полного цикла см. profiles/example_mission_cycle.yaml
"""
from __future__ import annotations

import os
import re
import time
import random
import logging
from typing import Optional

import yaml
import numpy as np

log = logging.getLogger("wf.profile")


class ProfileError(Exception):
    pass


class ProfileStep:
    def __init__(self, d: dict):
        self.name: str = d.get("name", "step")
        self.when: str = d.get("when", "always")
        self.actions: list[dict] = d.get("actions", []) or []
        self.next: Optional[str] = d.get("next")
        self.repeat: int = int(d.get("repeat", 1))
        self.timeout_sec: float = float(d.get("timeout_sec", 0))


class FarmProfile:
    """Один профиль-плейлист."""

    def __init__(self, data: dict, source: str = "<inline>"):
        self.name = data.get("name", os.path.basename(source))
        self.description = data.get("description", "")
        steps = data.get("steps", [])
        if not steps:
            raise ProfileError(f"Профиль {source}: нет шагов")
        self.steps: dict[str, ProfileStep] = {}
        order = []
        for s in steps:
            st = ProfileStep(s)
            self.steps[st.name] = st
            order.append(st.name)
        self.order = order
        self.start = data.get("start", order[0])
        self.vars_default: dict = data.get("vars", {}) or {}
        # проверка переходов
        for st in self.steps.values():
            if st.next and st.next not in self.steps:
                raise ProfileError(
                    f"Профиль {source}: шаг '{st.name}' -> неизвестный '{st.next}'")


class ProfileEngine:
    """Интерпретатор профилей поверх bot.capture/vision/input."""

    VAR_RE = re.compile(r"\$\{(\w+)\}")

    def __init__(self, bot, cfg: dict):
        self.bot = bot
        self.cfg = cfg or {}
        self.log = logging.getLogger("wf.profile")
        self.tick_interval = float(cfg.get("check_interval_sec", 0.4))
        self.profile: Optional[FarmProfile] = None
        self.current: Optional[ProfileStep] = None
        self.vars: dict = {}
        self._last_screen: str = "unknown"
        self._last_dets: dict[str, list] = {}
        self._paused = False
        self.load_profile(cfg.get("profile_file"))

    # ------------------------- загрузка -------------------------
    def load_profile(self, path: Optional[str]):
        if not path:
            return
        full = path if os.path.isabs(path) else path
        try:
            with open(full, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self.profile = FarmProfile(data, full)
            self.vars = dict(self.profile.vars_default)
            self.current = self.profile.steps[self.profile.start]
            self.log.info("Профиль загружен: %s (%d шагов)",
                          self.profile.name, len(self.profile.steps))
        except FileNotFoundError:
            self.log.warning("Файл профиля %s не найден", full)
        except Exception as e:
            self.log.error("Ошибка профиля %s: %s", full, e)

    # ------------------------- переменные -------------------------
    def _resolve(self, val):
        if isinstance(val, str):
            def sub(m):
                return str(self.vars.get(m.group(1), m.group(0)))
            out = self.VAR_RE.sub(sub, val)
            # строка могла стать числом
            try:
                return float(out) if "." in out else int(out)
            except ValueError:
                return out
        if isinstance(val, list):
            return [self._resolve(v) for v in val]
        return val

    # ------------------------- условия when -------------------------
    def _eval_condition(self, cond: str, frame: np.ndarray) -> bool:
        cond = cond.strip()
        if cond in ("always", "", "true"):
            return True
        # screen == mission | screen != loading
        m = re.match(r"screen\s*(==|!=)\s*(\w+)", cond)
        if m:
            scr = self._scan_screen(frame)
            return (scr == m.group(2)) if m.group(1) == "==" else (scr != m.group(2))
        # template "file.png" > 0.85  |  template "f" exists | missing
        m = re.match(r'template\s+"?([\w.\-]+)"?\s*(exists|missing|>\s*[\d.]+)', cond)
        if m:
            tpl, op = m.group(1), m.group(2)
            thr = 0.85
            if op.startswith(">"):
                thr = float(op[1:])
            dets = self.bot.vision.match_template(frame, tpl, threshold=thr,
                                                  max_results=1)
            found = bool(dets)
            self._last_dets[f"tpl:{tpl}"] = dets
            if op == "missing":
                return not found
            return found
        # color loot_marker exists | count > N
        m = re.match(r"color\s+(\w+)\s*(exists|missing|count\s*>\s*\d+)", cond)
        if m:
            key, op = m.group(1), m.group(2)
            blobs = self.bot.vision.find_color_blobs(frame, key, min_area=25)
            self._last_dets[f"col:{key}"] = blobs
            if op == "missing":
                return len(blobs) == 0
            if op.startswith("count"):
                need = int(op.split(">")[1])
                return len(blobs) > need
            return bool(blobs)
        self.log.warning("Не разобрал условие: %r — считаю ложным", cond)
        return False

    def _stat_add(self, key: str, n: int = 1):
        self.bot.stats[key] = self.bot.stats.get(key, 0) + n

    def _scan_screen(self, frame) -> str:
        self._last_screen = self.bot.vision.detect_screen(frame)
        return self._last_screen

    # ------------------------- действия -------------------------
    def _do_action(self, act: dict, frame: np.ndarray) -> Optional[str]:
        """Выполнить одно действие; вернуть 'goto:<step>' если был goto."""
        inp, vis = self.bot.input, self.bot.vision
        for kind, params in act.items():
            if kind in ("wait", "sleep"):
                p = self._resolve(params)
                if isinstance(p, list):
                    time.sleep(random.uniform(float(p[0]), float(p[1])))
                else:
                    time.sleep(float(p))
            elif kind == "press":
                if isinstance(params, str):
                    inp.press_key(params)
                else:
                    p = self._resolve(params)
                    inp.press_key(p["key"], hold=float(p.get("hold", 0.03)))
            elif kind in ("down", "up"):
                inp.sequence([{"type": kind, "key": self._resolve(params)}])
            elif kind == "click_template":
                name = self._resolve(params)
                dets = vis.match_template(frame, name, max_results=1)
                if dets:
                    x, y = self.bot.capture.to_screen_coords(dets[0].cx, dets[0].cy)
                    inp.click_at(x, y)
                    self._stat_add("screens_clicked", 1)
                    return None
                else:
                    self.log.debug("click_template: '%s' не найден", name)
            elif kind == "click_color":
                key = self._resolve(params)
                blobs = vis.find_color_blobs(frame, key)
                if blobs:
                    x, y = self.bot.capture.to_screen_coords(
                        blobs[0].cx, blobs[0].cy)
                    inp.click_at(x, y)
                    self._stat_add("loot_picked", 1)
            elif kind == "click_point":
                x, y = self._resolve(params)
                sx, sy = self.bot.capture.to_screen_coords(float(x), float(y))
                inp.click_at(int(sx), int(sy))
            elif kind == "move_rel":
                dx, dy = self._resolve(params)
                inp.move_rel(int(dx), int(dy))
            elif kind == "scroll":
                inp.scroll(int(self._resolve(params)))
            elif kind == "strafe":
                p = self._resolve(params) if isinstance(params, dict) \
                    else {"dir": params}
                inp.strafe(str(p.get("dir", "a")), float(p.get("sec", 0.15)))
            elif kind == "fire":
                p = self._resolve(params) if isinstance(params, dict) \
                    else {"sec": params}
                inp.fire_held(float(p.get("sec", 1.0)),
                              button=p.get("button", "left"))
                self._stat_add("shots_fired", int(p.get("sec", 1.0) * 9))
            elif kind == "cast":
                # автокаст способности по слоту из базы фреймов:
                #   cast: {frame: revenant, slot: "2"}  или просто cast: "2"
                from data.frames_db import get_frame
                p2 = self._resolve(params) if isinstance(params, dict) \
                    else {"slot": params}
                fname = str(p2.get("frame", self.cfg.get("frame", ""))).lower()
                slot = str(p2.get("slot", "1"))
                fr = get_frame(fname or "_")
                ab = fr["abilities"].get(slot)
                if ab:
                    key = ab.get("hotkey", "q")
                    if ab.get("cast") == "hold":
                        inp.hold_key(key, float(ab.get("hold_sec", 2.0)))
                    else:
                        inp.press_key(key)
                    self._stat_add("ability_casts", 1)
                else:
                    self.log.warning("cast: слот %s не найден для '%s'", slot, fname)
            elif kind == "reload":
                if params:
                    inp.press_key(self.bot.cfg.get("afk_zones", {})
                                  .get("effusion_farm", {})
                                  .get("reload_key", "r"))
            elif kind == "set":
                for k, v in self._resolve(params).items():
                    self.vars[k] = v
            elif kind == "inc":
                for k, v in (params or {}).items():
                    self.vars[k] = int(self.vars.get(k, 0)) + int(self._resolve(v))
            elif kind == "log":
                self.log.info("[profile] %s", self._resolve(params))
            elif kind == "goto":
                target = str(self._resolve(params))
                if self.profile and target in self.profile.steps:
                    self.current = self.profile.steps[target]
                    return "restart"
                self.log.warning("goto: неизвестный шаг %r", target)
            elif kind == "repeat_until":
                p = self._resolve(params) if isinstance(params, dict) else {}
                max_sec = float(p.get("max_sec", 60))
                t0 = time.time()
                while time.time() - t0 < max_sec:
                    if not self.bot.running:
                        return None
                    f2 = self.bot.get_frame()
                    cond = p.get("condition", "screen == mission")
                    if self._eval_condition(cond, f2):
                        return None
                    time.sleep(0.3)
        return None

    # ------------------------- тик -------------------------
    def on_tick(self, frame: np.ndarray):
        if self._paused or self.profile is None or self.current is None:
            return
        step = self.current
        # условие входа
        if not self._eval_condition(step.when, frame):
            return
        self.log.debug("шаг '%s'", step.name)
        restart = False
        for _ in range(max(1, step.repeat)):
            for act in step.actions:
                if not self.bot.running:
                    return
                if self._do_action(act, frame) == "restart":
                    restart = True
                    break
            if restart:
                break
        if restart:
            return
        self.bot.stats.setdefault("profile_steps_done", 0)
        self.bot.stats["profile_steps_done"] += 1
        # переход
        nxt = step.next or (self.profile.order[
            (self.profile.order.index(step.name) + 1)
            % len(self.profile.order)])
        if nxt in self.profile.steps:
            self.current = self.profile.steps[nxt]

    def pause(self, flag: bool = True):
        self._paused = flag
