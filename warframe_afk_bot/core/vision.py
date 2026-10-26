#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vision.py — компьютерное зрение для Warframe AFK Bot.

Возможности:
  • match_template  — поиск PNG-шаблонов (кнопки, иконки, карточки модов)
                      с multi-scale и масками прозрачности;
  • find_color_blobs— HSV-поиск цветных маркеров (лут, враги, HP) без шаблонов;
  • pick_reward_card— эвристика выбора карточки награды (синий фон = мод);
  • debug overlay    — отрисовка всех найденных объектов (для калибровки).

Все методы возвращают список Detection(x, y, w, h, confidence, label),
где x,y — ЦЕНТР объекта в координатах кадра.
"""
from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

log = logging.getLogger("wf.vision")


@dataclass
class Detection:
    cx: float
    cy: float
    w: float
    h: float
    confidence: float
    label: str = ""

    def bbox(self):
        return (int(self.cx - self.w / 2), int(self.cy - self.h / 2),
                int(self.w), int(self.h))


@dataclass
class Template:
    name: str
    bgr: np.ndarray
    alpha: Optional[np.ndarray]  # маска из канала A PNG
    scales: tuple = (1.0,)
    _cache: dict = field(default_factory=dict, repr=False)


class VisionEngine:
    def __init__(self, cfg: dict):
        v = cfg.get("vision", {})
        self.tpl_dir = v.get("template_dir", "templates")
        self.threshold = float(v.get("default_threshold", 0.80))
        self.multi_scale = bool(v.get("multi_scale", True))
        self.scales = tuple(v.get("scales", [1.0]))
        self.hsv_ranges: dict = v.get("hsv", {})
        self.templates: dict[str, Template] = {}
        self.load_templates()

    # ------------------------- Шаблоны -------------------------
    def load_templates(self):
        self.templates.clear()
        if not os.path.isdir(self.tpl_dir):
            log.warning("Папка шаблонов %s не существует", self.tpl_dir)
            return
        for fn in sorted(os.listdir(self.tpl_dir)):
            if not fn.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            path = os.path.join(self.tpl_dir, fn)
            raw = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if raw is None:
                continue
            alpha = None
            if raw.ndim == 3 and raw.shape[2] == 4:
                alpha = raw[:, :, 3]
                bgr = raw[:, :, :3]
            else:
                bgr = raw if raw.ndim == 3 else cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
            scales = self.scales if self.multi_scale else (1.0,)
            self.templates[fn] = Template(fn, bgr, alpha, scales)
        log.info("Загружено шаблонов: %d", len(self.templates))

    def _scaled(self, tpl: Template, scale: float):
        key = round(scale, 3)
        if key not in tpl._cache:
            img = cv2.resize(tpl.bgr, None, fx=scale, fy=scale,
                             interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
            mask = None
            if tpl.alpha is not None:
                mask = cv2.resize(tpl.alpha, None, fx=scale, fy=scale,
                                  interpolation=cv2.INTER_NEAREST)
            tpl._cache[key] = (img, mask)
        return tpl._cache[key]

    def match_template(self, frame: np.ndarray, template_name: str,
                       threshold: Optional[float] = None,
                       max_results: int = 10,
                       roi: Optional[tuple] = None) -> list[Detection]:
        """Найти шаблон на кадре. roi = (x, y, w, h) — зона поиска."""
        tpl = self.templates.get(template_name)
        if tpl is None:
            log.debug("Шаблон %s не загружен", template_name)
            return []
        thr = threshold if threshold is not None else self.threshold

        off_x, off_y = 0, 0
        if roi:
            off_x, off_y, rw, rh = roi
            frame = frame[off_y:off_y + rh, off_x:off_x + rw]

        results: list[Detection] = []
        best_by_pos: list[tuple[float, float, float, float, float]] = []  # cx,cy,w,h,conf
        for scale in tpl.scales:
            img, mask = self._scaled(tpl, scale)
            ih, iw = img.shape[:2]
            if ih > frame.shape[0] or iw > frame.shape[1]:
                continue
            method = cv2.TM_CCOEFF_NORMED
            res = (cv2.matchTemplate(frame, img, method, mask=mask)
                   if mask is not None else
                   cv2.matchTemplate(frame, img, method))
            ys, xs = np.where(res >= thr)
            for x, y, conf in zip(xs, ys, res[ys, xs]):
                best_by_pos.append((x + iw / 2 + off_x, y + ih / 2 + off_y,
                                    iw, ih, float(conf)))
        # NMS: склейка дублей от разных масштабов/соседних пикселей
        best_by_pos.sort(key=lambda d: -d[4])
        kept: list[Detection] = []
        for cx, cy, w, h, conf in best_by_pos:
            if all(abs(cx - k.cx) > max(w, k.w) * 0.5 or
                   abs(cy - k.cy) > max(h, k.h) * 0.5 for k in kept):
                kept.append(Detection(cx, cy, w, h, conf, template_name))
            if len(kept) >= max_results:
                break
        return kept

    def wait_for_template(self, frame_provider, template_name: str,
                          timeout: float = 10, threshold: float | None = None):
        """Ждать появления шаблона; вернуть первый Detection или None."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            frame = frame_provider()
            dets = self.match_template(frame, template_name, threshold)
            if dets:
                return dets[0]
            time.sleep(0.1)
        return None

    # ------------------------- HSV-маркеры -------------------------
    def hsv_mask(self, frame: np.ndarray, color_key: str) -> np.ndarray:
        rng = self.hsv_ranges.get(color_key)
        if rng is None:
            raise KeyError(f"HSV-диапазон '{color_key}' не задан в конфиге")
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lo = np.array([rng["h_min"], rng.get("s_min", 0), rng.get("v_min", 0)], np.uint8)
        hi = np.array([rng["h_max"], rng.get("s_max", 255), rng.get("v_max", 255)], np.uint8)
        if rng["h_min"] > rng["h_max"]:   # wrap через 0 (красный/мадурай)
            m1 = cv2.inRange(hsv, lo, np.array([179, hi[1], hi[2]], np.uint8))
            m2 = cv2.inRange(hsv, np.array([0, lo[1], lo[2]], np.uint8), hi)
            return cv2.bitwise_or(m1, m2)
        return cv2.inRange(hsv, lo, hi)

    def find_color_blobs(self, frame: np.ndarray, color_key: str,
                         min_area: int = 25, max_area: int = 200_000,
                         sort_by_distance_to: Optional[tuple] = None) -> list[Detection]:
        """Крупные связные области заданного цвета (маркер лута/врага)."""
        mask = self.hsv_mask(frame, color_key)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                                np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        h, w = frame.shape[:2]
        center = sort_by_distance_to or (w / 2, h / 2)
        dets = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area or area > max_area:
                continue
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
            bx, by, bw, bh = cv2.boundingRect(c)
            dets.append(Detection(cx, cy, bw, bh, min(1.0, area / 5000), color_key))
        dets.sort(key=lambda d: (d.cx - center[0]) ** 2 + (d.cy - center[1]) ** 2)
        return dets

    # ---------------- цветовой пиксельный триггер (AHK PixelCheck) ----------------
    def color_in_roi(self, frame: np.ndarray, roi_rel, hex_color: str,
                     tolerance: int = 30) -> bool:
        """Есть ли в зоне кадра пиксели заданного цвета (BGR ±tolerance).

        roi_rel — [x, y, w, h] в ДОЛЯХ экрана (как hud_hp_roi), либо None = весь кадр.
        Аналог триггеров Cyte-09.ahk: готовность способности по цвету иконки в HUD.
        """
        h, w = frame.shape[:2]
        if roi_rel is not None:
            x = int(roi_rel[0] * w); y = int(roi_rel[1] * h)
            rw = max(int(roi_rel[2] * w), 1); rh = max(int(roi_rel[3] * h), 1)
            sub = frame[y:y + rh, x:x + rw]
        else:
            sub = frame
        if sub.size == 0:
            return False
        hc = hex_color.lstrip("#")
        r, g, b = (int(hc[i:i + 2], 16) for i in (0, 2, 4))
        target = np.array([b, g, r], np.int16)          # BGR
        diff = np.abs(sub.astype(np.int16) - target).max(axis=2)
        return bool((diff <= tolerance).any())

    def bar_ratio(self, frame: np.ndarray, roi_rel, color_key: str) -> float:
        """Доля пикселей цвета color_key в прямоугольнике HUD (0..1)."""
        h, w = frame.shape[:2]
        x = int(roi_rel[0] * w); y = int(roi_rel[1] * h)
        rw = max(int(roi_rel[2] * w), 1); rh = max(int(roi_rel[3] * h), 1)
        sub = frame[y:y + rh, x:x + rw]
        if sub.size == 0:
            return 0.0
        mask = self.hsv_mask(sub, color_key)
        return float(np.count_nonzero(mask)) / float(mask.size)

    # ------------------------- Эвристики UI -------------------------
    def detect_screen(self, frame: np.ndarray) -> str:
        """Классификатор состояния игры по одному кадру (для profile-движка).

        Порядок: сначала специфичные шаблоны, потом «ловушки», затем HSV-евристики.
        Возвращает один из тегов:
          mission | reward_card | extraction | navigation | loading | menu | unknown
        """
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame

        # 1. Шаблоны-«якоря» экранов (если нарезаны пользователем)
        for tpl_name, tag in (("extraction_button.png", "extraction"),
                              ("mission_hud.png", "mission"),
                              ("navigation_map.png", "navigation")):
            if tpl_name in self.templates:
                if self.match_template(frame, tpl_name, threshold=self.threshold,
                                       max_results=1):
                    return tag

        # 2. Экран наград: крупные цветные карточки в центре
        try:
            card = self.pick_reward_card(frame)
            if card is not None:
                return "reward_card"
        except KeyError:
            pass

        # 3. Loading/заставка: почти монохромный тёмный кадр без краёв? — нет,
        #    надёжнее: Warframe loading = чёрный фон + тонкая полоса прогресса.
        mean_val = float(np.mean(gray))
        edge_density = float(np.count_nonzero(cv2.Canny(gray, 50, 150))) / (h * w)
        if mean_val < 25 and edge_density < 0.004:
            return "loading"

        # 4. В бою есть HUD: перекрестие+маркеры → много ярких пикселей в центре;
        #   simple heuristic: синий вражеский маркер или оранжевый лут = миссия
        for key in ("enemy_marker", "loot_marker"):
            if key in self.hsv_ranges:
                m = self.hsv_mask(frame, key)
                if np.count_nonzero(m) > (h * w * 0.0003):
                    return "mission"

        # 5. Меню/орбитер: светлый «стерильный» интерфейс с кучей прямых линий
        if mean_val > 60 and edge_density > 0.02:
            return "menu"
        return "unknown"

    def pick_reward_card(self, frame: np.ndarray) -> Optional[Detection]:
        """Экран наград: карточка с СИНЕЙ рамкой — мод, с ЗОЛОТОЙ — кредиты.
        Возвращает центр самой «синей» карточки (вариант «дешёвого» реварда)."""
        mask = self.hsv_mask(frame, "mod_reward_blue")
        kernel = np.ones((9, 9), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = frame.shape[:2]
        best, best_score = None, 0.0
        for c in contours:
            area = cv2.contourArea(c)
            if area < (w * h * 0.005):   # карточка минимум ~0.5% экрана
                continue
            bx, by, bw, bh = cv2.boundingRect(c)
            aspect = bw / max(bh, 1)
            score = area * (1.0 if 0.4 < aspect < 1.6 else 0.3)
            if score > best_score:
                best_score = score
                best = Detection(bx + bw / 2, by + bh / 2, bw, bh, 0.9, "reward_card")
        return best

    def health_bar_ratio(self, frame: np.ndarray, hud_roi: tuple) -> float:
        """Доля красной полосы HP в зоне HUD (0..1). hud_roi=(x,y,w,h)."""
        x, y, w, h = hud_roi
        sub = frame[y:y + h, x:x + w]
        if sub.size == 0:
            return 1.0
        red = self.hsv_mask(sub, "health_red")
        return float(np.count_nonzero(red)) / float(red.size)

    # ------------------------- Отладка -------------------------
    def draw_debug(self, frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
        out = frame.copy()
        for d in detections:
            x, y, w, h = d.bbox()
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(out, f"{d.label} {d.confidence:.2f}", (x, max(y - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return out
