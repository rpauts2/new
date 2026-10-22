#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py — ядро Warframe AFK Bot: оркестрация модулей, хоткеи, статистика.

Архитектура:
    ScreenCapture ──> кадры ──> VisionEngine (что видим на экране?)
                                    │
                                    v
    Scheduler (все активные модули-фермы) ──> InputController (что делать?)

Модули-фермы регистрируются в реестре MODULE_REGISTRY; каждый — конечный
автомат со своими состояниями. Добавлять новые зоны = один файл в modules/.

Хоткеи (глобальные, работают поверх игры):
    F8 — пауза/старт, F9 — полный стоп.
"""
from __future__ import annotations

import os
import sys
import json
import time
import signal
import logging
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml

from core.screen_capture import ScreenCapture
from core.vision import VisionEngine
from core.input_controller import InputController

log = logging.getLogger("wf.bot")

# Реестр ферм: имя модуля -> путь к классу подтягивается динамически
MODULE_REGISTRY = {
    "effusion_farm": ("modules.effusion_farm", "EffusionFarm"),
    "lith_anomaly":  ("modules.lith_anomaly",  "LithAnomalyFarm"),
    "duviri_loop":   ("modules.duviri_loop",   "DuviriLoopFarm"),
    "nightwave_farm": ("modules.nightwave_farm", "NightwaveFarm"),
    "focus_fire":    ("modules.focus_fire",    "FocusFire"),
    "auto_reward":   ("modules.auto_reward",   "AutoRewardClicker"),
    "repeat_macro":  ("modules.repeat_macro",  "RepeatMacro"),
    "profile_runner": ("modules.profile_runner", "ProfileRunner"),
    "antiafk":       ("modules.antiafk",       "AntiAFKKeeper"),
}


def import_module_class(module_path: str, class_name: str):
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


class WarframeAFKBot:
    def __init__(self, config_path: str = "config.yaml", debug: bool = False):
        self.debug = debug
        base_dir = os.path.dirname(os.path.abspath(config_path)) or "."
        os.chdir(base_dir)
        with open(config_path, encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)

        self._setup_logging()
        log.info("=== Warframe AFK Bot стартует (debug=%s) ===", debug)

        self.capture = ScreenCapture(self.cfg)
        self.vision = VisionEngine(self.cfg)
        self.input = InputController(self.cfg)

        self.running = False
        self.should_exit = False
        self.last_frame: Optional["object"] = None
        self.started_at = time.time()
        self.stats = {"shots_fired": 0, "loot_picked": 0,
                      "screens_clicked": 0, "cycles_done": 0}

        self.modules: list = []
        self._load_modules()
        self._register_hotkeys()

        signal.signal(signal.SIGINT, lambda *_: self.stop())
        signal.signal(signal.SIGTERM, lambda *_: self.stop())

    # ----------------------------------------------------------
    def _setup_logging(self):
        lg = self.cfg.get("logging", {})
        os.makedirs(os.path.dirname(lg.get("file", "logs/bot.log")) or ".", exist_ok=True)
        level = getattr(logging, str(lg.get("level", "INFO")).upper(), logging.INFO)
        handlers = [logging.FileHandler(lg.get("file", "logs/bot.log"), encoding="utf-8")]
        if self.debug:
            handlers.append(logging.StreamHandler())
        logging.basicConfig(level=level,
                            format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                            handlers=handlers)

    def _load_modules(self):
        zones = self.cfg.get("afk_zones", {})
        for name, (mod_path, cls_name) in MODULE_REGISTRY.items():
            zcfg = zones.get(name, {})
            if name == "antiafk":
                zcfg = self.cfg.get("antiafk", {})
            if not zcfg.get("enabled", False):
                continue
            try:
                cls = import_module_class(mod_path, cls_name)
                inst = cls(bot=self, cfg=zcfg, name=name)
                self.modules.append(inst)
                log.info("Модуль загружен: %s (%s)", name, cls_name)
            except Exception as e:
                log.error("Не удалось загрузить модуль %s: %s", name, e)
        log.info("Активных модулей: %d", len(self.modules))

    def _register_hotkeys(self):
        hk = self.cfg.get("hotkeys", {})
        try:
            import keyboard
            keyboard.on_press_key(hk.get("toggle_bot", "f8"),
                                  lambda _: self.toggle(), suppress=False)
            keyboard.on_press_key(hk.get("panic_stop", "f9"),
                                  lambda _: self.stop(exit_after=True), suppress=False)
            log.info("Хоткеи: %s — старт/стоп, %s — полный выход",
                     hk.get("toggle_bot", "f8").upper(), hk.get("panic_stop", "f9").upper())
        except Exception as e:
            log.warning("Глобальные хоткеи недоступны (%s) — используйте Ctrl+C", e)

    # ----------------------------------------------------------
    def toggle(self):
        self.running = not self.running
        log.info(">>> Бот %s", "ЗАПУЩЕН" if self.running else "на паузе")

    def stop(self, exit_after: bool = False):
        self.running = False
        if exit_after:
            self.should_exit = True
        log.info("Остановка запрошена")

    def get_frame(self):
        """Свежий кадр для модулей (один захват на цикл планировщика)."""
        return self.capture.grab()

    def save_stats(self):
        lg = self.cfg.get("logging", {})
        path = lg.get("stats_file", "logs/stats.json")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        data = dict(self.stats)
        data["uptime_sec"] = round(time.time() - self.started_at)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ----------------------------------------------------------
    def run(self):
        """Главный цикл: tick каждого модуля с собственной частотой."""
        self.running = True
        log.info("Цикл запущен. F8 — пауза, F9 — стоп, Ctrl+C — выход.")
        last_stats_save = 0.0
        try:
            while not self.should_exit:
                t0 = time.perf_counter()
                if self.running:
                    frame = self.capture.grab()
                    self.last_frame = frame
                    # эксклюзивный профиль глушит боевые модули, пока у руля
                    profile_mod = next((m for m in self.modules
                                        if m.name == "profile_runner"), None)
                    suppress = set()
                    if profile_mod is not None and getattr(profile_mod, "active", False):
                        suppress = set(profile_mod.pause_others())
                    for m in self.modules:
                        if m.name in suppress:
                            continue
                        try:
                            m.tick(frame)
                        except Exception as e:
                            log.exception("Сбой модуля %s: %s", m.name, e)
                    if time.time() - last_stats_save > 30:
                        self.save_stats()
                        last_stats_save = time.time()
                else:
                    time.sleep(0.1)
                # фиксируем темп ~capture.fps, но не больше
                dt = time.perf_counter() - t0
                budget = 1.0 / max(self.capture.fps, 1) - dt
                if budget > 0:
                    time.sleep(budget)
        finally:
            self.save_stats()
            self.capture.close()
            log.info("Бот остановлен. Статистика: %s", self.stats)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Warframe AFK Bot")
    p.add_argument("-c", "--config", default="config.yaml")
    p.add_argument("--debug", action="store_true", help="лог в консоль + отладка зрения")
    args = p.parse_args()
    WarframeAFKBot(args.config, debug=args.debug).run()


if __name__ == "__main__":
    main()
