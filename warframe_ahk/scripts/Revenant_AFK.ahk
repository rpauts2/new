; ============================================================
; Revenant_AFK.ahk — Nightwave/Effusion AFK-комбо Mesmer-машины
; Работает через полную базу 34 фреймов (lib/WF_Frames.ahk, 1:1 из frames_db.py).
; По умолчанию Revenant: Q Mesmer Skin(25s) E Mesmer(22s) R Danse Macabre(30s) F Reave(35s)
; Mutalist Revenant: E = Defection (притяжение+обращение врагов) — тот же тайминг.
;
; HOTKEYS: F7 — циклическая смена фрейма (Revenant -> Mutalist -> Nova-Mutalist -> Mag-Corpse -> Khora)
;          F8 старт/стоп цикла | ^!P пауза | ^!X выход | F10 сброс сессии
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk
#Include %A_ScriptDir%\..\lib\WF_Frames.ahk

FrameList := ["revenant", "revenant-mutalist", "nova-mutalist", "mag-corpse-eater", "khora"]
FrameIdx := 1

ApplyFrame() {
    global
    name := FrameList[FrameIdx]
    if (!WF_UseFrame(name)) {
        MsgBox Фрейм '%name%' не найден в базе WF_Frames.ahk
        return
    }
    survival := WF_SetSurvivalSlot("skin")       ; Mesmer Skin у Revenant-ов
    if (survival = "")
        survival := WF_SetSurvivalSlot("ward")   ; Chroma-style щиты если вдруг
    WF_Status("Фрейм: " name " | combo: " WF_FrameCombo() " | sustain: " WF_FrameSustain())
}

F7::
    FrameIdx := Mod(FrameIdx, FrameList.MaxIndex()) + 1
    ApplyFrame()
return

ApplyFrame()   ; инициализация при старте скрипта

Running := false
F8::
    Running := !Running
    if Running {
        ApplyFrame()
        WF_Status("AFK-цикл: " WF_CurrentFrame " запущен")
        SetTimer RevLoop, 1200
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer RevLoop, Off
        WF_Status("AFK-цикл: стоп")
    }
return

RevLoop:
    if (!Running || !WF_Enabled) return
    ; открытие комбо из базы фрейма, дальше sustain по КД
    WF_RunCombo(WF_FrameCombo())
    WF_RotateSustain(WF_FrameSustain())
    WF_CheckDeathGuard()
    WF_AntiIdle()
return
