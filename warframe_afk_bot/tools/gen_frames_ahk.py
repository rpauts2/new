#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_frames_ahk.py — перегенерация warframe_ahk/lib/WF_Frames.ahk
из Python-базы data/frames_db.py (единый источник правды для обеих версий).

Запуск из репозитория:
    python3 tools/gen_frames_ahk.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_BOT = os.path.dirname(HERE)                       # warframe_afk_bot/
ROOT_AHK = os.path.join(os.path.dirname(ROOT_BOT), "warframe_ahk")
OUT = os.path.join(ROOT_AHK, "lib", "WF_Frames.ahk")

sys.path.insert(0, ROOT_BOT)
from data.frames_db import FRAMES_DB, ABILITY_KEYS     # noqa: E402

HEADER = """; ============================================================
; WF_Frames.ahk — база варфреймов для AHK-скриптов (AHK v1.1)
; АВТОГЕНЕРАЦИЯ из data/frames_db.py — НЕ ПРАВИТЬ РУКАМИ!
; Обновить:  python3 tools/gen_frames_ahk.py   ({n} фреймов)
;
; Использование:
;   WF_UseFrame("revenant")        ; инициализировать КД-движок под фрейм
;   WF_FrameCombo()  -> "e,q,r"    ; комбо открытия из базы
;   WF_FrameSustain()-> "e,q,r,f"  ; sustain-ротация из базы
;   WF_SetSurvivalSlot("skin")     ; survival-слот по имени способности
; ============================================================

WF_FRAMES := {{}}
""".format(n=len(FRAMES_DB))


def ahk_str(s: str) -> str:
    return s.replace('"', '""')


def slot_to_key(slot: str) -> str:
    return ABILITY_KEYS.get(slot, slot.lower())


def gen_frame(name: str, f: dict) -> str:
    ab_parts = []
    for slot in sorted(f["abilities"].keys()):
        a = f["abilities"][slot]
        k = slot_to_key(slot)
        cd = int(round(float(a["cooldown"]) * 1000))
        p = int(a.get("priority", 5))
        cast = a.get("cast", "press")
        ab_parts.append(
            '{k}:{{n:"{n}",k:"{k}",cd:{cd},p:{p},t:"{t}"}}'.format(
                k=k, n=ahk_str(a["name"]), cd=cd, p=p, t=cast))
    combo = ",".join(slot_to_key(s) for s in f.get("combo", []))
    sustain = ",".join(slot_to_key(s) for s in f.get("sustain", []))
    return ('WF_FRAMES["{name}"] := {{role:"{role}", combo:"{combo}", '
            'sustain:"{sust}", ab:{{{ab}}}}}').format(
        name=name, role=f.get("role", "unknown"), combo=combo,
        sust=sustain, ab=",".join(ab_parts))


ALIAS_BLOCK = """
; Алиасы имён (1:1 с get_frame() из frames_db.py)
WF_FRAME_ALIAS := {}
"""

FOOTER = """
; ---------------- API ----------------
WF_CurrentFrame := ""

; Разрешение имени: lower, пробелы/подчёркивания -> дефис, алиасы
WF_ResolveFrame(name) {
    global
    key := Trim(name)
    StringLower, key, key
    StringReplace, key, key, %A_Space%, -, All
    StringReplace, key, key, _, -, All
    if (WF_FRAME_ALIAS.HasKey(key))
        key := WF_FRAME_ALIAS[key]
    return key
}

; Инициализация КД-движка WF_Lib под фрейм. true = найден в базе
; ВАЖНО: делает полный WF_ResetAbilities() сначала — иначе от предыдущего
; фрейма остаются КД/клавиши в слотах, которых нет у нового.
WF_UseFrame(name) {
    global
    key := WF_ResolveFrame(name)
    if (!WF_FRAMES.HasKey(key))
        return false
    f := WF_FRAMES[key]
    WF_CurrentFrame := key
    WF_ResetAbilities()
    for slot, a in f.ab
        WF_InitAbility(slot, a.k, Round(a.cd / 1000), a.t, a.p)
    return true
}

WF_FrameCombo() {
    global
    if (WF_FRAMES.HasKey(WF_CurrentFrame))
        return WF_FRAMES[WF_CurrentFrame].combo
    return ""
}

WF_FrameSustain() {
    global
    if (WF_FRAMES.HasKey(WF_CurrentFrame))
        return WF_FRAMES[WF_CurrentFrame].sustain
    return ""
}

; Слот способности по части имени ("Mesmer Skin" -> q, регистронезависимо)
WF_SlotByAb(namePart) {
    global
    if (!WF_FRAMES.HasKey(WF_CurrentFrame))
        return ""
    needle := Trim(namePart)
    StringLower, needle, needle
    for slot, a in WF_FRAMES[WF_CurrentFrame].ab {
        lowName := a.n
        StringLower, lowName, lowName
        if (InStr(lowName, needle))
            return slot
    }
    return ""
}

; Назначить WF_SurvivalSlot из WF_Lib по имени способности
WF_SetSurvivalSlot(namePart) {
    global
    s := WF_SlotByAb(namePart)
    if (s != "")
        WF_SurvivalSlot := s
    return s
}

WF_ListFrames(sep := ", ") {
    global
    out := ""
    for k in WF_FRAMES
        out .= k sep
    return RTrim(out, sep)
}
"""


def extract_aliases_from_source() -> dict:
    """Вытаскивает словарь aliases из get_frame() исходника frames_db.py."""
    src = open(os.path.join(ROOT_BOT, "data", "frames_db.py"), encoding="utf-8").read()
    m = re.search(r"aliases\s*=\s*\{(.*?)\n\s*\}", src, re.S)
    if not m:
        return {}
    body = m.group(1)
    body = re.sub(r"#.*", "", body)          # убрать комментарии
    pairs = re.findall(r'"([^"]+)"\s*:\s*(?:"([^"]*)"|(None))', body)
    out = {}
    for k, v, none in pairs:
        out[k] = v if not none else None
    return out


def main():
    lines = [HEADER]
    for name in sorted(FRAMES_DB.keys()):
        lines.append(gen_frame(name, FRAMES_DB[name]))
    lines.append(ALIAS_BLOCK)
    for k, v in sorted(extract_aliases_from_source().items()):
        if v is None:
            continue
        lines.append('WF_FRAME_ALIAS["%s"] := "%s"' % (k, v))
    lines.append(FOOTER)
    with open(OUT, "w", encoding="utf-8-sig") as fh:
        fh.write("\n".join(lines) + "\n")
    print("written:", OUT, "| frames:", len(FRAMES_DB))


if __name__ == "__main__":
    main()
