"""Exercise 576 structure/menu branches with combat mocked and nested choices cancelled.

Run: .venv/bin/python tests/structure_menu_audit.py
This finds branch exceptions; it is not a full combat or reward-balance simulation.
"""

from copy import deepcopy
from unittest.mock import patch
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import data, original_game as game, original_ui as ui
from original_worker import initial_player


def main():
    results = []
    functions = [
        "visit_library",
        "visit_arena",
        "visit_blacksmith",
        "visit_cave",
        "visit_graveyard",
        "visit_camp",
        "visit_shrine",
        "visit_dungeon",
        "visit_tower",
    ]
    for region in data.REGIONS + [data.SECRET_REGION]:
        for name in functions:
            for answer in ("1", "2", "3", "4"):
                p = initial_player({})
                game.player = p
                p.update(region=region, gold=10000, hp=10000, max_hp=10000)
                p["unlocked_regions"] = set(data.REGIONS + [data.SECRET_REGION])
                p["ingredients"] = data.REGION_INGREDIENTS.get(region, [])[:]
                p["weapons"] = deepcopy(data.WEAPONS[:2])
                p["weapon"] = p["weapons"][0]
                p["armours"] = deepcopy(data.ARMOURS[:2])
                p["armour"] = p["armours"][0]
                p["staffs"] = deepcopy(data.STAFFS[:2])
                p["cores"] = list(data.CORES)[:2]
                p["woods"] = list(data.WOODS)[:2]
                p["metals"] = list(data.METALS)[:2]
                ui.init_ui(p)
                ui.village = None
                try:
                    with patch(
                        "builtins.input", side_effect=[answer] + ["0"] * 30
                    ), patch("builtins.print"), patch.object(
                        game, "fight", return_value=True
                    ):
                        function = getattr(game, name)
                        structure = {
                            "name": "Audit " + name,
                            "type": name.removeprefix("visit_"),
                        }
                        (
                            function(structure)
                            if name == "visit_shrine"
                            else function(structure, region)
                        )
                    results.append(
                        dict(region=region, menu=name, choice=answer, passed=True)
                    )
                except Exception as error:
                    results.append(
                        dict(
                            region=region,
                            menu=name,
                            choice=answer,
                            error=type(error).__name__ + ": " + str(error),
                        )
                    )
    failures = [result for result in results if not result.get("passed")]
    print(len(results), "menu paths checked;", len(failures), "failures")
    for row in failures:
        print(row)
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
