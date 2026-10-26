#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
overlay.py — прозрачный HUD-виджет поверх игры (аналог кастомного UI из
Lazy-World warframe-ahk/LazyHub: статус, таймеры, предупреждения).

Рендерит маленькое always-on-top окошко с:
  • статусом бота (RUN / PAUSE), активным фреймом и состоянием модулей;
  • счётчиками фарма (касты, лут, циклы, skip'ы);
  • аптаймом;
  • предупреждениями стабильности (идея WarnCheck из vs_propa_zenith.ahk):
    CapsLock включён, не английская раскладка клавиатуры.

Работает только если установлен tkinter (входит в стандартную поставку Python
на Windows). Иначе модуль молча деградирует до логов.

Конфиг (afk_zones.overlay):
    enabled: true
    pos_rel: [0.006, 0.45]   # положение окна (доли экрана), как gPosX/gPosY в AHK
    refresh_sec: 1.0
    show_warnings: true      # CapsLock/раскладка
"""
from __future__ import annotations

import time
import threading

from modules.base import FarmModule


class OverlayHUD(FarmModule):

    def __init__(self, bot, cfg, name="overlay"):
        super().__init__(bot, cfg, name)
        self.tick_interval = float(cfg.get("refresh_sec", 1.0))
        self.pos_rel = cfg.get("pos_rel", [0.006, 0.45])
        self.show_warn = bool(cfg.get("show_warnings", True))
        self._tk_ok = False
        self._labels = {}
        self._text = ""
        try:
            self._init_tk()
        except Exception as e:
            self.log.warning("Overlay недоступен (%s) — только логи", e)

    # ---------------- Tkinter в отдельном потоке ----------------
    def _init_tk(self):
        import tkinter as tk
        self._tk = tk
        self._root = None
        self._ui_thread = threading.Thread(target=self._mainloop, daemon=True)
        self._ui_thread.start()
        self._tk_ok = True

    def _mainloop(self):
        try:
            root = self._tk.Tk()
            self._root = root
            root.title("wf-bot")
            root.overrideredirect(True)          # без рамки, как окно LazyHub
            root.attributes("-topmost", True)
            root.attributes("-alpha", 0.82)
            try:
                root.attributes("-transparentcolor", "#010203")
                bg = "#010203"
            except Exception:
                bg = "#151515"                   # Linux/macOS: просто тёмный фон
            root.configure(bg=bg)
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            x, y = int(self.pos_rel[0] * sw), int(self.pos_rel[1] * sh)
            root.geometry(f"+{x}+{y}")
            lbl = self._tk.Label(root, text="wf-bot init", fg="#86C8BC", bg=bg,
                                 font=("Consolas", 10), justify="left")
            lbl.pack(padx=8, pady=6)
            self._labels["main"] = lbl
            # клик-драг за окно + закрытие правой кнопкой
            lbl.bind("<Button-4>", lambda e: root.destroy())  # колесо вверх = закрыть
            self._text_label = lbl
            root.mainloop()
        except Exception:
            self.log.debug("Overlay mainloop завершился")

    def _set_text(self, text: str):
        if not self._tk_ok or self._root is None:
            return
        try:
            self._root.after(0, lambda: self._labels["main"].config(text=text))
        except Exception:
            pass

    # ---------------- содержимое ----------------
    def _keyboard_state(self):
        warns = []
        try:
            import keyboard
            if keyboard.is_pressed("caps lock"):
                warns.append("CAPS")
        except Exception:
            pass
        try:
            import ctypes
            lang = ctypes.windll.user32.GetKeyboardLayout(0) & 0xFFFF
            if lang and lang != 0x0409:
                warns.append("EN?")   # не англ. раскладка — команды могут не считываться
        except Exception:
            pass
        return warns

    def on_tick(self, frame):
        b = self.bot
        lines = []
        status = "▶ RUN" if b.running else "⏸ PAUSE"
        uptime = int(time.time() - b.started_at)
        lines.append(f"WF-BOT {status}  [{uptime//60}m{uptime%60:02d}s]")
        st = b.stats
        lines.append(f"casts:{st.get('ability_casts',0)} loot:{st.get('loot_picked',0)} "
                     f"zaw:{st.get('zaw_throws',0)} skips:{st.get('nora_skips',0)}")
        mods = ", ".join(m.name for m in b.sorted_modules()
                         if m.name != "overlay")
        lines.append(mods[:40])
        if self.show_warn:
            w = self._keyboard_state()
            if w:
                lines.append("⚠ " + " ".join(w))
        text = "\n".join(lines)
        if text != self._text:
            self._text = text
            self._set_text(text)
