; ============================================================
; Nekros_Endo.ahk — Endo-выживание / Requiem-луп (Nekros + Corpse-eater)
; КД/клавиши/комбо теперь из базы lib/WF_Frames.ahk:
;   nekros: Q Despoil(12s) E Spores(prio99=не жмём) R Transvect(25s,побег) F Requiem(40s аура лута)
;   corpse-eater подтягивается по алиасу из той же базы.
; Тактика: стоишь в точке спавна, F держишь активной, Q по кулдауну (урон+дроп),
; R — телепорт к луту когда пиксель-триггер видит оранжевую иконку.
; Выживание: death-guard = Transvect + отход S+Space.
; F7 — сменить фрейм: nekros -> corpse-eater -> revenant (если не тянет соло).
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk
#Include %A_ScriptDir%\..\lib\WF_Frames.ahk

FrameList := ["nekros", "corpse-eater", "revenant"]
FrameIdx := 1

ApplyFrame() {
    global
    name := FrameList[FrameIdx]
    if (!WF_UseFrame(name)) {          ; сам делает WF_ResetAbilities()
        MsgBox Фрейм '%name%' не найден в базе WF_Frames.ahk
        return
    }
    s := WF_SetSurvivalSlot("transvect")     ; Nekros R — телепорт-побег
    if (s = "")
        s := WF_SetSurvivalSlot("skin")      ; Revenant Mesmer Skin
    WF_Status("Фрейм: " name " | combo: " WF_FrameCombo() " | sustain: " WF_FrameSustain())
}

F7::
    FrameIdx := Mod(FrameIdx, FrameList.MaxIndex()) + 1
    ApplyFrame()
return

ApplyFrame()   ; инициализация при запуске скрипта

; --- Калибровка: поставь перекрестие на место где появляется иконка подбора
;     и запусти PickPixel.ahk, затем впиши координаты/цвет сюда:
LOOT_X := 960           ; калибруй через PickPixel.ahk
LOOT_Y := 540
LOOT_HEX := "FFB347"    ; оранжевая иконка подбора

Running := false
F8::
    Running := !Running
    if Running {
        ApplyFrame()
        WF_Status("Nekros Endo: луп запущен (" WF_CurrentFrame ")")
        SetTimer NecroLoop, 2000
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer NecroLoop, Off
        WF_Status("Nekros Endo: стоп")
    }
return

NecroLoop:
    if (!Running || !WF_Enabled) return
    WF_Cast("f")                       ; держать Requiem активной (по КД из базы)
    WF_CheckDeathGuard()               ; красный HP -> survival-слот + отход
    ; если рядом засветился лут — телепортнёмся и подберём (X по умолчанию)
    if WF_PixelOn(LOOT_X, LOOT_Y, LOOT_HEX) {
        WF_Cast("r")
        WF_Tap("x", 60)                ; подобрать
    }
    WF_Cast("q")                       ; Despoil по КД — эндоморфы сами сыпятся
    WF_AntiIdle()
return
