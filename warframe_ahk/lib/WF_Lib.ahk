; ============================================================
; WF_Lib.ahk — общая библиотека Warframe AFK-скриптов (AHK v1.1)
; Без чтения памяти / инъекций: только клавиши + пиксели экрана.
; Кулдаун-движок, humanize, комбо-машина, триггеры по пикселям.
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv
SendMode Input
SetWorkingDir %A_ScriptDir%

; ---------------- Глобальные настройки ----------------
WF_Humanize    := true     ; рандомные задержки (анти-BYRO поведенчески)
WF_MinDelay    := 40       ; мс мин. джиттер между нажатиями
WF_MaxDelay    := 130      ; мс макс.
WF_PanicHP     := false    ; включается скриптом если PixelCheck на HP-полосу
WF_SessionMax  := 5400000  ; 90 минут авто-стоп сессии (BYRO любит >2ч подряд)
WF_Enabled     := true     ; главный рубильник

; Пауза всей автоматизации (не путать с встроенной Pause AHK)
^!p::
    WF_Enabled := !WF_Enabled
    ToolTip % WF_Enabled ? "WF: ВКЛ" : "WF: ПАУЗА (стрельба/движение свободны)"
    SetTimer RemoveToolTip, 1500
return
RemoveToolTip:
    ToolTip
return

; Аварийный стоп скрипта
^!x::ExitApp

; Примечание: «мышь в угол = стоп» оставлено только в ручном/меню-режиме —
; в бою курсор игры залочен и проверка A_Cursor не сработает корректно.
; Для экстренного стопа используй Ctrl+Alt+X (глобальный, работает из игры).

; ---------------- Humanize ----------------
WF_Delay(minD:="", maxD:="") {
    global
    mn := minD!="" ? minD : WF_MinDelay
    mx := maxD!="" ? maxD : WF_MaxDelay
    if (!WF_Humanize) {
        Sleep, 30
        return
    }
    Random r, mn, mx
    Sleep %r%
}

; Нажатие с человеческим jitter вокруг базовой длительности
WF_Tap(key, baseMs:=45) {
    global
    if (!WF_Enabled) return
    lo := Round(baseMs*0.7)
    hi := Round(baseMs*1.6)
    Random hold, lo, hi
    SendInput {%key% down}
    Sleep %hold%
    SendInput {%key% up}
    WF_Delay()
}

; Удержание (например Ash Bladestorm / Wisp Radial Javelin hold-cast)
WF_Hold(key, ms) {
    global
    if (!WF_Enabled) return
    lo := Round(ms*0.9)
    hi := Round(ms*1.25)
    Random real, lo, hi
    SendInput {%key% down}
    Sleep %real%
    SendInput {%key% up}
    WF_Delay()
}

; Кулдаун-движок способностей (плоские глобалы — надёжно для #Include)
; slot_last_<slot> = A_TickCount последнего каста, slot_cd_<slot> = мс
; castType: press | hold | passive
; holdMs — реальная длительность удержания для hold-кастов (Ash Bladestorm и т.п.)
WF_InitAbility(slot, hotkey, cdSec, castType:="press", prio:=1, holdMs:=350) {
    global
    SlotKey_%slot% := hotkey
    SlotCd_%slot%  := Round(cdSec * 1000)
    SlotType_%slot% := castType
    SlotPrio_%slot% := prio
    SlotHold_%slot% := holdMs
    SlotLast_%slot% := 0
}

; Полный сброс КД-движка (вызывать перед WF_UseFrame при смене фрейма!)
WF_ResetAbilities() {
    global
    for slot in ["q","e","r","f"] {
        SlotKey_%slot% := ""
        SlotCd_%slot%  := 0
        SlotType_%slot% := "press"
        SlotPrio_%slot% := 1
        SlotHold_%slot% := 350
        SlotLast_%slot% := 0
    }
    WF_SurvivalSlot := ""
}

; Попытка скастовать слот если КД прошёл. true = скастовано
WF_Cast(slot) {
    global
    if (!WF_Enabled || slot = "")
        return false
    hk   := SlotKey_%slot%
    if (!hk)
        return false
    if (SlotType_%slot% = "passive")
        return false
    cd := SlotCd_%slot%
    last := SlotLast_%slot%
    if (A_TickCount - last < cd * 0.92)   ; 8% запас на variance баффов
        return false
    holdMs := SlotHold_%slot%
    if (!holdMs)
        holdMs := 350
    if (SlotType_%slot% = "hold")
        WF_Hold(hk, holdMs)
    else
        WF_Tap(hk)
    SlotLast_%slot% := A_TickCount
    return true
}

; Принудительный каст (игнорирует КД — для survival/паники)
WF_ForceCast(slot) {
    global
    if (!WF_Enabled || slot = "") return false
    hk := SlotKey_%slot%
    if (!hk) return false
    WF_Tap(hk)
    SlotLast_%slot% := A_TickCount
    return true
}

; Разбор строки "e,q,r" в массив слотов
WF_ParseSeq(seq) {
    StringSplit arr, seq, `,,
    out := []
    Loop %arr0% {
        s := Trim(arr%A_Index%)
        if (s != "")
            out.Push(s)
    }
    return out
}

; Комбо-машина: WF_RunCombo("e,q,r") — каскад по готовности
; (жмёт только готовые скиллы; не скачет через КД)
WF_RunCombo(seq) {
    global
    a := WF_ParseSeq(seq)
    for i, slot in a {
        WF_Cast(slot)
        WF_Delay(120, 260)   ; темп каста как у живого игрока
    }
}

; Sustain-ротация: проход по списку слотов, жмёт только готовые
WF_RotateSustain(seq) {
    global
    a := WF_ParseSeq(seq)
    for i, slot in a {
        if WF_Cast(slot)
            return true
    }
    return false
}

; ---------------- Пиксельные триггеры ----------------
; Классика rpauts2/warframe-ahk: PixelGetColor по HUD-точкам.
; Координаты калибруются F9-меню или tools/PickPixel.ahk
; Примеры точек: полоса здоровья, маркер Extraction, лампа Necralisk,
; иконка Mote/Endo над телом, таймер Defense-волны.
WF_PixelOn(x, y, wantHex, tol:=30) {
    PixelGetColor c, x, y, RGB
    if (c = "")
        return false
    cr := "0x" SubStr(c,3,2)
    cg := "0x" SubStr(c,5,2)
    cb := "0x" SubStr(c,7,2)
    wr := "0x" SubStr(wantHex,1,2)
    wg := "0x" SubStr(wantHex,3,2)
    wb := "0x" SubStr(wantHex,5,2)
    dr := Abs(cr-wr)
    dg := Abs(cg-wg)
    db := Abs(cb-wb)
    return (dr<=tol && dg<=tol && db<=tol)
}

; Ждёт пока пиксель станет нужным цветом (или timeout). true = увидели
WF_WaitPixel(x, y, hex, timeoutMs:=10000, step:=250) {
    t0 := A_TickCount
    while (A_TickCount - t0 < timeoutMs) {
        if WF_PixelOn(x, y, hex)
            return true
        Sleep %step%
    }
    return false
}

; ---------------- Анти-АФК / выживание ----------------
; Дёрганье камеры + микро-шаги, чтобы игра не выкинула за idle
WF_AntiIdle() {
    global
    if (!WF_Enabled) return
    Random dx, -30, 30
    Random dy, -10, 10
    MouseMove dx, dy,, R
    WF_Delay(50, 150)
    Random pick, 1, 4
    if (pick=1) WF_Tap("w", 60)
    else if (pick=2) WF_Tap("s", 60)
    else if (pick=3) WF_Tap("space", 60)   ; прыжок/данж
    else WF_Tap("a", 60)
}

; Death-guard: если HP-пиксель красный -> отход + ability выживания
; WF_HP_X/Y задаются скриптом после калибровки (0 = выключено)
WF_HP_X := 0
WF_HP_Y := 0
WF_SurvivalSlot := ""
WF_CheckDeathGuard() {
    global
    if (!WF_HP_X || !WF_Enabled) return false
    ; красный цвет здоровья при низком HP (калибруется PickPixel)
    if WF_PixelOn(WF_HP_X, WF_HP_Y, "FF3B30", 45) {
        WF_ForceCast(WF_SurvivalSlot)          ; напр. Revenant Q Mesmer Skin
        SendInput {s down}{space down}
        Sleep 400
        SendInput {space up}{s up}
        WF_Delay(200, 400)
        return true
    }
    return false
}

; ---------------- Сессионный лимит (анти-BYRO) ----------------
; BYRO флажит аккаунты за 6+ часов идеального фарма подряд.
; Таймер глушит автоматику после WF_SessionMax и требует ручного F10.
WF_SessionStart := A_TickCount
WF_SessionWatchdog() {
    global
    if (A_TickCount - WF_SessionStart > WF_SessionMax) {
        WF_Enabled := false
        MsgBox, 64, WF Session Limit, Автопауза: сессия >90 мин.`nОтдохни сам, потом F10 для сброса таймера.
    }
}
F10::
    WF_SessionStart := A_TickCount
    WF_Enabled := true
    ToolTip, WF: сессия сброшена
    SetTimer RemoveToolTip, 1200
return

; ---------------- Статус-строка ----------------
WF_Status(text) {
    static last := ""
    if (text != last) {
        last := text
        ToolTip %text%
    }
}
