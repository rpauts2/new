#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calibrate.py — быстрая проверка «что видит бот» на вашем экране прямо сейчас.

    python tools/calibrate.py                 # захват + все HSV-детекты + debug-окно
    python tools/calibrate.py --tpl claim_button.png   # плюс поиск шаблона

Полезно для настройки порогов vision.default_threshold и HSV-диапазонов.
"""
from __future__ import annotations

import os
import sys
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import yaml

from core.screen_capture import ScreenCapture
from core.vision import VisionEngine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", default="config.yaml")
    ap.add_argument("--tpl", nargs="*", default=[], help="шаблоны для проверки")
    ap.add_argument("--no-gui", action="store_true", help="без окна предпросмотра")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    cap = ScreenCapture(cfg)
    vis = VisionEngine(cfg)

    print("Захватываю кадры 5 сек... (Ctrl+C — стоп)")
    t0 = time.time()
    try:
        while time.time() - t0 < 5:
            frame = cap.grab()
            dets = []
            for color in vis.hsv_ranges:
                try:
                    dets += vis.find_color_blobs(frame, color)[:8]
                except KeyError:
                    pass
            for tpl in list(args.tpl) + list(vis.templates.keys()):
                dets += vis.match_template(frame, tpl, max_results=5)
            h, w = frame.shape[:2]
            cv2.circle(frame, (w // 2, h // 2), 12, (255, 0, 255), 2)
            out = vis.draw_debug(frame, dets)
            print(f"\rобъектов: {len(dets)}  " +
                  " | ".join(f"{d.label}:{d.confidence:.2f}" for d in dets[:5]),
                  end="", flush=True)
            if not args.no_gui:
                cv2.imshow("calibrate", cv2.resize(out, (w // 2, h // 2)))
                if cv2.waitKey(1) & 0xFF == 27:
                    break
    finally:
        print()
        cap.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
