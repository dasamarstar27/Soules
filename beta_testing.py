"""Explicit, opt-in beta supplies. Never changes story completion."""

from copy import deepcopy
import data
from season_two import GOODS


def grant_collectibles(player):
    def add(key, item):
        bag = player.setdefault(key, [])
        name = item.get("name") if isinstance(item, dict) else item
        if not any((old.get("name") if isinstance(old, dict) else old) == name for old in bag):
            bag.append(deepcopy(item))

    for key, catalog in [
        ("weapons", data.WEAPONS),
        ("armours", data.ARMOURS),
        ("staffs", data.STAFFS),
        ("runes", data.RUNES),
    ]:
        for item in catalog:
            add(key, item)
    for key, catalog in [
        ("metals", data.METALS),
        ("woods", data.WOODS),
        ("cores", data.CORES),
        ("cloths", data.CLOTHS),
        ("leathers", data.LEATHERS),
        ("elemental_cores", data.ELEMENTAL_CORES),
    ]:
        for name in catalog:
            add(key, name)
    for item in data.SCROLLS + data.LOOT_ITEMS + data.FOOD_ITEMS:
        add("inventory", item)
    for items in data.REGION_INGREDIENTS.values():
        for item in items:
            add("ingredients", item["name"] if isinstance(item, dict) else item)
    for potion in data.POTION_RECIPES:
        add("potions", potion["name"])
    for goods in GOODS.values():
        for key, item, _ in goods:
            add(key, item)
    player["beta_mode"] = True
    print(
        "DAMAR activated! One of every catalogued weapon, armour, staff, rune, metal, wood, core, cloth, leather, scroll, loot, food, ingredient and stock potion is now in your bags."
    )
    print(
        "Season Two village services are open for testing. Story progress is unchanged. Repeating DAMAR replaces missing types; it does not stack duplicates."
    )
