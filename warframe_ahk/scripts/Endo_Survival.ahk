; ============================================================
; Endo_Survival.ahk — ЭНДО-выживание (Survival: Luna Dera / Uranus)
; Фрейм на выбор через F7 перед стартом (Revenant/Valkyr/Khora).
; Вся инициализация способностей ЧЕРЕЗ базу lib/WF_Frames.ahk
; (автоген из data/frames_db.py, 34 фрейма) — КД/клавиши/тип каста
; больше не хардкодятся в скрипте.
; Тактика из комьюнити: стоять у точки дропа ящика, крутить sustain,
; пиксель-триггер на золотой ящик, авто-подбор X.
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%
#Include %A_ScriptDir%\..\lib\WF_Lib.ahk
#Include %A_ScriptDir%\..\lib\WF_Frames.ahk

FrameList := ["revenant", "valkyr", "khora"]   ; все есть в базе WF_Frames
FrameIdx := 1
ComboSeq := ""
SustainSeq := ""

ApplyFrame() {
    global
    name := FrameList[FrameIdx]
    if (!WF_UseFrame(name)) {          ; WF_UseFrame сам делает WF_ResetAbilities()
        MsgBox Фрейм '%name%' не найден в базе WF_Frames.ahk
        return
    }
    ; survival-слот по имени способности из базы (Revenant -> Mesmer Skin)
    s := WF_SetSurvivalSlot("skin")
    if (s = "")
        s := WF_SetSurvivalSlot("scourge")   ; Valkyr -> Scourge
    if (s = "")
        s := WF_SetSurvivalSlot("ensnare")   ; Khora -> Ensnare (контроль вместо щита)
    ComboSeq := WF_FrameCombo()
    SustainSeq := WF_FrameSustain()
    WF_Status("Фрейм: " name " | combo: " ComboSeq " | sustain: " SustainSeq)
}

F7::
    FrameIdx := Mod(FrameIdx, FrameList.MaxIndex()) + 1
    ApplyFrame()
return

ApplyFrame()   ; инициализация при запуске скрипта

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
        ApplyFrame()                    ; перестраховка: движок под текущий фрейм
        if (HP_X) {
            WF_HP_X := HP_X
            WF_HP_Y := HP_Y
        }
        WF_Status("Endo Survival: фарм запущен (" WF_CurrentFrame ")")
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
