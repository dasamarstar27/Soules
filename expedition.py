"""Regional exploration activities, finite sites and route preparation."""

from copy import deepcopy
import data
from expansion_state import state, mark, pay, count, choose


def field(player):
    return state(player)["field"]


def turn(player):
    player["wander_count"] = player.get("wander_count", 0) + 1
    player["hunger"] = max(0, player.get("hunger", 100) - 3)
    count(player, "field_actions")


def quota(player, key, limit=2):
    cycle = player.get("wander_count", 0) // 20
    record = (
        field(player)
        .setdefault("sites", {})
        .setdefault(player["region"] + "::" + key, {"cycle": cycle, "used": 0})
    )
    if record["cycle"] != cycle:
        record.update(cycle=cycle, used=0)
    if record["used"] >= limit:
        return False
    record["used"] += 1
    return True


def observe(player):
    observations = field(player).setdefault("observations", [])
    text = (
        player["region"]
        + " · "
        + player.get("weather", "Clear")
        + " · "
        + ("night" if player.get("is_night") else "day")
    )
    if text not in observations:
        observations.append(text)
    field(player).setdefault("regions", {})[player["region"]] = player.get(
        "wander_count", 0
    )


def activity(game, feature):
    p = game.player
    f = field(p)
    r = p["region"]
    rng = game.random
    if feature == 41:
        bait = p.get("ingredients", [])
        print(
            "Fishing: one regional ingredient as bait, two catches per 20-wander cycle."
        )
        if not bait or not quota(p, "fishing"):
            print("Bring bait or wait for the fishing spot to replenish.")
            return
        bait.pop(0)
        turn(p)
        fish = dict(name=r + " River Fish", food=True, hunger=20, value=12, region=r)
        p.setdefault("inventory", []).append(fish)
        print("Caught " + fish["name"] + ". Eat it or cook with it.")
        mark(p, 41)
    elif feature == 42:
        if not quota(p, "mining", 3):
            print("The local vein is exhausted this cycle.")
            return
        index = (data.REGIONS + [data.SECRET_REGION]).index(r)
        native = {
            "Whispering Woods": "Iron",
            "Ashen Wastes": "Iron",
            "Crimson Depths": "Crimson Steel",
            "Frostbound Tundra": "Froststeel",
            "Crystal Spire": "Crystal Alloy",
            "Sunken Coast": "Iron",
            "Ironpeak Mountains": "Titanium",
            "Blight Swamp": "Iron",
            "Shadow Vale": "Shadow Iron",
            "Infernal Depths": "Infernium",
            "Celestial Expanse": "Celestium",
            "Riftlands": "Riftsteel",
            "Abyss of Souls": "Soulsteel",
            "Shattered Wastes": "Void Alloy",
            "The Dreamscape": "Chronosteel",
            data.SECRET_REGION: "Creator Alloy",
        }[r]
        p.setdefault("metals", []).append(native)
        p.setdefault("building_materials", {})["Stone"] = (
            p.get("building_materials", {}).get("Stone", 0) + 1
        )
        turn(p)
        print("Mined " + native + " and one Stone.")
        mark(p, 42)
    elif feature == 43:
        weather = p.get("weather", "Clear")
        print(
            "Weather trail: "
            + weather
            + ". Clear reveals landmarks; fog reveals tracks; storms expose ore."
        )
        if not quota(p, "weather_trail", 1):
            print("Already surveyed this trail during this cycle.")
            return
        turn(p)
        if weather == "Clear":
            known = p.setdefault("discovered_structures", {}).setdefault(r, [])
            pool = [
                s for s in data.REGION_STRUCTURES.get(r, []) if s["name"] not in known
            ]
            if pool:
                known.append(pool[0]["name"])
                print("Mapped " + pool[0]["name"] + ".")
        elif weather in ("Stormy", "Storm"):
            p.setdefault("building_materials", {})["Stone"] = (
                p.get("building_materials", {}).get("Stone", 0) + 2
            )
            print("Storm runoff exposed two Stone.")
        else:
            f["tracking_discount"] = True
            print("Fresh tracks will save your next tracking fee.")
        mark(p, 43)
    elif feature == 44:
        monsters = data.NORMAL_MONSTERS.get(r, [])
        index = choose("TRACK A CREATURE", [x["name"] for x in monsters])
        if index is None:
            return
        if not f.pop("tracking_discount", False) and not pay(p, 10):
            print("Need 10 souls for scouting supplies.")
            return
        f["tracked_target"] = dict(region=r, enemy=deepcopy(monsters[index]))
        print(
            "Next wander here follows these tracks before ordinary random encounters."
        )
        mark(p, 44)
    elif feature == 45:
        if not quota(p, "survey", 1):
            print("Only one new survey per regional cycle.")
            return
        known = p.setdefault("discovered_structures", {}).setdefault(r, [])
        pool = [s for s in data.REGION_STRUCTURES.get(r, []) if s["name"] not in known]
        if pool:
            known.append(pool[0]["name"])
            print(
                "Surveyed "
                + pool[0]["name"]
                + ". Hidden clans are not on ordinary survey maps."
            )
        else:
            print("All ordinary landmarks here are already mapped.")
        turn(p)
        mark(p, 45)
    elif feature == 46:
        if not quota(p, "lost_camp", 1):
            print("You already searched the abandoned camp this cycle.")
            return
        c = choose(
            "LOST CAMP",
            [
                "Leave a ration for travellers: costs one food, +2 public trust",
                "Rest briefly: +10 HP, uses a local activity turn",
                "Read the abandoned diary",
            ],
        )
        if c is None:
            return
        if c == 0:
            from addon_quests import food_take

            if not food_take(p, 1):
                print("You have no food to leave.")
                return
            state(p)["relationships"]["public_trust"] = (
                state(p)["relationships"].get("public_trust", 0) + 2
            )
        elif c == 1:
            p["hp"] = min(p["max_hp"], p["hp"] + 10)
        else:
            print(
                "The diary remembers peaceful creatures before the invasion. A caravan may return if its routes are restored."
            )
        turn(p)
        mark(p, 46)
    elif feature == 47:
        observe(p)
        for text in f["observations"]:
            print(text)
        note = input("Add field note (blank keeps existing notes) > ").strip()[:240]
        if note:
            f.setdefault("notes", {})[r] = note
        mark(p, 47)
    elif feature == 48:
        contract = f.get("escort")
        if not contract:
            unlocked = [
                x for x in data.REGIONS if x in p["unlocked_regions"] and x != r
            ]
            index = choose("SAFE ESCORT DESTINATION", unlocked)
            if index is None:
                return
            if not pay(p, 10):
                print("Need 10 souls for escort supplies.")
                return
            f["escort"] = dict(
                origin=r, destination=unlocked[index], accepted=p.get("wander_count", 0)
            )
            print(
                "Escort accepted. Scout at least once and reach "
                + unlocked[index]
                + ", then return to this activity."
            )
        else:
            if (
                r != contract["destination"]
                or p.get("wander_count", 0) <= contract["accepted"]
            ):
                print("Scout a route and reach " + contract["destination"] + ".")
                return
            from addon_quests import food_take

            if not food_take(p, 1):
                print("Bring one carried food for the final leg.")
                return
            p["gold"] += 80 + (10 if state(p).get("systems", {}).get("mount") else 0)
            f.pop("escort")
            count(p, "escorts_completed")
            mark(p, 48)
            print("The escort arrived safely. +80 souls.")
    elif feature == 49:
        crossings = f.setdefault("crossings", {})
        c = choose(
            "UNSTABLE CROSSING",
            [
                "Repair: 3 Timber and 2 Stone; future crossings safe",
                "Scout: 15 souls; safe passage this time",
                "Risk the damaged crossing: a fight may occur",
            ],
        )
        if c is None:
            return
        if c == 0:
            if not pay(p, materials={"Timber": 3, "Stone": 2}):
                print("Need three Timber and two Stone.")
                return
            crossings[r] = True
            print("Crossing repaired. Local gathering crews gain one extra resource.")
        elif c == 1:
            if not pay(p, 15):
                print("Need 15 souls.")
                return
        elif not crossings.get(r) and rng.random() < 0.5:
            from expansion_combat import encounter

            if not encounter(
                game,
                [deepcopy(rng.choice(data.NORMAL_MONSTERS[r]))],
                terrain="crossing",
            ):
                return
        turn(p)
        mark(p, 49)
    elif feature == 50:
        if not quota(p, "peaceful_search", 1):
            print("The creatures need space; return next regional cycle.")
            return
        turn(p)
        if rng.random() > 0.25:
            print("No peaceful creature approaches today.")
            return
        from addon_quests import food_take

        print("An uncorrupted creature watches you. Offer one food to help it?")
        if input("(y/n) > ").strip().lower() == "y" and food_take(p, 1):
            ingredient = data.REGION_INGREDIENTS.get(r, ["Thorn Petal"])[0]
            p.setdefault("ingredients", []).append(ingredient)
            state(p)["relationships"]["wildlife_trust"] = (
                state(p)["relationships"].get("wildlife_trust", 0) + 1
            )
            print("It leaves " + ingredient + " beside your pack.")
            mark(p, 50)
        else:
            print("You give the creature space and observe it peacefully.")
            mark(p, 50)


def before_wander(game):
    p = game.player
    observe(p)
    tracked = field(p).get("tracked_target")
    if tracked and tracked["region"] == p["region"]:
        field(p).pop("tracked_target")
        game.fight(deepcopy(tracked["enemy"]))
        return True
    return False
