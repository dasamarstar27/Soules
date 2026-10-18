"""Searchable content reference built from the game's actual catalogues."""

import data
from core_charging import CORE_ELEMENTS, limits

LABELS = {
    "atk": "ATK",
    "def": "DEF",
    "hp": "HP",
    "xp": "XP",
    "mp": "MP",
    "desc": "Description",
    "power": "Staff power",
    "value": "Catalogue value (souls)",
    "gold": "Souls",
    "tier": "Gear tier",
    "hunger": "Hunger restored",
    "heal": "HP restored",
    "regions": "Native regions",
}
ITEM_TABLES = {
    "WEAPONS": "Weapons",
    "ARMOURS": "Armour",
    "STAFFS": "Staffs",
    "RUNES": "Runes",
    "SCROLLS": "Scrolls",
    "LOOT_ITEMS": "Loot & food",
    "FOOD_ITEMS": "Loot & food",
    "REGION_INGREDIENTS": "Ingredients",
    "POTION_RECIPES": "Potions",
    "INGREDIENT_COMBOS": "Potions",
    "METALS": "Materials",
    "WOODS": "Materials",
    "CLOTHS": "Materials",
    "LEATHERS": "Materials",
    "CORES": "Cores",
    "ELEMENTAL_CORES": "Cores",
    "ARTIFACTS": "Artifacts",
    "LIBRARY_TOMES": "Tomes",
    "GRAVEYARD_LOOT": "Loot & food",
    "CORE_STABILISER": "Cores",
    "BOSS_DROPS": "Boss drops",
    "TREASURE_MAPS": "Maps & mounts",
    "MOUNTS": "Maps & mounts",
    "COSMETICS_SHOP": "Cosmetics",
}


def label(key):
    return LABELS.get(str(key), str(key).replace("_", " ").capitalize())


def readable(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None:
        return "None"
    if isinstance(value, dict):
        return (
            "; ".join(label(k) + ": " + readable(v) for k, v in value.items()) or "None"
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        return "; ".join(readable(v) for v in value) or "None"
    return str(value)


def category(table):
    if table in ITEM_TABLES:
        return ITEM_TABLES[table]
    if "MONSTER" in table or "BOSSES" in table:
        return "Creatures"
    if "STRUCTURE" in table or table in ("REGIONS", "ELEMENTAL_VILLAGES"):
        return "Places"
    if table in ("COMPANIONS", "COMPANION_MOVES"):
        return "Companions"
    return "Systems"


def records(value, path=()):
    """Keep all catalogue fields, including keyed materials and nested pools."""
    if isinstance(value, dict):
        if (
            "name" in value
            or any(
                k in value
                for k in ("atk", "def", "desc", "description", "effect", "cost")
            )
            or all(not isinstance(v, (dict, list)) for v in value.values())
        ):
            yield value.get("name", " · ".join(map(readable, path))), value, path
        else:
            for key, child in value.items():
                yield from records(child, path + (key,))
    elif isinstance(value, (list, tuple)):
        for i, child in enumerate(value):
            yield from records(
                child, path + ((i + 1) if isinstance(child, dict) else readable(child),)
            )
    else:
        yield str(value), {}, path


def item_odds(table, item, context):
    """These are conditional loot-roll odds, never invented per-wander rarity."""
    if table == "LOOT_ITEMS":
        regions = item.get("regions") or list(data.REGION_STRUCTURES)
        odds = []
        for region in regions:
            pool = [
                x
                for x in data.LOOT_ITEMS
                if not x.get("regions") or region in x["regions"]
            ]
            odds.append(
                f"{region}: {60/len(pool):.4g}% (Divine Luck {50/len(pool):.4g}%)"
            )
        return (
            "Chance per ordinary loot roll, when native: "
            + "; ".join(odds)
            + ". Other structure/reward sources have their own rules."
        )
    if table in ("WEAPONS", "ARMOURS"):
        pool = getattr(data, table)
        chance = 10 if table == "WEAPONS" else 5
        bands = [
            ("levels 1–4", ("basic",)),
            ("levels 5–9", ("mid",)),
            ("levels 10–14", ("mid", "high")),
            ("levels 15+", ("high", "legendary")),
        ]
        return (
            "Chance per ordinary loot roll: "
            + "; ".join(
                (
                    f"{name}: {chance/sum(x['tier'] in tiers for x in pool):.4g}%"
                    if item.get("tier") in tiers
                    else f"{name}: unavailable in this pool"
                )
                for name, tiers in bands
            )
            + ". Gear tier selects the level pool; it is not a separate rarity roll. Shops/crafting have separate availability."
        )
    if table == "SCROLLS":
        return f"Chance per ordinary loot roll: {15/len(data.SCROLLS):.4g}%. All scrolls in this pool are equally likely."
    if table in ("RUNES", "STAFFS"):
        if table == "RUNES" and item.get("effect") == "fusion":
            return "Crafting: fuse two normal runes. No independent normal-rune drop chance."
        pool = getattr(data, table)
        from original_game import is_region_rune, is_region_staff

        allowed = is_region_rune if table == "RUNES" else is_region_staff
        chance = 7 if table == "RUNES" else 3
        lucky = 7 if table == "RUNES" else 13
        regions = []
        for region in data.REGION_STRUCTURES:
            native = [x for x in pool if allowed(x, region)] or pool
            if item in native:
                regions.append(
                    f"{region}: {chance/len(native):.4g}% (Divine Luck {lucky/len(native):.4g}%)"
                )
        return "Chance per ordinary loot roll: " + "; ".join(regions) + "."
    if table == "BOSS_DROPS":
        region = context[0]
        return f"Boss-specific reward pool in {region}: each listed reward is selected uniformly when that boss reward roll occurs (1/{len(data.BOSS_DROPS[region])}). This is separate from ordinary loot rolls."
    if table == "REGION_INGREDIENTS":
        region = context[0]
        return f"Native ingredient in {region}. The reached ingredient check is 8%; a specific native ingredient is 8% ÷ {len(data.REGION_INGREDIENTS[region])} at that check. Earlier encounters may bypass it. Also available through native gathering and relevant shops."
    return "No independent item rarity roll is assigned here. Obtain through the listed recipe, shop, quest or activity; costs and stocks are shown there."


def reference():
    entries = []
    for table, value in vars(data).items():
        if not table.isupper() or not isinstance(value, (list, dict)):
            continue
        for name, item, path in records(value):
            if not name:
                name = label(table)
            details = [
                label(k) + ": " + readable(v) for k, v in item.items() if k != "name"
            ]
            details.insert(
                0,
                "Found under: "
                + label(table)
                + (
                    " · " + " / ".join(map(readable, path[:-1]))
                    if len(path) > 1
                    else ""
                ),
            )
            if table in ("REGION_STRUCTURES", "ELEMENTAL_VILLAGES") and (
                item.get("type") == "village" or table == "ELEMENTAL_VILLAGES"
            ):
                from village_life import profile, SERVICE_NAMES

                place = profile(path[0], name, table == "ELEMENTAL_VILLAGES")
                details.append(
                    "Starting services: "
                    + "; ".join(
                        f"{SERVICE_NAMES.get(key, key)} level {place['starting_levels'][key]}, quality {place['quality'][key]}"
                        for key in place["services"]
                    )
                )
                details.append(
                    "Actual local levels, stock, notes and construction upgrades appear in the village sidebar and directory."
                )
            if category(table) == "Creatures":
                details.append(
                    "Base catalogue stats. Combat scaling, difficulty, night and relevant world-event rules may change the encountered creature's stats."
                )
            if isinstance(item.get("effect"), str):
                from effects import EFFECTS

                if item["effect"] in EFFECTS:
                    effect = EFFECTS[item["effect"]]
                    details.append(
                        "Ability: " + effect["name"] + " — " + effect["description"]
                    )
            if table in ("METALS", "WOODS", "CLOTHS", "LEATHERS"):
                details.append(
                    "Material for crafting and commissions. Ordinary village weapons do not inherit custom core powers; the charged-core elemental recipe requires the reclaimed Crimson Forge."
                )
            if table in ITEM_TABLES:
                details.append(item_odds(table, item, path))
                shops = [region for region, stock in data.VILLAGE_STOCK.items() if name in stock.get("food", []) + stock.get("gear", [])]
                if shops:
                    details.append("Native village-stock catalogue: " + ", ".join(shops) + ". Actual local services, quantities, restocks and prices vary; read that shop's quote.")
                kinds = {"WEAPONS":"weapons", "ARMOURS":"armours", "STAFFS":"staffs", "RUNES":"runes", "LOOT_ITEMS":"inventory", "FOOD_ITEMS":"inventory", "SCROLLS":"inventory"}
                if table in kinds:
                    from inventory_tools import sale_value
                    details.append(f"Base sale value: {sale_value(item, kinds[table])} souls; equipped, bound, favourite or protected equipment may be kept by automated sales.")
            if table == "CORES":
                details.extend(
                    [
                        "Core energy: " + CORE_ELEMENTS[name],
                        limits(name),
                        "Charging consumes a loose compatible rune and this ordinary core; only the reclaimed Crimson Forge spends the result. Ordinary village forging stays physical.",
                    ]
                )
            entries.append(
                dict(
                    name=str(name),
                    description="\n".join(details),
                    type=category(table),
                    source=table,
                )
            )
    from season_two import GOODS, goods_line

    for element, goods in GOODS.items():
        for bag, item, price in goods:
            name = item["name"] if isinstance(item, dict) else item
            entries.append(
                dict(
                    name=name,
                    type="Clan shops",
                    source="ELEMENTAL_SHOPS",
                    description=goods_line(bag, item, price, "finite")
                    + "\nSold in the "
                    + element
                    + " clan's expanded halls after Season Two opens (or during testing). Shop availability is not a random drop rate.",
                )
            )
    for clan in data.ELEMENTAL_VILLAGES.values():
        entries.append(dict(name=clan["name"] + " Scout Blade", type="Clan shops", source="CLAN_TRAVELLER_SHOPS", description="Season One traveller shop in " + clan["name"] + f". ATK +12 | Element: {clan['element']} | Price: 120 souls | Stock: 1 per 20-wander cycle. This is finite shop stock, not a random drop rate."))
    from addon_catalog import ADDONS
    from community_addons import INSTRUCTIONS

    for key, addon in ADDONS.items():
        entries.append(
            dict(
                name=addon["name"],
                description=f"Adventure {key}. {addon['description']}\n"
                + INSTRUCTIONS.get(
                    key,
                    "Open World & Social → Adventures, projects & research, then its category. Follow the displayed objective, cost and numbered choices.",
                ),
                type="Activities",
                source="ADDONS",
            )
        )
    from village_projects import PROJECTS

    for project in PROJECTS:
        entries.append(
            dict(
                name=project["name"],
                description=readable(project)
                + "\nBuild through village option 20 where the matching service exists. Each is a unique local project, not a random drop.",
                type="Village projects",
                source="VILLAGE_PROJECTS",
            )
        )
    from game_guide import SECTIONS

    for key, name, paragraphs in SECTIONS:
        entries.append(
            dict(
                name=name,
                description="\n".join(paragraphs),
                type="How to play",
                source="TUTORIAL",
            )
        )
    entries.append(
        dict(
            name="Rusty Sword",
            description=f"Starting weapon. ATK +{data.WEAPONS[0]['atk']}. Every fresh character starts with this sword and no runes. Not a random rarity roll.",
            type="Weapons",
            source="STARTING_GEAR",
        )
    )
    entries.append(
        dict(
            name="How rarity works",
            type="Rarity rules",
            source="LOOT_RULES",
            description="Ordinary loot rolls choose a category first: trinket 60%, armour 5%, weapon 10%, scroll 15%, rune 7%, staff 3%. Divine Luck changes trinkets to 50% and staffs to 13%. Each eligible item within the selected pool is equally likely. These are per loot roll, not per wander; some victories award more than one roll. Gear tier, catalogue value and random drop chance mean different things. A shop-only item or chosen activity has no invented drop percentage. Generated items, custom weapon names, charged-core/rune combinations and individual village variants follow their recipes and local rules rather than an infinite list of named copies.",
        )
    )
    return dict(
        entries=entries,
        categories=sorted({entry["type"] for entry in entries}),
        count=len(entries),
    )
