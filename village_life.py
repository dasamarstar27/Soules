"""Distinct village services, saved notes, finite stock and local activities."""

from copy import deepcopy
import data

SERVICE_NAMES = {
    "forge": "Blacksmith / Forge",
    "loom": "Loom",
    "tower": "Enchantment Tower",
    "alchemy": "Alchemy Lab",
    "disenchantry": "Disenchantry",
    "temple": "Imbuing Temple",
    "restaurant": "Restaurant",
    "inn": "Inn",
    "farm": "Farm",
    "trade": "Trading Post",
}
QUALITY = {
    "farming": {
        "restaurant": 2,
        "inn": 1,
        "farm": 3,
        "alchemy": 2,
        "loom": 1,
        "trade": 1,
    },
    "forge": {"forge": 3, "tower": 2, "disenchantry": 3, "inn": 1, "trade": 2},
    "market": {
        "restaurant": 1,
        "inn": 2,
        "alchemy": 2,
        "trade": 3,
        "disenchantry": 1,
        "tower": 3,
    },
    "mountain": {"forge": 2, "loom": 3, "restaurant": 1, "inn": 2, "trade": 1},
    "sanctuary": {
        "restaurant": 2,
        "inn": 3,
        "loom": 2,
        "alchemy": 3,
        "temple": 3,
        "tower": 1,
    },
}
QUALITY_NAMES = {1: "Basic", 2: "Skilled", 3: "Excellent"}

ARCHETYPES = {
    "farming": dict(
        services=["restaurant", "inn", "farm", "alchemy", "loom", "trade"],
        smith_tier=0,
        food_rate=0.75,
    ),
    "forge": dict(
        services=["forge", "tower", "disenchantry", "inn", "trade"],
        smith_tier=3,
        food_rate=1.1,
    ),
    "market": dict(
        services=["restaurant", "inn", "alchemy", "trade", "disenchantry", "tower"],
        smith_tier=0,
        food_rate=0.9,
    ),
    "mountain": dict(
        services=["forge", "loom", "restaurant", "inn", "trade"],
        smith_tier=2,
        food_rate=1.1,
    ),
    "sanctuary": dict(
        services=["restaurant", "inn", "loom", "alchemy", "temple", "tower"],
        smith_tier=0,
        food_rate=1.0,
    ),
}
KINDS = {
    "Whispering Woods": "farming",
    "Ashen Wastes": "mountain",
    "Crimson Depths": "forge",
    "Frostbound Tundra": "sanctuary",
    "Crystal Spire": "market",
    "Sunken Coast": "market",
    "Ironpeak Mountains": "mountain",
    "Blight Swamp": "farming",
    "Shadow Vale": "sanctuary",
    "Infernal Depths": "forge",
    "Celestial Expanse": "sanctuary",
    "Riftlands": "market",
    "Abyss of Souls": "mountain",
    "Shattered Wastes": "forge",
    "The Dreamscape": "sanctuary",
}


def village_id(region, name):
    return region + "::" + name


def profile(region, name, elemental=False):
    spec = next(
        (x for x in data.REGION_STRUCTURES.get(region, []) if x["name"] == name), {}
    )
    kind = spec.get("archetype", KINDS.get(region, "market"))
    p = deepcopy(ARCHETYPES[kind])
    if elemental:
        p["services"] = list(
            dict.fromkeys(p["services"] + ["loom", "alchemy", "restaurant", "temple"])
        )
    p["quality"] = {key: QUALITY[kind].get(key, 1) for key in p["services"]}
    if region == "Ashen Wastes":
        p["smith_tier"] = 1
        p["quality"]["forge"] = 1
    if region == "Sunken Coast":
        p["quality"]["restaurant"] = 3
    if region == "Blight Swamp":
        p["quality"].update(farm=1, alchemy=1, restaurant=1)
        p["food_rate"] = 0.85
    if region == "Riftlands":
        p["services"] = list(dict.fromkeys(p["services"] + ["temple"]))
        p["quality"].update(temple=2, disenchantry=2)
    if not elemental:
        p["services"] = [key for key in p["services"] if key != "temple"]
        p["quality"].pop("temple", None)
    p["starting_levels"] = {
        key: (2 if p["quality"][key] >= 2 else 1) for key in p["services"]
    }
    p.update(
        id=village_id(region, name),
        name=name,
        region=region,
        kind=kind,
        elemental=elemental,
    )
    p["stock_variant"] = spec.get("stock_variant", 0)
    p["smith_label"] = ["None", "Apprentice", "Skilled", "Master"][p["smith_tier"]]
    return p


def state(player, village):
    record = player.setdefault("village_records", {}).setdefault(
        village["id"], {"reputation": 0}
    )
    record.setdefault("levels", deepcopy(village["starting_levels"]))
    return record


def building_level(player, village, key):
    return state(player, village)["levels"].get(
        key, village["starting_levels"].get(key, 1)
    )


def service_quality(player, village, key):
    from village_projects import service_bonus
    from community_addons import project

    local = project(player, village)
    visitor = local.get("visitor", {})
    extra = (
        2 if visitor.get("service") == key and visitor.get("shifts", 0) > 0 else 0
    ) + (1 if key in ("inn", "restaurant") and local.get("clean_water") else 0)
    return min(
        9,
        village["quality"].get(key, 1)
        + building_level(player, village, key)
        - 1
        + service_bonus(player, village, key)
        + extra,
    )


def cycle(player):
    return player.get("wander_count", 0) // 20


def stock(player, village):
    record = state(player, village)
    if record.get("stock_cycle") != cycle(player):
        record["stock_cycle"] = cycle(player)
        record["food_stock"] = {
            x["name"]: 2
            + building_level(player, village, "restaurant")
            + village.get("stock_variant", 0)
            for x in food_catalog(village)
        }
    return record["food_stock"]


def food_catalog(village):
    names = data.VILLAGE_STOCK.get(village["region"], {}).get("food", [])
    foods = [x for x in data.FOOD_ITEMS if x["name"] in names] or data.FOOD_ITEMS[:3]
    shift = village.get("stock_variant", 0) % len(foods)
    return (foods[shift:] + foods[:shift])[
        : max(1, len(foods) - village.get("stock_variant", 0))
    ]


def food_price(player, village, food):
    discount = 1 - min(5, state(player, village).get("reputation", 0)) * 0.02
    return max(1, round(food["value"] * village["food_rate"] * discount))


def snapshot(player, village):
    record = state(player, village)
    saved = player.get("saved_villages", {}).get(village["id"], {})
    return dict(
        village,
        levels=dict(state(player, village)["levels"]),
        materials=dict(player.get("building_materials", {})),
        service_details={
            key: service_detail(village, key, player) for key in village["services"]
        },
        reputation=record.get("reputation", 0),
        discount=min(5, record.get("reputation", 0)) * 2,
        work_orders=[
            dict(kind=x["kind"], remaining=x["remaining"], worker=x["worker"])
            for x in record.get("work_orders", [])
        ],
        development=development_status(player, village),
        projects=len(record.get("projects", [])),
        wares=material_rows(player, village) if "trade" in village["services"] else [],
        saved=bool(saved),
        note=saved.get("note", ""),
        tags=saved.get("tags", []),
        restock_in=20 - player.get("wander_count", 0) % 20,
        farm_ready=record.get("harvest_cycle") != cycle(player),
        errand_ready=record.get("errand_cycle") != cycle(player),
        foods=(
            [
                dict(
                    name=f["name"],
                    price=food_price(player, village, f),
                    hunger=f["hunger"],
                    left=stock(player, village).get(f["name"], 0),
                )
                for f in food_catalog(village)
            ]
            if "restaurant" in village["services"]
            else []
        ),
    )


def bookmark(player, village, note=None, tags=None):
    saved = player.setdefault("saved_villages", {}).setdefault(
        village["id"],
        dict(name=village["name"], region=village["region"], note="", tags=[]),
    )
    if note is not None:
        saved["note"] = note[:240]
    if tags is not None:
        saved["tags"] = [x.strip()[:30] for x in tags.split(",") if x.strip()][:6]
    return saved


def has_service(game, key):
    import original_ui as ui

    if ui.village and key not in ui.village["services"]:
        print(
            f"{ui.village['name']} has no {SERVICE_NAMES.get(key,key)}. Check another discovered village."
        )
        return False
    return True


def smith(game, village):
    p = game.player
    tier = (
        service_quality(game.player, village, "forge")
        if "forge" in village["services"]
        else 0
    )
    if tier < 1:
        print("There is no blacksmith here.")
        return
    print(
        f"\n{village['smith_label']} blacksmith: weapon upgrade +{2+tier} ATK; armour +{3+tier} DEF."
    )
    cost = 60 + 20 * tier
    print(f"1. Weapon  2. Armour  0. Back — {cost} souls per upgrade")
    choice = input("Blacksmith > ").strip()
    if choice not in ("1", "2"):
        return
    bag = p["weapons"] if choice == "1" else p["armours"]
    for i, item in enumerate(bag, 1):
        print(f"{i}. {item['name']}")
    try:
        index = int(input("Equipment number (0 cancel) > ")) - 1
    except ValueError:
        return
    if not 0 <= index < len(bag):
        return
    key = "atk" if choice == "1" else "def"
    bonus = 2 + tier if choice == "1" else 3 + tier
    print(
        f"{bag[index]['name']}: {bag[index].get(key,0)} → {bag[index].get(key,0)+bonus}; {cost} souls"
    )
    if input("Upgrade? (y/n) > ").strip().lower() != "y":
        return
    if p["gold"] < cost:
        print("Not enough souls.")
        return
    p["gold"] -= cost
    bag[index][key] = bag[index].get(key, 0) + bonus
    from source_story import craft_xp

    craft_xp(p, "smithing" if choice == "1" else "weaving")
    print("Upgrade complete. Permanent runes stay attached.")


def restaurant(game, village, meal=False):
    p = game.player
    if not has_service(game, "restaurant"):
        return
    foods = food_catalog(village)
    remaining = stock(p, village)
    for i, f in enumerate(foods, 1):
        price = food_price(p, village, f) + (5 if meal else 0)
        print(
            f"{i}. {f['name']} — {price} souls, +{f['hunger']} hunger"
            + (
                f', +{service_quality(p,village,"restaurant")*5} HP, +{(service_quality(p,village,"restaurant")-1)*5} extra hunger'
                if meal
                else ""
            )
            + f" ({remaining.get(f['name'],0)} left)"
        )
    try:
        index = int(input("Food number (0 cancel) > ")) - 1
    except ValueError:
        return
    if not 0 <= index < len(foods):
        return
    food = foods[index]
    price = food_price(p, village, food) + (5 if meal else 0)
    quantity = 1
    if not meal:
        try:
            quantity = int(
                input("How many portions? Enter a positive quantity (0 = cancel) > ")
            )
        except ValueError:
            return
        if quantity <= 0:
            return
    if remaining.get(food["name"], 0) < quantity:
        print("Sold out until the next restock.")
        return
    if p["gold"] < price * quantity:
        print("Not enough souls.")
        return
    p["gold"] -= price * quantity
    remaining[food["name"]] -= quantity
    if meal:
        q = service_quality(p, village, "restaurant")
        p["hunger"] = min(100, p.get("hunger", 100) + food["hunger"] + (q - 1) * 5)
        p["hp"] = min(p["max_hp"], p["hp"] + q * 5)
        print("You enjoy a freshly cooked meal.")
    else:
        p["inventory"].extend(deepcopy(food) for _ in range(quantity))
        print(
            str(quantity)
            + " portions packed for your journey; paid "
            + str(price * quantity)
            + " souls."
        )


def harvest(game, village):
    p = game.player
    if not has_service(game, "farm"):
        return
    record = state(p, village)
    if record.get("harvest_cycle") == cycle(p):
        print("This patch needs to regrow. Return after the next village restock.")
        return
    pool = data.REGION_INGREDIENTS.get(village["region"], [])
    if not pool:
        print("Nothing grows here.")
        return
    harvested = [
        pool[i % len(pool)] for i in range(service_quality(p, village, "farm") + 1)
    ]
    for name in harvested:
        p.setdefault("ingredients", []).append(name)
    record["harvest_cycle"] = cycle(p)
    print("Harvested: " + ", ".join(harvested) + ". Regrows every 20 wanders.")


def errand(game, village):
    p = game.player
    record = state(p, village)
    if record.get("errand_cycle") == cycle(p):
        print("You already helped this village during this restock cycle.")
        return
    ingredient = data.REGION_INGREDIENTS.get(village["region"], ["Moonleaf"])[0]
    print(
        f"Village request: deliver 3 {ingredient}. Reward: 80 souls, +1 reputation. Each reputation gives 2% food discount, up to 10%."
    )
    if input("Deliver? (y/n) > ").strip().lower() != "y":
        return
    bag = p.setdefault("ingredients", [])
    if bag.count(ingredient) < 3:
        print("You need more ingredients.")
        return
    for _ in range(3):
        bag.remove(ingredient)
    p["gold"] += 80
    record["reputation"] = record.get("reputation", 0) + 1
    record["errand_cycle"] = cycle(p)
    record["errands_completed"] = record.get("errands_completed", 0) + 1
    print("Village helped! Reputation increased.")


def village_options(village):
    """Keep familiar answer numbers while hiding absent local facilities."""
    from regional_sellers import PROFILES

    services = set(village["services"])
    options = [
        (1, "Buy food to take away", "restaurant"),
        (2, "Trading post", "trade"),
        (3, "Eat carried food", None),
        (4, "Inn (local price / quality shown in sidebar)", "inn"),
        (5, "Local errand", None),
        (6, "Brew potions", "alchemy"),
        (7, "Leave", None),
        (
            8,
            "Crafting benches",
            {"forge", "loom", "tower", "alchemy", "disenchantry", "temple"},
        ),
        (9, "Blacksmith", "forge"),
        (10, "Harvest farm", "farm"),
        (11, "Save village / edit note", None),
        (12, "Edit village tags", None),
        (13, "Restaurant meal", "restaurant"),
        (14, "Talk to the keeper", None),
        (15, "Ask for a rumour", None),
        (16, "Side quest board", None),
        (17, "Upgrade village buildings", services),
        (18, "Speak to your mentor", "old_village"),
        (19, "Material stock (metals / wood / building supplies)", "trade"),
        (20, "Community projects", services),
        (21, "Village development history", None),
        (
            22,
            "Village workers / commissions",
            {"forge", "loom", "tower", "alchemy", "trade"},
        ),
        (23, "Community activities / addons", None),
        (24, "Blend / fortify potions", "alchemy"),
        (25, "Regional specialist traders", "specialist"),
        (26, "Old Village companion sanctuary", "old_village"),
    ]

    def exists(requirement):
        if requirement is None:
            return True
        if requirement == "old_village":
            return (
                village["name"] == "Old Village"
                and village["region"] == "Whispering Woods"
            )
        if requirement == "specialist":
            return village["region"] in PROFILES
        if isinstance(requirement, set):
            return bool(requirement & services)
        return requirement in services

    return [
        (number, label) for number, label, requirement in options if exists(requirement)
    ]


def visit(game, struct, region):
    import original_ui as ui

    previous = ui.village
    v = profile(region, struct["name"], struct.get("elemental", False))
    ui.village = v
    from source_story import meet_mentor

    if not struct.get("same_visit"):
        register_visit(game.player, v, game.random)
    meet_mentor(game.player, v)
    found = game.player.setdefault("discovered_structures", {}).setdefault(region, [])
    if v["name"] not in found:
        found.append(v["name"])
    try:
        while True:
            info = snapshot(game.player, v)
            print(f"\n--- {v['name'].upper()} · {v['kind']} village ---")
            print(
                "Services: "
                + ", ".join(
                    SERVICE_NAMES[x] + " [" + QUALITY_NAMES[v["quality"][x]] + "]"
                    for x in v["services"]
                )
            )
            print(
                (
                    f"Blacksmith: {v['smith_label']} | "
                    if "forge" in v["services"]
                    else ""
                )
                + f"Reputation {info['reputation']} | Food discount {info['discount']}% | Restock in {info['restock_in']} wanders"
            )
            if info["note"]:
                print("Your note: " + info["note"])
            print("Choose a listed number. Only facilities available in this village are shown.")
            for number, label in village_options(v):
                print(f"{number}. {label}")
            before_activity = (
                game.player["gold"],
                len(game.player.get("ingredients", [])),
                len(game.player.get("inventory", [])),
            )
            c = input("Village > ").strip().lower()
            if c == "7":
                return
            from expansion_state import state as expansion_state

            if (
                c in ("1", "2", "4", "9", "13", "17", "19", "20")
                and expansion_state(game.player)
                .get("systems", {})
                .get("mode", {})
                .get("id")
                == "budget_run"
            ):
                print("Budget Run blocks purchases and paid upgrades.")
                continue
            if c == "1":
                restaurant(game, v)
            elif c == "13":
                restaurant(game, v, meal=True)
            elif c == "26":
                from player_qol import sanctuary

                sanctuary(game)
            elif c == "25":
                from regional_sellers import menu

                menu(game)
            elif c == "24":
                if has_service(game, "alchemy"):
                    from food_addons import mix_potions

                    mix_potions(game)
            elif c == "22":
                from village_jobs import menu

                menu(game, v)
            elif c == "23":
                from addons import hub

                hub(game)
            elif c == "19":
                material_shop(game, v)
            elif c == "20":
                from village_projects import menu

                menu(game, v)
            elif c == "21":
                record = state(game.player, v)
                print(development_status(game.player, v))
                for event in record.get("development_log", []):
                    print(event)
            elif c == "17":
                upgrade_buildings(game, v)
            elif c == "18":
                from source_story import mentor_talk

                mentor_talk(game, v)
            elif c == "16":
                game.quest_board(region)
            elif c == "14":
                from source_story import talk

                talk(game, v)
            elif c == "15":
                from source_story import rumour

                rumour(game.player, v)
            elif c == "2":
                if has_service(game, "trade"):
                    game.merchant()
            elif c == "3":
                game._eat_food()
            elif c == "4":
                if not has_service(game, "inn"):
                    continue
                q = service_quality(game.player, v, "inn")
                cost = (
                    0
                    if state(game.player, v).get("reputation", 0) >= 10
                    and state(game.player, v).get("free_rest_cycle")
                    != cycle(game.player)
                    else 40 + q * 10
                )
                heal = 20 + q * 10
                if game.player["gold"] < cost:
                    print("Not enough souls.")
                    continue
                if (
                    input(f"Rest for {cost} souls and up to {heal} HP? (y/n) > ")
                    .strip()
                    .lower()
                    != "y"
                ):
                    continue
                game.player["gold"] -= cost
                if cost == 0:
                    state(game.player, v)["free_rest_cycle"] = cycle(game.player)
                    print(
                        "The innkeeper offers a free rest for your reputation (once per 20-wander cycle)."
                    )
                game.player["hp"] = min(game.player["max_hp"], game.player["hp"] + heal)
                from village_jobs import advance
                from food_addons import decay

                decay(game.player, 10)
                advance(game.player, v, 2)
                print("Rested at the inn. Local work advanced two shifts.")
            elif c == "5":
                errand(game, v)
            elif c == "6":
                if has_service(game, "alchemy"):
                    game._ingredient_brew_menu()
            elif c == "8":
                game.view_crafting_hub()
            elif c == "9":
                smith(game, v)
            elif c == "10":
                harvest(game, v)
            elif c in ("11", "note"):
                bookmark(
                    game.player, v, note=input("Village note (blank clears) > ").strip()
                )
                print("Village saved with your note.")
            elif c in ("12", "tags"):
                bookmark(
                    game.player, v, tags=input("Tags, separated by commas > ").strip()
                )
                print("Village tags saved.")
            elif c == "save":
                bookmark(game.player, v)
                print("Village saved.")
            after_activity = (
                game.player["gold"],
                len(game.player.get("ingredients", [])),
                len(game.player.get("inventory", [])),
            )
            if c not in ("4", "22", "23") and after_activity != before_activity:
                from village_jobs import advance

                advance(game.player, v)

    finally:
        ui.village = previous


def known_villages(player):
    result = []
    for region in data.REGIONS + [data.SECRET_REGION]:
        names = player.get("discovered_structures", {}).get(region, [])
        for struct in data.REGION_STRUCTURES.get(region, []):
            if struct["type"] == "village" and struct["name"] in names:
                result.append(profile(region, struct["name"]))
        ev = data.ELEMENTAL_VILLAGES.get(region)
        if ev and ev["name"] in names:
            result.append(profile(region, ev["name"], True))
    for vid, local in player.get("expansion", {}).get("projects", {}).items():
        if local.get("restored_refuge"):
            region = vid.split("::")[0]
            result.append(profile(region, local["restored_refuge"]))
    return result


def directory(game):
    p = game.player
    query = ""
    saved_only = False
    while True:
        all_villages = known_villages(p)
        entries = []
        for v in all_villages:
            saved = p.get("saved_villages", {}).get(v["id"], {})
            haystack = " ".join(
                [
                    v["name"],
                    v["region"],
                    v["kind"],
                    v["smith_label"],
                    *v["services"],
                    *saved.get("tags", []),
                    saved.get("note", ""),
                ]
            ).lower()
            if (not saved_only or saved) and query.lower() in haystack:
                entries.append((v, saved))
        print("\n--- VILLAGE DIRECTORY · discovered places only ---")
        for i, (v, saved) in enumerate(entries, 1):
            print(
                f"{i}. {'★ ' if saved else ''}{v['name']} — {v['region']} | {v['smith_label']} smith | {', '.join(v['services'])}"
            )
            if saved:
                print(
                    "   "
                    + saved.get("note", "")
                    + " ["
                    + ", ".join(saved.get("tags", []))
                    + "]"
                )
        if not entries:
            print(
                "No matching villages. Discover villages through wandering and Structures."
            )
        print(
            "Number: revisit · F: filter by name/region/service/tag/note · S: saved-only toggle · N: edit note · T: edit tags · R: remove bookmark · 0: back"
        )
        c = input("Directory > ").strip().lower()
        if c == "0":
            return
        if c == "f":
            query = input("Search (blank clears) > ").strip()
            continue
        if c == "s":
            saved_only = not saved_only
            continue
        mode = c
        if c in ("n", "t", "r"):
            c = input("Village number > ").strip()
        try:
            index = int(c) - 1
        except ValueError:
            continue
        if not 0 <= index < len(entries):
            continue
        v, saved = entries[index]
        if mode == "n":
            bookmark(p, v, note=input("Village note > ").strip())
            continue
        if mode == "t":
            bookmark(p, v, tags=input("Tags, separated by commas > ").strip())
            continue
        if mode == "r":
            p.setdefault("saved_villages", {}).pop(v["id"], None)
            continue
        if v["region"] not in p["unlocked_regions"]:
            print("That region is locked.")
            continue
        p["region"] = v["region"]
        p["current_location"] = v["region"]
        if v["elemental"]:
            game.visit_elemental_village()
        else:
            game.visit_village({"name": v["name"], "type": "village"}, v["region"])


def quality(key):
    import original_ui as ui

    return (
        service_quality(ui.get_ui().player, ui.village, key)
        if ui.village and ui.get_ui()
        else 1
    )


def require_service(key):
    import original_ui as ui

    if not ui.village:
        print(
            "Visit a discovered village through Structures or the Village Directory to use its local services."
        )
        return False
    if key not in ui.village["services"]:
        print(f"{ui.village['name']} has no {SERVICE_NAMES.get(key,key)}.")
        return False
    return True


def service_detail(v, key, player=None):
    q = service_quality(player, v, key) if player is not None else v["quality"][key]
    details = {
        "forge": f"+{2+q} ATK / +{3+q} DEF upgrades; crafted weapons +{(q-1)*2} ATK",
        "loom": f"crafted armour +{(q-1)*2} DEF",
        "tower": f"crafted staffs +{(q-1)*3} power",
        "alchemy": f"{(q-1)*10}% chance to save one ingredient on a successful recipe",
        "disenchantry": f"{25+10*(q-1)}% equipment sell value recovered, plus materials",
        "temple": f"imbued staff +{(q-1)*2} power",
        "restaurant": f'meals +{q*5} HP, +{(q-1)*5} extra hunger; food price ×{v["food_rate"]:g}',
        "inn": f"{20+q*10} HP for {40+q*10} souls",
        "farm": f"{q+1} ingredients per harvest",
        "trade": f"{(q-1)*5}% equipment discount",
    }
    return details[key]


def crafting_hub(game):
    import original_ui as ui

    if not ui.village:
        print(
            "Choose a discovered village through Structures or the Village Directory first."
        )
        return
    v = ui.village
    actions = [
        ("forge", "Forge weapons", game.forge_weapon),
        ("loom", "Loom armour", game.craft_armor),
        ("tower", "Enchantment Tower", game.craft_staff),
        ("alchemy", "Alchemy Lab", game._ingredient_brew_menu),
        ("disenchantry", "Disenchantry", game.salvage_equipment),
        ("temple", "Imbue staff", game.imbue_staff),
        ("trade", "Trading Post", game.merchant),
    ]
    while True:
        available = [row for row in actions if row[0] in v["services"]]
        print("\n--- " + v["name"].upper() + " · LOCAL WORKSTATIONS ---")
        for i, (key, label, fn) in enumerate(available, 1):
            print(
                f'{i}. {label} · Level {building_level(game.player,v,key)} [{QUALITY_NAMES[v["quality"][key]]}] — {service_detail(v,key,game.player)}'
            )
        missing = [
            SERVICE_NAMES[key] for key, _, _ in actions if key not in v["services"]
        ]
        if missing:
            print("Unavailable here: " + ", ".join(missing))
        print("R. Rune library\nC. Sacrifice a rune to charge a weapon core\n0. Back")
        choice = input("Workstation > ").strip().lower()
        if choice == "0":
            return
        if choice == "c":
            from core_charging import menu

            menu(game)
        elif choice == "r":
            game.view_rune_library()
            continue
        try:
            index = int(choice) - 1
        except ValueError:
            continue
        if 0 <= index < len(available):
            available[index][2]()


def salvage(game):
    from inventory_tools import sale_value
    import math

    if not require_service("disenchantry"):
        return
    p = game.player
    q = quality("disenchantry")
    eligible = []
    for kind in ("weapons", "armours", "staffs"):
        for item in p.get(kind, []):
            if (
                item is p.get("weapon")
                or item is p.get("armour")
                or item.get("rune")
                or item.get("stored_runes")
                or item.get("charged")
                or item.get("elemental_charged")
                or item.get("elemental_core")
                or item["name"] in p.get("inventory_favourites", [])
            ):
                continue
            eligible.append((kind, item))
    for i, (kind, item) in enumerate(eligible, 1):
        print(
            f"{i}. {item['name']} — {max(1,int(sale_value(item,kind)*(.25+.1*(q-1))))} souls plus recovered materials"
        )
    if not eligible:
        print("No unprotected equipment to salvage.")
        return
    try:
        index = int(input("Salvage number (0 cancel) > ")) - 1
    except ValueError:
        return
    if not 0 <= index < len(eligible):
        return
    kind, item = eligible[index]
    if input(f"Destroy {item['name']}? (y/n) > ").strip().lower() != "y":
        return
    p[kind].remove(item)
    for crafted in ("crafted_armor", "crafted_staffs"):
        if item in p.get(crafted, []):
            p[crafted].remove(item)
    p["gold"] += max(1, int(sale_value(item, kind) * (0.25 + 0.1 * (q - 1))))
    for material, amount in item.get("materials", {}).items():
        if isinstance(amount, str):
            material, amount = amount, 1
        if not isinstance(amount, (int, float)) or amount <= 0:
            continue
        for bag, catalog in [
            ("metals", data.METALS),
            ("woods", data.WOODS),
            ("cores", data.CORES),
            ("cloths", data.CLOTHS),
            ("leathers", data.LEATHERS),
        ]:
            if material in catalog:
                p.setdefault(bag, []).extend(
                    [material] * max(1, math.floor(amount * q / 4))
                )
    from source_story import craft_xp

    craft_xp(p, "salvaging")
    print("Equipment salvaged. Equipped, favourite and bound items were protected.")


BUILDING_MATERIALS = ("Timber", "Stone", "Iron fittings")


def gather_building_material(player, rng):
    from wander_reference import BUILDING_SUPPLY

    if rng.random() < BUILDING_SUPPLY:
        name = rng.choice(BUILDING_MATERIALS)
        bag = player.setdefault("building_materials", {})
        bag[name] = bag.get(name, 0) + 1
        print(f"Building supply found: 1 {name}.")


def upgrade_buildings(game, village):
    p = game.player
    record = state(p, village)
    while True:
        bag = p.setdefault("building_materials", {})
        print("\n--- VILLAGE BUILDINGS · " + village["name"] + " ---")
        print(
            "Materials: "
            + ", ".join(f"{name}: {bag.get(name,0)}" for name in BUILDING_MATERIALS)
        )
        for i, key in enumerate(village["services"], 1):
            level = building_level(p, village, key)
            print(
                f"{i}. {SERVICE_NAMES[key]} · Level {level}/5 · "
                + (
                    "MAX"
                    if level >= 5
                    else f"next level: {level*2} Timber, {level*2} Stone, {level} Iron fittings, {level*50} souls"
                )
            )
        print(
            "W. Convert one carried wood into 2 Timber\nM. Convert one carried metal into 2 Iron fittings\n0. Back"
        )
        print(
            "Find building supplies while wandering (25% per wander). Upgrades improve this village only; new shop capacity applies at the next restock."
        )
        c = input("Building > ").strip().lower()
        if c == "0":
            return
        if c in ("w", "m"):
            key = "woods" if c == "w" else "metals"
            material = "Timber" if c == "w" else "Iron fittings"
            if not p.get(key):
                print("No carried material to convert.")
                continue
            names = list(dict.fromkeys(p[key]))
            for i, name in enumerate(names, 1):
                print(f"{i}. {name} ({p[key].count(name)} owned)")
            try:
                index = int(input("Material number (0 cancel) > ")) - 1
            except ValueError:
                continue
            if not 0 <= index < len(names):
                continue
            p[key].remove(names[index])
            bag[material] = bag.get(material, 0) + 2
            print("Building materials prepared.")
            continue
        try:
            index = int(c) - 1
        except ValueError:
            continue
        if not 0 <= index < len(village["services"]):
            continue
        key = village["services"][index]
        level = building_level(p, village, key)
        if level >= 5:
            print("Already at maximum level.")
            continue
        required = {"Timber": level * 2, "Stone": level * 2, "Iron fittings": level}
        if (
            any(bag.get(name, 0) < count for name, count in required.items())
            or p["gold"] < level * 50
        ):
            print("Not enough materials or souls.")
            continue
        if (
            input(f"Upgrade {SERVICE_NAMES[key]} to Level {level+1}? (y/n) > ")
            .strip()
            .lower()
            != "y"
        ):
            continue
        for name, count in required.items():
            bag[name] -= count
        p["gold"] -= level * 50
        record["levels"][key] = level + 1
        print(
            f"{SERVICE_NAMES[key]} upgraded to Level {level+1}! Local service bonuses improve immediately."
        )


def register_visit(player, village, rng):
    """One arrival counts once; browsing menus never advances development."""
    record = state(player, village)
    record["visits"] = record.get("visits", 0) + 1
    if "next_development" not in record:
        record["next_development"] = record["visits"] - 1 + rng.randint(10, 15)
    if record["visits"] < record["next_development"]:
        return
    eligible = [
        key for key in village["services"] if building_level(player, village, key) < 5
    ]
    if eligible:
        key = rng.choice(eligible)
        record["levels"][key] = building_level(player, village, key) + 1
        event = f"Visit {record['visits']}: residents improved {SERVICE_NAMES[key]} to Level {record['levels'][key]}."
    else:
        # Growth stays useful after every workshop reaches the level cap.
        record["reputation"] = min(100, record.get("reputation", 0) + 1)
        event = f"Visit {record['visits']}: a community celebration increased your reputation. All buildings are already Level 5."
    record.setdefault("development_log", []).append(event)
    record["development_log"] = record["development_log"][-30:]
    record["next_development"] = record["visits"] + rng.randint(10, 15)
    print("Village development! " + event)
    print(
        "Residents keep improving this settlement between your journeys. Shop increases apply on the next restock."
    )


def development_status(player, village):
    record = state(player, village)
    left = max(0, record.get("next_development", 10) - record.get("visits", 0))
    return f"{record.get('visits', 0)} visits · next resident improvement in {left} visits (10–15 visits between improvements)."


def material_catalog(village):
    tier = (data.REGIONS + [data.SECRET_REGION]).index(village["region"])
    variant = village.get("stock_variant", 0)
    # Rare materials remain tied to later regions; early traders cannot sell Creator Alloy.
    metals = list(data.METALS)[: min(len(data.METALS), 2 + tier)]
    woods = list(data.WOODS)[: min(len(data.WOODS), 2 + tier)]
    index = (tier + variant) % len(metals)
    wi = (tier + variant) % len(woods)
    return [
        dict(
            name=metals[index],
            bag="metals",
            price=35 + 3 * data.METALS[metals[index]]["atk"],
        ),
        dict(name=woods[wi], bag="woods", price=30 + wi * 4),
        dict(name="Timber", bag="building_materials", price=12),
        dict(name="Stone", bag="building_materials", price=12),
        dict(name="Iron fittings", bag="building_materials", price=20),
    ]


def material_rows(player, village):
    record = state(player, village)
    if record.get("material_cycle") != cycle(player):
        record["material_cycle"] = cycle(player)
        record["material_stock"] = {
            x["name"]: 1
            + building_level(player, village, "trade")
            + village.get("stock_variant", 0)
            for x in material_catalog(village)
        }
    rate = max(0.5, 1 - 0.03 * (service_quality(player, village, "trade") - 1))
    return [
        dict(
            x,
            price=max(1, round(x["price"] * rate)),
            left=record["material_stock"].get(x["name"], 0),
        )
        for x in material_catalog(village)
    ]


def material_shop(game, village):
    if not has_service(game, "trade"):
        return
    p = game.player
    rows = material_rows(p, village)
    print("\n--- LOCAL MATERIAL STOCK ---")
    for i, row in enumerate(rows, 1):
        print(f"{i}. {row['name']} — {row['price']} souls each; {row['left']} left")
    print("Stock refreshes every 20 wanders, not on revisits.")
    try:
        index = int(input("Material number (0 back) > ")) - 1
    except ValueError:
        return
    if not 0 <= index < len(rows):
        return
    row = rows[index]
    if row["left"] < 1:
        print("Sold out.")
        return
    if p["gold"] < row["price"]:
        print("Not enough souls.")
        return
    p["gold"] -= row["price"]
    state(p, village)["material_stock"][row["name"]] -= 1
    if row["bag"] == "building_materials":
        bag = p.setdefault("building_materials", {})
        bag[row["name"]] = bag.get(row["name"], 0) + 1
    else:
        p.setdefault(row["bag"], []).append(row["name"])
    print("Bought " + row["name"] + ".")
