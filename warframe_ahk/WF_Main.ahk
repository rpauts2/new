; ============================================================
; WF_Main.ahk — лаунчер: выбери фарм из списка и запускай
; F1 — меню | F8 — старт/стоп активного скрипта | ^!P пауза | ^!X выход
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SetWorkingDir %A_ScriptDir%

Scripts := { "1": "Revenant_AFK.ahk"        ; Nightwave/Effusion Mesmer-camp
           , "2": "Nova_Mutalist_Pull.ahk"  ; Null Pull стяжка + Molecular Prime
           , "3": "Nekros_Endo.ahk"         ; Requiem лут-луп / Endo
           , "4": "Endo_Survival.ahk"       ; Survival Luna/Uranus (3 фрейма)
           , "5": "Arbitration_AFK.ahk"     ; Арбитраж camp (Revenant/Valkyr)
           }

F1::
    list := "Warframe AHK — что фармим?`n`n"
    for k, name in Scripts
        list .= k " — " name "`n"
    list .= "`n0 — закрыть все скрипты"
    InputBox, choice,, %list%, , 380, 320
    if ErrorLevel
        return
    StringReplace, choice, choice, %A_Space%,, All
    if (choice = "0") {
        DetectHiddenWindows On
        for k, name in Scripts
            try Process, Close, %name%
        ToolTip Все скрипты закрыты
        SetTimer KillTip, 1500
        return
    }
    if Scripts.HasKey(choice) {
        Run % A_ScriptDir "\scripts\" Scripts[choice]
        ToolTip Запущен: %Scripts[choice]%`nF8 внутри него — старт цикла
        SetTimer KillTip, 2500
    } else
        MsgBox Неверный выбор: %choice%
return

KillTip:
    ToolTip
return

^!x::ExitApp
