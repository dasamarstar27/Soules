"""Regional specialist stalls; dwarven traders remain specific to Ironpeak."""

from copy import deepcopy
import hashlib
import random
import data
from expansion_state import state, choose, pay
from core_charging import make_charged

PROFILES = {
    "Whispering Woods": (
        "Ivy the Herbalist",
        "Local herbalists",
        "Native ingredients in bulk",
    ),
    "Frostbound Tundra": (
        "Sella the Weaver",
        "Tundra cloth merchants",
        "Cloth and warm provisions",
    ),
    "Crystal Spire": (
        "Vey the Runebroker",
        "Rune merchants",
        "Regional loose normal runes",
    ),
    "Sunken Coast": (
        "Nima the Fishmonger",
        "Coastal food traders",
        "Food and coastal ingredients",
    ),
    "Infernal Depths": (
        "Berrin the Tanner",
        "Leatherworkers",
        "Durable hides and leather",
    ),
    "Riftlands": (
        "Mara the Core Dealer",
        "Weapon-core dealers",
        "Abundant ordinary cores; scarce charged shipments",
    ),
}


def shipment(player):
    region = player["region"]
    cycle = player.get("wander_count", 0) // 20
    if region not in PROFILES:
        return None
    market = (
        state(player)["activities"]
        .setdefault("regional_sellers", {})
        .setdefault(region, {})
    )
    if market.get("cycle") == cycle:
        return market
    offers = []

    def add(bag, item, price, stock, token=None):
        name = item["name"] if isinstance(item, dict) else item
        offers.append(
            dict(
                id=token or bag + "::" + name,
                bag=bag,
                item=deepcopy(item),
                price=price,
                left=stock,
            )
        )

    if region == "Whispering Woods":
        for name in data.REGION_INGREDIENTS[region]:
            add("ingredients", name, 6, 20)
        for i, name in enumerate(list(data.WOODS)[:4]):
            add("woods", name, 8 + i * 5, 12)
    elif region == "Frostbound Tundra":
        for i, name in enumerate(list(data.CLOTHS)[:6]):
            add("cloths", name, 12 + i * 8, 15)
        add(
            "inventory",
            next(f for f in data.FOOD_ITEMS if f["name"] == "Frost Berry Jam"),
            10,
            20,
        )
    elif region == "Crystal Spire":
        pool = [
            r
            for r in data.RUNES
            if r.get("element") in data.REGION_ITEM_ELEMENTS[region]
        ]
        for rune in pool[:8]:
            add("runes", rune, 80, 3)
    elif region == "Sunken Coast":
        for name in data.REGION_INGREDIENTS[region]:
            add("ingredients", name, 6, 20)
        foods = data.VILLAGE_STOCK[region].get("food", [])
        for food in data.FOOD_ITEMS:
            if food["name"] in foods:
                add("inventory", food, max(5, round(food["value"] * 0.65)), 20)
    elif region == "Infernal Depths":
        for i, name in enumerate(data.LEATHERS):
            add("leathers", name, 15 + i * 12, 12)
    elif region == "Riftlands":
        for i, name in enumerate(data.CORES):
            add("cores", name, 30 + i * 4, 8)
        key = state(player)["character_id"] + "::Riftlands::" + str(cycle)
        rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:16], 16))
        if rng.random() < 0.25:
            core = rng.choice(list(data.CORES))
            from core_charging import compatible

            rune = rng.choice([r for r in data.RUNES if compatible(core, r)])
            add(
                "charged_cores",
                make_charged(core, rune, region),
                225,
                1,
                "rare_charged_core",
            )
    market.update(cycle=cycle, offers=offers)
    return market


def buy(player, index, quantity):
    market = shipment(player)
    if not market or type(index) is not int or not 0 <= index < len(market["offers"]):
        return False, "Choose a listed specialist offer."
    offer = market["offers"][index]
    if type(quantity) is not int or not 1 <= quantity <= offer["left"]:
        return False, "Choose a positive quantity within the displayed stock."
    cost = offer["price"] * quantity
    if not pay(player, cost):
        return False, "The displayed souls and an allowed purchasing mode are required."
    for _ in range(quantity):
        player.setdefault(offer["bag"], []).append(deepcopy(offer["item"]))
    offer["left"] -= quantity
    return (
        True,
        "Purchased "
        + str(quantity)
        + " "
        + (offer["item"]["name"] if isinstance(offer["item"], dict) else offer["item"])
        + " for "
        + str(cost)
        + " souls.",
    )


def menu(game):
    p = game.player
    if p["region"] == "Ironpeak Mountains":
        print(
            "Bromm and the dwarven bulk-metal traders work at Ironpeak Mountains Quarry. Visit that discovered quarry through Structures."
        )
        return
    if p["region"] not in PROFILES:
        print(
            "This region’s ordinary village shops carry its supplies; there is no specialist stall here."
        )
        return
    name, people, focus = PROFILES[p["region"]]
    while True:
        market = shipment(p)
        print("\n" + name + " · " + people + " · " + focus)
        print(
            "Stocks refresh each 20-wander cycle. C: sacrifice a normal rune into a carried ordinary core. Charged cores are only spent in the reclaimed Crimson Forge."
        )
        if p["region"] == "Riftlands":
            print(
                "Ordinary weapon cores: eight of every type per shipment. A shipment has a 25% chance of one charged core; reopening or reloading cannot reroll it."
            )
        for i, offer in enumerate(market["offers"], 1):
            item = offer["item"]
            print(
                f"{i}. "
                + (item["name"] if isinstance(item, dict) else item)
                + f' · {offer["price"]} souls each · {offer["left"]} left'
            )
        answer = input("Specialist (number / C / 0 back) > ").strip().lower()
        if answer == "0":
            return
        if answer == "c":
            from core_charging import menu as charging

            charging(game)
            continue
        try:
            index = int(answer) - 1
        except ValueError:
            continue
        if not 0 <= index < len(market["offers"]):
            continue
        try:
            quantity = int(input("Quantity (0 cancels) > "))
        except ValueError:
            continue
        if quantity == 0:
            continue
        print(buy(p, index, quantity)[1])
