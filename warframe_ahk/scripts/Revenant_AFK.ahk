; ============================================================
; Revenant_AFK.ahk — Nightwave/Effusion AFK-комбо Mesmer-машины
; База КД взята 1:1 из frames_db.py Python-версии бота.
; Revenant: Q Mesmer Skin(25s) E Mesmer(22s) R Danse Macabre(30s) F Reave(35s)
; Комбо: E -> Q -> R, sustain E,Q. Выживание: Q (щиты).
; Mutalist Revenant: E = Defection (притяжение+обращение врагов) — тот же тайминг.
;
; HOTKEYS: F8 старт/стоп цикла | ^!P пауза | ^!X выход | F10 сброс сессии
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk

; --- инициализация способностей Revenant ---
WF_InitAbility("q", "q", 25)          ; Mesmer Skin (выживание)
WF_InitAbility("e", "e", 22)          ; Mesmer / Defection (ядро AFK)
WF_InitAbility("r", "r", 30)          ; Danse Macabre
WF_InitAbility("f", "f", 35)          ; Reave
WF_SurvivalSlot := "q"

Running := false
F8::
    Running := !Running
    if Running {
        WF_Status("Revenant AFK: цикл запущен")
        SetTimer RevLoop, 1200
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer RevLoop, Off
        WF_Status("Revenant AFK: стоп")
    }
return

RevLoop:
    if (!Running || !WF_Enabled) return
    ; открытие комбо (E->Q->R), дальше только sustain по КД
    WF_RunCombo("e,q,r")
    WF_RotateSustain("e,q,r,f")
    WF_CheckDeathGuard()
    WF_AntiIdle()
return
