; ============================================================
; PickPixel.ahk — калибратор пиксельных триггеров (аналог tools/calibrate)
; Наведи курсор на нужную точку HUD (полоса HP, иконка лута, ящик выживания),
; нажми Ctrl+Shift+C — в буфер попадёт строка:  X := 960, Y := 540, HEX := "FFB347"
; Вставь её в нужный скрипт вместо заглушек. Esc — выход.
; ============================================================
#Requires AutoHotkey v1.1
#NoEnv

^+c::
    MouseGetPos px, py
    PixelGetColor c, px, py, RGB
    out := "X := " px ", Y := " py ", HEX := """ SubStr(c,3) """"
    Clipboard := out
    ToolTip Скопировано:`n%out%
    SetTimer KillTip, 2000
return

KillTip:
    ToolTip
return

Esc::ExitApp
