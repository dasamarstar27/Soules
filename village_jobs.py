"""Escrowed commissions, finite gathering crews and local activity-driven shifts."""

from copy import deepcopy
import hashlib
import random
import data
import village_life as villages
from expansion_state import number, pay, state, count

KINDS = {
    "weapon": ("forge", "metals", 3, 35),
    "armour": ("loom", "cloths", 2, 35),
    "staff": ("tower", "woods", 1, 40),
    "potion": ("alchemy", "ingredients", 2, 20),
    "gather": ("trade", None, 0, 15),
}


def record(player, village):
    local = villages.state(player, village)
    local.setdefault("work_orders", [])
    local.setdefault("work_serial", 0)
    return local


def workers(player, village):
    return [
        dict(
            id=key,
            name=village["name"] + " " + title,
            level=villages.building_level(player, village, key),
            quality=villages.service_quality(player, village, key),
        )
        for key, title in [
            ("forge", "Smith"),
            ("loom", "Weaver"),
            ("tower", "Enchanter"),
            ("alchemy", "Alchemist"),
            ("trade", "Gathering Crew"),
        ]
    ]


def order_fee(player, village, kind):
    from community_addons import project

    fee = KINDS[kind][3]
    if project(player, village).get("roads"):
        fee = max(1, round(fee * 0.8))
    market = state(player).get("systems", {}).get("town", {}).get("market", 0)
    return max(1, round(fee * (1 - 0.05 * market)))


def resources(kind, selections):
    if kind == "weapon":
        if len(selections) != 3:
            return []
        return list(zip(("metals", "cores", "woods"), selections))
    return [(KINDS[kind][1], name) for name in selections]


def commission_stock(player, village):
    local = record(player, village)
    cycle = villages.cycle(player)
    if local.get("commission_stock_cycle") != cycle:
        region_index = (data.REGIONS + [data.SECRET_REGION]).index(village["region"])
        local["commission_stock"] = {
            bag: {
                name: 3 for name in list(catalog)[: min(len(catalog), 2 + region_index)]
            }
            for bag, catalog in (
                ("metals", data.METALS),
                ("cores", data.CORES),
                ("woods", data.WOODS),
            )
        }
        local["commission_stock_cycle"] = cycle
    return local["commission_stock"]


def materials_cost(selections):
    return sum(
        (
            25
            if bag == "cores"
            else 10 + data.METALS.get(name, {}).get("atk", 0) if bag == "metals" else 15
        )
        for bag, name in selections
    )


def commission(
    player,
    village,
    kind,
    selections=None,
    resource="ingredients",
    assistant=False,
    village_stock=False,
):
    if kind not in KINDS:
        return False, "Unknown work order."
    service, bag, required, fee = KINDS[kind]
    if service not in village["services"]:
        return False, "This village lacks that workshop or crew."
    local = record(player, village)
    if len(local["work_orders"]) >= 30:
        return False, "Collect completed orders first."
    if not assistant and any(
        job["worker"] == service and job["remaining"] > 0
        for job in local["work_orders"]
    ):
        return False, "That worker is already assigned."
    selections = selections or []
    from collections import Counter

    supplied = resources(kind, selections)
    if len(selections) != required or (
        kind == "weapon"
        and (
            selections[0] not in data.METALS
            or selections[1] not in data.CORES
            or selections[2] not in data.WOODS
        )
    ):
        return (
            False,
            "Weapons require one metal, one ordinary core and one wood. Supply every listed material.",
        )
    counts = Counter(supplied)
    stock = commission_stock(player, village) if village_stock else None
    if any(
        (
            stock.get(bag, {}).get(name, 0)
            if stock is not None
            else player.get(bag, []).count(name)
        )
        < count
        for (bag, name), count in counts.items()
    ):
        return False, "Not enough carried materials or finite village commission stock."
    if kind == "potion" and frozenset(selections) not in data.INGREDIENT_COMBOS:
        return (
            False,
            "The alchemist cannot promise a potion from that unrecognised mixture.",
        )
    if kind == "gather":
        if resource not in ("ingredients", "woods", "metals", "Timber", "Stone"):
            return False, "Invalid gathering assignment."
        cycle = villages.cycle(player)
        if local.get("crew_cycle") != cycle:
            local.update(crew_cycle=cycle, crew_trips=0)
        if local["crew_trips"] >= 2:
            return (
                False,
                "Local gathering grounds need the next 20-wander restock (two trips per cycle).",
            )
    from community_addons import project
    from expansion_state import state as expansion_state

    fee = order_fee(player, village, kind) + (
        materials_cost(supplied) if village_stock else 0
    )
    if not pay(player, fee):
        return False, "Not enough souls."
    for bag, material in supplied:
        if village_stock:
            stock[bag][material] -= 1
        else:
            player[bag].remove(material)
    quality = villages.service_quality(player, village, service)
    from expansion_state import state as expansion_state

    friends = expansion_state(player)["relationships"].get("friends", {})
    if any(
        name.startswith(village["name"]) and person.get("rank", 0) >= 3
        for name, person in friends.items()
    ):
        quality += 1
    level = villages.building_level(player, village, service)
    local["work_serial"] += 1
    key = village["id"] + "::" + str(local["work_serial"])
    rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:12], 16))
    if kind in ("weapon", "armour", "staff"):
        stat = {"weapon": "atk", "armour": "def", "staff": "power"}[kind]
        base = 5 + quality * 2 + rng.randint(0, quality + 2)
        if kind == "weapon":
            base += data.METALS.get(selections[0], {}).get("atk", 0) // 2
        result = dict(
            name=f"{village['name']} {['Plain','Fine','Masterwork'][min(2,quality//3)]} {kind.title()}",
            value=fee // 2,
            provenance=village["region"],
            artisan=village["name"] + " " + service,
            commissioned=True,
            **{stat: base},
        )
        destination = {"weapon": "weapons", "armour": "armours", "staff": "staffs"}[
            kind
        ]
    elif kind == "potion":
        result = [data.INGREDIENT_COMBOS[frozenset(selections)]["name"]] * min(
            3, 1 + quality // 4
        )
        destination = "potions"
    else:
        region_index = (data.REGIONS + [data.SECRET_REGION]).index(village["region"])
        catalogs = {
            "ingredients": data.REGION_INGREDIENTS.get(village["region"], []),
            "metals": list(data.METALS)[: min(len(data.METALS), 2 + region_index)],
            "woods": list(data.WOODS)[: min(len(data.WOODS), 2 + region_index)],
            "Timber": ["Timber"],
            "Stone": ["Stone"],
        }
        pool = catalogs[resource]
        if not pool:
            raise ValueError("No local gathering catalogue.")
        extra = (
            (
                1
                if player.get("faction") == "frost_council" and rng.random() < 0.15
                else 0
            )
            + int(project(player, village).get("roads", False))
            + int(
                expansion_state(player)["field"]
                .get("crossings", {})
                .get(village["region"], False)
            )
        )
        result = [rng.choice(pool) for _ in range(min(9, 1 + level + extra))]
        destination = resource
        local["crew_trips"] += 1
    if isinstance(result, dict):
        from artisan_addons import apply_traits

        result["materials"] = list(selections)
        apply_traits(
            player,
            result,
            {"weapon": "smithing", "armour": "weaving", "staff": "enchanting"}[kind],
        )
        result["provenance"] = village["region"]
        result["maker"] = result["artisan"]
    job = dict(
        id=key,
        worker=(service + " apprentice" if assistant else service),
        kind=kind,
        remaining=max(
            1, 5 - level - (1 if player.get("faction") == "crimson_order" else 0)
        ),
        quality=quality,
        materials=list(selections),
        fee=fee,
        destination=destination,
        result=result,
        region=village["region"],
    )
    local["work_orders"].append(job)
    count(player, "commissions_placed")
    return (
        True,
        f'Work ordered: {kind}; {job["remaining"]} local activity shifts. Materials and {fee} souls are held for this order. Quality is based on this village’s Level {level} service.',
    )


def advance(player, village, shifts=1):
    local = record(player, village)
    local["work_clock"] = local.get("work_clock", 0) + shifts
    from community_addons import project

    visitor = project(player, village).get("visitor", {})
    if visitor:
        visitor["shifts"] = max(0, visitor.get("shifts", 0) - shifts)
    for job in record(player, village)["work_orders"]:
        job["remaining"] = max(0, job["remaining"] - shifts)


def advance_all(player):
    """One wander is one work shift everywhere; opening menus is not time."""
    for record_ in state(player)["projects"].values():
        if isinstance(record_, dict) and record_.get("visitor"):
            record_["visitor"]["shifts"] = max(
                0, record_["visitor"].get("shifts", 0) - 1
            )
    for local in player.get("village_records", {}).values():
        if not isinstance(local, dict):
            continue
        local["work_clock"] = local.get("work_clock", 0) + 1
        for job in local.get("work_orders", []):
            job["remaining"] = max(0, job["remaining"] - 1)


def collect(player, village, index):
    jobs = record(player, village)["work_orders"]
    if type(index) is not int or not 0 <= index < len(jobs):
        return False, "Choose a work order."
    job = jobs[index]
    if job["remaining"]:
        return False, "The work is still in progress."
    destination, result = job["destination"], deepcopy(job["result"])
    if destination in ("Timber", "Stone"):
        bag = player.setdefault("building_materials", {})
        bag[destination] = bag.get(destination, 0) + len(result)
    elif isinstance(result, list):
        player.setdefault(destination, []).extend(result)
    else:
        player.setdefault(destination, []).append(result)
    jobs.pop(index)
    if job["kind"] in ("weapon", "armour", "staff", "potion"):
        from challenge_progress import update

        update(player, "craft_count")
    count(player, "commissions_collected")
    return True, "Collected " + str(result) + ". Worker available again."


def menu(game, village):
    p = game.player
    while True:
        jobs = record(p, village)["work_orders"]
        print("\n--- VILLAGE WORKERS & COMMISSIONS ---")
        print(
            "One active assignment per specialist. Every Wander advances all orders one shift. Inn rest advances two shifts; productive local actions advance one. Gathering is finite. Leaving or reopening this menu does not advance work."
        )
        for worker in workers(p, village):
            if worker["id"] in village["services"]:
                print(
                    f"{worker['name']}: Level {worker['level']}, quality {worker['quality']}"
                )
        for i, job in enumerate(jobs, 1):
            print(
                f"Order {i}: {job['kind']} · {job['remaining']} shifts left · result {job['result']}"
            )
        for number, kind in enumerate(
            ("weapon", "armour", "staff", "potion", "gather"), 1
        ):
            if KINDS[kind][0] in village["services"]:
                print(
                    f"{number}. "
                    + ("Hire gatherers" if kind == "gather" else "Commission " + kind)
                )
        print("6. Collect order\n7. Work a local shift (5 souls, 5 hunger)")
        if "forge" in village["services"]:
            print("8. Apprentice batch commission")
        print("0. Back")
        c = input("Workers > ").strip()
        if c == "0":
            return
        if c == "8":
            level = state(p)["professions"].get("apprentice", 0)
            if not level:
                print("Train an apprentice through Adventures → Artisans first.")
                continue
            metal = choose_material(p, "metals")
            if metal is None:
                continue
            try:
                quantity = int(input(f"Batch quantity (1–{level+1}) > "))
            except ValueError:
                continue
            core = choose_material(p, "cores")
            wood = choose_material(p, "woods")
            if core is not None and wood is not None:
                print(batch(p, village, "weapon", [metal, core, wood], quantity)[1])
            continue
        if c == "6":
            index = number("Order number (0 cancel) > ", len(jobs))
            if index is not None:
                print(collect(p, village, index)[1])
            continue
        if c == "7":
            if p.get("hunger", 100) < 10:
                print("Eat before working a shift.")
                continue
            if not pay(p, 5):
                print("Not enough souls.")
                continue
            p["hunger"] -= 5
            advance(p, village)
            print("One local shift passed.")
            continue
        if c not in ("1", "2", "3", "4", "5"):
            continue
        kind = ["weapon", "armour", "staff", "potion", "gather"][int(c) - 1]
        service, bag, amount, fee = KINDS[kind]
        if service not in village["services"]:
            print("This village does not offer that service.")
            continue
        selections = []
        buy_stock = False
        resource = "ingredients"
        if kind == "gather":
            gathering_options = ["ingredients", "woods", "metals", "Timber", "Stone"]
            for i, x in enumerate(gathering_options, 1):
                print(f"{i}. {x}")
            index = number(
                "Gather which resource (0 cancel) > ", len(gathering_options)
            )
            if index is None:
                continue
            resource = gathering_options[index]
        elif kind == "weapon":
            provider = number(
                "Materials: 1 = supply your own; 2 = pay extra for village stock; 0 = cancel > ",
                2,
            )
            if provider is None:
                continue
            buy_stock = provider == 1
            for needed in ("metals", "cores", "woods"):
                pool = (
                    list(commission_stock(p, village).get(needed, {}))
                    if buy_stock
                    else list(dict.fromkeys(p.get(needed, [])))
                )
                for i, name in enumerate(pool, 1):
                    count_ = (
                        commission_stock(p, village).get(needed, {}).get(name, 0)
                        if buy_stock
                        else p.get(needed, []).count(name)
                    )
                    print(
                        f"{i}. {name} · {count_} available"
                        + (
                            f" · {materials_cost([(needed,name)])} extra souls"
                            if buy_stock
                            else " · supplied by you"
                        )
                    )
                index = number("Choose " + needed + " (0 = cancel) > ", len(pool))
                if index is None:
                    break
                selections.append(pool[index])
            if len(selections) != 3:
                continue
        else:
            pool = list(dict.fromkeys(p.get(bag, [])))
            for i, name in enumerate(pool, 1):
                print(f"{i}. {name} ({p[bag].count(name)} owned)")
            for _ in range(amount):
                index = number("Supply material (0 cancel) > ", len(pool))
                if index is None:
                    break
                selections.append(pool[index])
            if len(selections) != amount:
                continue
        fee = order_fee(p, village, kind) + (
            materials_cost(resources(kind, selections)) if buy_stock else 0
        )
        if (
            input(
                f"Pay {fee} souls ({'labour plus village materials' if buy_stock else 'labour; bring your materials'}) for {selections}? (y/n) > "
            )
            .strip()
            .lower()
            == "y"
        ):
            print(
                commission(
                    p, village, kind, selections, resource, village_stock=buy_stock
                )[1]
            )


def choose_material(player, bag):
    names = list(dict.fromkeys(player.get(bag, [])))
    for i, name in enumerate(names, 1):
        print(f"{i}. {name}")
    index = number("Material (0 cancel) > ", len(names))
    return names[index] if index is not None else None


def batch(player, village, kind, selections, quantity):
    from collections import Counter

    maximum = 1 + state(player)["professions"].get("apprentice", 0)
    if (
        type(quantity) is not int
        or not 1 <= quantity <= maximum
        or kind not in ("weapon", "armour", "staff", "potion")
    ):
        return False, "Invalid apprentice batch size."
    service, bag, amount, fee = KINDS[kind]
    fee = order_fee(player, village, kind)
    local = record(player, village)
    if len(local["work_orders"]) + quantity > 30:
        return False, "Collect completed orders first."
    if service not in village["services"] or any(
        j["worker"] == service and j["remaining"] > 0 for j in local["work_orders"]
    ):
        return False, "The required specialist is unavailable."
    if kind == "potion" and frozenset(selections) not in data.INGREDIENT_COMBOS:
        return False, "Unrecognised potion recipe."
    if state(player).get("systems", {}).get("mode", {}).get("id") == "budget_run":
        return False, "Budget mode blocks paid commissions."
    if (
        len(selections) != amount
        or any(
            player.get(material_bag, []).count(name) < n * quantity
            for (material_bag, name), n in Counter(resources(kind, selections)).items()
        )
        or player["gold"] < fee * quantity
    ):
        return (
            False,
            "Supply the full material and fee cost for every item in the batch.",
        )
    for i in range(quantity):
        okay, message = commission(player, village, kind, selections, assistant=i > 0)
        if not okay:
            return False, message
    return (
        True,
        f"{quantity} separate orders placed; your apprentice assists the specialist.",
    )


def validate_job(job, regions):
    kind = job.get("kind")
    if (
        kind not in (*KINDS, "drying")
        or not isinstance(job.get("id"), str)
        or job.get("region") not in regions
    ):
        raise ValueError("Invalid work-order identity.")
    for key, limit in [("fee", 100000), ("quality", 20)]:
        if type(job.get(key)) is not int or not 0 <= job[key] <= limit:
            raise ValueError("Invalid commission terms.")
    if not isinstance(job.get("materials"), list) or any(
        not isinstance(name, str) for name in job["materials"]
    ):
        raise ValueError("Invalid commission supplies.")
    result = job["result"]
    if kind in ("weapon", "armour", "staff"):
        key = {"weapon": "atk", "armour": "def", "staff": "power"}[kind]
        if (
            not isinstance(result, dict)
            or not isinstance(result.get("name"), str)
            or type(result.get(key)) not in (int, float)
            or not 0 <= result[key] <= 10**9
        ):
            raise ValueError("Invalid commissioned equipment.")
    elif (
        not isinstance(result, list)
        or len(result) > 20
        or any(not isinstance(name, str) for name in result)
    ):
        raise ValueError("Invalid commissioned supplies.")
