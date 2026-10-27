# Warframe Mission & Frame Advisor

A local, manual-play companion that suggests Warframes by mission type and preferred role. It does not capture the game screen, send keyboard/mouse input, automate combat, or attempt to bypass inactivity checks.

## Requirements
- Python 3.10+
- No third-party packages

## Run
~~~bash
python warframe_companion/advisor.py --list-missions
python warframe_companion/advisor.py --mission Survival
python warframe_companion/advisor.py --mission Spy --goal stealth --limit 5
python -m unittest discover -s warframe_companion/tests -v
~~~

## How it works
- Mission types have broad role priorities.
- Each frame has broad role tags and a short caveat.
- Results show matched roles and a transparent score.
- This is a starter advisor, not a live meta tier list. Updates, mods, Archon Shards, Helminth choices, enemy faction, modifiers, player investment, and squad composition can change the answer.

## Expand the catalog
Add or update a Frame entry only after checking a current reference. Prefer the current WARFRAME Wiki or maintained WFCD item data:
- Mission types: https://wiki.warframe.com/w/Mission
- Reward rotations: https://wiki.warframe.com/w/AABC
- Frame and ability data: https://github.com/WFCD/warframe-items

This tool provides planning information for a player who remains in control. It is not a game bot and does not automate gameplay.
