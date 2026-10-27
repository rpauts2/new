# Open-source Warframe tooling research

Research snapshot: 2026-10-27. This is a shortlist of public projects and data sources worth evaluating for a manual-play companion. It is not an exhaustive list of everything on the internet, and no third-party code has been copied into this repository.

## Recommended sources to evaluate

### 1. WFCD / warframe-items
- Repository: https://github.com/WFCD/warframe-items
- Potential use: canonical-ish community-maintained item, Warframe, weapon, ability, and image metadata.
- Integration idea: import upstream JSON into a generated local snapshot, pin the source commit/date, validate required fields, and never let unverified imported data drive input automation.

### 2. WFHelper
- Repository: https://github.com/WFHelper/wfhelper
- Overview: https://wfhelper.com/
- Potential use: product reference for inventory, relic rewards, foundry requirements, mastery, market prices, world state, and arbitration summaries.
- Integration idea: learn from its feature boundaries and UX. Do not copy implementation without checking its license, attribution requirements, and any third-party notices.

### 3. TennoScope
- Repository: https://github.com/Deftera186/tennoscope
- Potential use: local-first relic reward overlay, platinum/ducat value comparison, and inventory-aware planning.
- Integration idea: inspect the project's architecture, supported platforms, and license before reusing code. Candidate feature inspiration: relic planner and local-first design.

### 4. Warframe world state
- Community project: https://github.com/WFCD/warframe-worldstate-data
- Potential use: time-limited world events, fissures, invasions, and rotating activities.
- Integration idea: fetch public data on a schedule, cache with timestamps, and show when the data was last updated.

### 5. Warframe drop tables
- Community source: https://drops.warframestat.us/
- Potential use: drop-source lookup and farm planning.
- Integration idea: normalize drop tables into a local read-only index; include source version and probability notes so the UI doesn't overstate expected results.

### 6. Warframe Market
- Website: https://warframe.market/
- Potential use: market prices and order-book context for item value estimates.
- Integration idea: keep market values clearly marked as estimates, include the retrieval time, and respect the site's current API rules and rate limits.

### 7. Official mission and item references
- Missions: https://wiki.warframe.com/w/Mission
- AABC rotations: https://wiki.warframe.com/w/AABC
- Potential use: explain mission objectives and reward rotations to players.

## What not to import

There are public repositories advertising AFK farming, randomized input, or anti-idle behavior. Their existence does not establish that their behavior is permitted or reliable. This project will not vendor or adapt scripts whose purpose is to make unattended gameplay appear active, evade inactivity checks, automate combat, or conceal bot behavior. Digital Extremes' support policy says it does not support automated play that removes human interaction and warns that AFK abuse can lead to penalties or removal of mission rewards:
- https://support.warframe.com/hc/en-us/articles/200287090-How-to-deal-with-Cheaters-AFKing-trolling
- https://support.warframe.com/hc/en-us/articles/360030014351-Third-Party-Software-and-You

## Proposed implementation plan

1. Build a data importer for WFCD metadata with source commit, timestamp, schema validation, and a generated local snapshot.
2. Add mission objectives, rotations, and drop-source lookup using clearly versioned data.
3. Add relic planner and item value estimates, keeping source and timestamp visible.
4. Add local config validation, structured logs, and offline unit tests.
5. Keep the companion separate from any game-input process. No memory writes, injection, aim assistance, ESP, anti-idle evasion, or unattended combat.

## License and provenance checklist

Before copying any code from a public repository:
- record the exact repository URL and commit SHA;
- read LICENSE and bundled third-party notices;
- preserve copyright and attribution notices;
- check dependencies and license compatibility;
- prefer consuming public data over copying large code modules;
- document any code adapted and its origin.

This shortlist is a research starting point, not a legal determination or a claim that each project is safe to run alongside the game.
