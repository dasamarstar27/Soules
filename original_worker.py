"""Run the original synchronous RPG behind a JSON input/output bridge."""

import builtins
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import original_game as game
import original_ui as ui
from data import CLASSES, STRUCTURES, SKILL_TREES, WEAPONS

wire = sys.stdout


def emit(event, **payload):
    wire.write(
        json.dumps(dict(event=event, **payload), ensure_ascii=True, allow_nan=False)
        + "\n"
    )
    wire.flush()


def output(*args, sep=" ", end="\n", file=None, flush=False):
    if file not in (None, sys.stdout):
        return builtins_print(*args, sep=sep, end=end, file=file, flush=flush)
    emit("output", text=sep.join(str(a) for a in args) + end)


def input_line(prompt=""):
    while True:
        if game.player.get("hp", 1) <= 0:
            raise ui.RunEnded()
        from artisan_addons import record_materials

        record_materials(game.player)
        from legacy_workshops import sync_sets

        sync_sets(game.player)
        from challenge_progress import observe_inventory

        observe_inventory(game.player)
        snapshot = ui.snapshot()
        from expansion_hooks import prompt as record_prompt

        record_prompt(game.player, prompt, snapshot)
        emit("prompt", prompt=prompt, snapshot=snapshot)
        line = sys.stdin.readline()
        if not line:
            raise EOFError("Browser session closed")
        body = json.loads(line)
        value = body["text"]
        # A mode switch never answers a pending purchase or consumes a turn.
        if value.strip().upper() == "SAMAR":
            from beta_testing import disable_beta

            disable_beta(game.player)
            continue
        if value.strip() == "/back":
            raise ui.ReturnToMenu()
        return value


NEW_PLAYER_TEMPLATE = deepcopy(game.player)


def initial_player(config):
    player = deepcopy(NEW_PLAYER_TEMPLATE)
    player.update(
        name=str(config.get("name", "Wanderer")).strip()[:24] or "Wanderer",
        structures={k: {"level": 1, "xp": 0} for k in STRUCTURES},
        current_location=game.REGIONS[0],
        crafted_armor=[],
        cloths=[],
        leathers=[],
        ingredients=[],
        skill_tree={k: {} for k in SKILL_TREES},
        boss_rush_stats={
            "total_runs": 0,
            "best_run_normal": 0,
            "best_run_hard": 0,
            "best_run_nightmare": 0,
            "highest_score": 0,
        },
        active_effects={},
        chapter=1,
    )
    if config.get("save"):
        player.update(deepcopy(config["save"]["player"]))
        player["unlocked_regions"] = set(player["unlocked_regions"])
    else:
        player.update(
            {"hp": 55, "max_hp": 55, "atk": 5, "def": 1, "speed": 5, "mana": 0}
        )
        player.pop("source_story", None)
        key = config.get("cls", "warrior")
        player["class_id"] = key
        for stat, value in CLASSES[key]["bonus"].items():
            player[stat] = player.get(stat, 0) + int(value * 0.5)
    if not config.get("save"):
        sword = deepcopy(WEAPONS[0])
        sword["name"] = "Rusty Sword"
        player["weapons"] = [sword]
        player["weapon"] = sword
        player["runes"] = []
        player["staffs"] = []
        player["armours"] = []
        player["inventory"] = []
        player["potions"] = []
    else:
        for equipped, owned in [("weapon", "weapons"), ("armour", "armours")]:
            item = player.get(equipped)
            if item:
                player[equipped] = next(
                    (v for v in player.get(owned, []) if v == item), item
                )
    from companion_care import normalise

    for companion in player.get("companions", []):
        normalise(companion, player["region"])
    from expansion_state import state

    state(player)
    player.pop("password_hash", None)
    return player


builtins_print = builtins.print


def structure_wrappers():
    from functools import wraps
    from data import ELEMENTAL_VILLAGES

    names = {
        "visit_village": "village",
        "visit_ruins": "ruins",
        "visit_shrine": "shrine",
        "visit_dungeon": "dungeon",
        "visit_tower": "tower",
        "visit_library": "library",
        "visit_arena": "arena",
        "visit_blacksmith": "forge",
        "visit_cave": "cave",
        "visit_graveyard": "graveyard",
        "visit_camp": "camp",
        "source_temple": "temple",
        "imbue_staff": "temple",
        "view_crafting_hub": "village",
        "_ingredient_brew_menu": "alchemy",
        "forge_weapon": "forge",
        "craft_armor": "loom",
        "craft_staff": "tower",
        "visit_elemental_village": "elemental",
    }

    def decorate(function, kind):
        @wraps(function)
        def wrapped(*args, **kwargs):
            previous = ui.location
            previous_village = ui.village
            structure = args[0] if args and isinstance(args[0], dict) else {}
            name = structure.get("name", function.__name__.replace("_", " ").title())
            if kind == "elemental":
                name = ELEMENTAL_VILLAGES.get(game.player["region"], {}).get(
                    "name", name
                )
            if function.__name__ == "visit_elemental_village":
                from village_life import profile

                ui.village = profile(game.player["region"], name, elemental=True)
            ui.location = dict(name=name, kind=kind)
            try:
                return function(*args, **kwargs)
            finally:
                ui.location = previous
                ui.village = previous_village

        return wrapped

    for name, kind in names.items():
        setattr(game, name, decorate(getattr(game, name), kind))


def main():
    config = json.loads(sys.stdin.readline())
    game.player = initial_player(config)
    game.SAVE_FILE = str(Path.cwd() / "soulcrypt_save.json")
    game.load_game = lambda: None
    structure_wrappers()
    builtins.print = output
    builtins.input = input_line
    try:
        print(
            "SOULES — your original text adventure. Every original numbered action is available in the category tabs."
        )
        print(
            "Choose a category, then click an action or type its number. During a submenu, answer the question in the story panel. Back to category safely leaves a submenu."
        )
        from source_story import opening

        opening(game.player)
        if not config.get("save"):
            ui.init_ui(game.player)
            ui.context("action", "explore")
            print(
                "You wake beneath the eaves of Old Village. Elian and the village keeper are here; speak to them before heading into the woods."
            )
            try:
                game.visit_village(
                    {"name": "Old Village", "type": "village"}, game.REGIONS[0]
                )
            except ui.ReturnToMenu:
                pass
        game.game()
    except ui.RunEnded:
        game.player["hp"] = 0
        ui.context("dead")
        print(
            "Your character has died. This journey is over. Create a new character to begin again."
        )
    except (EOFError, BrokenPipeError):
        pass
    except Exception as error:
        emit("error", message=f"{type(error).__name__}: {error}")
    finally:
        emit("exit", snapshot=ui.snapshot())


if __name__ == "__main__":
    main()
