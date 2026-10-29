"""Finite ingredient batches using the original alchemy recipe/progression rules."""

from collections import Counter
from food_addons import brew_recipe, food_state

MAX_BATCH = 1000


def capacity(player, first, second):
    owned = Counter(player.get("ingredients", []))
    return min(
        [MAX_BATCH]
        + [owned[name] // count for name, count in Counter((first, second)).items()]
    )


def brew(game, first, second, quantity):
    from village_life import require_service, quality
    from source_story import rank, craft_xp

    if not require_service("alchemy"):
        return False, "Visit an alchemy lab first."
    p = game.player
    maximum = capacity(p, first, second)
    if type(quantity) is not int or not 1 <= quantity <= maximum:
        return False, f"Choose a quantity from 1 to {maximum}; ingredients are finite."
    result = brew_recipe(p, first, second)
    if not result:
        return (
            False,
            "This combination has no working recipe. Experiment with a single brew first.",
        )
    preserved = 0
    bag = p["ingredients"]
    for _ in range(quantity):
        bag.remove(first)
        bag.remove(second)
        chance = (quality("alchemy") - 1) * 0.10 + (rank(p, "alchemy") - 1) * 0.02
        if game.random.random() < chance:
            bag.append(second)
            preserved += 1
        craft_xp(p, "alchemy")
        game.update_challenge_progress("craft_count")
        p.setdefault("potions", []).append(result["name"])
    discovered = food_state(p).setdefault("discovered", [])
    if result["name"] not in discovered:
        discovered.append(result["name"])
    return (
        True,
        f"BREW COMPLETE · {quantity} {result['name']} bottled and added to your potion belt. Preserved {preserved} ingredients through alchemy skill.",
    )


def menu(game):
    from village_life import require_service

    if not require_service("alchemy"):
        return
    p = game.player
    names = sorted(set(p.get("ingredients", [])))
    if not names:
        print("Bring ingredients to the alchemy lab first.")
        return
    print("\n--- BULK POTION BREWING ---")
    for number, name in enumerate(names):
        print(f'{number}. {name} · {p["ingredients"].count(name)} owned')
    print("C. Cancel")
    try:
        first = input("First ingredient # (C cancel) > ").strip()
        if first.lower() == "c":
            return
        second = input("Second ingredient # (C cancel) > ").strip()
        if second.lower() == "c":
            return
        a, b = int(first), int(second)
        if not (0 <= a < len(names) and 0 <= b < len(names)):
            print("Choose two displayed ingredient numbers.")
            return
        first, second = names[a], names[b]
        maximum = capacity(p, first, second)
        recipe = brew_recipe(p, first, second)
        if not recipe:
            print(
                "This combination has no working recipe. Try one experimental brew instead; no ingredients were spent."
            )
            return
        if maximum < 1:
            print(
                "You need two ingredients per potion, including two copies when selecting the same ingredient."
            )
            return
        print(
            f"Recipe: {recipe['name']}. Each potion uses 1 {first} + 1 {second}. You can brew up to {maximum} with your current supplies. All results will be bottled."
        )
        number = input(f"How many potions (1–{maximum}, 0 cancel) > ").strip()
        quantity = int(number)
        if quantity == 0:
            return
        if not 1 <= quantity <= maximum:
            print("Choose a quantity within the displayed limit.")
            return
    except ValueError:
        print("Choose a whole number. No ingredients were spent.")
        return
    if (
        input(f"Brew and bottle {quantity} {recipe['name']}? (y/n) > ").strip().lower()
        != "y"
    ):
        print("Batch cancelled. No ingredients were spent.")
        return
    print(brew(game, first, second, quantity)[1])
