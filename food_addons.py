"""Cooking, preserved herbs, toxicity, medical orders and annotated recipes."""

from copy import deepcopy
import data
from expansion_state import state, mark, pay, choose


def food_state(player):
    current = state(player).setdefault("food", {})
    for key, value in dict(
        cooking_xp=0, toxicity=0, notes={}, substitutions=False
    ).items():
        current.setdefault(key, value)
    return current


def is_food(item):
    return item.get("name") in {f["name"] for f in data.FOOD_ITEMS} or (
        item.get("food") is True
        and type(item.get("hunger")) is int
        and 0 < item["hunger"] <= 100
    )


def catalog(item):
    return next((f for f in data.FOOD_ITEMS if f["name"] == item.get("name")), item)


def potion_effect(player, name):
    if name in food_state(player).get("blends", {}):
        return "blend"
    for _, recipe in data.INGREDIENT_COMBOS.items():
        if recipe["name"] == name:
            return recipe["effect"]
    return next((r["effect"] for r in data.POTION_RECIPES if r["name"] == name), None)


def toxicity(player):
    f = food_state(player)
    f["toxicity"] = min(100, f.get("toxicity", 0) + 8)
    if f["toxicity"] >= 64:
        damage = max(1, f["toxicity"] // 20)
        player["hp"] = max(1, player["hp"] - damage)
        print(
            f'Toxicity {f["toxicity"]}/100: the strain costs {damage} HP. Wandering and resting reduce toxicity.'
        )
    mark(player, 73)


def decay(player, amount=2):
    f = food_state(player)
    f["toxicity"] = max(0, f.get("toxicity", 0) - amount)


def use_potion(game):
    p = game.player
    potions = p.get("potions", [])
    index = choose("POTIONS", potions)
    if index is None:
        return False
    name = potions[index]
    effect = potion_effect(p, name)
    if not effect:
        print("Unknown potion; it was kept.")
        return False
    potions.pop(index)
    game._apply_potion_effect(effect, name)
    return True


def brew_recipe(player, a, b):
    direct = data.INGREDIENT_COMBOS.get(
        frozenset((a.removeprefix("Dried "), b.removeprefix("Dried ")))
    )
    if direct:
        return direct
    if food_state(player).get("substitutions"):
        substitutions = {
            "Forest Mushroom": "Dew Blossom",
            "Forest Mushroom": "Dew Blossom",
        }
        for first, second in ((a, b), (b, a)):
            key = frozenset((substitutions.get(first, first), second))
            if key in data.INGREDIENT_COMBOS:
                return data.INGREDIENT_COMBOS[key]
    return None


def activity(game, feature):
    p = game.player
    f = food_state(p)
    r = p["region"]
    if feature == 71:
        foods = [x for x in p.get("inventory", []) if is_food(x)]
        ingredients = p.get("ingredients", [])
        if not foods or not ingredients:
            print("Bring one carried food and one regional ingredient.")
            return
        index = choose("COOK REGIONAL MEAL", [x["name"] for x in foods])
        if index is None:
            return
        ingredient = next(
            (x for x in ingredients if x in data.REGION_INGREDIENTS.get(r, [])), None
        )
        if not ingredient:
            print("Need an ingredient native to the current region.")
            return
        base = foods[index]
        p["inventory"].remove(base)
        ingredients.remove(ingredient)
        meal = dict(
            name=r + " " + base["name"] + " Meal",
            food=True,
            hunger=min(
                100, catalog(base)["hunger"] + 10 + min(10, f["cooking_xp"] // 5)
            ),
            value=20,
            region=r,
            also_heal=7 if state(p)["magic"].get("philosophy") == "restoration" else 5,
        )
        if f.get("family_recipe") and r == "Sunken Coast":
            meal["name"] = "Coastal Family Stew"
            meal["also_heal"] += 3
        p["inventory"].append(meal)
        f["cooking_xp"] += 1
        mark(p, 71)
        print("Cooked " + meal["name"] + ".")
    elif feature == 72:
        rank = min(5, 1 + f["cooking_xp"] // 5)
        print(
            f'Cooking rank {rank}/5 · XP {f["cooking_xp"]}; successful regional meals improve nourishment. Rank 2 unlocks Feast preparation.'
        )
        mark(p, 72)
        if (
            rank >= 2
            and input(
                "Prepare a Feast with three foods and two regional ingredients? (y/n) > "
            )
            .strip()
            .lower()
            == "y"
        ):
            from addon_quests import food_take

            native = [
                x
                for x in p.get("ingredients", [])
                if x in data.REGION_INGREDIENTS.get(r, [])
            ]
            if len(native) < 2:
                print("Bring two native ingredients.")
                return
            if not food_take(p, 3):
                print("Bring three carried foods.")
                return
            for item in native[:2]:
                p["ingredients"].remove(item)
            p["inventory"].append(
                dict(name=r + " Feast", food=True, hunger=70, also_heal=15, value=45)
            )
            f["cooking_xp"] += 2
            print("Feast prepared: 70 hunger and 15 HP.")
    elif feature == 73:
        print(
            f'Toxicity {f["toxicity"]}/100. Potions add 8; at 64+ strain hurts you. Wandering removes 2; a village rest removes 10.'
        )
        mark(p, 73)
    elif feature == 74:
        import original_ui as ui

        if not ui.village or "alchemy" not in ui.village["services"]:
            print("Visit an alchemist to commission herb drying.")
            return
        pool = p.get("ingredients", [])
        index = choose("DRY A HERB · 5 SOULS · TWO LOCAL SHIFTS", pool)
        if index is None:
            return
        from village_jobs import record

        if len(record(p, ui.village)["work_orders"]) >= 30:
            print("Collect completed work orders first.")
            return
        if pool[index].startswith("Dried "):
            print("This herb is already dried.")
            return
        if not pay(p, 5):
            print("Need five souls.")
            return
        ingredient = pool.pop(index)
        from village_jobs import record

        local = record(p, ui.village)
        local["work_serial"] += 1
        local["work_orders"].append(
            dict(
                id=ui.village["id"] + "::dry" + str(local["work_serial"]),
                kind="drying",
                worker="drying rack",
                remaining=2,
                result=["Dried " + ingredient],
                destination="ingredients",
                fee=5,
                quality=1,
                materials=[ingredient],
                region=r,
            )
        )
        mark(p, 74)
        print(
            "Herb drying commissioned. The dried herb is an accepted substitute for that same herb in brewing."
        )
    elif feature == 75:
        cycle = p.get("wander_count", 0) // 20
        if f.get("medical_cycle") == cycle:
            print("Medical supplies already delivered this cycle.")
            return
        eligible = [
            x
            for x in p.get("potions", [])
            if potion_effect(p, x) and potion_effect(p, x).startswith("heal_")
        ]
        index = choose("APOTHECARY ORDER: HEALING POTION FOR 100 SOULS", eligible)
        if index is None:
            return
        p["potions"].remove(eligible[index])
        p["gold"] += 100
        f["medical_cycle"] = cycle
        mark(p, 75)
    elif feature == 76:
        names = [recipe["name"] for recipe in data.INGREDIENT_COMBOS.values()] + [
            x["name"] for x in data.FOOD_ITEMS
        ]
        index = choose("TASTE / RECIPE NOTES", names)
        if index is None:
            return
        note = input("Your note (blank clears) > ").strip()[:240]
        f["notes"][names[index]] = note
        mark(p, 76)
    elif feature == 77:
        from addon_quests import food_take

        if not food_take(p, 2):
            print("Bring two carried food items.")
            return
        p["inventory"].append(
            deepcopy(
                next(x for x in data.FOOD_ITEMS if x["name"] == "Traveller's Ration")
            )
        )
        mark(p, 77)
        print("Two foods packed into one compact travelling ration.")
    elif feature == 78:
        import original_ui as ui

        if not ui.village:
            print("Visit a village garden first.")
            return
        from village_jobs import record

        local = record(p, ui.village)
        clock = local.get("work_clock", 0)
        garden = local.setdefault("medicinal_garden", [])
        index = choose(
            "MEDICINAL GARDEN",
            [
                "Plant one ingredient (three plots; three local shifts to grow)",
                "Harvest ready plots",
            ],
        )
        if index == 0:
            if len(garden) >= 3 or not p.get("ingredients"):
                print("Need a free plot and one ingredient seed.")
                return
            name = p["ingredients"].pop(0)
            garden.append(dict(ingredient=name, ready=clock + 3))
            print("Planted " + name + ".")
        elif index == 1:
            grown = [x for x in garden if x["ready"] <= clock]
            for x in grown:
                p.setdefault("ingredients", []).extend([x["ingredient"]] * 2)
                garden.remove(x)
            print(
                "Harvested " + str(len(grown)) + " plots; each yields two ingredients."
            )
        if index is not None:
            mark(p, 78)
    elif feature == 79:
        if f.get("substitutions"):
            print("Known substitution: Forest Mushroom may replace Dew Blossom.")
            return
        if not pay(p, 50, ingredients=["Forest Mushroom", "Dew Blossom"]):
            print(
                "Research requires 50 souls, one Forest Mushroom and one Dew Blossom."
            )
            return
        f["substitutions"] = True
        mark(p, 79)
        print(
            "Learned: Forest Mushroom can replace Dew Blossom in a recognised recipe."
        )
    elif feature == 80:
        needed = ["Ember Bread", "Frost Berry Jam", "Forest Berries", "Stormfruit"]
        inventory = p.get("inventory", [])
        if f.get("banquet_complete"):
            print("The first four-clan banquet is already remembered.")
            return
        if any(not any(x["name"] == name for x in inventory) for name in needed):
            print(
                "Bring Ember Bread, Frost Berry Jam, Forest Berries and Stormfruit from the four clans."
            )
            return
        for name in needed:
            inventory.remove(next(x for x in inventory if x["name"] == name))
        p["gold"] += 200
        f["banquet_complete"] = True
        state(p)["relationships"]["public_trust"] = (
            state(p)["relationships"].get("public_trust", 0) + 5
        )
        mark(p, 80)
        print("The four clans share a table. +200 souls, +5 public trust.")


def mix_potions(game):
    p = game.player
    f = food_state(p)
    potions = p.get("potions", [])
    c = choose(
        "POTION MIXING",
        [
            "Blend two ordinary healing potions",
            "Fortify one ordinary potion with a regional ingredient",
        ],
    )
    if c is None:
        return
    ordinary = [
        x
        for x in potions
        if potion_effect(p, x) and potion_effect(p, x).startswith("heal_")
    ]
    first = choose("FIRST POTION", ordinary)
    if first is None:
        return
    a = ordinary[first]
    if c == 0:
        remaining = list(ordinary)
        remaining.pop(first)
        second = choose("SECOND POTION", remaining)
        if second is None:
            return
        b = remaining[second]
        amount = min(
            120,
            int(potion_effect(p, a).split("_")[1])
            + int(potion_effect(p, b).split("_")[1]),
        )
        # Blends use a bounded direct heal effect rather than recursively mixing blends.
        name = f"Blended {a} + {b}"
        potions.remove(a)
        potions.remove(b)
        f.setdefault("blends", {})[name] = dict(heal=amount, ingredients=[a, b])
        potions.append(name)
        print(name + f" restores {amount} HP. Two bottles became one.")
    else:
        local = next(
            (
                x
                for x in data.REGION_INGREDIENTS.get(p["region"], [])
                if x in p.get("ingredients", [])
            ),
            None,
        )
        if not local:
            print("Bring an ingredient from the current region.")
            return
        effect = potion_effect(p, a)
        amount = min(120, int(effect.split("_")[1]) + 20)
        name = "Fortified " + a + " with " + local
        potions.remove(a)
        p["ingredients"].remove(local)
        f.setdefault("blends", {})[name] = dict(heal=amount, ingredients=[a, local])
        potions.append(name)
        print(
            name + f" restores {amount} HP. Recipe recorded in your personal notebook."
        )
