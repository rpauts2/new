; ============================================================
; Arbitration_AFK.ahk — Арбитраж (Endo/Neuroptics/Cryotic)
; Комьюнити-тактика: узкая точка спавна + Revenant Mesmer или Valkyr Scourge.
; F6 — выбрать режим: 1=Mesmer-camp (Revenant), 2=Scourge-tank (Valkyr), 3=Manual+AntiIdle
; Пиксель-триггер на красную "Arbitration" полосу урона -> паника survival.
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk

Mode := 1
F6::
    Mode := Mod(Mode, 3) + 1
    m := {1:"Mesmer-camp (Revenant)", 2:"Scourge-tank (Valkyr)", 3:"Manual+AntiIdle"}
    WF_InitAbilitiesFor(Mode)
    WF_Status("Арбитраж: " m[Mode])
return

WF_InitAbilitiesFor(m) {
    global
    if (m = 1) {
        WF_InitAbility("q","q",25)
        WF_InitAbility("e","e",22)
        WF_InitAbility("r","r",30)
        WF_InitAbility("f","f",35)
        WF_SurvivalSlot := "q"
    } else if (m = 2) {
        WF_InitAbility("q","q",18)
        WF_InitAbility("e","e",8)
        WF_InitAbility("r","r",30)
        WF_InitAbility("f","f",35)
        WF_SurvivalSlot := "f"
    }
}

; калибруй: пиксель красной рамки-виньетки арбитражного урона по краю экрана
DMG_X := 40             ; калибруй красную виньетку урона
DMG_Y := 540
DMG_HEX := "C0392B"

Running := false
F8::
    Running := !Running
    if Running {
        WF_InitAbilitiesFor(Mode)
        WF_Status("Арбитраж: цикл запущен")
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
    if (Mode = 1) {
        WF_RunCombo("e,q,r")
        WF_RotateSustain("e,q,r,f")
    } else {
        WF_RunCombo("f,r")
        WF_RotateSustain("f,e,r")   ; Parry(8s) почти вечный с Recharge
    }
    WF_AntiIdle()
return
