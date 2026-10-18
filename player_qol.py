"""Safe inventory actions and the Old Village companion sanctuary."""

from copy import deepcopy
import data
from expansion_state import choose


def food(item):
    return bool(
        item.get("food")
        or "hunger" in item
        or item.get("name") in {f["name"] for f in data.FOOD_ITEMS}
    )


def loot(item):
    return (
        "value" in item
        and not food(item)
        and "turns" not in item
        and not item.get("protected")
    )


def drink(game, index):
    from food_addons import potion_effect

    p = game.player
    if type(index) is not int or not 0 <= index < len(p.get("potions", [])):
        return False, "Choose a carried potion."
    name = p["potions"][index]
    effect = potion_effect(p, name)
    if not effect:
        return False, "This potion has no usable recipe; bottle kept."
    if (effect.startswith("heal_") or effect == "blend") and p["hp"] >= p["max_hp"]:
        return False, "Already at full health. Potion kept."
    p["potions"].pop(index)
    game._apply_potion_effect(effect, name)
    return True, "Drank " + name + ". One bottle consumed."


def potion_menu(game):
    from food_addons import potion_effect, food_state

    while True:
        p = game.player
        potions = p.get("potions", [])
        rows = []
        for name in potions:
            effect = potion_effect(p, name)
            info = food_state(p).get("blends", {}).get(name, {})
            rows.append(
                name
                + " · "
                + (
                    "restores " + str(info["heal"]) + " HP"
                    if info
                    else str(effect).replace("_", " ")
                )
            )
        index = choose("USE A CARRIED POTION · ONE BOTTLE PER USE", rows)
        if index is None:
            return
        print(drink(game, index)[1])


def quick(game, text):
    parts = text.split()
    if len(parts) != 2:
        return "Choose an equipment or potion button."
    try:
        index = int(parts[1])
    except ValueError:
        return "Choose a numbered carried item."
    if parts[0] == "/equip":
        if not 0 <= index < len(game.player["weapons"]):
            return "Weapon no longer available."
        game.player["weapon"] = game.player["weapons"][index]
        return "Equipped " + game.player["weapon"]["name"] + "."
    if parts[0] == "/drink":
        return drink(game, index)[1]
    return "Unknown inventory action."


def sanctuary(game):
    import original_ui as ui

    if (
        not ui.village
        or ui.village["name"] != "Old Village"
        or game.player["region"] != "Whispering Woods"
    ):
        print("Visit Old Village in Whispering Woods to change your companion party.")
        return
    p = game.player
    while True:
        active = p.setdefault("companions", [])
        home = p.setdefault("home_companions", [])
        print(
            "Party " + str(len(active)) + "/3: " + ", ".join(c["name"] for c in active)
        )
        print(
            "Staying safely in Old Village: "
            + (", ".join(c["name"] for c in home) or "None")
        )
        choice = choose(
            "OLD VILLAGE COMPANION SANCTUARY",
            ["Send a party companion home", "Add a home companion to the party"],
        )
        if choice is None:
            return
        source, destination = (active, home) if choice == 0 else (home, active)
        if choice == 1 and len(active) >= 3:
            print("Party full. Send one home first.")
            continue
        index = choose("CHOOSE COMPANION", [c["name"] for c in source])
        if index is not None:
            pet = source.pop(index)
            destination.append(pet)
            print(
                pet["name"]
                + (
                    " is safe in Old Village."
                    if choice == 0
                    else " joined your travelling party."
                )
            )
