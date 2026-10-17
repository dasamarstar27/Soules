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

## Original text edition

The default page preserves the original 46 actions, grouped into top categories. Click an action or type its original number. Category tabs wrap to remain visible; you can also type a category name such as `inventory` or `crafting`. A live sidebar shows character stats, region, weather, equipment, effects, enemies, companions, progress and six save slots. The title menu contains Dictionary, Tutorial, Customise and Saves, with a separate Play / Continue button.

Start with only a Rusty Sword. Loose runes are one-use consumables. Binding a rune to a weapon consumes the loose rune and creates a permanent attachment: it cannot be removed, replaced or spent by attacking. Staff charges remain finite.

Automatic colours follow regions and structures; Customise also offers fixed themes and your own colours. Saves checkpoint at category menus. Reloading restores the last checkpoint, rather than a half-finished battle. Death ends the active run, clears its autosave and opens new character creation. Separate named save slots remain intact. Export important saves before clearing browser storage.

`original_game.py` contains the active original gameplay; `original_menus.py` groups its actions. `original_worker.py`, `original_sessions.py` and `original_ui.py` connect isolated game processes to the browser. `season_two.py` provides the elemental-village expansion. Untouched uploaded files remain under `legacy/`.

## Season Two and future plans

Unlock all main regions and defeat The Dreaming God in The Dreamscape to complete Chapter 1. The Creator is optional. Chapter 2 opens expanded services in the four existing hidden elemental villages: finite-stock shops, keepers, training, exclusive libraries, side quests and mana-powered elemental arts. Discovery remains rare; discovered villages can be revisited through Structures. See PLANNED_CHAPTER_2.md and SEASON_THREE_PLAN.md.

## Earlier browser edition

The previous streamlined interface remains available at `/edition`, with its own save format. Its brewing and fusion systems are preserved there; saves do not transfer between editions. The default original edition retains its original crafting rules and ingredient recipes. Some original optional systems remain limited or unfinished; this release does not claim a completed multiplayer or Creator campaign.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Browser smoke checks under `tests/browser_*.py` use Playwright and Chromium. The default text interface is checked by `tests/browser_original.py`. These are development checks, not dependencies needed to play.
