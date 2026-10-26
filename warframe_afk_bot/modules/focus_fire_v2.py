#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
focus_fire.py v2 — фарм Фокуса (Focus Lamps) с автовыбором школы.

Механика из гайдов: после убийств врагов появляются светящиеся «лампы»
фокуса (цвет = школа): Madurai=красный, Zenist=синий, Unairu=зелёный,
Vazarin=жёлтый, Naramon=белый/фиолетовый. Бот ищет лампы по HSV и
взаимодействует (F), выбирая приоритетную школу.

Конфиг (afk_zones.focus_fire):
  priority_school: "madurai"   # какую школу фармить
  lamp_hsv_overrides: {}       # тонкая подстройка цветов ламп
  interact_key: "f"
  min_area: 60
"""
from __future__ import annotations

import time

from modules.base import FarmModule

SCHOOL_HSV = {
    "madurai": {"h_min": 170, "h_max": 10, "s_min": 150, "v_min": 150},  # красный (wrap)
    "zenist":  {"h_min": 100, "h_max": 130, "s_min": 150, "v_min": 150},  # синий
    "unairu":  {"h_min": 40, "h_max": 85, "s_min": 150, "v_min": 150},    # зелёный
    "vazarin": {"h_min": 22, "h_max": 40, "s_min": 150, "v_min": 150},    # жёлтый
    "naramon": {"h_min": 140, "h_max": 165, "s_min": 60, "v_min": 200},   # фиолетово-белый
}


class FocusFire(FarmModule):

    def __init__(self, bot, cfg, name="focus_fire"):
        super().__init__(bot, cfg, name)
        self.school = str(cfg.get("priority_school", "madurai")).lower()
        self.interact_key = cfg.get("interact_key", "f")
        self.min_area = int(cfg.get("min_area", 60))
        self.hsv = dict(SCHOOL_HSV.get(self.school, SCHOOL_HSV["madurai"]))
        self.hsv.update(cfg.get("lamp_hsv_overrides") or {})
        # регистрируем цвет в vision, если его там нет
        key = f"focus_{self.school}"
        if key not in self.bot.vision.hsv_ranges:
            self.bot.vision.hsv_ranges[key] = self.hsv
        self.color_key = key
        self._last_lamp = 0.0

    def on_tick(self, frame):
        try:
            lamps = self.bot.vision.find_color_blobs(frame, self.color_key,
                                                     min_area=self.min_area)
        except KeyError:
            lamps = []
        if not lamps:
            return
        near = min(lamps, key=lambda d: (d.cx - frame.shape[1]/2)**2 +
                   (d.cy - frame.shape[0]/2)**2)
        dist = ((near.cx - frame.shape[1]/2)**2 +
                (near.cy - frame.shape[0]/2)**2) ** 0.5
        if dist < 150:
            self.bot.input.press_key(self.interact_key)
        else:
            self.click_detection(near)
        self._last_lamp = time.time()
        self.bot.stats.setdefault("focus_lamps", 0)
        self.bot.stats["focus_lamps"] += 1
