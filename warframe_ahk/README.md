# Warframe AHK — чистые AutoHotkey-скрипты для AFK-фарма

Всё как ты просил, бро: **это именно .ahk скрипты** (AHK v1.1), в стиле
`Lazy-World/warframe-ahk`, `rpauts2/warframe-ahk-scripts` и `wf-macro`, но с
движком способностей из нашей Python-базы (`warframe_afk_bot/data/frames_db.py`, 34 фрейма).

## Структура
```
warframe_ahk/
├── WF_Main.ahk                 # лаунчер: F1 — меню выбора фарма
├── lib/WF_Lib.ahk              # ядро: КД-движок, humanize, пиксель-триггеры, death-guard
├── scripts/
│   ├── Revenant_AFK.ahk        # Mesmer-camp (E->Q->R), Nightwave/Effusion
│   ├── Nova_Mutalist_Pull.ahk  # Null Pull стяжка + Molecular Prime + Null Star
│   ├── Nekros_Endo.ahk         # Requiem луп, Transvect к луту, Endo
│   ├── Endo_Survival.ahk       # Survival Luna/Uranus, F7 — смена фрейма (Rev/Valkyr/Khora)
│   └── Arbitration_AFK.ahk     # Арбитраж camp, F6 — режим (Mesmer/Scourge/Manual)
└── tools/PickPixel.ahk         # калибровка пикселей HUD (Ctrl+Shift+C копирует X,Y,HEX)
```

## Быстрый старт
1. Поставь **AutoHotkey v1.1** (https://www.autohotkey.com — инсталлятор сам даёт v1; для v2 нужен отдельный порт либы).
2. Запусти `WF_Main.ahk` → **F1** → выбери скрипт цифрой.
3. В игре зайди в миссию, наведи камеру в фарм-точку, жми **F8**.

## Калибровка (обязательно для триггеров)
Открой `tools/PickPixel.ahk`, наведи курсор на:
- полосу HP (левый верх HUD) → впиши `HP_X/HP_Y` в `Endo_Survival.ahk`;
- оранжевую иконку подбора → `LOOT_X/LOOT_Y/LOOT_HEX` в `Nekros_Endo.ahk`;
- золотой ящик выживания → `BOX_X/BOX_Y/BOX_HEX`;
- красную виньетку урона по краю экрана → `DMG_X/DMG_Y/DMG_HEX` в `Arbitration_AFK.ahk`.

Без калибровки скрипты всё равно работают — просто без авто-подбора и death-guard'а
(только КД-ротации комбо).

## Хоткеи (все скрипты)
| Клавиши | Действие |
|---|---|
| F8 | старт/стоп фарм-цикла |
| F7 | смена фрейма (Endo_Survival) |
| F6 | смена режима (Arbitration) |
| Ctrl+Alt+P | пауза автоматики (ручной режим) |
| Ctrl+Alt+X | полная остановка |
| F10 | сброс сессионного лимита |

## Про античит (честно)
AHK шлёт синтетический ввод — **BYRO/EAC его не читает из памяти**, но банят за
*поведение*. Поэтому в либе уже:
- `WF_Humanize` — джиттер 40–130мс на каждое действие, длительность нажатия рандомная;
- КД-движок не спамит скиллы «в ноль» (8% запас к кулдауну);
- сессионный watchdog: автопауза после 90 минут;
- anti-idle двигает камеру/персонажа — нет идеальной статики.

Никакие скрипты нельзя назвать «небанящимися». Держи паузы между миссиями, не оставляй
на ночь, используй свой основной аккаунт на свой страх и риск.
