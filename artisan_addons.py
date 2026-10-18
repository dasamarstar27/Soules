"""Specialties, tools, apprentices, commissions and constrained equipment work."""

from copy import deepcopy
import data
from expansion_state import state, mark, pay, choose


def professions(player):
    return state(player)["professions"]


def record_materials(player):
    from collections import Counter

    info = professions(player)
    counts = {
        bag: dict(Counter(player.get(bag, [])))
        for bag in ("metals", "woods", "cloths", "leathers", "cores")
    }
    previous = info.get("material_counts")
    info["material_counts"] = counts
    if previous is None:
        return
    origins = info.setdefault("material_origins", {})
    from challenge_progress import update

    gained = sum(
        max(0, amount - previous.get(bag, {}).get(name, 0))
        for bag, items in counts.items()
        for name, amount in items.items()
    )
    if gained:
        update(player, "material_collect", gained)
    for bag, items in counts.items():
        for name, amount in items.items():
            if amount > previous.get(bag, {}).get(name, 0):
                regions = origins.setdefault(name, [])
                if player["region"] not in regions:
                    regions.append(player["region"])


def material_sources(player, materials):
    known = professions(player).get("material_origins", {})
    if isinstance(materials, dict):
        names = [
            str(value) if key in ("core", "metal", "wood") else key
            for key, value in materials.items()
        ]
    else:
        names = list(materials or [])
    return {
        name: list(known.get(name, [])) or ["unknown / acquired before records"]
        for name in names
    }


def apply_traits(player, item, profession):
    if item.get("artisan_traits_applied"):
        return
    info = professions(player)
    specialty = info.get(profession + "_specialty")
    item["provenance"] = player["region"]
    item["maker"] = player["name"]
    item["material_origins"] = material_sources(
        player, item.get("materials", item.get("runes", []))
    )
    item["artisan_traits_applied"] = True
    if not item.get("commissioned"):
        from challenge_progress import update

        update(player, "craft_count")
    materials = item.get("materials", [])
    if isinstance(materials, dict):
        materials = [
            v if k in ("core", "metal", "wood") else k for k, v in materials.items()
        ]
    mastery = player.setdefault("material_mastery", {})
    for material in materials:
        progress = mastery.setdefault(material, dict(xp=0, level=0))
        progress["xp"] += 10
        if progress["xp"] >= (progress["level"] + 1) * 50 and progress["level"] < 5:
            progress["xp"] -= (progress["level"] + 1) * 50
            progress["level"] += 1
    if materials:
        bonus = min(2, sum(mastery[x]["level"] for x in materials))
        stat = {"smithing": "atk", "weaving": "def", "enchanting": "power"}[profession]
        item[stat] = item.get(stat, 0) + bonus
    if specialty:
        if profession == "smithing":
            item["atk"] = item.get("atk", 0) + (
                3 if specialty == "tempering" else 2 if specialty == "balanced" else 5
            )
        elif profession == "weaving":
            item["def"] = item.get("def", 0) + (3 if specialty == "protection" else 1)
            if specialty == "resistance":
                item["element_resistance"] = 0.15
            if specialty == "movement":
                item["damage_reduction"] = 0.08
        else:
            item["power"] = item.get("power", 0) + 2
        item["specialty"] = specialty
        if specialty == "heavy arms":
            item["slow_strikes"] = True
    tool = info.get("tool", {})
    if tool.get("durability", 0) > 0:
        key = (
            "atk"
            if profession == "smithing"
            else "def" if profession == "weaving" else "power"
        )
        item[key] = item.get(key, 0) + 1
        tool["durability"] -= 1
    if info.get("mastered", {}).get(profession):
        item["masterwork"] = True
    apprentice = info.get("apprentice", 0)
    if apprentice:
        item["value"] = item.get("value", 0) + apprentice
    mark(player, 34)


def unbound(player):
    return [
        w
        for w in player.get("weapons", [])
        if not any(
            w.get(k) for k in ("rune", "elemental_charged", "charged", "stored_runes")
        )
    ]


def activity(game, feature):
    p = game.player
    info = professions(p)
    if feature in (31, 32):
        profession = "smithing" if feature == 31 else "weaving"
        options = (
            ["tempering", "balanced", "heavy arms"]
            if feature == 31
            else ["protection", "movement", "resistance"]
        )
        if info.get(profession + "_specialty"):
            print("Already specialised in " + info[profession + "_specialty"] + ".")
            return
        from source_story import rank

        if rank(p, profession) < 2:
            print("Reach profession rank 2 first by successful crafting.")
            return
        index = choose("SPECIALTY", options)
        if index is not None:
            info[profession + "_specialty"] = options[index]
            mark(p, feature)
            print("New crafts inherit this specialty. Permanent runes are untouched.")
    elif feature == 33:
        cycle = p.get("wander_count", 0) // 20
        if info.get("commission_cycle") == cycle:
            print("This artisan already received an order this cycle.")
            return
        eligible = [
            w for w in unbound(p) if w is not p.get("weapon") and w.get("atk", 0) >= 12
        ]
        index = choose(
            "ARTISAN ORDER: DELIVER A SPARE WEAPON WITH AT LEAST 12 ATK",
            [f"{w['name']} · {w.get('atk',0)} ATK → 120 souls" for w in eligible],
        )
        if index is None:
            return
        p["weapons"].remove(eligible[index])
        p["gold"] += 120
        info["commission_cycle"] = cycle
        mark(p, 33)
    elif feature == 34:
        for key in ("weapons", "armours", "staffs"):
            for item in p.get(key, []):
                print(
                    item["name"]
                    + " · origin "
                    + item.get("provenance", "older item; origin unknown")
                    + " · maker "
                    + item.get("maker", item.get("artisan", "unknown"))
                    + " · materials "
                    + str(item.get("material_origins", {}))
                )
        mark(p, 34)
    elif feature == 35:
        print(
            "An artisan toolkit grants +1 to a new craft while it has durability. 15 souls and one Iron fitting repairs it to 10 uses."
        )
        if pay(p, 15, {"Iron fittings": 1}):
            info["tool"] = {"durability": 10}
            mark(p, 35)
            print("Toolkit repaired to 10 uses.")
        else:
            print("Bring 15 souls and one Iron fitting.")
    elif feature == 36:
        if info.get("apprentice", 0) >= 3:
            print(
                "Your apprentice is fully trained. Batch commissions can hold three extra collected orders."
            )
            return
        if not pay(p, 60):
            print("Training costs 60 souls per rank.")
            return
        info["apprentice"] = info.get("apprentice", 0) + 1
        mark(p, 36)
        print(
            "Apprentice rank "
            + str(info["apprentice"])
            + ". Your next weapon commission can request an extra item for its full material and labour cost."
        )
    elif feature == 37:
        from source_story import rank

        eligible = [x for x in ("smithing", "weaving", "enchanting") if rank(p, x) >= 5]
        index = choose("MASTERWORK TRIAL", eligible)
        if index is None:
            return
        from expansion_combat import practice

        if practice(game):
            info.setdefault("mastered", {})[eligible[index]] = True
            mark(p, 37)
            print(
                "Masterwork certification earned. New equipment can carry your signature."
            )
    elif feature == 38:
        items = unbound(p)
        index = choose(
            "REFORGE UNBOUND PHYSICAL WEAPON",
            [f"{w['name']} · {w.get('reforges',0)}/3 reforges" for w in items],
        )
        if index is None:
            return
        item = items[index]
        if item.get("reforges", 0) >= 3 or not p.get("metals") or not pay(p, 20):
            print("Need one metal, 20 souls and a weapon below three reforges.")
            return
        p["metals"].pop(0)
        item["atk"] = item.get("atk", 0) + 2
        item["reforges"] = item.get("reforges", 0) + 1
        mark(p, 38)
        print("Physical attack +2. Bound weapons are never eligible.")
    elif feature == 39:
        patterns = info.setdefault("patterns", [])
        if p.get("protected_relics") and "warded coat" not in patterns:
            patterns.append("warded coat")
        if "padded coat" not in patterns:
            patterns.append("padded coat")
        index = choose("TEXTILE PATTERN · TWO CLOTHS AND 35 SOULS", patterns)
        if index is None:
            return
        if len(p.get("cloths", [])) < 2 or not pay(p, 35):
            print("Need two cloths and 35 souls.")
            return
        del p["cloths"][:2]
        item = dict(
            name=patterns[index].title(),
            value=20,
            **{"def": 9 if patterns[index] == "padded coat" else 12},
        )
        if patterns[index] == "warded coat":
            item["element_resistance"] = 0.1
        apply_traits(p, item, "weaving")
        p.setdefault("armours", []).append(item)
        mark(p, 39)
        print("Armour crafted from the learned pattern.")
    elif feature == 40:
        items = [
            x
            for bag in ("weapons", "armours", "staffs")
            for x in p.get(bag, [])
            if x.get("masterwork")
        ]
        index = choose("SIGN A MASTERWORK", [x["name"] for x in items])
        if index is None:
            return
        signature = input("Signature (up to 40 characters) > ").strip()[:40]
        if signature:
            items[index]["signature"] = signature
            items[index]["maker"] = p["name"]
            mark(p, 40)
