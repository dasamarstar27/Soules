# Soules V25.11 — Echoes of the World Tree

**Play on a tablet without running a laptop:** deploy the online game once, then send Nanu its website link. [Tablet setup instructions](TABLET%20PLAY.txt).

[![Deploy Soules to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/dasamarstar27/Soules)

The button configures hosting; it is not a live game address. Render assigns the playable HTTPS link after you sign in and deploy. Tablet mode supplies button controls; the ZIP alone cannot execute Python on an iPad.


A playable, single-player browser edition of the uploaded SoulCrypt/Soules RPG. Monsters used to be rarer and peaceful; the Dreamscape boss is now sending hostile monsters to take over the world. Free the original fifteen regions and defeat The Dreaming God in The Dreamscape to finish Chapter 1. Season Two begins afterward with the Core Stabiliser sabotage. The Creator is not required to beat the original game.

## Play on your laptop

With Python 3.11+ installed, Windows users can double-click **Play Soules.bat**; Mac users can use **Play Soules.command**. The launcher prepares the dependencies on first launch and opens the game in a browser. Keep its window open while playing. It uses a stable local port (8765) to preserve browser save slots between launches. See START HERE.txt. An iPad needs a hosted version; this repository has not been deployed to a public website.

## Simple laptop edition

For a smaller game, open **[Play Soules Simple.html](simple/Play%20Soules%20Simple.html)** from the extracted folder, or double-click **Play Soules Simple.bat** on Windows. It opens directly in your browser, works offline and needs no Python. This is a new simplified edition inspired by early Soules, not a restored historical V15 release.

It keeps a character sidebar, dictionary, tutorial, 15 regions, combat, one-time guardians, equipment, four permanent rune bindings, basic forging, a village shop, Easy/Normal, colour choices and three save slots. The full edition keeps all its systems. Saves are separate: use Simple’s Export/Import to move between laptops or versions; export before moving or renaming the HTML file.

Full-game quarries now give **2 Stone + 1 regional metal**; timber yards give **2 Timber + 1 regional wood**. These go into construction supplies and crafting bags respectively. One trip per named site per 20-wander cycle, including Ironpeak’s dwarven quarry.

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

The default page preserves the original actions and adds the village directory and Adventures hub (49 actions total), grouped into top categories. The first menu shows numbered categories: 1 Explore, 2 Inventory & Equip, and so on. Choose a category to open its secondary numbered action menu; 0 returns to the main category menu. Category tabs also remain available. A live sidebar shows character stats, region, weather, equipment, effects, enemies, companions, progress and six save slots. The title menu contains Dictionary, Tutorial, Customise and Saves, with a separate Play / Continue button.

Start with only a Rusty Sword. Loose runes are one-use consumables. Binding a rune to a weapon consumes the loose rune and creates a permanent attachment: it cannot be removed, replaced or spent by attacking. Staff charges remain finite.

Automatic colours follow regions and structures; Customise also offers fixed themes and your own colours. Saves checkpoint at category menus. Reloading restores the last checkpoint, rather than a half-finished battle. Death ends the active run, clears its autosave and opens new character creation. Separate named save slots remain intact. Export important saves before clearing browser storage.

`original_game.py` contains the active original gameplay; `original_menus.py` groups its actions. `original_worker.py`, `original_sessions.py` and `original_ui.py` connect isolated game processes to the browser. `season_two.py` provides the elemental-village expansion. `village_life.py` defines local services, quality, village notes and repeat visits. Untouched uploaded files remain under `legacy/`.

Inventory offers sorting by name, attack/power, defence, element or sell value, with an optional secondary sort. Sorting changes the display order. Auto-sell duplicates is off initially; enable it in Inventory or sell duplicates once. It sells identical spare weapons, armour and staffs for souls, keeping an exact variant and protecting equipped or bound/imbued gear. Consumables and crafting materials stay in your bags. The setting and sort preferences persist in saves.

## Season Two and Season Three

Unlock all main regions and defeat The Dreaming God in The Dreamscape to complete Chapter 1. The Creator is optional. Chapter 2 opens expanded services in the four existing hidden elemental villages: finite-stock shops, keepers, training, exclusive libraries, side quests and mana-powered elemental arts. Discovery remains rare; discovered villages can be revisited through Structures. See SEASON_TWO_GUIDE.md and SEASON_THREE_GUIDE.md.

## Earlier browser edition

The previous streamlined interface remains available at `/edition`, with its own save format. Its brewing and fusion systems are preserved there; saves do not transfer between editions. The default original edition retains its original crafting rules and ingredient recipes. Optional menus now have playable progression in the default text edition. Community trading, guilds and arena ghosts share one running server; this is not live multiplayer combat or an account-synchronisation service.

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

The opening scene, early monster evidence, village conversations and sidebar objective begin Chapter One immediately. Story & Lore opens the journal. Chapter One stays focused on the Dreamscape invasion; Source sabotage is introduced after the Dreaming God's defeat. Season Two includes four keeper testimonies, a confrontation at the Broken Bridge and a repair ending using the clans’ harmonic knowledge while the cores stay guarded in their villages. See SEASON_TWO_GUIDE.md.

New characters start from 55 HP, 5 attack and 1 defence, with half-sized class starting bonuses and a Rusty Sword. A new Warrior has 70 HP, 7 base attack and 2 defence. Early Ranger and Necromancer damage skills scale with level. Existing saved character stats are preserved.

Five expandable features are active: the story journal, keeper conversations, crafting professions, recorded rumours and postgame Source anomalies. Their implemented follow-ups are described in FEATURE_GUIDE.md. Profession ranks come from successful paid/resource-consuming actions, cap at five, and add small forge/loom/tower bonuses or ingredient-preservation chances. Rumours do not automatically discover locations. Anomalies are available every ten postgame wanders; a collected fragment can restore up to 15 HP and 5 mana through the journal.

The full history is recorded in STORY_CANON.md: the Riftlands once separated the realms; the Dreamscape King corrupted the Sacred Temple's core energy; the elemental civilisations fought until four remained; their warriors sacrificed themselves to stabilise the power and banish him. The current reopening begins Chapter One. Its underlying cause is reserved for the overarching-antagonist reveal in Season Three. The Dreaming God is the existing boss name for the corrupted Dreamscape King.

## Village buildings and season timing

Attacks, village menus and other options follow automatically when you are near the bottom. Very long blocks and reading older text preserve your position; use Latest to jump down. Crimson Forge appears in the travel menu without a preliminary popup. Imbuing temples are available only in elemental villages. The Sacred Temple in Riftlands remains the story location and contains the stabiliser, not the four surviving cores.

Building level is separate from service quality. Better facilities start at Level 2; others start at Level 1. Village option 17 upgrades existing buildings to Level 5 using Timber, Stone, Iron fittings and souls. The one-roll gathering range can yield one building supply (10% of a full Normal wander, 15% on Easy where ingredients exist), and the upgrade menu converts carried wood or metal. Levels improve local service results and future restaurant stock capacity. These upgrades belong to each village and persist in saves.

Elian is an old man met in the first village visited and the grandson of one of the fallen warriors. At the Season One ending he warns that someone must have reopened the rift and understands core energy. Complete 20 side quests after the victory, then begin Season Two through the journal or mentor. Its opening is five months later in lore, without a real-time wait. Existing Season Two saves keep their progress. Blessings allow paid channeling at elemental villages without taking their protected cores.

## Complete two-normal-rune fusions

All 132 distinct normal rune types can be fused in unordered pairs, including two inventory copies of the same type: 8,778 combinations. A fused rune cannot be used as an ingredient. Each result retains its component abilities and gets a pair-specific named synergy. Synergies are generated from reusable mechanical families with deterministic strengths; they are not 8,778 individually hand-written combat systems. Compatible original named recipes are retained.

Dictionary → Fusions includes a two-rune ability preview. The original combat loop now uses the complete effect registry through original_magic.py, including periodic effects, stat changes, shields, reflection, lifesteal, control effects and expiry. Rage/Berserk gives +50% attack and -30% defence for three turns. Loose runes remain single-use; weapon-bound runes remain permanent.

ADDON_CATALOG_100.md lists the 100 addon designs now accessible through Adventures. IMPLEMENTATION_CHECKLIST.md records their implementation and checks.


## Village arrivals and development

New characters begin inside Old Village with Elian, the elderly grandson of a fallen warrior, and keeper conversations. Leave with **7** to reach the main categories. Existing saves resume normally. Starting equipment remains only the Rusty Sword.

There are **32 additional ordinary villages**, two in each region including the optional Creator's Realm. Villages have different service combinations, starting levels, food selections, prices and finite metal/wood/construction stocks. Ordinary villages never have an Imbuing Temple. Quarry, timber-yard and watch-post structure types are available throughout the world; watch posts reveal ordinary village routes, never hidden elemental villages.

Use **11** inside a village or **Edit note** in the sidebar to save a note, and **12 / Tags** for labels such as `cheap food`, `farming` or `good smith`. Explore → Village Directory filters names, regions, services, tags and notes and revisits discovered villages.

Each arrival counts once. A village independently improves a random existing building after **10–15 visits**, then chooses another interval. Levels stop at 5; fully developed settlements grant reputation instead. Reloading or browsing menus does not advance arrivals. Development history is village option **21**, also displayed in the sidebar.

Village option **17** spends gathered building materials to upgrade workshops. Option **19** buys local materials with visible prices and quantities; stock refreshes every 20 wanders. Quarries and timber yards provide finite construction supplies at that same exploration cadence. Option **20** offers the locally compatible selection from **100 named community construction projects**. Projects cost supplies and souls, grant local reputation, and every three for one service grant +1 effective service quality, capped at +3. These are 100 projects using shared construction mechanics, not 100 independently implemented gameplay systems. See [VILLAGE_PROJECTS_100.md](VILLAGE_PROJECTS_100.md).

## Protected ruins and the Riftlands temple

Every region contains ancient civilisation ruins. Searches have a 35% broken-core fragment chance, 25% tome chance and 40% empty result; one search per site per 20-wander cycle, with each kind recoverable once at that site. Finds live in a protected collection: they cannot be sold, salvaged or used for crafting or imbuing. Season Three uses their preserved memories to tune an expedition ward, without consuming the finds. The four surviving cores remain protected by their clans.

The Riftlands Source Temple sells portable Core Stabilisers for 300 souls and uses core energy to imbue a weapon or staff. A portable stabiliser is consumed. Old physical cores are consumed if used; a clan attunement channels energy while leaving the clan's core at home. Permanent bound runes survive imbuing.

The separate [100-addon catalogue](ADDON_CATALOG_100.md) is now accessible through World & Social → Adventures, projects & research. These activities are separate from the earlier 100 construction projects. [Implementation checklist](IMPLEMENTATION_CHECKLIST.md) records the code and validation coverage.

## Companion care and the complete field guide

Character → Companions now includes feeding and a regional food guide. Companions start at 100 hunger and lose 5 per wander. They eat food types stocked in their home region, even while travelling elsewhere. Feeding consumes one carried item and restores its normal hunger value; full companions, unsuitable food and cancellation keep your supplies. Below 30 hunger they rest from combat and stop earning battle XP, without leaving or dying.

Feeding restores hunger and grants no evolution XP. A companion must actually help win a battle to earn combat bond XP: 20 unlocks an Awakened form, and 60 unlocks an element-themed final form such as Sunfire Ember Fox. Ordinary victories grant 5 bond XP and original guardian victories grant 10. Juvenile battle companions help weakly; peaceful companions can earn credit by healing an injured player. Final forms strengthen passive combat support. Peaceful species also evolve and remain peaceful. Battle-level XP remains separate. Old saves gain the correct home region and full hunger on migration; subsequent care progress persists normally. Earth support now provides a temporary defence buff instead of permanently increasing base defence, and crystal companions have a working special move.

The current question is displayed at full adventure text size in the main story panel, above the action buttons. The answer box describes that question for assistive technology. Attacks and ordinary menus follow automatically near the bottom; very long blocks and reading older entries preserve your position.

Tutorial now covers starting, controls, survival, exploration, combat, equipment, runes and fusions, crafting/professions, alchemy, local economies, construction, companion evolution, ruins, temples, the chapter storyline, side quests, saves, appearance and all 48 actions plus the expanded systems and their requirements. Secret testing commands are omitted from player-facing help. Turning off testing access works at any pending game prompt and is saved at the next safe checkpoint; an already-open postgame shop also rechecks access before purchase.

Automatic following measures the rendered height of each new response, so wrapped paragraphs on a phone count as long text. It follows ordinary responses and option menus, including attacks and villages. Only very long batches—more than roughly 60 rendered lines or three journal screens, whichever is larger—stay put. It never jumps down while you are reading earlier entries.


Full hunger recovery: starting a wander at 100/100 hunger restores up to 3 HP, capped at maximum health, before the normal hunger drain. It does not trigger from menus, elapsed real time or combat turns and cannot revive a dead character.

Ordinary loot drops, arena prizes, cave caches and dungeon rewards now filter themed trinkets by region. Sea Pearls are native to Sunken Coast; common coins/relics remain global. Previously acquired items are retained. The tagged loot catalogue is the shared source for these original-game loot paths.


## Deferred systems release — 18 October 2026

**World & Social → Adventures, projects & research** opens the 100-addon catalogue: twenty side stories, settlement projects, artisan progression, field activities, tactical encounters, rune research, cooking and alchemy, relationships and journal tools. Shared engines support related activities; these are not 100 separate combat engines. The original 100 named construction projects remain available alongside them.

**Village workers (22)** accept supplied materials and a displayed labour fee. Smiths, weavers, enchanters and alchemists require the matching local service. Service level determines completion time and quality determines the result. Each Wander advances all pending work one shift. Inn rest advances two local shifts, productive local actions one; menus and reopening saves never advance work. Gatherers have two trips per village per 20-wander cycle. Apprentice batches pay every item's full cost. **Community activities (23)** includes worker assignments during defence, storage, roads, gardens, visiting specialists, festivals, votes, wells and refuge restoration. **Potion blending (24)** combines ordinary healing bottles or fortifies one with a native ingredient, capped at 120 healing.

**Character → Login streak** now claims one reward per Malaysian calendar date per saved character. A missed date resets the streak. Dictionary → Potions lists the ingredient recipes. Cosmetics, shared-instance guilds, calendar festivals, challenge modes, New Game+, adventure-pass tiers, rituals, NPC/ghost arena, trading, town facilities, faction contracts and vendors, finite treasure maps and mounts have working actions instead of catalogue-only menus.

**Season Three: Beyond the Broken Bridge** begins after the Season Two repair. A supplied expedition visits the Written Shore, Archive of Beginnings and Hall of Creation, with Sera's ward quest, protected fragment research, two permanent paired-element recipes, a confrontation and three custody endings. The optional Unwritten Vault follows. Only this chapter reveals the antagonist's goal to destroy the male Creator and take the Book and Pen of Creation. His underlying motive remains undisclosed; the Creator is capable of kindness and cruelty. The four clan cores stay at home.

Saves adds a five-checkpoint explicit-save timeline, ten local run chronicles and readable character-sheet export. Customise adds shortcut remapping, optional concise screen-reader combat announcements and a separate rune-sound volume, muted initially. Rune cards have 132 distinct seals. Tactical replays, quest routes, map notes, build comparison and optional statistics are in the journal tools. Local browser data and the server community database are separate; export important saves, and back up `instance/community.sqlite3` if moving a shared server.

The gameplay still requires only the dependencies in `requirements.txt`. Daily and weekly challenge counters now advance from real kills, XP, crafting and collection, with unique region clears and usable rewards. Boss Rush runs live tactical fights and saves its records. Adventures → Original workshops & collections also finishes advanced skills, material mastery, equipment collection bonuses, the legendary forge commission, prestige supplies, artifacts and fresh prestige ascension.

No paid service, real-time waiting or account is required. Public hosting has not been deployed. Download the ZIP, extract it, and run **Play Soules.bat** on Windows. Keep using the same browser and launcher address to retain slots.


### Clan defence, exploration reference and regional forge update

The sidebar keeps its manual scrollbar but never follows game updates automatically. The journal keeps its existing short-menu following behaviour. Dictionary adds Wandering, Weather, World events and Loot, including starting-roll probabilities and gathering follow-up encounter totals based on difficulty and the current character's discoveries, six weather types, eight cycling world events, regional drops and chosen exploration activities.

Elemental clan history and purchases return to the village menu; only leaving explicitly ends the visit. Discovered clans remain accessible through Structures. Automatic scenery matches each clan's element, including local services; fixed/custom themes are preserved. Both clan shops show ATK, DEF, staff power, food/potion recovery, elements, prices and remaining stock in consistent rows. The larger Season Two halls retain their progression gate.

**Protect Whispering Woods** begins during Season One: Elian conversation 4, Story journal 9 or clan option 8. Prepare 2 Timber + 1 Stone, survive three live attacks in the Woods, then report to Elian in Old Village. Optional discovered-clan volunteers can defend, gather, treat or repair. This does not require discovering the rare clans or replace the original Dreamscape ending. Clan option 7 opens repeatable, cycle-limited settlement raids with worker assignments; surviving cores stay with their clans.

**Ironpeak Mountains Quarry** has Bromm's dwarven bulk-metal counter: 8 metal types initially, 14 at level 10, all 20 at level 20 or Season Two, with cheap prices and finite quantities. **Village option 25** opens other regional specialists: woods/herbs, cloth, runes, food, hides or Riftlands weapon cores. Only the Ironpeak quarry traders are dwarves. Riftlands has eight of each ordinary core per shipment and a 25% shipment chance of one charged core; stocks refresh every 20 wanders without reopening/save rerolls.

**Crimson Forge** remains in Crimson Depths. Travel F enters the actual forge, also revisitable via Structures. Clear its three monster-held chambers to reclaim the hearth. Crafting hub C, specialist shop C or forge option 5 consumes one ordinary core and one compatible loose normal rune (or matching-energy fusion) to make a charged core. Only the reclaimed hearth spends that charged core, one metal and one wood to create a named elemental weapon with permanent native-core and sacrificed-rune abilities. Ordinary village forging stays physical. Clan cores and protected relics are never ingredients.

Charging rejects opposing elements, displays limits before selection and keeps supplies on invalid attempts. Phoenix/other hot cores reject water/tide and ice families; Glacier/Ocean reject hot runes; dark cores reject light families; Celestial rejects dark families; Nature rejects death/necrotic/inferno and Blight rejects life/harmony. Other normal elements remain allowed. Rare shop/debug charged cores follow the same rules. These restrictions do not change the existing two-normal-rune fusion catalogue. Charged cores are listed in Inventory; permanent elemental weapons cannot be auto-sold as duplicates or salvaged.


### Expanded dictionary and clearer action prompts

Dictionary → **All** indexes the game's full data catalogues, clan shop equipment, 100 addon activities, 100 village construction projects and tutorial systems. Search across names, regions, stats, abilities, materials and rarity rules; filter by category and page through results 60 at a time. Gear entries show level-dependent per-item loot probabilities, native loot lists its regional chance, and runes/staffs show regional and Divine Luck odds. Crafting/shop/quest availability is kept distinct from random rarity. The reference lists base creature stats and starting village services; live encounters and village development can change them. Generated custom items follow their recipes rather than an infinite enumeration.

Shared activity prompts now tell the player to type the number at the left and press Enter, with 0 returning. Adventures explains that displayed ID ranges are not answers. Community activity rows explain costs, consumed supplies, outcomes and limits before the player selects an action.

**Fusion core charging:** a loose fusion of exactly two normal runes can charge an ordinary core only when both original components match its elemental energy family. Compatibility is determined by elemental energy, not a numerical power total. Phoenix accepts fire-family pairs and rejects mixed fire/water; a neutral or incompatible component cannot be hidden by a matching partner. Every core lists its permitted fusion energies. The charge consumes the fusion and core once, and the resulting permanent weapon retains both component effects and the fusion synergy. Fusions remain invalid as ingredients for another fusion.


### Raid board and playability update

Raids now have 3–5 attackers by level, and the Woods quest has 2/3/4 monsters across its waves. A visual assignment board shows available villagers, levels, completed assignments and four clickable role cards with costs/effects. Text answers remain available.

Wandering starts with **one weighted main roll**. Normal: monster 51%, gathering 20%, structures 10%, events 10%, merchant 5%, companion 1%, peaceful 3%. Easy: 36%, 30%, 12%, 12%, 6%, 1%, 3%. Gathering keeps one native ingredient or building supply, then triggers exactly one follow-up: 70% ordinary monster / 30% undiscovered ordinary structure. Exhausted ordinary structure tickets become monsters, including gathering follow-ups. No recursive gathering or timer advancement occurs. With new ordinary structures remaining, total combat is 65% Normal / 57% Easy and structures/clans 16% / 21%, before event fights. Rare bounties and hidden clans remain in their main-roll ranges. Weather, hunger, work shifts and scheduled story/perk effects still update; a paid tracked target replaces the random draw. Dictionary shows both starting odds and encounter totals. This change applies to the full game; Simple retains its smaller original rules.

Potion controls are in Inventory & Equip and in the equipment sidebar alongside a quick weapon selector. Potion blends show their result and wait for Enter. Short potion output follows automatically; long journal output retains the existing reading policy. Food and scrolls are excluded from bulk loot sales. Takeaway food supports positive bulk quantities with full price/stock checks.

Weapon commissions require one metal, one ordinary core and one wood, including apprentice batches. The worker menu can instead quote paid finite village material stock. Every Wander advances all pending work one shift; inn rest advances two. Reputation 10 grants one free inn rest per 20-wander cycle. Three pets travel at once; additional recruits live in Old Village, whose sanctuary swaps the party. Home pets do not lose travelling hunger or gain remote combat XP.

Tablet mode can be toggled in the top bar and is automatically selected for detected tablet-size touch devices. It enlarges controls and adjusts the layout without automatically scrolling the sidebar.

New testing sessions keep a clean restore point; leaving testing restores the entire pre-test character, removing test items, crafted results and test progress. Older testing saves have no exact prior snapshot: catalogue test supplies are removed and a recovery copy remains in the exported JSON under `beta_legacy_recovery` and can also be downloaded through Saves → Export older testing recovery; genuine prior catalogue copies cannot be distinguished retrospectively. Keep a normal pre-test save for exact recovery.


### Easy reading and facility-aware village menus

**Easy reading** in the top bar is an optional presentation mode: clear sans-serif text (18–28px), larger controls, stronger contrast, less visual decoration/motion, labelled clickable submenu answers and direct Save / Load access. Standard presentation and game rules are preserved when switched off. Its text size is separate, and preferences stay in the browser. **Explain game words** opens a plain-language glossary. **Read latest aloud / Stop reading** use browser speech only when requested; selected text takes priority, otherwise the latest output and question are read (up to 6,000 characters). Voice and speed can be selected in Customise when supported by the device.

Village menus now list only facilities available locally: no harvest option without a farm, no blacksmith without a forge, no food/meal options without a restaurant, and no potion services without an alchemy lab. Mentor and sanctuary choices appear only in Old Village. Worker menus likewise omit missing specialists. Existing answer numbers stay stable, including gaps. Hidden unavailable actions retain their backend service guards.


### V25.2 — Hindi narration and named release folders

The packaged download is `releases/Soules-V25.2.zip`, extracting into `V25.2/`. Keep that folder together and open **Play Soules.bat** inside it. `VERSION` is the source of the browser/launcher release label; future packages use their own version folder. `python build_release.py` builds the versioned archive from tracked source files, excludes local saves/environments and earlier release ZIPs, and includes a SHA-256 source manifest.

**Hindi narration:** Settings / Customise → Narration language → **हिंदी · Hindi**, or press **हिंदी में सुनें** in the game. Soules automatically chooses an installed Hindi voice and translates the passage using the browser's on-device Translator API when available. This API and Hindi language-pair support vary by browser/device; downloading the voice/model may require Internet. Soules does not send passages to a translation API server. When automatic translation is unavailable, use the browser's **Translate page → Hindi**, select a translated passage, then read it aloud. Hindi already visible in the current journal can also be read directly. Hindi setup help explains Windows/iPad voice installation. Missing voices/translation produce instructions rather than English speech labelled as Hindi.

English and Hindi voice preferences are saved separately. Stop reading, new output or a language change cancels pending narration, including delayed translation. The written game, original answers and save format remain unchanged. `/api/version` reports the running release; the launcher asks you to close a different/older running version before reopening it.

Tablet mode and Easy reading use button answers, quantity steppers and preset names/notes without a keyboard. Save labels are automatic in these modes. Standard desktop mode retains free text input and custom names/notes.

### V25.3 · Easy and Normal difficulty

Choose Normal (the existing balance) or Easy when creating a character. Easy enemies have 25% less health and their direct strikes deal 40% less damage, including bosses and tactical/raid enemies. Rewards, starting supplies, encounter chances and the story stay the same; status damage and hazards remain dangerous, and death still ends the character. The choice travels in exports and save slots; existing saves without it stay Normal. Settings allows a change only at category/village menus outside combat and purchases. Easy reading and Tablet mode remain independent.

Build `releases/Soules-V25.3.zip` with `python build_release.py`; the extracted folder is `V25.3`.

The idea backlog is now [IDEAS.md](IDEAS.md), containing only unresolved work. Implemented addon and campaign documents have been renamed as catalogues/guides so they no longer appear to be pending features. Small changes use minor versions such as V25.3; major version numbers are reserved for major updates.

### V25.4 · Tablet hosting setup

`render.yaml` prepares a single-process, threaded Gunicorn service with an automatically generated session secret, secure cookies and four active browser sessions. Hosted dependencies are separate in `requirements-hosted.txt`, so the Windows launcher does not install Gunicorn. The `/health` readiness route is used by the host. This is deployment configuration and tested local hosting, not a claim of an already-deployed public site. The free deployment needs Internet, can sleep/restart and uses ephemeral local disk; portable browser saves and export/import remain the way to keep character progress. See `TABLET PLAY.txt` for the one-time owner setup and simple steps for Nanu.

### V25.5 · Version corner and older releases

The top corner shows the actual running release. Press it for published V25.4/V25.3/V25.2 downloads, checkpoint export and downgrade instructions. Older links are pinned to their published commits. Downloads do not change the current game or saves. Computer players extract a separate version folder, close their current server and launch the older folder. Hosted/tablet players need the website owner to deploy the chosen release commit through the host dashboard; that restarts the shared service for all players. Keep untouched save backups because older builds may not understand newer items or systems. Only builds with published archives appear; historic V21/V22 packages are not invented.

### V25.6 · Tablet purchase confirmations

Tablet and Easy reading modes now render Yes/No answers directly from the current question, including confirmations that arrive without a new printed story line. A confirmation takes priority over old item lists, quantities and naming text. Short `y/n` questions send `y` or `n`; `yes/no` questions send the full words. Enter-only questions get Continue. No cancels a merchant purchase, and Yes buys the selected item once. Character and NPC names are unchanged in this patch.

### V25.7 · One weighted wander outcome

Normal and Easy now share a single-draw encounter system with different weights, as listed above. There is no monster-first check followed by discovery checks. The independent construction-supply roll is removed from automatic wandering; building materials are one of the gathering results. Rare subtypes and event identities are already in the main table, so they do not require another outcome roll. Detail choices such as monster species, item identity, combat rolls, weather updates and player decisions are separate. Existing source-story scenes, companion perks, full-hunger regeneration and work shifts remain; no save conversion is needed.

### V25.8 · Camp and menu debugging

Bandit Camp option 2 now uses the normal XP/level-up function instead of calling a nonexistent function. The duplicate camp definition is removed, ingredient trades show their result, invalid choices reprompt, and rest reports actual capped recovery. Existing camp names and rewards are preserved. The worker menu no longer shadows its selection helper with the displayed option number, fixing placing/collecting orders and hiring gatherers. Sidebar weapon/potion selections survive polling and state refreshes, with unchanged snapshots avoiding unnecessary DOM replacement. See [DEBUG_CHECKS_V25.8.md](DEBUG_CHECKS_V25.8.md) for validation scope and the reusable menu audit.

### V25.11 · Four monster evolution stages

Each of the 30 ordinary species has four named forms at player levels 1, 5, 10 and 15: 120 forms total. HP, ATK and DEF grow within each stage and continue beyond level 15. Existing base names remain at level 1; distinct evolved names return at level 10. At level 10+, existing regional mini-bosses take 25% of the usual two-species/two-mini-boss pool and grow with level. Known-species tracked targets use the same evolution rules. Ordinary evolved attacks now use scaled ATK rather than the old flat 5–15 roll; stronger forms grant higher XP/souls. Easy retains its 25% enemy-health and 40% direct-damage reductions, and the one-roll wander tables are unchanged. Regional/story bosses keep their separate rules. Enemy cards show stage/level/ATK/DEF; **Dictionary → Evolutions** lists every chain. See [ENEMY_EVOLUTION.md](ENEMY_EVOLUTION.md) for sample stats and scaling scope.
