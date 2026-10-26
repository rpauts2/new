; ============================================================
; Nekros_Endo.ahk — Endo-выживание / Requiem-луп
; По базе frames_db: Q Despoil(12s) E Spores(20s,priority 99) R Transvect(25s,побег) F Requiem(40s аура лута)
; Тактика: стоишь в точке спавна, F держишь активной, Q жмёшь по кулдауну (урон+дроп),
; R — телепорт к телам/луту когда пиксель-триггер видит иконку рядом.
; Выживание: Valkyr-style нет, поэтому death-guard = отход S+Space + R.
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk

WF_InitAbility("q", "q", 12)   ; Despoil — AoE урон + дроп
WF_InitAbility("e", "e", 20)   ; Suffragan Spores — не жмём (prio 99)
WF_InitAbility("r", "r", 25)   ; Transvect — телепорт к луту
WF_InitAbility("f", "f", 40)   ; Requiem Reliquary — ядро лут-фарма
WF_SurvivalSlot := "r"         ; при красном HP — сваливаем телепортом

; --- Калибровка: поставь перекрестие на место где появляется иконка подбора
;     и запусти PickPixel.ahk, затем впиши координаты/цвет сюда:
LOOT_X := 960           ; калибруй через PickPixel.ahk
LOOT_Y := 540
LOOT_HEX := "FFB347"    ; оранжевая иконка подбора

Running := false
F8::
    Running := !Running
    if Running {
        WF_Status("Nekros Endo: луп запущен")
        SetTimer NecroLoop, 2000
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer NecroLoop, Off
        WF_Status("Nekros Endo: стоп")
    }
return

NecroLoop:
    if (!Running || !WF_Enabled) return
    WF_Cast("f")                       ; держать Requiem активной
    WF_CheckDeathGuard()               ; красный HP -> Transvect + отход
    ; если рядом засветился лут — телепортнёмся и подберём (X по умолчанию)
    if WF_PixelOn(LOOT_X, LOOT_Y, LOOT_HEX) {
        WF_Cast("r")
        WF_Tap("x", 60)                ; подобрать
    }
    WF_Cast("q")                       ; Despoil по КД — эндоморфы сами сыпятся
    WF_AntiIdle()
return
