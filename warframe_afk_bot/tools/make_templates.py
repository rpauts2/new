#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_templates.py — интерактивная нарезка PNG-шаблонов из скриншотов.

Как пользоваться:
    1) Находясь в игре, нажмите PrintScreen (бот сохранит кадр в captures/),
       либо сделайте скриншот сами и положите в captures/.
    2) python tools/make_templates.py captures/myscreen.png --name claim_button.png
    3) Откроется окно: выделите мышью область (кнопку/иконку),
       Enter — сохранить шаблон в templates/, S — сохранить с альфа-маской
       (выделение по цвету фона), ESC — отмена, R — сброс выделения.

Флаг --hsv-calib открывает коллбэк калибровки HSV-диапазона для маркеров
(враги/лут) вместо шаблонов.
"""
from __future__ import annotations

import os
import sys
import argparse

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_DIR = os.path.join(ROOT, "templates")


class RectSelector:
    def __init__(self, win, image):
        self.win = win
        self.image = image.copy()
        self.drawing = False
        self.ok = False
        self.x1 = self.y1 = self.x2 = self.y2 = 0
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(win, self.on_mouse)

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.x1, self.y1 = x, y
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.x2, self.y2 = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.x2, self.y2 = x, y

    def select(self):
        while True:
            overlay = self.image.copy()
            cv2.rectangle(overlay, (self.x1, self.y1), (self.x2, self.y2),
                          (0, 255, 0), 2)
            cv2.imshow(self.win, overlay)
            k = cv2.waitKey(30) & 0xFF
            if k == 13:  # Enter
                self.ok = abs(self.x2 - self.x1) > 4 and abs(self.y2 - self.y1) > 4
                break
            elif k == 27:  # Esc
                break
            elif k == ord("r"):
                self.x1 = self.y1 = self.x2 = self.y2 = 0
        return self.ok

    @property
    def rect(self):
        x, y = min(self.x1, self.x2), min(self.y1, self.y2)
        w, h = abs(self.x2 - self.x1), abs(self.y2 - self.y1)
        return x, y, w, h


def crop_template(image_path: str, name: str):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Не удалось прочитать {image_path}")
        return
    sel = RectSelector("Выдели область и жми ENTER (ESC — выход)", img)
    if not sel.select():
        print("Отменено.")
        return
    x, y, w, h = sel.rect
    crop = img[y:y + h, x:x + w]
    os.makedirs(TPL_DIR, exist_ok=True)
    out = os.path.join(TPL_DIR, name)

    key = cv2.waitKey(0)  # ожидание решения уже обработано; спрашиваем отдельно
    # Сохраняем обычный PNG + версию с авто-маской по фону (для матчинга без фона)
    cv2.imwrite(out, crop)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    border = np.concatenate([hsv[:2].reshape(-1, 3), hsv[-2:].reshape(-1, 3),
                             hsv[:, :2].reshape(-1, 3), hsv[:, -2:].reshape(-1, 3)])
    bg_hue = int(np.median(border[:, 0]))
    mask = (np.abs(hsv[:, :, 0].astype(int) - bg_hue) > 8).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    bgra = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = mask
    stem = os.path.splitext(name)[0]
    cv2.imwrite(os.path.join(TPL_DIR, f"{stem}_masked.png"), bgra)
    cv2.destroyAllWindows()
    print(f"Сохранено: {out} (+ {stem}_masked.png с альфа-маской)")


def hsv_calibrate(image_path: str):
    """Живая калибровка HSV: ползунки -> диапазон для config.yaml."""
    img = cv2.imread(image_path)
    win = "HSV calibration"
    cv2.namedWindow(win)
    tr = {"h_min": 0, "h_max": 179, "s_min": 0, "s_max": 255, "v_min": 0, "v_max": 255}

    def cb(_):
        pass

    for k, mx in [("h_min", 179), ("h_max", 179), ("s_min", 255),
                  ("s_max", 255), ("v_min", 255), ("v_max", 255)]:
        cv2.createTrackbar(k, win, tr[k], mx, cb)

    while True:
        for k in tr:
            tr[k] = cv2.getTrackbarPos(k, win)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lo = np.array([tr["h_min"], tr["s_min"], tr["v_min"]])
        hi = np.array([tr["h_max"], tr["s_max"], tr["v_max"]])
        mask = cv2.inRange(hsv, lo, hi)
        res = cv2.bitwise_and(img, img, mask=mask)
        cv2.imshow(win, np.hstack([img, res]))
        if cv2.waitKey(30) == 27:
            break
    cv2.destroyAllWindows()
    print("\nВставь в config.yaml -> vision.hsv.<имя_маркера>:")
    print("    {h_min: %d, h_max: %d, s_min: %d, s_max: %d, v_min: %d, v_max: %d}"
          % (tr["h_min"], tr["h_max"], tr["s_min"], tr["s_max"],
             tr["v_min"], tr["v_max"]))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("image", help="путь к скриншоту в captures/")
    p.add_argument("--name", default=None, help="имя сохраняемого шаблона .png")
    p.add_argument("--hsv-calib", action="store_true", help="режим калибровки HSV")
    a = p.parse_args()
    if a.hsv_calib:
        hsv_calibrate(a.image)
    elif a.name:
        crop_template(a.image, a.name)
    else:
        print("Укажите --name claim_button.png или --hsv-calib")
