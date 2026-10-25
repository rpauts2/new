#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
frames_db.py — база данных варфреймов для авто-способностей (Ability Autopilot).

Описывает роли фреймов, кулдауны/клавиши способностей и устоявшиеся
AFK-паттерны сообщества. Автопилот строит из этого ротацию кастов:
  combo   — предстартовый набор баффов перед волной;
  sustain — цикл поддержки по кулдаунам во время фарма.

Стандартная раскладка Warframe: 1=Q, 2=E, 3=R, 4=F.
"""

ABILITY_KEYS = {"1": "q", "2": "e", "3": "r", "4": "f"}

FRAMES_DB = {

    # ==================== КЛАССИКА AFK-ФАРМА ====================
    "volt": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Electric Shield", "hotkey": "q", "cooldown": 20,
                  "cast": "press", "priority": 2,
                  "notes": "щит + разряд при попадании"},
            "2": {"name": "Speed", "hotkey": "e", "cooldown": 15,
                  "cast": "press", "priority": 99, "notes": "AFK не нужен"},
            "3": {"name": "Capacitance", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 3, "notes": "бафф урона от молний"},
            "4": {"name": "Overload", "hotkey": "f", "cooldown": 30,
                  "cast": "press", "priority": 1,
                  "notes": "AOE-стан + урон — главный афк-инструмент Volt"},
        },
        "combo": ["4", "3", "1"],
        "sustain": ["4"],
        "afk_fit": ("good", "Урон только от способностей — нужен поток врагов"),
    },

    "nova": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Molecular Prime", "hotkey": "q", "cooldown": 12,
                  "cast": "press", "priority": 2,
                  "notes": "вредность+урон по площади, дешёвый кулдаун"},
            "2": {"name": "Anti-Energy Wall", "hotkey": "e", "cooldown": 25,
                  "cast": "press", "priority": 99},
            "3": {"name": "World of Quiet", "hotkey": "r", "cooldown": 30,
                  "cast": "press", "priority": 99},
            "4": {"name": "Null Star", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 1,
                  "notes": "взрыв с радиусом — ядро AFK-комбо Nova"},
        },
        "combo": ["4", "1"],
        "sustain": ["4", "1"],
        "afk_fit": ("good", "Классика Эффосов: Null Star + Molecular Prime"),
    },

    "frost": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Ice Wave", "hotkey": "q", "cooldown": 12,
                  "cast": "press", "priority": 2, "notes": "заморозка волной"},
            "2": {"name": "Ice Dome", "hotkey": "e", "cooldown": 20,
                  "cast": "press", "priority": 99},
            "3": {"name": "Snow Globe", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 1,
                  "notes": "неуязвимость внутри — сердце AFK Frost"},
            "4": {"name": "Blizzard", "hotkey": "f", "cooldown": 35,
                  "cast": "press", "priority": 2, "notes": "АОЕ заморозка+урон"},
        },
        "combo": ["3", "4", "1"],
        "sustain": ["3", "4"],
        "afk_fit": ("excellent", "Snow Globe = неуязвимость; Blizzard добивает"),
    },

    "khora": {
        "role": "support",
        "abilities": {
            "1": {"name": "Sirocco", "hotkey": "q", "cooldown": 16,
                  "cast": "press", "priority": 99},
            "2": {"name": "Ensnare", "hotkey": "e", "cooldown": 18,
                  "cast": "press", "priority": 1,
                  "notes": "ловушка: стан + доп. урон всем в сети"},
            "3": {"name": "Tilting Point", "hotkey": "r", "cooldown": 22,
                  "cast": "press", "priority": 99},
            "4": {"name": "Strangle PRISM", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 2,
                  "notes": "поле: враги задыхаются, союзники лечатся"},
        },
        "combo": ["2", "4"],
        "sustain": ["2", "4"],
        "afk_fit": ("excellent", "Соло-фарм Эффосов: Ensnare-ловушки у точки спавна"),
    },

    "wukong": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Pride of the Locusts", "hotkey": "q", "cooldown": 30,
                  "cast": "press", "priority": 99},
            "2": {"name": "Cloud Walker", "hotkey": "e", "cooldown": 15,
                  "cast": "press", "priority": 99},
            "3": {"name": "Defect", "hotkey": "r", "cooldown": 20,
                  "cast": "press", "priority": 99},
            "4": {"name": "Avatar", "hotkey": "f", "cooldown": 60,
                  "cast": "press", "priority": 1,
                  "notes": "клон-босс сам убивает всё вокруг — топ AFK"},
        },
        "combo": ["4"],
        "sustain": ["4"],
        "afk_fit": ("excellent", "Avatar сам воюет; можно стоять в стороне"),
    },

    "inaros": {
        "role": "hybrid",
        "abilities": {
            "1": {"name": "Desert Swarm", "hotkey": "q", "cooldown": 20,
                  "cast": "press", "priority": 2, "notes": "пожирание врагов"},
            "2": {"name": "Sands of Inaros", "hotkey": "e", "cooldown": 15,
                  "cast": "press", "priority": 1,
                  "notes": "конус: урон + вампиризм — основа выживания"},
            "3": {"name": "Quicksand", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 3, "notes": "замедление зоны"},
            "4": {"name": "Thirsting Sphere", "hotkey": "f", "cooldown": 45,
                  "cast": "press", "priority": 99},
        },
        "combo": ["2", "3"],
        "sustain": ["2"],
        "afk_fit": ("good", "Sands лечат сами; нужно направлять конус на маркеры"),
    },

    # ==================== НЕОНОВЫЙ УРОН / NIGHTWAVE-ФАРМ ====================
    "revenant": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Mesmer Skin", "hotkey": "q", "cooldown": 25,
                  "cast": "press", "priority": 2,
                  "notes": "щиты + детонация при получении урона"},
            "2": {"name": "Mesmer", "hotkey": "e", "cooldown": 22,
                  "cast": "press", "priority": 1,
                  "notes": "АФФЛИКЦИЯ: враги стреляют друг в друга — легенда AFK"},
            "3": {"name": "Danse Macabre", "hotkey": "r", "cooldown": 30,
                  "cast": "press", "priority": 3, "notes": "вампиризм по площади"},
            "4": {"name": "Reave", "hotkey": "f", "cooldown": 35,
                  "cast": "press", "priority": 4},
        },
        "combo": ["2", "1", "3"],
        "sustain": ["2", "1"],
        "afk_fit": ("excellent", "Эталон Nightwave-фарма в углу: Mesmer делает всё сам"),
    },

    "garuda": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Aerial Bounty", "hotkey": "q", "cooldown": 18,
                  "cast": "press", "priority": 99},
            "2": {"name": "Blade Storm", "hotkey": "e", "cooldown": 15,
                  "cast": "press", "priority": 1,
                  "notes": "авто-ножи бьют по ближайшим врагам — идеально AFK"},
            "3": {"name": "Petra", "hotkey": "r", "cooldown": 30,
                  "cast": "press", "priority": 99},
            "4": {"name": "Reign of Scars", "hotkey": "f", "cooldown": 60,
                  "cast": "press", "priority": 2, "notes": "кровавая буря AoE"},
        },
        "combo": ["2", "4"],
        "sustain": ["2"],
        "afk_fit": ("excellent", "Blade Storm — самонаводящийся AFK-урон"),
    },

    "harrow": {
        "role": "support",
        "abilities": {
            "1": {"name": "Penance", "hotkey": "q", "cooldown": 20,
                  "cast": "press", "priority": 2},
            "2": {"name": "Thurible", "hotkey": "e", "cooldown": 18,
                  "cast": "press", "priority": 1,
                  "notes": "кадило: урон+крит всем рядом"},
            "3": {"name": "Contract", "hotkey": "r", "cooldown": 40,
                  "cast": "press", "priority": 99},
            "4": {"name": "Covenant", "hotkey": "f", "cooldown": 50,
                  "cast": "press", "priority": 99},
        },
        "combo": ["2", "1"],
        "sustain": ["2"],
        "afk_fit": ("good", "Thurible — аура урона; Harrow стоит и фармит"),
    },

    "oberon": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Smite", "hotkey": "q", "cooldown": 15,
                  "cast": "press", "priority": 1,
                  "notes": "свет: урон врагам, лечение союзникам"},
            "2": {"name": "Hallowed Ground", "hotkey": "e", "cooldown": 25,
                  "cast": "press", "priority": 2},
            "3": {"name": "Renewal", "hotkey": "r", "cooldown": 30,
                  "cast": "press", "priority": 99},
            "4": {"name": "Phaedra's Solace", "hotkey": "f", "cooldown": 45,
                  "cast": "press", "priority": 99},
        },
        "combo": ["1", "2"],
        "sustain": ["1"],
        "afk_fit": ("good", "Smite — дешёвый кулдаун, стабильный свет-урон"),
    },

    # ==================== СТелс / БЕСПЛАТНЫЕ УБИЙСТВА ====================
    "loki": {
        "role": "stealth",
        "abilities": {
            "1": {"name": "Invisibility", "hotkey": "q", "cooldown": 17,
                  "cast": "press", "priority": 1, "notes": "невидимость"},
            "2": {"name": "Radial Disarm", "hotkey": "e", "cooldown": 14,
                  "cast": "press", "priority": 2},
            "3": {"name": "Decoy", "hotkey": "r", "cooldown": 20,
                  "cast": "press", "priority": 99},
            "4": {"name": "Switch Teleport", "hotkey": "f", "cooldown": 25,
                  "cast": "press", "priority": 99},
        },
        "combo": ["1"],
        "sustain": ["1"],
        "afk_fit": ("weak", "Стелс не убивает сам — годится только для escape-ранов"),
    },

    "ash": {
        "role": "stealth",
        "abilities": {
            "1": {"name": "Shuriken", "hotkey": "q", "cooldown": 12,
                  "cast": "press", "priority": 2},
            "2": {"name": "Bladestorm", "hotkey": "e", "cooldown": 20,
                  "cast": "hold", "hold_sec": 3.0, "priority": 1,
                  "notes": "вихрь клинков — держи и стой в центре"},
            "3": {"name": "Smoke Finger", "hotkey": "r", "cooldown": 17,
                  "cast": "press", "priority": 99},
            "4": {"name": "Grindhouse", "hotkey": "f", "cooldown": 30,
                  "cast": "press", "priority": 3},
        },
        "combo": ["2"],
        "sustain": ["2"],
        "afk_fit": ("good", "Bladestorm — мобильный мясорубочный AFK"),
    },

    # ==================== ТАНКИ / ВЫЖИВАНИЕ ====================
    "rhino": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Rhino Charge", "hotkey": "q", "cooldown": 12,
                  "cast": "press", "priority": 99},
            "2": {"name": "Iron Skin", "hotkey": "e", "cooldown": 13,
                  "cast": "press", "priority": 1,
                  "notes": "стакается до 100% DR — ставь каждый кулдаун"},
            "3": {"name": "Rommel Reaver", "hotkey": "r", "cooldown": 20,
                  "cast": "press", "priority": 99},
            "4": {"name": "Roar", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 2, "notes": "бафф урона всей пачке"},
        },
        "combo": ["2", "4"],
        "sustain": ["2"],
        "afk_fit": ("good", "Бессмертие, но урона мало — нужна стрельба из оружия"),
    },

    "valkyrie": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Supersonic Bladewing", "hotkey": "q", "cooldown": 15,
                  "cast": "press", "priority": 99},
            "2": {"name": "Wings of Death", "hotkey": "e", "cooldown": 18,
                  "cast": "press", "priority": 2},
            "3": {"name": "Paralysis", "hotkey": "r", "cooldown": 12,
                  "cast": "press", "priority": 1,
                  "notes": "быстрый стан — дешёвый кулдаун для ротации"},
            "4": {"name": "Impale", "hotkey": "f", "cooldown": 30,
                  "cast": "press", "priority": 3},
        },
        "combo": ["3", "2"],
        "sustain": ["3"],
        "afk_fit": ("good", "Частый Paralysis держит толпу обездвиженной"),
    },

    # ==================== ЭЛЕМЕНТАЛЬНЫЙ АОЕ ====================
    "ember": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Fire Blast", "hotkey": "q", "cooldown": 10,
                  "cast": "press", "priority": 1,
                  "notes": "самый дешёвый кулдаун в игре — спамить"},
            "2": {"name": "Flame Wall", "hotkey": "e", "cooldown": 15,
                  "cast": "press", "priority": 2},
            "3": {"name": "Accelerate", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 99},
            "4": {"name": "World on Fire", "hotkey": "f", "cooldown": 50,
                  "cast": "press", "priority": 3},
        },
        "combo": ["4", "1"],
        "sustain": ["1"],
        "afk_fit": ("good", "Fire Blast каждые 10 сек — постоянный AoE-огонь"),
    },

    "mag": {
        "role": "hybrid",
        "abilities": {
            "1": {"name": "Burst", "hotkey": "q", "cooldown": 12,
                  "cast": "press", "priority": 2},
            "2": {"name": "Crumbling Collapse", "hotkey": "e", "cooldown": 18,
                  "cast": "press", "priority": 1,
                  "notes": "сжатие металла: AoE-урон + разоружение"},
            "3": {"name": "Pull", "hotkey": "r", "cooldown": 15,
                  "cast": "press", "priority": 3,
                  "notes": "стягивает врагов в кучу под Burst/Collapse"},
            "4": {"name": "Magnify", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 99},
        },
        "combo": ["3", "2", "1"],
        "sustain": ["3", "2"],
        "afk_fit": ("good", "Комбо Pull→Collapse — классический сплав AFK-урона"),
    },

    "vesk": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Bloodletting", "hotkey": "q", "cooldown": 14,
                  "cast": "press", "priority": 2},
            "2": {"name": "Arbitration Glitch", "hotkey": "e", "cooldown": 20,
                  "cast": "press", "priority": 99},
            "3": {"name": "Vhoolx Sigil", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 99},
            "4": {"name": "Calculated Strike", "hotkey": "f", "cooldown": 35,
                  "cast": "press", "priority": 1},
        },
        "combo": ["4"],
        "sustain": ["4", "1"],
        "afk_fit": ("weak", "Полагается на хитскит-билды — слаб в чистом AFK"),
    },

    # ==================== НОВЫЕ / СПЕЦИФИЧЕСКИЕ ====================
    "qorvex": {
        "role": "hybrid",
        "abilities": {
            "1": {"name": "Radiant Heat", "hotkey": "q", "cooldown": 16,
                  "cast": "press", "priority": 2},
            "2": {"name": "Melting Arc", "hotkey": "e", "cooldown": 12,
                  "cast": "press", "priority": 1,
                  "notes": "лучевая дуга — можно водить по спавну"},
            "3": {"name": "Scattering Inferno", "hotkey": "r", "cooldown": 22,
                  "cast": "press", "priority": 3},
            "4": {"name": "Wrathful Hymn", "hotkey": "f", "cooldown": 45,
                  "cast": "press", "priority": 99},
        },
        "combo": ["2", "1"],
        "sustain": ["2"],
        "afk_fit": ("good", "Melting Arc — стабильный луч по таймеру"),
    },

    "cyte-korunas": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Stalker's Hunt", "hotkey": "q", "cooldown": 18,
                  "cast": "press", "priority": 2},
            "2": {"name": "Echo Lace", "hotkey": "e", "cooldown": 15,
                  "cast": "press", "priority": 1,
                  "notes": "эхо-урон по врагам вокруг"},
            "3": {"name": "Horned Surge", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 99},
            "4": {"name": "Ravenous Crush", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 3},
        },
        "combo": ["2"],
        "sustain": ["2"],
        "afk_fit": ("good", "Echo Lace — пассивноподобный AoE по кулдауну"),
    },

    # ============ Арбитраж-ротации (по AHK-профилям wf-yagami/Arbitrations) ============
    "saryn": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Spores", "hotkey": "q", "cooldown": 85,
                  "cast": "hold", "hold_sec": 0.25, "priority": 1,
                  "notes": "DoT-стаки на всю волну; в арбитраже держат бафф ~85 сек"},
            "2": {"name": "Toxic Lash (Muta)", "hotkey": "e", "cooldown": 95,
                  "cast": "press", "priority": 2},
            "3": {"name": "Molt", "hotkey": "r", "cooldown": 60,
                  "cast": "press", "priority": 99},
            "4": {"name": "Transpoles", "hotkey": "f", "cooldown": 75,
                  "cast": "press", "priority": 99},
        },
        "combo": ["1"],
        "sustain": ["1", "2"],
        "afk_fit": ("good", "Saryn DoT стаки — классика авто-арбитража"),
    },

    "mirage": {
        "role": "support",
        "abilities": {
            "1": {"name": "Hall of Mirrors", "hotkey": "q", "cooldown": 20,
                  "cast": "press", "priority": 3,
                  "notes": "доп. урон команды, можно спамить"},
            "2": {"name": "Prism", "hotkey": "e", "cooldown": 30,
                  "cast": "press", "priority": 99},
            "3": {"name": "Eclipse", "hotkey": "r", "cooldown": 53,
                  "cast": "press", "priority": 1,
                  "notes": "бафф урона+защиты ~53 сек — ядро автобафа"},
            "4": {"name": "Curtain Call", "hotkey": "f", "cooldown": 45,
                  "cast": "press", "priority": 99},
        },
        "combo": ["3"],
        "sustain": ["3", "1"],
        "afk_fit": ("good", "Eclipse — долгий бафф, идеален для автоподдержки"),
    },

    "wisp": {
        "role": "support",
        "abilities": {
            "1": {"name": "Will-o-Whisp", "hotkey": "q", "cooldown": 25,
                  "cast": "press", "priority": 1,
                  "notes": "+скорость перезарядки команде — автобаф"},
            "2": {"name": "Reservoir", "hotkey": "e", "cooldown": 30,
                  "cast": "press", "priority": 2},
            "3": {"name": "Lullaby", "hotkey": "r", "cooldown": 35,
                  "cast": "press", "priority": 3},
            "4": {"name": "Breach Surge", "hotkey": "f", "cooldown": 45,
                  "cast": "press", "priority": 99},
        },
        "combo": ["1", "2"],
        "sustain": ["1"],
        "afk_fit": ("good", "Wisp-бафы раздаются одной кнопкой в начале миссии"),
    },

    "nidus": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Viral Spread", "hotkey": "q", "cooldown": 20,
                  "cast": "press", "priority": 1},
            "2": {"name": "Radiant Strain", "hotkey": "e", "cooldown": 30,
                  "cast": "press", "priority": 2,
                  "notes": "грибы-баффы; раскладка камеры подбирается вручную"},
            "3": {"name": "Packleader", "hotkey": "r", "cooldown": 40,
                  "cast": "press", "priority": 3},
            "4": {"name": "Larva", "hotkey": "f", "cooldown": 60,
                  "cast": "press", "priority": 99},
        },
        "combo": ["1", "2"],
        "sustain": ["1"],
        "afk_fit": ("medium", "Нужно размещать грибы — полный AFK только с автострельбой"),
    },

    "hildryn": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Shield Wall", "hotkey": "q", "cooldown": 20,
                  "cast": "press", "priority": 1,
                  "notes": "щит -> энергия; ключ выживания"},
            "2": {"name": "Pacifying Flame", "hotkey": "e", "cooldown": 12,
                  "cast": "press", "priority": 2,
                  "notes": "спам под удержанием ЛКМ (AHK hildryn.ahk)"},
            "3": {"name": "Spirit Shield", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 3},
            "4": {"name": "Provoked Wrath", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 99},
        },
        "combo": ["1"],
        "sustain": ["2", "1"],
        "afk_fit": ("excellent", "Потребляет щит вместо энергии — вечная аура Pacifist"),
    },

    "trinity": {
        "role": "support",
        "abilities": {
            "1": {"name": "Well of Life", "hotkey": "q", "cooldown": 15,
                  "cast": "press", "priority": 1,
                  "notes": "лечение всей пачки — страховка AFK"},
            "2": {"name": "Energy Vampire", "hotkey": "e", "cooldown": 18,
                  "cast": "press", "priority": 2,
                  "notes": "выкачивает энергию из связываемых врагов"},
            "3": {"name": "Link", "hotkey": "r", "cooldown": 20,
                  "cast": "press", "priority": 3,
                  "notes": "делит урон между врагами"},
            "4": {"name": "Blessing", "hotkey": "f", "cooldown": 45,
                  "cast": "press", "priority": 99},
        },
        "combo": ["3", "2"],
        "sustain": ["3", "1"],
        "afk_fit": ("good", "Link перенаправляет урон; Trinity сама себя лечит"),
    },

    "nekros": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Necro Siege", "hotkey": "q", "cooldown": 12,
                  "cast": "press", "priority": 1,
                  "notes": "постоянный DoT-туман вокруг"},
            "2": {"name": "Transvect", "hotkey": "e", "cooldown": 20,
                  "cast": "press", "priority": 99},
            "3": {"name": "Abominate", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 2,
                  "notes": "абоминиация взрывается и лечит"},
            "4": {"name": "Suffragan Spores", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 3},
        },
        "combo": ["1", "3"],
        "sustain": ["1"],
        "afk_fit": ("good", "Necro Siege — вечный туман урона без прицеливания"),
    },

    "chroma": {
        "role": "tank",
        "abilities": {
            "1": {"name": "Elemental Ward", "hotkey": "q", "cooldown": 20,
                  "cast": "press", "priority": 2},
            "2": {"name": "Effigy", "hotkey": "e", "cooldown": 25,
                  "cast": "press", "priority": 3},
            "3": {"name": "Spoils of Battle", "hotkey": "r", "cooldown": 18,
                  "cast": "press", "priority": 99},
            "4": {"name": "Voss Quake", "hotkey": "f", "cooldown": 35,
                  "cast": "press", "priority": 1,
                  "notes": "землетрясение: AoE-урон + защита от урона"},
        },
        "combo": ["4", "1"],
        "sustain": ["4"],
        "afk_fit": ("good", "Voss Quake — и урон, и танкование одновременно"),
    },

    "mesa": {
        "role": "dps",
        "abilities": {
            "1": {"name": "Shooting Gallery", "hotkey": "q", "cooldown": 15,
                  "cast": "press", "priority": 1,
                  "notes": "двойные револьверы — авто-турель Mesa"},
            "2": {"name": "Matri-bullets", "hotkey": "e", "cooldown": 20,
                  "cast": "press", "priority": 2},
            "3": {"name": "Pellet Fortress", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 99},
            "4": {"name": "Regulator's Chorus", "hotkey": "f", "cooldown": 45,
                  "cast": "press", "priority": 3},
        },
        "combo": ["1", "2"],
        "sustain": ["1"],
        "afk_fit": ("good", "Shooting Gallery + автомат = стабильный DPS"),
    },

    "excalibur": {
        "role": "hybrid",
        "abilities": {
            "1": {"name": "Slash Dash", "hotkey": "q", "cooldown": 12,
                  "cast": "press", "priority": 2},
            "2": {"name": "Radial Javelin", "hotkey": "e", "cooldown": 15,
                  "cast": "press", "priority": 1,
                  "notes": "AoE-урон + бронелом по кругу"},
            "3": {"name": "Moment of Brilliance", "hotkey": "r", "cooldown": 25,
                  "cast": "press", "priority": 3},
            "4": {"name": "Exalted Blade", "hotkey": "f", "cooldown": 40,
                  "cast": "press", "priority": 99},
        },
        "combo": ["2"],
        "sustain": ["2"],
        "afk_fit": ("weak", "Слабые AoE-кулдауны — лучше играть руками"),
    },
}


def get_frame(name: str) -> dict:
    """Возвращает запись фрейма или безопасный дефолт (без способностей)."""
    key = name.strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "mesa-mk-i": "mesa", "excalibur-prime": "excalibur",
        "frost-prime": "frost", "nova-prime": "nova", "volt-prime": "volt",
        "wukong-prime": "wukong", "khora-prime": "khora",
        "garuda-prime": "garuda", "revenant-and-dextera": "revenant",
        "cytekorunas": "cyte-korunas", "cyte": "cyte-korunas",
        "korunas": "cyte-korunas", "primed": None,
    }
    key = aliases.get(key, key) or key
    if key in FRAMES_DB:
        return FRAMES_DB[key]
    return {
        "role": "unknown",
        "abilities": {},
        "combo": [],
        "sustain": [],
        "afk_fit": ("unknown", f"Фрейм '{name}' не в базе — используйте generic-профиль"),
    }


def list_frames() -> list:
    return sorted(FRAMES_DB.keys())
