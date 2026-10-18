"""Ten settlement systems: shared storage, gardens, defence and restoration."""

from copy import deepcopy
import data
import original_ui as ui
import village_life as villages
from expansion_state import state, mark, pay, choose


def project(player, village):
    return state(player)["projects"].setdefault(village["id"], {})


def defence(game, village):
    p = game.player
    local = project(p, village)
    cycle = p.get("wander_count", 0) // 20
    if local.get("defence_cycle") == cycle:
        print("This settlement’s defence contract is finished for this cycle.")
        return
    roles = ["defend", "gather", "repair", "treat"]
    assignments = []
    from village_jobs import workers

    available = [w for w in workers(p, village) if w["id"] in village["services"]][:3]
    for worker in available:
        index = choose("ASSIGN " + worker["name"], roles)
        if index is None:
            return
        assignments.append(
            dict(worker=worker["name"], role=roles[index], level=worker["level"])
        )
    repair = sum(x["level"] for x in assignments if x["role"] == "repair")
    if repair and not pay(p, materials={"Timber": 1}):
        print("Repair teams need one Timber.")
        return
    defenders = sum(
        x["level"] for x in assignments if x["role"] == "defend"
    ) + local.get("watch_training", 0)
    healers = sum(x["level"] for x in assignments if x["role"] == "treat")
    if healers:
        p["hp"] = min(p["max_hp"], p["hp"] + healers * 3)
    enemy = dict(
        name=village["name"] + " Siege Raider",
        hp=45 + p["level"] * 7,
        atk=max(2, 10 + p["level"] - defenders - repair),
        **{"def": 2},
        xp=30,
        gold=25,
        intelligent=True
    )
    local["defence_assignments"] = assignments
    local["defence_cycle"] = cycle
    from expansion_combat import encounter

    if encounter(game, [enemy], terrain=None):
        gatherers = sum(x["level"] for x in assignments if x["role"] == "gather")
        pool = data.REGION_INGREDIENTS.get(village["region"], [])
        if pool:
            p.setdefault("ingredients", []).extend([pool[0]] * min(6, gatherers))
        p["gold"] += 80
        local["defences_won"] = local.get("defences_won", 0) + 1
        villages.state(p, village)["reputation"] = (
            villages.state(p, village).get("reputation", 0) + 2
        )
        from village_jobs import advance

        advance(p, village, 2)
        print(
            "Village defended. Gatherers delivered "
            + str(min(6, gatherers))
            + " ingredients. +80 souls and +2 reputation."
        )
    local["defence_assignments"] = []


def activity(game, feature):
    p = game.player
    v = ui.village
    if not v:
        print("Enter a village first, then choose Community activities.")
        return
    local = project(p, v)
    cycle = p.get("wander_count", 0) // 20
    if feature == 21:
        if not local.get("storehouse"):
            if not pay(p, 30, {"Timber": 3, "Stone": 2}):
                print("Build a storehouse with 30 souls, 3 Timber and 2 Stone.")
                return
            local["storehouse"] = {x: 0 for x in villages.BUILDING_MATERIALS}
        bank = local["storehouse"]
        print("Stored locally: " + str(bank))
        index = choose(
            "STOREHOUSE",
            ["Deposit construction supplies", "Withdraw construction supplies"],
        )
        if index is None:
            return
        material = choose("MATERIAL", list(villages.BUILDING_MATERIALS))
        if material is None:
            return
        name = villages.BUILDING_MATERIALS[material]
        try:
            amount = int(input("Amount (0 cancel) > "))
        except ValueError:
            return
        if amount <= 0:
            return
        carried = p.setdefault("building_materials", {})
        source, destination = (carried, bank) if index == 0 else (bank, carried)
        if source.get(name, 0) < amount or (
            index == 0 and sum(bank.values()) + amount > 100
        ):
            print("Not enough supply or storehouse full (100 total).")
            return
        source[name] -= amount
        destination[name] = destination.get(name, 0) + amount
        mark(p, 21)
    elif feature == 22:
        if local.get("roads"):
            print("Roads repaired: local work fees -20%, gathering yields +1.")
            return
        if not pay(p, 30, {"Timber": 3, "Stone": 3}):
            print("Road repairs need 30 souls, 3 Timber and 3 Stone.")
            return
        local["roads"] = True
        mark(p, 22)
        print(
            "Local transport restored. Work commissions are cheaper and gathering crews bring one extra resource."
        )
    elif feature == 23:
        from village_jobs import record

        clock = record(p, v).get("work_clock", 0)
        if not local.get("greenhouse_built"):
            if not pay(p, 25, {"Timber": 3, "Stone": 1}):
                print("Greenhouse needs 25 souls, 3 Timber and one Stone.")
                return
            local["greenhouse_built"] = True
        plots = local.setdefault("greenhouse", [])
        index = choose(
            "GREENHOUSE · TWO PLOTS",
            ["Plant a regional ingredient", "Harvest ready plants"],
        )
        if index == 0:
            pool = [
                x
                for x in data.REGION_INGREDIENTS.get(v["region"], [])
                if x in p.get("ingredients", [])
            ]
            if len(plots) >= 2 or not pool:
                print("Need a free plot and a local ingredient seed.")
                return
            seed = pool[-1]
            p["ingredients"].remove(seed)
            plots.append(dict(seed=seed, ready=clock + 3))
            print("Planted " + seed + ".")
        elif index == 1:
            grown = [x for x in plots if x["ready"] <= clock]
            for x in grown:
                p.setdefault("ingredients", []).extend([x["seed"]] * 3)
                plots.remove(x)
            print("Harvested " + str(len(grown)) + " plants, three ingredients each.")
        if index is not None:
            mark(p, 23)
    elif feature == 24:
        c = choose(
            "VILLAGE WATCH",
            [
                "Donate a spare unbound weapon to train the watch (max rank 3)",
                "Begin village defence and assign workers",
            ],
        )
        if c == 0:
            from artisan_addons import unbound

            eligible = [w for w in unbound(p) if w is not p.get("weapon")]
            index = choose("DONATE EQUIPMENT", [x["name"] for x in eligible])
            if index is None:
                return
            if local.get("watch_training", 0) >= 3:
                print("Watch training is already at rank 3.")
                return
            p["weapons"].remove(eligible[index])
            local["watch_training"] = local.get("watch_training", 0) + 1
            mark(p, 24)
        elif c == 1:
            defence(game, v)
            mark(p, 24)
    elif feature == 25:
        if local.get("kitchen_cycle") != cycle:
            local.update(kitchen_cycle=cycle, kitchen_meals=0)
        if local["kitchen_meals"] >= 2:
            print("The kitchen has enough donations for this cycle.")
            return
        from addon_quests import food_take

        if not food_take(p, 1):
            print("Bring one carried food for the refugees.")
            return
        local["kitchen_meals"] += 1
        villages.state(p, v)["reputation"] = (
            villages.state(p, v).get("reputation", 0) + 1
        )
        mark(p, 25)
        print("A refugee meal served; +1 local reputation.")
    elif feature == 26:
        service = choose("INVITE A SPECIALIST · 60 SOULS", v["services"])
        if service is None:
            return
        if local.get("visitor", {}).get("shifts", 0) > 0:
            print("A visiting artisan is already here.")
            return
        if not pay(p, 60):
            print("Need 60 souls.")
            return
        local["visitor"] = dict(service=v["services"][service], shifts=4)
        mark(p, 26)
        print(
            "Specialist invited for four local activity shifts: +2 effective quality to that service."
        )
    elif feature == 27:
        if local.get("festival_cycle") == cycle:
            print("This cycle’s festival is already over.")
            return
        from addon_quests import food_take

        if p["gold"] < 20 or not food_take(p, 1):
            print("Bring one carried food and 20 souls.")
            return
        pay(p, 20)
        local["festival_cycle"] = cycle
        answer = choose(
            "FESTIVAL HISTORY RIDDLE: WHY DO THE FOUR CLANS GUARD THEIR CORES?",
            [
                "Their cores protect their people; eleven others were destroyed",
                "They want to conquer the Dreamscape",
                "The cores are ordinary trading goods",
            ],
        )
        if answer == 0:
            p["mana"] = p.get("mana", 0) + 10
            villages.state(p, v)["reputation"] = (
                villages.state(p, v).get("reputation", 0) + 1
            )
            print("Correct! +10 mana and +1 reputation.")
        mark(p, 27)
    elif feature == 28:
        if local.get("vote_cycle") == cycle:
            print("One village vote per exploration cycle.")
            return
        services = [
            key for key in v["services"] if villages.building_level(p, v, key) < 5
        ]
        index = choose("PUBLIC BUILDING VOTE · 15 SOULS + 2 STONE", services)
        if index is None:
            return
        if not pay(p, 15, {"Stone": 2}):
            print("Bring 15 souls and two Stone.")
            return
        import hashlib

        seed = int(hashlib.sha256((v["id"] + str(cycle)).encode()).hexdigest()[:8], 16)
        votes = [seed % len(services), (seed // 7) % len(services), index, index]
        winner = max(range(len(services)), key=lambda i: (votes.count(i), i == index))
        key = services[winner]
        villages.state(p, v)["levels"][key] = villages.building_level(p, v, key) + 1
        local["vote_cycle"] = cycle
        mark(p, 28)
        print(
            "Residents voted: "
            + str([services[x] for x in votes])
            + ". "
            + key
            + " upgraded."
        )
    elif feature == 29:
        if local.get("clean_water"):
            print("The restored well improves inn and restaurant quality by one.")
            return
        if not pay(p, 20, {"Timber": 2, "Stone": 3}):
            print("Restore the well with 20 souls, two Timber and three Stone.")
            return
        local["clean_water"] = True
        mark(p, 29)
        print("Clean water restored. Local meals and recovery improve immediately.")
    elif feature == 30:
        if v["region"] not in p.get("bosses_defeated", []):
            print(
                "Free this region from its guardian before restoring a ruined settlement."
            )
            return
        if local.get("restored_refuge"):
            print("The rebuilt refuge is already in your Village Directory.")
            return
        if not pay(p, 150, {"Timber": 8, "Stone": 8, "Iron fittings": 3}):
            print(
                "Restoration needs 150 souls, eight Timber, eight Stone and three Iron fittings."
            )
            return
        name = v["region"] + " Rebuilt Refuge"
        local["restored_refuge"] = name
        p.setdefault("discovered_structures", {}).setdefault(v["region"], []).append(
            name
        )
        mark(p, 30)
        print(
            "Rebuilt "
            + name
            + ". Its lost core is not recreated. Revisit through the Village Directory."
        )
