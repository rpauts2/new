# Repository audit: Warframe AFK Farm Script

Audited branch: warframe-afk-farm-script-70124  
Audit date: 2026-10-27

## High-priority findings

1. Frame ability data is not reliable enough to drive an action system. In warframe_afk_bot/data/frames_db.py, Nova's standard ability names/slots are assigned incorrectly: her standard order is Null Star, Antimatter Drop, Wormhole, Molecular Prime. Other labels include names that do not match the standard ability kits of the named frames. Verify every entry against a current source before trusting the database.
2. warframe_afk_bot/modules/antiafk.py explicitly simulates activity through randomized key presses, mouse movement, and strafing. This audit does not recommend making it harder to detect or more human-like.
3. warframe_afk_bot/modules/afk_anomaly.py describes rapid repeated ability input and automated loops. Avoid extending this into evasion-oriented behavior.
4. Generated Python bytecode is committed in multiple __pycache__ directories. Remove tracked bytecode and ensure .gitignore excludes __pycache__/, *.py[cod], virtual environments, logs, captures, and local settings.
5. Two listed PNG templates are only 137 bytes and share the same blob SHA, so they appear to be placeholders rather than distinct production templates.
6. No obvious automated test suite is present in the tree. Add tests for config parsing, profile schema validation, state transitions, and pure utility functions. Keep tests away from live game input.
7. The profile engine is a broad action interpreter supporting key presses, mouse movement, clicks, firing, and transitions. Validate profile schema and reject malformed or unknown actions before execution. Use dry-run/simulation tests for profile logic.

## Recommended order
1. Treat frame data as untrusted; validate names, ability slot order, aliases, and source date.
2. Add schema validation and unit tests that do not send game input.
3. Remove generated artifacts from version control and add a reproducible setup guide.
4. Separate reference/planning tools from input automation.
5. Add mission and role guidance as a manual-play companion. The initial version is in warframe_companion/.
6. Review current game rules before any future automation changes and avoid anti-idle evasion.

## References
- Mission types: https://wiki.warframe.com/w/Mission
- Reward rotations: https://wiki.warframe.com/w/AABC
- Nova's standard abilities: https://wiki.warframe.com/w/Nova
- Maintained frame data: https://github.com/WFCD/warframe-items

This is a static review, not a claim that every issue has been found or that existing AFK scripts are safe to run.
