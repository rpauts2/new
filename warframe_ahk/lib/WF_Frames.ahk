; ============================================================
; WF_Frames.ahk — база варфреймов для AHK-скриптов (AHK v1.1)
; АВТОГЕНЕРАЦИЯ из data/frames_db.py — НЕ ПРАВИТЬ РУКАМИ!
; Обновить:  python3 tools/gen_frames_ahk.py   (34 фреймов)
;
; Использование:
;   WF_UseFrame("revenant")        ; инициализировать КД-движок под фрейм
;   WF_FrameCombo()  -> "e,q,r"    ; комбо открытия из базы
;   WF_FrameSustain()-> "e,q,r,f"  ; sustain-ротация из базы
;   WF_SetSurvivalSlot("skin")     ; survival-слот по имени способности
; ============================================================

WF_FRAMES := {}

WF_FRAMES["ash"] := {role:"stealth", combo:"e", sustain:"e", ab:{q:{n:"Shuriken",k:"q",cd:12000,p:2,t:"press"},e:{n:"Bladestorm",k:"e",cd:20000,p:1,t:"hold"},r:{n:"Smoke Finger",k:"r",cd:17000,p:99,t:"press"},f:{n:"Grindhouse",k:"f",cd:30000,p:3,t:"press"}}}
WF_FRAMES["banshee"] := {role:"support", combo:"e,f", sustain:"e", ab:{q:{n:"Sound Quake",k:"q",cd:15000,p:3,t:"press"},e:{n:"Sonic Nexus",k:"e",cd:12000,p:1,t:"press"},r:{n:"Acoustic Basin",k:"r",cd:25000,p:99,t:"press"},f:{n:"Despair",k:"f",cd:30000,p:2,t:"press"}}}
WF_FRAMES["chroma"] := {role:"tank", combo:"f,q", sustain:"f", ab:{q:{n:"Elemental Ward",k:"q",cd:20000,p:2,t:"press"},e:{n:"Effigy",k:"e",cd:25000,p:3,t:"press"},r:{n:"Spoils of Battle",k:"r",cd:18000,p:99,t:"press"},f:{n:"Voss Quake",k:"f",cd:35000,p:1,t:"press"}}}
WF_FRAMES["cyte-korunas"] := {role:"dps", combo:"e", sustain:"e", ab:{q:{n:"Stalker's Hunt",k:"q",cd:18000,p:2,t:"press"},e:{n:"Echo Lace",k:"e",cd:15000,p:1,t:"press"},r:{n:"Horned Surge",k:"r",cd:25000,p:99,t:"press"},f:{n:"Ravenous Crush",k:"f",cd:40000,p:3,t:"press"}}}
WF_FRAMES["ember"] := {role:"dps", combo:"f,q", sustain:"q", ab:{q:{n:"Fire Blast",k:"q",cd:10000,p:1,t:"press"},e:{n:"Flame Wall",k:"e",cd:15000,p:2,t:"press"},r:{n:"Accelerate",k:"r",cd:25000,p:99,t:"press"},f:{n:"World on Fire",k:"f",cd:50000,p:3,t:"press"}}}
WF_FRAMES["excalibur"] := {role:"hybrid", combo:"e", sustain:"e", ab:{q:{n:"Slash Dash",k:"q",cd:12000,p:2,t:"press"},e:{n:"Radial Javelin",k:"e",cd:15000,p:1,t:"press"},r:{n:"Moment of Brilliance",k:"r",cd:25000,p:3,t:"press"},f:{n:"Exalted Blade",k:"f",cd:40000,p:99,t:"press"}}}
WF_FRAMES["frost"] := {role:"tank", combo:"r,f,q", sustain:"r,f", ab:{q:{n:"Ice Wave",k:"q",cd:12000,p:2,t:"press"},e:{n:"Ice Dome",k:"e",cd:20000,p:99,t:"press"},r:{n:"Snow Globe",k:"r",cd:25000,p:1,t:"press"},f:{n:"Blizzard",k:"f",cd:35000,p:2,t:"press"}}}
WF_FRAMES["garuda"] := {role:"dps", combo:"e,f", sustain:"e", ab:{q:{n:"Aerial Bounty",k:"q",cd:18000,p:99,t:"press"},e:{n:"Blade Storm",k:"e",cd:15000,p:1,t:"press"},r:{n:"Petra",k:"r",cd:30000,p:99,t:"press"},f:{n:"Reign of Scars",k:"f",cd:60000,p:2,t:"press"}}}
WF_FRAMES["harrow"] := {role:"support", combo:"e,q", sustain:"e", ab:{q:{n:"Penance",k:"q",cd:20000,p:2,t:"press"},e:{n:"Thurible",k:"e",cd:18000,p:1,t:"press"},r:{n:"Contract",k:"r",cd:40000,p:99,t:"press"},f:{n:"Covenant",k:"f",cd:50000,p:99,t:"press"}}}
WF_FRAMES["hildryn"] := {role:"tank", combo:"q", sustain:"e,q", ab:{q:{n:"Shield Wall",k:"q",cd:20000,p:1,t:"press"},e:{n:"Pacifying Flame",k:"e",cd:12000,p:2,t:"press"},r:{n:"Spirit Shield",k:"r",cd:25000,p:3,t:"press"},f:{n:"Provoked Wrath",k:"f",cd:40000,p:99,t:"press"}}}
WF_FRAMES["inaros"] := {role:"hybrid", combo:"e,r", sustain:"e", ab:{q:{n:"Desert Swarm",k:"q",cd:20000,p:2,t:"press"},e:{n:"Sands of Inaros",k:"e",cd:15000,p:1,t:"press"},r:{n:"Quicksand",k:"r",cd:25000,p:3,t:"press"},f:{n:"Thirsting Sphere",k:"f",cd:45000,p:99,t:"press"}}}
WF_FRAMES["khora"] := {role:"support", combo:"e,f", sustain:"e,f", ab:{q:{n:"Sirocco",k:"q",cd:16000,p:99,t:"press"},e:{n:"Ensnare",k:"e",cd:18000,p:1,t:"press"},r:{n:"Tilting Point",k:"r",cd:22000,p:99,t:"press"},f:{n:"Strangle PRISM",k:"f",cd:40000,p:2,t:"press"}}}
WF_FRAMES["loki"] := {role:"stealth", combo:"q", sustain:"q", ab:{q:{n:"Invisibility",k:"q",cd:17000,p:1,t:"press"},e:{n:"Radial Disarm",k:"e",cd:14000,p:2,t:"press"},r:{n:"Decoy",k:"r",cd:20000,p:99,t:"press"},f:{n:"Switch Teleport",k:"f",cd:25000,p:99,t:"press"}}}
WF_FRAMES["mag"] := {role:"hybrid", combo:"r,e,q", sustain:"r,e", ab:{q:{n:"Burst",k:"q",cd:12000,p:2,t:"press"},e:{n:"Crumbling Collapse",k:"e",cd:18000,p:1,t:"press"},r:{n:"Pull",k:"r",cd:15000,p:3,t:"press"},f:{n:"Magnify",k:"f",cd:40000,p:99,t:"press"}}}
WF_FRAMES["mag-corpse-eater"] := {role:"hybrid", combo:"r,e,q", sustain:"r,e", ab:{q:{n:"Burst",k:"q",cd:12000,p:2,t:"press"},e:{n:"Crushing Ruin",k:"e",cd:18000,p:1,t:"press"},r:{n:"Pull",k:"r",cd:15000,p:3,t:"press"},f:{n:"Magnify",k:"f",cd:40000,p:99,t:"press"}}}
WF_FRAMES["mesa"] := {role:"dps", combo:"q,e", sustain:"q", ab:{q:{n:"Shooting Gallery",k:"q",cd:15000,p:1,t:"press"},e:{n:"Matri-bullets",k:"e",cd:20000,p:2,t:"press"},r:{n:"Pellet Fortress",k:"r",cd:25000,p:99,t:"press"},f:{n:"Regulator's Chorus",k:"f",cd:45000,p:3,t:"press"}}}
WF_FRAMES["mirage"] := {role:"support", combo:"r", sustain:"r,q", ab:{q:{n:"Hall of Mirrors",k:"q",cd:20000,p:3,t:"press"},e:{n:"Prism",k:"e",cd:30000,p:99,t:"press"},r:{n:"Eclipse",k:"r",cd:53000,p:1,t:"press"},f:{n:"Curtain Call",k:"f",cd:45000,p:99,t:"press"}}}
WF_FRAMES["nekros"] := {role:"tank", combo:"f,q", sustain:"f", ab:{q:{n:"Despoil",k:"q",cd:12000,p:2,t:"press"},e:{n:"Suffragan Spores",k:"e",cd:20000,p:99,t:"press"},r:{n:"Transvect",k:"r",cd:25000,p:99,t:"press"},f:{n:"Requiem Reliquary",k:"f",cd:40000,p:1,t:"press"}}}
WF_FRAMES["nidus"] := {role:"tank", combo:"q,e", sustain:"q", ab:{q:{n:"Viral Spread",k:"q",cd:20000,p:1,t:"press"},e:{n:"Radiant Strain",k:"e",cd:30000,p:2,t:"press"},r:{n:"Packleader",k:"r",cd:40000,p:3,t:"press"},f:{n:"Larva",k:"f",cd:60000,p:99,t:"press"}}}
WF_FRAMES["nova"] := {role:"dps", combo:"f,q", sustain:"f,q", ab:{q:{n:"Molecular Prime",k:"q",cd:12000,p:2,t:"press"},e:{n:"Antimatter Drop",k:"e",cd:25000,p:3,t:"press"},r:{n:"World of Quiet",k:"r",cd:30000,p:99,t:"press"},f:{n:"Null Star",k:"f",cd:40000,p:1,t:"press"}}}
WF_FRAMES["nova-mutalist"] := {role:"dps", combo:"e,q", sustain:"e", ab:{q:{n:"Molecular Prime",k:"q",cd:12000,p:2,t:"press"},e:{n:"Null Pull",k:"e",cd:18000,p:1,t:"press"},r:{n:"Antimatter Absorb",k:"r",cd:25000,p:99,t:"press"},f:{n:"Null Star",k:"f",cd:40000,p:3,t:"press"}}}
WF_FRAMES["oberon"] := {role:"tank", combo:"q,e", sustain:"q", ab:{q:{n:"Smite",k:"q",cd:15000,p:1,t:"press"},e:{n:"Hallowed Ground",k:"e",cd:25000,p:2,t:"press"},r:{n:"Renewal",k:"r",cd:30000,p:99,t:"press"},f:{n:"Phaedra's Solace",k:"f",cd:45000,p:99,t:"press"}}}
WF_FRAMES["qorvex"] := {role:"hybrid", combo:"e,q", sustain:"e", ab:{q:{n:"Radiant Heat",k:"q",cd:16000,p:2,t:"press"},e:{n:"Melting Arc",k:"e",cd:12000,p:1,t:"press"},r:{n:"Scattering Inferno",k:"r",cd:22000,p:3,t:"press"},f:{n:"Wrathful Hymn",k:"f",cd:45000,p:99,t:"press"}}}
WF_FRAMES["revenant"] := {role:"dps", combo:"e,q,r", sustain:"e,q", ab:{q:{n:"Mesmer Skin",k:"q",cd:25000,p:2,t:"press"},e:{n:"Mesmer",k:"e",cd:22000,p:1,t:"press"},r:{n:"Danse Macabre",k:"r",cd:30000,p:3,t:"press"},f:{n:"Reave",k:"f",cd:35000,p:4,t:"press"}}}
WF_FRAMES["revenant-mutalist"] := {role:"dps", combo:"e,q,r", sustain:"e,q", ab:{q:{n:"Mesmer Skin",k:"q",cd:25000,p:2,t:"press"},e:{n:"Defection",k:"e",cd:22000,p:1,t:"press"},r:{n:"Danse Macabre",k:"r",cd:30000,p:3,t:"press"},f:{n:"Reave",k:"f",cd:35000,p:4,t:"press"}}}
WF_FRAMES["rhino"] := {role:"tank", combo:"e,f", sustain:"e", ab:{q:{n:"Rhino Charge",k:"q",cd:12000,p:99,t:"press"},e:{n:"Iron Skin",k:"e",cd:15000,p:1,t:"press"},r:{n:"Rommel's Roar",k:"r",cd:20000,p:3,t:"press"},f:{n:"Roar",k:"f",cd:30000,p:2,t:"press"}}}
WF_FRAMES["saryn"] := {role:"dps", combo:"q", sustain:"q,e", ab:{q:{n:"Spores",k:"q",cd:85000,p:1,t:"hold"},e:{n:"Toxic Lash (Muta)",k:"e",cd:95000,p:2,t:"press"},r:{n:"Molt",k:"r",cd:60000,p:99,t:"press"},f:{n:"Transpoles",k:"f",cd:75000,p:99,t:"press"}}}
WF_FRAMES["trinity"] := {role:"support", combo:"r,e", sustain:"r,q", ab:{q:{n:"Well of Life",k:"q",cd:15000,p:1,t:"press"},e:{n:"Energy Vampire",k:"e",cd:18000,p:2,t:"press"},r:{n:"Link",k:"r",cd:20000,p:3,t:"press"},f:{n:"Blessing",k:"f",cd:45000,p:99,t:"press"}}}
WF_FRAMES["valkyr"] := {role:"tank", combo:"f,e", sustain:"f,e", ab:{q:{n:"Impale",k:"q",cd:18000,p:99,t:"press"},e:{n:"Parry",k:"e",cd:8000,p:2,t:"press"},r:{n:"Hysteria",k:"r",cd:30000,p:3,t:"press"},f:{n:"Scourge",k:"f",cd:35000,p:1,t:"press"}}}
WF_FRAMES["valkyrie"] := {role:"tank", combo:"r,e", sustain:"r", ab:{q:{n:"Supersonic Bladewing",k:"q",cd:15000,p:99,t:"press"},e:{n:"Wings of Death",k:"e",cd:18000,p:2,t:"press"},r:{n:"Paralysis",k:"r",cd:12000,p:1,t:"press"},f:{n:"Impale",k:"f",cd:30000,p:3,t:"press"}}}
WF_FRAMES["vesk"] := {role:"dps", combo:"f", sustain:"f,q", ab:{q:{n:"Bloodletting",k:"q",cd:14000,p:2,t:"press"},e:{n:"Arbitration Glitch",k:"e",cd:20000,p:99,t:"press"},r:{n:"Vhoolx Sigil",k:"r",cd:25000,p:99,t:"press"},f:{n:"Calculated Strike",k:"f",cd:35000,p:1,t:"press"}}}
WF_FRAMES["volt"] := {role:"dps", combo:"f,r,q", sustain:"f", ab:{q:{n:"Electric Shield",k:"q",cd:20000,p:2,t:"press"},e:{n:"Speed",k:"e",cd:15000,p:99,t:"press"},r:{n:"Capacitance",k:"r",cd:25000,p:3,t:"press"},f:{n:"Overload",k:"f",cd:30000,p:1,t:"press"}}}
WF_FRAMES["wisp"] := {role:"support", combo:"q,e", sustain:"q", ab:{q:{n:"Will-o-Whisp",k:"q",cd:25000,p:1,t:"press"},e:{n:"Reservoir",k:"e",cd:30000,p:2,t:"press"},r:{n:"Lullaby",k:"r",cd:35000,p:3,t:"press"},f:{n:"Breach Surge",k:"f",cd:45000,p:99,t:"press"}}}
WF_FRAMES["wukong"] := {role:"dps", combo:"f", sustain:"f", ab:{q:{n:"Pride of the Locusts",k:"q",cd:30000,p:99,t:"press"},e:{n:"Cloud Walker",k:"e",cd:15000,p:99,t:"press"},r:{n:"Defect",k:"r",cd:20000,p:99,t:"press"},f:{n:"Avatar",k:"f",cd:60000,p:1,t:"press"}}}

; Алиасы имён (1:1 с get_frame() из frames_db.py)
WF_FRAME_ALIAS := {}

WF_FRAME_ALIAS["banshee-prime"] := "banshee"
WF_FRAME_ALIAS["corpse-eater"] := "nekros"
WF_FRAME_ALIAS["crimson-mag"] := "mag-corpse-eater"
WF_FRAME_ALIAS["cyte"] := "cyte-korunas"
WF_FRAME_ALIAS["cytekorunas"] := "cyte-korunas"
WF_FRAME_ALIAS["defection"] := "revenant-mutalist"
WF_FRAME_ALIAS["excalibur-prime"] := "excalibur"
WF_FRAME_ALIAS["frost-prime"] := "frost"
WF_FRAME_ALIAS["garuda-prime"] := "garuda"
WF_FRAME_ALIAS["khora-prime"] := "khora"
WF_FRAME_ALIAS["korunas"] := "cyte-korunas"
WF_FRAME_ALIAS["mag-corpse"] := "mag-corpse-eater"
WF_FRAME_ALIAS["mesa-mk-i"] := "mesa"
WF_FRAME_ALIAS["mutalist-nova"] := "nova-mutalist"
WF_FRAME_ALIAS["mutalist-revenant"] := "revenant-mutalist"
WF_FRAME_ALIAS["necro"] := "nekros"
WF_FRAME_ALIAS["necros-prime"] := "nekros"
WF_FRAME_ALIAS["nova mutalist"] := "nova-mutalist"
WF_FRAME_ALIAS["nova-prime"] := "nova"
WF_FRAME_ALIAS["null-pull"] := "nova-mutalist"
WF_FRAME_ALIAS["revenant-and-dextera"] := "revenant"
WF_FRAME_ALIAS["revenant-defection"] := "revenant-mutalist"
WF_FRAME_ALIAS["rhino-prime"] := "rhino"
WF_FRAME_ALIAS["sonic-nexus"] := "banshee"
WF_FRAME_ALIAS["valkyr-prime"] := "valkyr"
WF_FRAME_ALIAS["volt-prime"] := "volt"
WF_FRAME_ALIAS["wukong-prime"] := "wukong"

; ---------------- API ----------------
WF_CurrentFrame := ""

; Разрешение имени: lower, пробелы/подчёркивания -> дефис, алиасы
WF_ResolveFrame(name) {
    global
    key := Trim(name)
    StringLower, key, key
    StringReplace, key, key, %A_Space%, -, All
    StringReplace, key, key, _, -, All
    if (WF_FRAME_ALIAS.HasKey(key))
        key := WF_FRAME_ALIAS[key]
    return key
}

; Инициализация КД-движка WF_Lib под фрейм. true = найден в базе
WF_UseFrame(name) {
    global
    key := WF_ResolveFrame(name)
    if (!WF_FRAMES.HasKey(key))
        return false
    f := WF_FRAMES[key]
    WF_CurrentFrame := key
    for slot, a in f.ab
        WF_InitAbility(slot, a.k, Round(a.cd / 1000), a.t, a.p)
    return true
}

WF_FrameCombo() {
    global
    if (WF_FRAMES.HasKey(WF_CurrentFrame))
        return WF_FRAMES[WF_CurrentFrame].combo
    return ""
}

WF_FrameSustain() {
    global
    if (WF_FRAMES.HasKey(WF_CurrentFrame))
        return WF_FRAMES[WF_CurrentFrame].sustain
    return ""
}

; Слот способности по части имени ("Mesmer Skin" -> q, регистронезависимо)
WF_SlotByAb(namePart) {
    global
    if (!WF_FRAMES.HasKey(WF_CurrentFrame))
        return ""
    needle := Trim(namePart)
    StringLower, needle, needle
    for slot, a in WF_FRAMES[WF_CurrentFrame].ab {
        lowName := a.n
        StringLower, lowName, lowName
        if (InStr(lowName, needle))
            return slot
    }
    return ""
}

; Назначить WF_SurvivalSlot из WF_Lib по имени способности
WF_SetSurvivalSlot(namePart) {
    global
    s := WF_SlotByAb(namePart)
    if (s != "")
        WF_SurvivalSlot := s
    return s
}

WF_ListFrames(sep := ", ") {
    global
    out := ""
    for k in WF_FRAMES
        out .= k sep
    return RTrim(out, sep)
}

