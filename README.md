# Soules — Echoes of the World Tree

A playable, single-player browser edition of the uploaded SoulCrypt/Soules RPG. Explore the original fifteen regions, collect runes, weave their effects together, unlock all main regions, and defeat The Dreaming God in The Dreamscape to finish Chapter 1. Chapter 2 begins afterward as the postgame. The Creator is not required to beat the original game.

## Play on your laptop

With Python 3.11+ installed, Windows users can double-click **Play Soules.bat**; Mac users can use **Play Soules.command**. The launcher prepares the dependencies on first launch and opens the game in a browser. Keep its window open while playing. It uses a stable local port (8765) to preserve browser save slots between launches. See START HERE.txt. An iPad needs a hosted version; this repository has not been deployed to a public website.

## Run

Python 3.11+ (tested with Python 3.12). No Node packages, external services, API keys, or image downloads are needed.

```sh
cd /workspace/Soules
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

The Flask development server uses port **5000**. Set `PORT` to choose another port. `npm run dev` runs the same Python command after installing the Python dependencies. For a public deployment, use a production WSGI server with `app:app` and set a stable `SESSION_SECRET` outside the repository.

## Organized source files

`data.py` defines each catalog once, grouped into world/exploration/events; monster types/bosses; combat equipment/runes; companions/classes; food/ingredients/alchemy; villages/crafting/materials; loot/trade; story/quests; and optional content. Late extension blocks have been merged into the original lists and dictionaries. Both formerly overlapping achievement sets are retained in one dictionary keyed by achievement ID.

`game.py` groups exploration/travel/rest, combat/rewards, runes/fusion, alchemy, villages/shops, story, and save handling under labeled sections. Its action dispatcher routes to those systems. Detailed crafting rules live in `village.py`; brewing rules remain in `alchemy.py`. Untouched uploads remain under `legacy/` for reference.

## Village and chapter progression

Every village offers the Forge, Loom, Enchantment Tower, Alchemy Lab, Disenchantry, and Source Temple from one menu. No workstation requires traveling to its old special-region location. The Forge tempers attack, the Loom reinforces defense, the tower crafts castable staffs from two runes, the Source Temple infuses a staff with another rune, and the Disenchantry salvages runes/staffs for soul shards and gold. The Alchemy Lab opens the existing brewing screen. All costs and consumed items are shown in the village menu.

**Chapter 1** is the original game: unlock every main region, then defeat **The Dreaming God** in **The Dreamscape**. This opens **Chapter 2: After the Dream**, the postgame. Existing exploration, crafting, and discovery continue. Creator's Realm is optional postgame content in the data and is not a Chapter 1 victory requirement; a new playable Creator's Realm campaign is not implemented here.

## Main menu, tutorial, and saves

The game opens on a main menu with Play / Continue, New journey, a seven-step guided tutorial, save slots, the complete rune dictionary, fusion recipes, alchemy, the world map, and the effects dictionary. All gameplay uses buttons; no terminal commands are needed to play once the server is started.

**Save slots:** six named, independent snapshots are stored in this browser. Overwriting, loading over the current autosave, and deleting ask for confirmation. Slots survive new characters and page reloads. Use Export to keep a portable backup; clearing browser data clears slots and autosaves. Old browser-edition version 1 save files automatically migrate to version 2 without losing progress.

## Alchemy

Gather three random local ingredients outside battle; encounters also drop ingredients. The original 39 ingredient recipes are supported, and other pairs produce discoverable formulas. Every new experiment is written into that character's recipe book.

Mix exactly two things: two ingredients (including two copies of the same one), an ingredient and a potion, or two separate potion bottles. Infusion and blending preserve the component properties, with caps of 160 direct healing and four distinct buff effects. Toxic ingredients/potions retain their risks. Potion buffs last combat turns; the displayed descriptions show the adapted mechanics instead of the legacy “fights” durations.

Brewing with ingredients uses one empty bottle. Infusing reuses the potion bottle; blending two returns a spare. Drinking returns an empty bottle. You can move the original quick-heal field draughts to the mixing shelf to infuse or blend them too.

The apothecary sells five original potion types and empty bottles. Its limited stock refreshes every three gatherings, never simply on page reload. Potions can be drunk outside battle or as one combat action. Dream Vial requires an enemy.

## Play

- **Adventure:** explore for gold, XP, a rune, and soul shards. Rest outside battle for free. Challenge a region guardian to unlock the next region.
- **Combat:** attack, invoke any owned rune, guard to recover mana and halve incoming damage, heal, cleanse, or flee a normal encounter. Guardians have three phases. Death preserves inventory; rest to recover.
- **Rune collection:** bind up to two runes. Each has a 35% chance to trigger when attacking. Casting consumes mana. The class choices trade mana, vitality/defense, and attack power.
- **Fusion altar:** select two inventory copies and preview the result. Every pair works, including two copies of the same type and already-fused runes. One soul shard and the inputs are consumed. All distinct component effects are retained. The 132 distinct rune types give **8,778 unordered base pairings including same-type pairs**, plus recursive combinations. There are **39 named recipes**, including a three-rune recipe. The old `Fire Rune` and `Reality Rune` recipe names resolve to `Flame Rune` and `Cosmic Rune`.
- **Codex:** search all **144 effects** and their exact mechanics. Buffs change effective stats temporarily. Statuses tick before expiring, and cleansing removes negative effects without removing buffs. Day/night changes every six combat turns.
- **World map:** unlock every main region and defeat The Dreaming God to finish Chapter 1. Exploration remains available in Chapter 2 afterward.

Area and chain effects concentrate their damage on the single opponent in this edition. Infinite boss effects now have finite durations; banish and execution damage guardians instead of instantly killing them. Bosses and XP were rebalanced for a playable region progression. Duplicate effects within fusions refresh rather than stacking exponentially.

## Saves

Progress automatically saves to this browser's local storage and restores on reload. **Export save** downloads a portable JSON backup. **Import save** validates and restores it, including an active encounter, ingredients, potion shelf, recipe discoveries, tutorial progress, and shop stock. On mobile, both actions are in the character menu at the top right. New journey replaces the current autosave; save in one of the six named slots first to keep multiple characters. Browser data clearing removes the local autosave, so retain exported backups.

Server-side sessions are isolated and held in memory. JSON exports or the browser autosave restore them after a restart. This is a single-player application, with no live multiplayer, guild service, or online economy.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
node --check static/app.js
```

Tests cover every rune cast, every base pair fusion, named recipe reachability, recursive and three-rune fusions, effect lifecycles, cures, resurrection, save validation, session isolation, and the campaign ending. Browser checks also exercise combat, bindings, fusion, search, navigation, mobile layout, autosave reload, and save export/import. To repeat them with Playwright and system Chromium installed, run `python3 tests/browser_smoke.py` , `python3 tests/browser_alchemy.py`, and `python3 tests/browser_village.py` while the app is running; screenshots are written under `/tmp/soules-checks/`.

## Project layout

- `app.py`: Flask routes, isolated sessions, transactional actions, and JSON save import/export.
- `game.py`: grouped exploration, combat, chapter progression, inventory, and fusion rules.
- `village.py`: the shared village crafting workstations.
- `alchemy.py`: gathering, original recipes, experimental mixtures, potion effects, and shop stock.
- `effects.py`: authoritative combat-effect registry and shared effect lifecycle.
- `data.py`, `status_effects.py`, `recipes.py`: original content and named recipes.
- `templates/`, `static/`: responsive UI and locally drawn forest illustration.
- `legacy/`: untouched copies of all seven uploads, including the original terminal game and Pygame UI. Personal save/account files are excluded from GitHub. The old `package.json` uses missing workspace dependencies and is retained only for reference.

The uploaded `soulcrypt_save.json` is malformed (including missing commas/braces). It is preserved locally unchanged in `legacy/`, excluded from GitHub because it contains personal account data, and not silently repaired or imported into the new schema. The archived terminal game's additional menus and unfinished systems are preserved for future development; this browser edition implements the complete exploration/combat/rune-fusion campaign described above.
