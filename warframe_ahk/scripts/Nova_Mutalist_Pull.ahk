; ============================================================
; Nova_Mutalist_Pull.ahk — притяжение Null Pull (E, 18s) + Molecular Prime (Q)
; Для Эффосов/Defense: стягиваешь толпу в одну точку, ждёшь взрыв Null Star (F).
; Комбо: E -> Q -> F. Sustain: E (каждые ~18с), Q.
; Обычная Nova: E = Antilift Dump — поменяй hotkey-секвенцию на "e,q,f".
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk

WF_InitAbility("q", "q", 12)   ; Molecular Prime
WF_InitAbility("e", "e", 18)   ; Null Pull (mutalist) — ПРИТЯЖЕНИЕ
WF_InitAbility("r", "r", 25)   ; Antimatter Absorb (пассивная польза, не жмём)
WF_InitAbility("f", "f", 40)   ; Null Star — взрыв скопленной толпы
WF_SurvivalSlot := ""          ; у Новы нет щита — просто отходи (S+Space)

Running := false
F8::
    Running := !Running
    if Running {
        WF_Status("Nova Mutalist: pull-цикл запущен")
        SetTimer NovaLoop, 1500
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer NovaLoop, Off
        WF_Status("Nova Mutalist: стоп")
    }
return

NovaLoop:
    if (!Running || !WF_Enabled) return
    ; раз в цикл: стянуть -> замедлить -> кинуть звезду
    WF_RunCombo("e,q,f")
    WF_RotateSustain("e,q")
    WF_AntiIdle()
return
