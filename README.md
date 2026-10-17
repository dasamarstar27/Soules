# Soules — Echoes of the World Tree

A playable, single-player browser edition of the uploaded SoulCrypt/Soules RPG. Monsters used to be rarer and peaceful; the Dreamscape boss is now sending hostile monsters to take over the world. Free the original fifteen regions and defeat The Dreaming God in The Dreamscape to finish Chapter 1. Season Two begins afterward with the Core Stabiliser sabotage. The Creator is not required to beat the original game.

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

## Original text edition

The default page preserves the original 46 actions, grouped into top categories. The first menu shows numbered categories: 1 Explore, 2 Inventory & Equip, and so on. Choose a category to open its secondary numbered action menu; 0 returns to the main category menu. Category tabs also remain available. A live sidebar shows character stats, region, weather, equipment, effects, enemies, companions, progress and six save slots. The title menu contains Dictionary, Tutorial, Customise and Saves, with a separate Play / Continue button.

Start with only a Rusty Sword. Loose runes are one-use consumables. Binding a rune to a weapon consumes the loose rune and creates a permanent attachment: it cannot be removed, replaced or spent by attacking. Staff charges remain finite.

Automatic colours follow regions and structures; Customise also offers fixed themes and your own colours. Saves checkpoint at category menus. Reloading restores the last checkpoint, rather than a half-finished battle. Death ends the active run, clears its autosave and opens new character creation. Separate named save slots remain intact. Export important saves before clearing browser storage.

`original_game.py` contains the active original gameplay; `original_menus.py` groups its actions. `original_worker.py`, `original_sessions.py` and `original_ui.py` connect isolated game processes to the browser. `season_two.py` provides the elemental-village expansion. `village_life.py` defines local services, quality, village notes and repeat visits. Untouched uploaded files remain under `legacy/`.

Inventory offers sorting by name, attack/power, defence, element or sell value, with an optional secondary sort. Sorting changes the display order. Auto-sell duplicates is off initially; enable it in Inventory or sell duplicates once. It sells identical spare weapons, armour and staffs for souls, keeping an exact variant and protecting equipped or bound/imbued gear. Consumables and crafting materials stay in your bags. The setting and sort preferences persist in saves.

## Season Two and future plans

Unlock all main regions and defeat The Dreaming God in The Dreamscape to complete Chapter 1. The Creator is optional. Chapter 2 opens expanded services in the four existing hidden elemental villages: finite-stock shops, keepers, training, exclusive libraries, side quests and mana-powered elemental arts. Discovery remains rare; discovered villages can be revisited through Structures. See PLANNED_CHAPTER_2.md and SEASON_THREE_PLAN.md.

## Earlier browser edition

The previous streamlined interface remains available at `/edition`, with its own save format. Its brewing and fusion systems are preserved there; saves do not transfer between editions. The default original edition retains its original crafting rules and ingredient recipes. Some original optional systems remain limited or unfinished; this release does not claim a completed multiplayer or Creator campaign.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Browser smoke checks under `tests/browser_*.py` use Playwright and Chromium. The default text interface is checked by `tests/browser_original.py`. These are development checks, not dependencies needed to play.

## Everyday conveniences

1. Press `/` outside an input to focus the command box.
2. Up/Down recalls session command history and restores your draft.
3. Escape uses Back when leaving the current prompt is allowed.
4. Recall Last fills your previous command without sending it.
5. Clear Journal clears the visible log without changing progress.
6. Copy Journal copies the text for sharing or bug reports.
7. Latest jumps to the newest journal output.
8. Compact Sidebar reduces spacing and persists across reloads.
9. A low-health warning appears at 25% HP or below.
10. Inventory search filters names, elements and effects.
11. Identical inventory entries show quantities in one line.
12. Favourite item names receive a star and are protected from auto-sell.

Inventory options 8 and 9 manage favourites and search. Blank search shows everything again. Scroll elements and attack/defence buffs are included when sorting.

## Village life update

Villages have stable specialties rather than identical workstations. Farming villages offer cheap food and productive plots; forge settlements have strong smiths and towers but may lack restaurants. Market towns excel at trade, mountain villages at looms, and sanctuaries at alchemy, healing and imbuing. The sidebar lists each available service, its quality and exact benefits. Missing crafting benches cannot be used through a global shortcut.

Ten connected additions:

1. Different local services and crafting benches.
2. Basic, Skilled and Excellent quality with actual crafting, healing, harvest and pricing differences.
3. Restaurants with takeaway food and freshly cooked meals.
4. Saved villages with editable notes.
5. Custom village tags such as cheap food, farming or good loom.
6. A directory searchable by name, region, service, specialty, tag or note.
7. Direct return visits to discovered villages in unlocked regions.
8. Harvestable village farms with finite yields and regrowth.
9. Ingredient errands that grant reputation and food discounts, capped at 10%.
10. Persistent food stock, restock/regrowth timers and sidebar availability.

Find the directory under Explore or in the sidebar. Village records, bookmarks, tags, reputation and supplies belong to each character and persist in save slots/exports. Food restocks and farms regrow at each 20-wander milestone; reopening the menu or reloading does not refill them. The elemental villages retain their core encounters and Season Two services, with local village services accessible from their expanded menu.

## Story and character progression

The opening scene, early monster evidence, village conversations and sidebar objective begin Chapter One immediately. Story & Lore opens the journal. Chapter One stays focused on the Dreamscape invasion; Source sabotage is introduced after the Dreaming God's defeat. Season Two includes four keeper testimonies, a confrontation at the Broken Bridge and a repair ending using the clans’ harmonic knowledge while the cores stay guarded in their villages. See PLANNED_CHAPTER_2.md.

New characters start from 55 HP, 5 attack and 1 defence, with half-sized class starting bonuses and a Rusty Sword. A new Warrior has 70 HP, 7 base attack and 2 defence. Early Ranger and Necromancer damage skills scale with level. Existing saved character stats are preserved.

Five expandable features are active: the story journal, keeper conversations, crafting professions, recorded rumours and postgame Source anomalies. Their follow-up plans are in EXPANDABLE_FEATURES_PLAN.md. Profession ranks come from successful paid/resource-consuming actions, cap at five, and add small forge/loom/tower bonuses or ingredient-preservation chances. Rumours do not automatically discover locations. Anomalies are available every ten postgame wanders; a collected fragment can restore up to 15 HP and 5 mana through the journal.

The full history is recorded in STORY_CANON.md: the Riftlands once separated the realms; the Dreamscape King corrupted the Sacred Temple's core energy; the elemental civilisations fought until four remained; their warriors sacrificed themselves to stabilise the power and banish him. The current reopening begins Chapter One. Its underlying cause is reserved for the overarching-antagonist reveal in Season Three. The Dreaming God is the existing boss name for the corrupted Dreamscape King.

## Village buildings and season timing

Attacks, village menus and other options follow automatically when you are near the bottom. Very long blocks and reading older text preserve your position; use Latest to jump down. Crimson Forge appears in the travel menu without a preliminary popup. Imbuing temples are available only in elemental villages. The Sacred Temple in Riftlands remains the story location and contains the stabiliser, not the four surviving cores.

Building level is separate from service quality. Better facilities start at Level 2; others start at Level 1. Village option 17 upgrades existing buildings to Level 5 using Timber, Stone, Iron fittings and souls. Wandering has a separate 25% chance to find a building supply, and the upgrade menu converts carried wood or metal. Levels improve local service results and future restaurant stock capacity. These upgrades belong to each village and persist in saves.

Elian is an old man met in the first village visited and the grandson of one of the fallen warriors. At the Season One ending he warns that someone must have reopened the rift and understands core energy. Complete 20 side quests after the victory, then begin Season Two through the journal or mentor. Its opening is five months later in lore, without a real-time wait. Existing Season Two saves keep their progress. Blessings allow paid channeling at elemental villages without taking their protected cores.

## Complete two-normal-rune fusions

All 132 distinct normal rune types can be fused in unordered pairs, including two inventory copies of the same type: 8,778 combinations. A fused rune cannot be used as an ingredient. Each result retains its component abilities and gets a pair-specific named synergy. Synergies are generated from reusable mechanical families with deterministic strengths; they are not 8,778 individually hand-written combat systems. Compatible original named recipes are retained.

Dictionary → Fusions includes a two-rune ability preview. The original combat loop now uses the complete effect registry through original_magic.py, including periodic effects, stat changes, shields, reflection, lifesteal, control effects and expiry. Rage/Berserk gives +50% attack and -30% defence for three turns. Loose runes remain single-use; weapon-bound runes remain permanent.

ADDON_IDEAS_100.md contains exactly 100 future addon designs. None of those proposals has been implemented as part of that planning document.


## Village arrivals and development

New characters begin inside Old Village with Elian, the elderly grandson of a fallen warrior, and keeper conversations. Leave with **7** to reach the main categories. Existing saves resume normally. Starting equipment remains only the Rusty Sword.

There are **32 additional ordinary villages**, two in each region including the optional Creator's Realm. Villages have different service combinations, starting levels, food selections, prices and finite metal/wood/construction stocks. Ordinary villages never have an Imbuing Temple. Quarry, timber-yard and watch-post structure types are available throughout the world; watch posts reveal ordinary village routes, never hidden elemental villages.

Use **11** inside a village or **Edit note** in the sidebar to save a note, and **12 / Tags** for labels such as `cheap food`, `farming` or `good smith`. Explore → Village Directory filters names, regions, services, tags and notes and revisits discovered villages.

Each arrival counts once. A village independently improves a random existing building after **10–15 visits**, then chooses another interval. Levels stop at 5; fully developed settlements grant reputation instead. Reloading or browsing menus does not advance arrivals. Development history is village option **21**, also displayed in the sidebar.

Village option **17** spends gathered building materials to upgrade workshops. Option **19** buys local materials with visible prices and quantities; stock refreshes every 20 wanders. Quarries and timber yards provide finite construction supplies at that same exploration cadence. Option **20** offers the locally compatible selection from **100 named community construction projects**. Projects cost supplies and souls, grant local reputation, and every three for one service grant +1 effective service quality, capped at +3. These are 100 projects using shared construction mechanics, not 100 independently implemented gameplay systems. See [VILLAGE_PROJECTS_100.md](VILLAGE_PROJECTS_100.md).

## Protected ruins and the Riftlands temple

Every region contains ancient civilisation ruins. Searches have a 35% broken-core fragment chance, 25% tome chance and 40% empty result; one search per site per 20-wander cycle, with each kind recoverable once at that site. Finds live in a protected collection: they cannot be sold, salvaged or used for crafting or imbuing. Their later purpose is reserved for Season Three. The four surviving cores remain protected by their clans.

The Riftlands Source Temple sells portable Core Stabilisers for 300 souls and uses core energy to imbue a weapon or staff. A portable stabiliser is consumed. Old physical cores are consumed if used; a clan attunement channels energy while leaving the clan's core at home. Permanent bound runes survive imbuing.

The separate [100-addon design backlog](ADDON_IDEAS_100.md) remains a broader expansion plan; it has not all been implemented by the village construction pack. Season Three's full campaign remains planned.

## Companion care and the complete field guide

Character → Companions now includes feeding and a regional food guide. Companions start at 100 hunger and lose 5 per wander. They eat food types stocked in their home region, even while travelling elsewhere. Feeding consumes one carried item and restores its normal hunger value; full companions, unsuitable food and cancellation keep your supplies. Below 30 hunger they rest from combat and stop earning battle XP, without leaving or dying.

Each successful meal grants one evolution XP. Three meals unlock an Awakened form at stage 1; six unlock an element-themed final form at stage 2, such as Sunfire Ember Fox. Final forms strengthen passive combat support. Peaceful species also evolve and remain peaceful. Battle-level XP remains separate. Old saves gain the correct home region and full hunger on migration; subsequent care progress persists normally. Earth support now provides a temporary defence buff instead of permanently increasing base defence, and crystal companions have a working special move.

The current question is displayed at full adventure text size in the main story panel, above the action buttons. The answer box describes that question for assistive technology. Attacks and ordinary menus follow automatically near the bottom; very long blocks and reading older entries preserve your position.

Tutorial now covers starting, controls, survival, exploration, combat, equipment, runes and fusions, crafting/professions, alchemy, local economies, construction, companion evolution, ruins, temples, the chapter storyline, side quests, saves, appearance and all 47 original actions. It identifies original preview menus honestly. Secret testing commands are omitted from player-facing help. Turning off testing access works at any pending game prompt and is saved at the next safe checkpoint; an already-open postgame shop also rechecks access before purchase.

Automatic following measures the rendered height of each new response, so wrapped paragraphs on a phone count as long text. It follows ordinary responses and option menus, including attacks and villages. Only very long batches—more than roughly 60 rendered lines or three journal screens, whichever is larger—stay put. It never jumps down while you are reading earlier entries.
