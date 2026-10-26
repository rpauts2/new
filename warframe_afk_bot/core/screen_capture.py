#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
screen_capture.py — быстрый захват экрана/окна игры.

• Windows: mss (DXGI) + поиск окна по заголовку через ctypes Win32 API.
• Linux/macOS: mss по монитору (играется в borderless-окне).
• Кадры отдаются как BGR numpy-массивы (совместимо с OpenCV).

Использование:
    cap = ScreenCapture(cfg)
    frame = cap.grab()            # один кадр
    for frame in cap.stream():    # генератор с ограничением FPS
        ...
"""
from __future__ import annotations

import sys
import time
import logging
from dataclasses import dataclass
from typing import Optional, Iterator

import numpy as np

try:
    import mss
except ImportError:  # pragma: no cover
    mss = None

log = logging.getLogger("wf.screen")

IS_WINDOWS = sys.platform.startswith("win")


@dataclass
class Region:
    left: int
    top: int
    width: int
    height: int

    def as_mss(self) -> dict:
        return {"left": self.left, "top": self.top,
                "width": self.width, "height": self.height}


class ScreenCapture:
    def __init__(self, cfg: dict):
        if mss is None:
            raise RuntimeError("Не установлен модуль 'mss'. pip install mss")
        game = cfg.get("game", {})
        cap = cfg.get("capture", {})
        self.fps: float = float(cap.get("fps", 12))
        self.downscale: float = float(cap.get("downscale", 1.0))
        self.sct = mss.mss()
        self._region: Optional[Region] = None
        self._hwnd = None

        title = game.get("window_title")
        if IS_WINDOWS and title:
            self._hwnd = self._find_window(title)
            if self._hwnd:
                self._region = self._window_region(self._hwnd)
                log.info("Найдено окно '%s' (hwnd=%s), область: %s",
                         title, hex(self._hwnd), self._region)
        if self._region is None and game.get("region"):
            r = game["region"]
            self._region = Region(int(r["left"]), int(r["top"]),
                                  int(r["width"]), int(r["height"]))
        if self._region is None:
            mon_idx = int(game.get("monitor", 1))
            mon_idx = min(mon_idx, len(self.sct.monitors) - 1)
            m = self.sct.monitors[mon_idx]
            self._region = Region(m["left"], m["top"], m["width"], m["height"])
            log.info("Окно не найдено — захват монитора #%d (%dx%d)",
                     mon_idx, m["width"], m["height"])

    # ---------------- Win32: поиск и геометрия окна ----------------
    @staticmethod
    def _find_window(title_substring: str):
        import ctypes
        user32 = ctypes.windll.user32
        result = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_cb(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            n = user32.GetWindowTextLengthW(hwnd)
            if n == 0:
                return True
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if title_substring.lower() in buf.value.lower():
                result.append(hwnd)
            return True

        user32.EnumWindows(enum_cb, 0)
        return result[0] if result else None

    @staticmethod
    def _window_region(hwnd) -> Optional[Region]:
        import ctypes
        rect = ctypes.wintypes.RECT() if hasattr(ctypes, "wintypes") else None
        from ctypes import wintypes
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
            return None
        w, h = rect.right - rect.left, rect.bottom - rect.top
        if w < 100 or h < 100:   # свёрнутое окно
            return None
        return Region(rect.left, rect.top, w, h)

    # ---------------- Публичный API ----------------
    @property
    def region(self) -> Region:
        # Перечитываем позицию окна на случай перемещения
        if IS_WINDOWS and self._hwnd:
            r = self._window_region(self._hwnd)
            if r:
                self._region = r
        return self._region

    def grab(self) -> np.ndarray:
        """Один кадр BGR numpy (H, W, 3)."""
        img = self.sct.grab(self.region.as_mss())
        frame = np.asarray(img, dtype=np.uint8)[:, :, :3]  # BGRA -> BGR
        if self.downscale != 1.0:
            import cv2
            frame = cv2.resize(frame, None, fx=self.downscale, fy=self.downscale,
                               interpolation=cv2.INTER_AREA)
        return frame

    def stream(self) -> Iterator[np.ndarray]:
        """Генератор кадров с ограничением частоты capture.fps."""
        interval = 1.0 / max(self.fps, 1)
        while True:
            t0 = time.perf_counter()
            yield self.grab()
            dt = time.perf_counter() - t0
            if dt < interval:
                time.sleep(interval - dt)

    def screen_size(self) -> tuple[int, int]:
        r = self.region
        return r.width, r.height

    def to_screen_coords(self, x: float, y: float) -> tuple[int, int]:
        """Координаты внутри кадра -> абсолютные координаты экрана."""
        r = self.region
        sx = r.left + x / max(self.downscale, 1e-6)
        sy = r.top + y / max(self.downscale, 1e-6)
        return int(sx), int(sy)

    def close(self):
        try:
            self.sct.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Быстрая самопроверка: make screenshot
    import yaml
    logging.basicConfig(level=logging.INFO)
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    cap = ScreenCapture(cfg)
    f = cap.grab()
    import cv2
    out = f"captures/test_{int(time.time())}.png"
    cv2.imwrite(out, f)
    print(f"Кадр {f.shape[1]}x{f.shape[0]} сохранён в {out}")
