; ============================================================
; Endo_Survival.ahk — ЭНДО-выживание (Survival: Luna Dera / Uranus)
; Фрейм на выбор через меню F7 перед стартом (Revenant/Valkyr/Khora).
; Тактика из комьюнити: стоять у точки дропа ящика, крутить sustain,
; пиксель-триггер на таймер/ящик, авто-подбор X.
; + Defense-вариант: волновой PixelCheck на "Wave incoming" иконку.
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk

FrameSel := 1   ; 1=Revenant 2=Valkyr 3=Khora
F7::
    FrameSel := Mod(FrameSel, 3) + 1
    names := {1:"Revenant", 2:"Valkyr", 3:"Khora"}
    WF_InitAbilitiesFor(FrameSel)
    WF_Status("Фрейм: " names[FrameSel] " (F7 — сменить)")
return

WF_InitAbilitiesFor(sel) {
    global
    if (sel = 1) {          ; Revenant
        WF_InitAbility("q","q",25)
        WF_InitAbility("e","e",22)
        WF_InitAbility("r","r",30)
        WF_InitAbility("f","f",35)
        WF_SurvivalSlot := "q"
        ComboSeq := "e,q,r"
        SustainSeq := "e,q,r,f"
    } else if (sel = 2) {   ; Valkyr — король AFK-выживания (Scourge неуязвимость)
        WF_InitAbility("q","q",18)
        WF_InitAbility("e","e",8)
        WF_InitAbility("r","r",30)
        WF_InitAbility("f","f",35)
        WF_SurvivalSlot := "f"
        ComboSeq := "f,r"
        SustainSeq := "f,r,e"
    } else {                ; Khora — Venom Cells точатся сами, луп по E/Q
        WF_InitAbility("q","q",15)
        WF_InitAbility("e","e",20)
        WF_InitAbility("r","r",30)
        WF_InitAbility("f","f",45)
        WF_SurvivalSlot := ""
        ComboSeq := "e,q"
        SustainSeq := "e,q,f"
    }
}

; --- калибруемые триггеры (PickPixel.ahk) ---
BOX_X := 960            ; калибруй золотой ящик выживания
BOX_Y := 500
BOX_HEX := "E8C469"
HP_X := 0               ; полоса HP для death-guard (0 = выкл)
HP_Y := 0

Running := false
F8::
    Running := !Running
    if Running {
        WF_InitAbilitiesFor(FrameSel)
        if (HP_X) {
            WF_HP_X := HP_X
            WF_HP_Y := HP_Y
        }
        WF_Status("Endo Survival: фарм запущен")
        SetTimer SurvLoop, 1400
        SetTimer WF_SessionWatchdog, 60000
    } else {
        SetTimer SurvLoop, Off
        WF_Status("Endo Survival: стоп")
    }
return

SurvLoop:
    if (!Running || !WF_Enabled) return
    WF_RunCombo(ComboSeq)
    WF_RotateSustain(SustainSeq)
    WF_CheckDeathGuard()
    ; засветился ящик эндоморфов -> встать под него и подобрать
    if WF_PixelOn(BOX_X, BOX_Y, BOX_HEX) {
        WF_Tap("w", 120)          ; шаг вперёд к ящику
        WF_Delay(300, 700)
        WF_Tap("x", 60)           ; loot pickup
    }
    WF_AntiIdle()
return
