#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
input_controller.py — эмуляция ввода (клавиатура/мышь) с «очеловечиванием».

Бэкенды:
  • keyboard (pyautogui) — клики мышью по экранным координатам + клавиши;
  • keyboard-only        — если pyautogui недоступен, клавиши через модуль `keyboard`.

Humanize: случайные джиттер-паузы и плавные движения мыши снижают
«роботоподобность» паттерна действий.

ВАЖНО: это НЕ обход античита и не инъекция в процесс — только ОС-уровень ввода.
"""
from __future__ import annotations

import random
import time
import logging
from typing import Optional

log = logging.getLogger("wf.input")


class InputController:
    def __init__(self, cfg: dict):
        inp = cfg.get("input", {})
        self.backend_name = inp.get("backend", "auto")
        self.move_time = float(inp.get("mouse_move_time", 0.08))
        self.humanize = bool(inp.get("humanize", True))
        self.jitter_ms = tuple(inp.get("jitter_ms", [40, 160]))
        self._pg = None       # pyautogui
        self._kb = None       # keyboard

        if self.backend_name in ("auto", "pyautogui"):
            try:
                import pyautogui
                pyautogui.FAILSAFE = True      # мышь в угол экрана = аварийный стоп
                pyautogui.PAUSE = 0.0
                self._pg = pyautogui
            except Exception as e:  # нет X-сервера / не установлен
                log.warning("pyautogui недоступен (%s) — только клавиатура", e)
        if self.backend_name in ("auto", "keyboard"):
            try:
                import keyboard as kb
                self._kb = kb
            except Exception as e:
                log.warning("keyboard недоступен (%s)", e)

        if not self._pg and not self._kb:
            raise RuntimeError("Нет доступного бэкенда ввода. Установите pyautogui/keyboard.")

    # ---------------- служебное ----------------
    def _pause(self, base: float = 0.0):
        if self.humanize:
            base += random.uniform(*self.jitter_ms) / 1000.0
        if base > 0:
            time.sleep(base)

    # ---------------- клавиатура ----------------
    def press_key(self, key: str, hold: float = 0.03):
        if self._pg:
            if hold > 0.01:
                self._pg.keyDown(key)
                time.sleep(hold)
                self._pg.keyUp(key)
            else:
                self._pg.press(key)
        elif self._kb:
            self._kb.press_and_release(key)
        self._pause(0.0)

    def hold_key(self, key: str, seconds: float):
        """Зажать клавишу на N секунд (спринт, приседание и т.п.)."""
        if self._pg:
            self._pg.keyDown(key)
        elif self._kb:
            self._kb.press(key)
        time.sleep(seconds)
        if self._pg:
            self._pg.keyUp(key)
        elif self._kb:
            self._kb.release(key)

    def combo(self, *keys: str):
        if self._pg:
            self._pg.hotkey(*keys)
        elif self._kb:
            self._kb.write("+".join(keys))
        self._pause()

    def type_text(self, text: str):
        if self._pg:
            self._pg.typewrite(text, interval=0.03)
        elif self._kb:
            self._kb.write(text)

    # ---------------- мышь ----------------
    def click_at(self, x: int, y: int, button: str = "left", double: bool = False):
        if not self._pg:
            log.warning("Клик невозможен: pyautogui неактивен (x=%d,y=%d)", x, y)
            return
        self._pg.moveTo(x, y, duration=self.move_time)
        self._pause(0.01)
        self._pg.click(button=button, clicks=2 if double else 1)
        self._pause()

    def mouse_down(self, button: str = "left"):
        if self._pg:
            self._pg.mouseDown(button=button)

    def mouse_up(self, button: str = "left"):
        if self._pg:
            self._pg.mouseUp(button=button)

    def move_rel(self, dx: int, dy: int):
        """Относительное движение (используется anti-AFK маятником)."""
        if self._pg:
            pos = self._pg.position()
            self._pg.moveTo(pos[0] + dx, pos[1] + dy, duration=0.05)

    def position(self) -> tuple[int, int]:
        return self._pg.position() if self._pg else (0, 0)

    # ---------------- игровые действия ----------------
    def fire_held(self, seconds: float, button: str = "left"):
        """Стрельба удержанием ЛКМ (автоматическое оружие Warframe)."""
        self.mouse_down(button)
        time.sleep(seconds)
        self.mouse_up(button)

    def strafe(self, direction: str = "a", duration: float = 0.15):
        """Микро-стрейф — лёгкое движение персонажа (W/A/S/D)."""
        self.hold_key(direction, duration)

    # ---------------- игровые действия (расширения v2) ----------------
    def scroll(self, clicks: int = -1, x: Optional[int] = None, y: Optional[int] = None):
        """Колесо мыши — смена оружия/слотов в Warframe. Отрицательное = вверх."""
        if self._pg:
            if x is not None and y is not None:
                self._pg.scrollTo(clicks, x=x, y=y)
            else:
                self._pg.scroll(clicks)
        self._pause()

    def mouse_to_center(self, screen_size: Optional[tuple] = None):
        """Вернуть «камеру» в центр (для доворота после лут-кликов)."""
        if self._pg and screen_size:
            w, h = screen_size
            self._pg.moveTo(w // 2, h // 2, duration=self.move_time)

    def sequence(self, events: list[dict], stop_check=None):
        """Проиграть список событий [{'type','key'/'button','x','y','hold'}].

        Используется профилями-плейлистами и макросами. stop_check — callable,
        если вернёт True — исполнение прерывается.
        """
        for ev in events:
            if stop_check and stop_check():
                return False
            t = ev.get("type")
            if t == "press":
                self.press_key(ev["key"], hold=float(ev.get("hold", 0.03)))
            elif t == "down":
                if self._pg:
                    self._pg.keyDown(ev["key"])
                elif self._kb:
                    self._kb.press(ev["key"])
            elif t == "up":
                if self._pg:
                    self._pg.keyUp(ev["key"])
                elif self._kb:
                    self._kb.release(ev["key"])
            elif t == "click":
                self.click_at(int(ev["x"]), int(ev["y"]),
                              button=ev.get("button", "left"))
            elif t == "move_rel":
                self.move_rel(int(ev.get("dx", 0)), int(ev.get("dy", 0)))
            elif t == "scroll":
                self.scroll(int(ev.get("clicks", -1)))
            elif t == "wait":
                time.sleep(float(ev.get("sec", 0.5)))
        return True
