"""Explicit, opt-in beta supplies. Never changes story completion."""

from copy import deepcopy
import data
from season_two import GOODS


def grant_collectibles(player):
    if not player.get("beta_mode"):
        player["beta_backup"] = deepcopy(
            {
                key: value
                for key, value in player.items()
                if key not in ("beta_backup", "beta_legacy_recovery")
            }
        )

    def add(key, item):
        bag = player.setdefault(key, [])
        name = item.get("name") if isinstance(item, dict) else item
        if not any(
            (old.get("name") if isinstance(old, dict) else old) == name for old in bag
        ):
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
    player["unlocked_regions"] = set(data.REGIONS + [data.SECRET_REGION])
    found = player.setdefault("discovered_structures", {})
    for region, structures in data.REGION_STRUCTURES.items():
        names = found.setdefault(region, [])
        for structure in structures:
            if structure["name"] not in names:
                names.append(structure["name"])
    for region, village in data.ELEMENTAL_VILLAGES.items():
        names = found.setdefault(region, [])
        if village["name"] not in names:
            names.append(village["name"])
    from core_charging import make_charged, compatible

    for i, core in enumerate(data.CORES):
        add(
            "charged_cores",
            make_charged(
                core,
                next(r for r in data.RUNES if compatible(core, r)),
                player["region"],
            ),
        )
    player["beta_mode"] = True
    print(
        "DAMAR activated! One of every catalogued weapon, armour, staff, rune, metal, wood, core, cloth, leather, scroll, loot, food, ingredient and stock potion is now in your bags."
    )
    print(
        "All regions and structures are unlocked. Season Two services are open for testing. Boss victories and chapter completion are unchanged. Repeating DAMAR replaces missing types; it does not stack duplicates."
    )


def disable_beta(player):
    if not player.get("beta_mode") and ("beta_mode" not in player or player.get("beta_clean_restore")):
        print("Beta mode is already off.")
        return
    backup = player.get("beta_backup")
    if isinstance(backup, dict):
        restored = deepcopy(backup)
        player.clear()
        player.update(restored)
        player["unlocked_regions"] = set(player["unlocked_regions"])
        for equipped, bag in (("weapon", "weapons"), ("armour", "armours")):
            if player.get(equipped):
                player[equipped] = next(
                    (item for item in player.get(bag, []) if item == player[equipped]),
                    player[equipped],
                )
        print(
            "Beta mode off. Your character, supplies and discoveries have been restored to before testing. Test items and test progress were discarded."
        )
    else:
        # Old releases did not record the original inventory. Preserve a recovery
        # copy, then remove catalogued grants; do not guess at story progress.
        player["beta_legacy_recovery"] = deepcopy(
            {
                key: value
                for key, value in player.items()
                if key not in ("beta_backup", "beta_legacy_recovery")
            }
        )
        for bag, catalog in (
            ("weapons", data.WEAPONS),
            ("armours", data.ARMOURS),
            ("staffs", data.STAFFS),
            ("runes", data.RUNES),
            ("inventory", data.FOOD_ITEMS + data.LOOT_ITEMS + data.SCROLLS),
        ):
            names = {item["name"] for item in catalog}
            names.update(
                item["name"]
                for goods in GOODS.values()
                for goods_bag, item, _ in goods
                if goods_bag == bag and isinstance(item, dict)
            )
            player[bag] = [
                item for item in player.get(bag, []) if item["name"] not in names
            ]
        for bag in (
            "cores",
            "woods",
            "metals",
            "cloths",
            "leathers",
            "ingredients",
            "potions",
            "charged_cores",
            "elemental_cores",
        ):
            player[bag] = []
        if not player.get("weapons"):
            sword = deepcopy(data.WEAPONS[0])
            sword["name"] = "Rusty Sword"
            player["weapons"] = [sword]
        player["weapon"] = player["weapons"][0]
        player["armour"] = None
        print(
            "Beta mode off. Removed catalogue test supplies from this older beta save. Its exact pre-beta inventory was not recorded; a recovery copy is retained in the exported save under beta_legacy_recovery. Story progress is unchanged."
        )
    player["beta_mode"] = False
    player["beta_clean_restore"] = True
