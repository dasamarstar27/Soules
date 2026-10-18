"""Ironpeak dwarven supplies and the reclaimed Crimson elemental forge."""

from copy import deepcopy
import data
import effects
from expansion_state import state, choose, pay


def forge_state(player):
    return state(player)["activities"].setdefault(
        "crimson_forge", dict(waves=0, cleared=False)
    )


def clear_wave(game):
    p = game.player
    progress = forge_state(p)
    if p["region"] != "Crimson Depths":
        return False, "Travel to Crimson Depths first."
    if progress["cleared"]:
        return (
            False,
            "The forge is already reclaimed; no monsters or rewards are regenerated.",
        )
    wave = progress["waves"] + 1
    names = [
        "Cinder Infestation",
        "Corrupted Bellows Guardian",
        "Dreamscape Forge Warden",
    ]
    foe = dict(
        name=names[wave - 1],
        hp=40 + wave * 15 + p["level"] * 3,
        atk=8 + wave * 2 + p["level"] // 2,
        **{"def": wave + 1},
        xp=20 + wave * 5,
        gold=15 + wave * 5,
    )
    from expansion_combat import encounter

    print(
        "CRIMSON FORGE · CLEARING "
        + str(wave)
        + "/3. Surviving progress is saved between waves."
    )
    if not encounter(game, [foe], terrain="Crimson Forge"):
        return False, "The infestation still holds this chamber."
    progress["waves"] = wave
    if wave == 3:
        progress["cleared"] = True
        return (
            True,
            "The Crimson Forge is clear. Its elemental hearth can now bind a charged core’s abilities into a custom weapon.",
        )
    return True, "Chamber cleared. Rest or gather supplies before the next fight."


def craft(player, core, metal, wood, name):
    if player["region"] != "Crimson Depths" or not forge_state(player)["cleared"]:
        return False, "Clear all three Crimson Forge chambers first."
    if (
        not isinstance(core, dict)
        or core not in player.get("charged_cores", [])
        or core.get("core_name") not in data.CORES
        or not core.get("charged")
    ):
        return (
            False,
            "Sacrifice a compatible loose rune into an ordinary core first. The elemental hearth requires a carried charged core.",
        )
    from core_charging import compatible, CORE_ELEMENTS

    core_name = core["core_name"]
    if not compatible(core_name, core.get("rune")):
        return False, "This core and rune have incompatible elements. Materials kept."
    if metal not in data.METALS or wood not in data.WOODS:
        return (
            False,
            "Choose ordinary forge materials. Protected clan cores and broken-core relics cannot be spent.",
        )
    if any(
        item not in player.get(bag, [])
        for item, bag in [(core, "charged_cores"), (metal, "metals"), (wood, "woods")]
    ):
        return False, "Carry one of each selected core, metal and wood."
    name = name.strip()[:40] or data.CORES[core_name]["prefix"] + " " + metal + " Blade"
    core_effect = data.CORES[core_name]["effect"]
    handle_bonus = min(
        3,
        1
        + sum(
            value for value in data.WOODS[wood].values() if type(value) in (int, float)
        )
        // 10,
    )
    item = dict(
        name=name,
        tier="crafted",
        atk=15 + data.METALS[metal].get("atk", 0) + int(handle_bonus),
        value=50 + data.METALS[metal].get("atk", 0) * 2,
        materials={"core": core_name, "metal": metal, "wood": wood},
        elemental_charged=True,
        elemental_core=core_name,
        forge_core_rune=deepcopy(core["rune"]),
        forge_core_effect=core_effect,
        element=CORE_ELEMENTS[core_name],
        crafted_at="Crimson Forge",
    )
    for resource, bag in [(core, "charged_cores"), (metal, "metals"), (wood, "woods")]:
        player[bag].remove(resource)
    from artisan_addons import apply_traits

    apply_traits(player, item, "smithing")
    player.setdefault("weapons", []).append(item)
    from source_story import craft_xp

    craft_xp(player, "smithing")
    return (
        True,
        name
        + " forged. Permanent core ability: "
        + effects.EFFECTS[core_effect]["name"]
        + " — "
        + effects.EFFECTS[core_effect]["description"]
        + "; sacrificed rune: "
        + core["rune"]["name"]
        + ". Both innate abilities are permanent. Ordinary rune binding remains a separate permanent slot.",
    )


def forge_menu(game):
    p = game.player
    if p["region"] != "Crimson Depths":
        print("The Crimson Forge stands in Crimson Depths.")
        return
    found = p.setdefault("discovered_structures", {}).setdefault("Crimson Depths", [])
    if "Crimson Forge" not in found:
        found.append("Crimson Forge")
    progress = forge_state(p)
    while True:
        print("\n--- CRIMSON FORGE · ELEMENTAL HEARTH ---")
        print(
            f'Chambers cleared: {progress["waves"]}/3 · '
            + ("Hearth ready" if progress["cleared"] else "Monsters block the hearth")
        )
        index = choose(
            "CRIMSON FORGE",
            [
                "Fight to clear the next chamber",
                "Create a custom elemental weapon",
                "Reinforce gear using a forge-core drop",
                "Read core abilities",
                "Sacrifice a rune to charge a weapon core",
            ],
        )
        if index is None:
            return
        if index == 0:
            print(clear_wave(game)[1])
        elif index == 1:
            if not progress["cleared"]:
                print("Clear the three monster-held chambers before using the hearth.")
                continue
            cores = p.get("charged_cores", [])
            chosen = choose(
                "CHARGED CORES · ONLY THESE WORK IN THE ELEMENTAL HEARTH",
                [c["name"] for c in cores],
            )
            if chosen is None:
                continue
            selected = [cores[chosen]]
            for title, bag, catalog in [
                ("METAL", "metals", data.METALS),
                ("WOOD", "woods", data.WOODS),
            ]:
                pool = list(dict.fromkeys(x for x in p.get(bag, []) if x in catalog))
                choice = choose(title, pool)
                if choice is None:
                    break
                selected.append(pool[choice])
            if len(selected) != 3:
                continue
            name = input(
                "Name your elemental weapon (blank chooses a core-themed name) > "
            )
            print(craft(p, *selected, name)[1])
        elif index == 2:
            if not progress["cleared"]:
                print("Reclaim the forge before reinforcing gear.")
                continue
            game._reinforce_crimson_gear()
        elif index == 4:
            from core_charging import menu

            menu(game)
        elif index == 3:
            from core_charging import limits

            for name, info in data.CORES.items():
                print(
                    name
                    + " → "
                    + effects.EFFECTS[info["effect"]]["name"]
                    + ": "
                    + effects.EFFECTS[info["effect"]]["description"]
                    + " | "
                    + limits(name)
                )
            print(
                "Only the reclaimed Crimson hearth grants these innate abilities. Ordinary village forges use core, metal and wood for physical equipment. First sacrifice a compatible normal rune or matching-energy fusion into an ordinary core to charge it. That charged core can only be spent here, with a metal and a wood. Neither a protected fragment nor a clan’s surviving core can be used."
            )


def dwarven_goods(player):
    maximum = (
        20
        if player.get("chapter", 1) >= 2 or player["level"] >= 20
        else 14 if player["level"] >= 10 else 8
    )
    return [
        (
            name,
            max(5, round(info.get("atk", 5) * 0.6)),
            30 if index < 2 else 15 if index < 8 else 8,
        )
        for index, (name, info) in enumerate(list(data.METALS.items())[:maximum])
    ]


def dwarven_market(game):
    p = game.player
    progress = state(p)["activities"].setdefault("dwarven_market", {})
    cycle = p.get("wander_count", 0) // 20
    goods = dwarven_goods(p)
    if progress.get("cycle") != cycle:
        progress.update(cycle=cycle, stock={})
    for name, _, amount in goods:
        progress["stock"].setdefault(name, amount)
    while True:
        index = choose(
            "BROMM’S DWARVEN METAL COUNTER · BULK PRICES",
            [
                f'{name} · {price} souls each · {progress["stock"][name]} left'
                for name, price, _ in goods
            ],
        )
        if index is None:
            return
        name, price, _ = goods[index]
        left = progress["stock"][name]
        if not left:
            print("Sold out until the next 20-wander restock.")
            continue
        try:
            quantity = int(input(f"Quantity (1–{left}, 0 cancels) > "))
        except ValueError:
            print("Enter a whole quantity.")
            continue
        if quantity == 0:
            continue
        if not 1 <= quantity <= left:
            print("Choose a positive quantity within the displayed stock.")
            continue
        total = quantity * price
        if not pay(p, total):
            print("Need " + str(total) + " souls and an allowed purchasing mode.")
            continue
        p.setdefault("metals", []).extend([name] * quantity)
        progress["stock"][name] -= quantity
        print(
            f"Bought {quantity} {name} for {total} souls. Stock is shared across this character’s visits and saves."
        )


def dwarven_quarry(game, structure):
    p = game.player
    while True:
        index = choose(
            "IRONPEAK QUARRY · THE STONEBEARD MINERS",
            [
                "Gather 2 Stone (one trip per 20-wander cycle)",
                "Buy cheap metals from Bromm",
                "Talk to the dwarven miners",
                "Ask about the Crimson Forge",
            ],
        )
        if index is None:
            return
        if index == 0:
            key = "Ironpeak Mountains::" + structure["name"]
            cycle = p.get("wander_count", 0) // 20
            visits = p.setdefault("work_sites", {})
            if visits.get(key) == cycle:
                print("This seam needs the next restock cycle.")
                continue
            visits[key] = cycle
            bag = p.setdefault("building_materials", {})
            bag["Stone"] = bag.get("Stone", 0) + 2
            print("The dwarves show you a safe seam. Gathered 2 Stone.")
        elif index == 1:
            dwarven_market(game)
        elif index == 2:
            print(
                'Bromm Stonebeard: "We dwarves trade by the wagonload. Eight metal types to start; fourteen at level 10, all twenty at level 20 or Season Two. Our counters restock every twenty wanders. The ancient elemental cores are not for sale."'
            )
        elif index == 4:
            from core_charging import menu

            menu(game)
        elif index == 3:
            print(
                'Bromm: "The Crimson Forge is in Crimson Depths. Clear the monsters from its three chambers, then its hearth can awaken the ability in an ordinary forge core. A village smith makes sound steel, but that hearth gives it a living element."'
            )
            if "Crimson Depths" in p["unlocked_regions"]:
                found = p.setdefault("discovered_structures", {}).setdefault(
                    "Crimson Depths", []
                )
                if "Crimson Forge" not in found:
                    found.append("Crimson Forge")
                print(
                    "Crimson Forge marked in Structures. Its monsters are still inside."
                )
