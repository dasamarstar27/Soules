"""Season Two: persistent, finite-stock services in the four hidden villages."""

from copy import deepcopy
import data

PROFILES = {
    "fire": ("Ignar", "Keeper Asha", "Ember Touch", "Hearth Mend", "Ember Bread", "burn"),
    "ice": ("Glacien", "Archivist Neris", "Frost Touch", "Snow Mend", "Frost Berry Jam", "freeze"),
    "storm": ("Voltis", "Stormkeeper Ren", "Spark Touch", "Cloud Mend", "Stormfruit", "shock"),
    "nature": ("Sylvar", "Gardener Lio", "Vine Touch", "Bloom Mend", "Forest Berries", "poison"),
}
ARTS = {}
GOODS = {}
for element, (clan, person, touch, mend, food, effect) in PROFILES.items():
    ARTS[touch] = {"element": element, "mana": 8, "damage": 12, "effect": effect}
    ARTS[mend] = {"element": element, "mana": 10, "heal": 25}
    GOODS[element] = [
        (
            "weapons",
            {"name": f"{clan} Guard Blade", "atk": 28, "element": element, "value": 450},
            450,
        ),
        (
            "armours",
            {"name": f"{clan} Woven Coat", "def": 16, "element": element, "value": 350},
            350,
        ),
        ("staffs", {"name": f"{clan} Apprentice Staff", "power": 18, "value": 400}, 400),
        (
            "inventory",
            next(
                (deepcopy(x) for x in data.FOOD_ITEMS if x["name"] == food),
                {"name": food, "hunger": 25, "value": 25},
            ),
            25,
        ),
        ("potions", "Health Potion", 80),
    ]


def available(player):
    return player.get("chapter", 1) >= 2 or player.get("beta_mode", False)


def village_services(game, village):
    p = game.player
    if not available(p):
        print(
            "The elders will open their halls after Chapter 1: unlock every region and defeat the Dreaming God in the Dreamscape."
        )
        return
    game._FOOD_BY_NAME.update({goods[3][1]["name"]: goods[3][1] for goods in GOODS.values()})
    element = village["element"]
    clan, person, touch, mend, food, effect = PROFILES[element]
    while True:
        print(f"\n--- {village['name']} · SEASON TWO ---")
        print("1. Elemental shop  2. Meet the keeper / training  3. Village library")
        print(
            "4. Side quest  5. Village crafting  6. Leave  7. Local services / restaurant  8. Discuss the Source"
        )
        print("N. Save village / edit note · T. Tags · B. Bookmark")
        choice = input("Village > ").strip()
        if choice.lower() in ("n", "note", "t", "tags", "b", "save"):
            import original_ui as ui
            from village_life import bookmark

            if ui.village:
                if choice.lower() in ("n", "note"):
                    bookmark(p, ui.village, note=input("Village note > ").strip())
                elif choice.lower() in ("t", "tags"):
                    bookmark(p, ui.village, tags=input("Tags, separated by commas > ").strip())
                else:
                    bookmark(p, ui.village)
                print("Village bookmark updated.")
            continue
        if choice == "6":
            return
        if choice == "1":
            stock = p.setdefault("elemental_shop_stock", {}).setdefault(element, [1, 1, 1, 3, 3])
            for i, (_, item, price) in enumerate(GOODS[element], 1):
                name = item["name"] if isinstance(item, dict) else item
                print(f"{i}. {name} — {price} souls ({stock[i-1]} left)")
            try:
                index = int(input("Buy number (0 cancel) > ")) - 1
            except ValueError:
                continue
            if not 0 <= index < len(stock):
                continue
            key, item, price = GOODS[element][index]
            if stock[index] <= 0:
                print("Sold out for this journey.")
                continue
            if p["gold"] < price:
                print("Not enough souls.")
                continue
            p["gold"] -= price
            stock[index] -= 1
            p.setdefault(key, []).append(deepcopy(item))
            print("Purchased. Supplies are finite.")
        elif choice == "2":
            print(f"{person}: Our element is a practice, not a possession. Spend mana with care.")
            print(f"I can teach {touch} for 75 souls. Enter 1 to learn, 0 to leave.")
            if input("Training > ").strip() == "1":
                known = p.setdefault("elemental_arts", [])
                if touch in known:
                    print("You already know this art.")
                elif p["gold"] < 75:
                    print("You need 75 souls.")
                else:
                    p["gold"] -= 75
                    known.append(touch)
                    print(f"Learned {touch}! Use combat option 9.")
        elif choice == "3":
            print(f"Only this village keeps the {clan} tomes.")
            print(
                f"1. Touch of {element.title()} — teaches {touch}\n2. The Gentle {element.title()} — teaches {mend}\n0. Leave"
            )
            book = input("Read > ").strip()
            if book in ("1", "2"):
                art = touch if book == "1" else mend
                known = p.setdefault("elemental_arts", [])
                print(
                    f'You study how {element} flows through living souls. This art costs {ARTS[art]["mana"]} mana per use.'
                )
                if art not in known:
                    known.append(art)
                    print(f"Learned {art}!")
                p.setdefault("elemental_tomes", [])
                if art not in p["elemental_tomes"]:
                    p["elemental_tomes"].append(art)
        elif choice == "4":
            quests = p.setdefault("elemental_quests", {})
            if quests.get(element) == "complete":
                print(f"{person}: Your gift keeps our village thriving. Thank you.")
                continue
            ingredient = data.REGION_INGREDIENTS.get(p["region"], ["Moonleaf"])[0]
            if isinstance(ingredient, dict):
                ingredient = ingredient["name"]
            print(f"{person}: Bring me 3 {ingredient}. Reward: 200 souls and one {food}.")
            quests[element] = "accepted"
            if input("Hand in? (y/n) > ").strip().lower() == "y":
                bag = p.setdefault("ingredients", [])
                if bag.count(ingredient) < 3:
                    print("You have not gathered enough yet.")
                    continue
                for _ in range(3):
                    bag.remove(ingredient)
                p["gold"] += 200
                p.setdefault("inventory", []).append(deepcopy(GOODS[element][3][1]))
                quests[element] = "complete"
                print("Quest complete! Reward received.")
        elif choice == "9":
            import original_ui as ui
            from source_story import remember_warriors

            if ui.village:
                remember_warriors(p, ui.village)
        elif choice == "8":
            import original_ui as ui
            from source_story import talk

            if ui.village:
                talk(game, ui.village)
        elif choice == "5":
            game.view_crafting_hub()
        elif choice == "7":
            game.visit_village(dict(name=village["name"], elemental=True), p["region"])


def use_art(player, enemy):
    known = [name for name in player.get("elemental_arts", []) if name in ARTS]
    if not known:
        print("Learn an elemental art from a hidden village keeper or library first.")
        return False
    for i, name in enumerate(known, 1):
        print(f'{i}. {name} ({ARTS[name]["mana"]} mana)')
    try:
        index = int(input("Elemental art (0 cancel) > ")) - 1
    except ValueError:
        return False
    if not 0 <= index < len(known):
        return False
    name = known[index]
    art = ARTS[name]
    if player.get("mana", 0) < art["mana"]:
        print("Not enough mana.")
        return False
    player["mana"] -= art["mana"]
    if art.get("heal"):
        player["hp"] = min(player["max_hp"], player["hp"] + art["heal"])
        print(f'{name} restores up to {art["heal"]} HP.')
    else:
        enemy["hp"] = max(0, enemy["hp"] - art["damage"])
        enemy.setdefault("status", {})[art["effect"]] = 2
        print(f'{name}: {art["damage"]} damage and {art["effect"]}.')
    return True
