#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run.py — точка входа Warframe AFK Bot.

    python run.py                 # обычный запуск (F8 старт/пауза, F9 стоп)
    python run.py --debug         # с логом в консоли
    python run.py --dry-run       # только проверка конфигурации и окружения
    python run.py -c my.yaml      # свой конфиг
"""
import os
import sys
import argparse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)


def dry_check(cfg_path: str) -> bool:
    ok = True
    print(f"[1/4] Конфиг: {cfg_path}")
    try:
        import yaml
        cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
        assert isinstance(cfg, dict)
        print("   OK")
    except Exception as e:
        print(f"   FAIL: {e}")
        return False

    print("[2/4] Модули:")
    for mod in ("cv2", "numpy", "mss"):
        try:
            __import__(mod)
            print(f"   {mod}: OK")
        except ImportError:
            print(f"   {mod}: НЕТ — pip install -r requirements.txt")
            ok = False
    for mod in ("keyboard", "pyautogui"):
        try:
            __import__(mod)
            print(f"   {mod}: OK")
        except Exception as e:
            print(f"   {mod}: недоступен ({type(e).__name__}) — часть функций ограничена")

    print("[3/4] Шаблоны:")
    tpl_dir = os.path.join(BASE, cfg.get("vision", {}).get("template_dir", "templates"))
    files = [f for f in os.listdir(tpl_dir)] if os.path.isdir(tpl_dir) else []
    pngs = [f for f in files if f.endswith((".png", ".jpg"))]
    print(f"   найдено {len(pngs)} шаблонов в {tpl_dir}"
          + ("" if pngs else " — нарежи через tools/make_templates.py (пока HSV работает без них)"))

    print("[4/4] Окно игры / захват:")
    try:
        from core.screen_capture import ScreenCapture
        cap = ScreenCapture(cfg)
        w, h = cap.screen_size()
        print(f"   область захвата {w}x{h} — OK")
        cap.close()
    except Exception as e:
        print(f"   FAIL: {e}")
        ok = False
    return ok


def main():
    p = argparse.ArgumentParser(description="Warframe AFK Bot")
    p.add_argument("-c", "--config", default=os.path.join(BASE, "config.yaml"))
    p.add_argument("--debug", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="проверить окружение и выйти")
    a = p.parse_args()

    if a.dry_run:
        sys.exit(0 if dry_check(a.config) else 1)

    from core.bot import WarframeAFKBot
    bot = WarframeAFKBot(a.config, debug=a.debug)
    print("=" * 60)
    print("  WARFRAME AFK BOT")
    print("  F8 — пауза/старт | F9 — полный останов | Ctrl+C — выход")
    print("  Аварийный стоп мыши: уведи курсор в ЛЕВЫЙ ВЕРХНИЙ угол экрана")
    print("=" * 60)
    bot.run()


if __name__ == "__main__":
    main()
