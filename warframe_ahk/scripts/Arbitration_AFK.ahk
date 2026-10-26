; ============================================================
; Arbitration_AFK.ahk — Арбитраж (Endo/Neuroptics/Cryotic)
; Комьюнити-тактика: узкая точка спавна + Revenant Mesmer или Valkyr Scourge.
; F6 — режим: 1=Mesmer-camp (Revenant), 2=Scourge-tank (Valkyr), 3=Manual+AntiIdle
; Все КД/клавиши/комбо теперь из базы lib/WF_Frames.ahk (без хардкода).
; Пиксель-триггер на красную виньетку урона -> паника survival-каст + отход.
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk
#Include %A_ScriptDir%\..\lib\WF_Frames.ahk

Mode := 1
Running := false

ApplyMode() {
    global
    if (Mode = 1) {
        if (!WF_UseFrame("revenant"))
            return
        WF_SetSurvivalSlot("skin")            ; Mesmer Skin = неуязвимость
    } else if (Mode = 2) {
        if (!WF_UseFrame("valkyr"))
            return
        WF_SetSurvivalSlot("scourge")         ; Scourge = щит-неуязвимость
    } else {
        WF_ResetAbilities()                   ; Manual: автоматики кастов нет
    }
}

F6::
    Mode := Mod(Mode, 3) + 1
    ApplyMode()
    m := {1:"Mesmer-camp (Revenant)", 2:"Scourge-tank (Valkyr)", 3:"Manual+AntiIdle"}
    if (Mode = 3)
        WF_Status("Арбитраж: " m[Mode])
    else
        WF_Status("Арбитраж: " m[Mode] " | combo: " WF_FrameCombo())
return

ApplyMode()   ; инициализация при запуске скрипта

; калибруй: пиксель красной рамки-виньетки арбитражного урона по краю экрана
DMG_X := 40             ; калибруй красную виньетку урона
DMG_Y := 540
DMG_HEX := "C0392B"

F8::
    Running := !Running
    if Running {
        ApplyMode()
        WF_Status("Арбитраж: цикл запущен (" WF_CurrentFrame ")")
        SetTimer ArbLoop, 1300
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer ArbLoop, Off
        WF_Status("Арбитраж: стоп")
    }
return

ArbLoop:
    if (!Running || !WF_Enabled) return
    if (Mode = 3) {
        WF_AntiIdle()
        return
    }
    ; красная виньетка = сыпется HP -> срочный survival-каст + отход
    if WF_PixelOn(DMG_X, DMG_Y, DMG_HEX, 50) {
        WF_ForceCast(WF_SurvivalSlot)
        SendInput {s down}{space down}
        Sleep 450
        SendInput {space up}{s up}
    }
    WF_RunCombo(WF_FrameCombo())
    WF_RotateSustain(WF_FrameSustain())
    WF_AntiIdle()
return
