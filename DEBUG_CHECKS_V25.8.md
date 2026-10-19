# V25.8 debugging checks

Fixed three reproduced problems:

- Bandit Camp option 2 raised `NameError: check_level_up`. There were two camp definitions; the later one also omitted trade feedback. One camp now uses `gain_xp`, with regression checks both below and across a level-up threshold, inventory/payment feedback, capped recovery and invalid responses.
- A sidebar weapon selection changed from index 1 back to 0 after an idle refresh. Unchanged snapshots no longer rebuild the sidebar, and choices are preserved by character, item identity and index when its contents change. Browser checks deliberately wait through multiple polls before equipping/drinking.
- Village worker menu selection raised `TypeError: 'int' object is not callable`: its display loop replaced the `number` helper. Menu-driven regression checks place a paid materials order, collect it, and hire gatherers.

Validation:

- 247 unit tests passed, including combat, one-roll wandering, saves, rune pairs, crafting, worker resources and story gates.
- 576 structure/menu paths: 16 regions × 9 structure handlers × 4 main choices. Combat is mocked and nested choices cancel; this checks branch exceptions, not full combat balance or every nested action.
- Static scan of 59 root Python modules: no undefined-name or parse errors after the fixes. A separate review found no remaining imported callable names overwritten by local assignments and then called in those modules.
- Nine browser scripts passed, covering actual Bandit Camp story/level-up/trade/exit in desktop, Tablet and Easy reading; sidebar equip/drink; worker commissions; original controls/saves; regional forge combat and trading; clan raids/Structures; purchase Yes/No; wander dictionary/manual sidebar position; version UI; hosted tablet restart/recovery.

Repeatable commands from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python tests/structure_menu_audit.py
python tests/browser_camp.py
PYTHONPATH=. python tests/browser_player_qol.py
```

Browser scripts need Playwright and Chromium plus a game server on port 5000. The hosted browser check starts its own Gunicorn server after hosted requirements are installed. Pyflakes 3.4.0 was used as a development diagnostic, not added as a game dependency. These checks are not a claim that every possible item combination or playthrough has been exhaustively tested.
