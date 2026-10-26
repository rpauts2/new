; ============================================================
; Nova_Mutalist_Pull.ahk — притяжение Null Pull (E, 18s) + Molecular Prime (Q)
; Для Эффосов/Defense: стягиваешь толпу в одну точку, ждёшь взрыв Null Star (F).
; Комбо/sustain подтягиваются из базы WF_Frames (nova-mutalist: e,q / sustain e).
; F7 — сменить вариант: nova-mutalist -> mag (Pull тоже E) -> revenant-mutalist (Defection E).
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk
#Include %A_ScriptDir%\..\lib\WF_Frames.ahk

FrameList := ["nova-mutalist", "mag", "revenant-mutalist"]
FrameIdx := 1

ApplyFrame() {
    global
    name := FrameList[FrameIdx]
    if (!WF_UseFrame(name)) {
        MsgBox Фрейм '%name%' не найден в базе
        return
    }
    WF_SetSurvivalSlot("skin")   ; Revenant Mesmer Skin если он выбран
    WF_Status("Фрейм: " name " | combo: " WF_FrameCombo())
}

F7::
    FrameIdx := Mod(FrameIdx, FrameList.MaxIndex()) + 1
    ApplyFrame()
return

ApplyFrame()

Running := false
F8::
    Running := !Running
    if Running {
        ApplyFrame()
        WF_Status(WF_CurrentFrame ": pull-цикл запущен")
        SetTimer NovaLoop, 1500
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer NovaLoop, Off
        WF_Status("Nova Mutalist: стоп")
    }
return

NovaLoop:
    if (!Running || !WF_Enabled) return
    ; раз в цикл: стянуть -> замедлить -> (у Новы) добить звездой
    WF_RunCombo(WF_FrameCombo())
    WF_RotateSustain(WF_FrameSustain())
    WF_AntiIdle()
return
