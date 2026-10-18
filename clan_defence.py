"""Season One clan visits, finite starter shops and the Whispering Woods defence."""

from copy import deepcopy
import data
import original_ui as ui
from expansion_state import state, choose, pay

ROLES = (
    "Defend the barricades",
    "Gather supplies",
    "Tend the wounded",
    "Repair the barricades",
)


def quest(player):
    return state(player)["activities"].setdefault(
        "woods_defence", dict(prepared=False, waves=0, assignments={}, complete=False)
    )


def known_clans(player):
    return [
        (region, clan)
        for region, clan in data.ELEMENTAL_VILLAGES.items()
        if clan["name"] in player.get("discovered_structures", {}).get(region, [])
    ]


def assign(player, region, role):
    if region not in dict(known_clans(player)) or role not in ROLES:
        return False, "Meet that clan before requesting its help."
    if quest(player)["complete"]:
        return False, "The Woods defence is already complete."
    quest(player)["assignments"][region] = role
    return (
        True,
        "Volunteers assigned: "
        + data.ELEMENTAL_VILLAGES[region]["name"]
        + " — "
        + role
        + ". Their core and its keepers stay at home.",
    )


def basic_market(game, clan):
    from season_two import GOODS, goods_line

    p = game.player
    cycle = p.get("wander_count", 0) // 20
    stock = (
        state(p)["activities"]
        .setdefault("clan_markets", {})
        .setdefault(clan["name"], {})
    )
    if stock.get("cycle") != cycle:
        stock.update(cycle=cycle, remaining=[3, 1, 1])
    food = deepcopy(GOODS[clan["element"]][3][1])
    food["food"] = True
    goods = [
        ("inventory", food, 25),
        (
            "weapons",
            dict(
                name=clan["name"] + " Scout Blade",
                atk=12,
                value=45,
                element=clan["element"],
            ),
            120,
        ),
        ("potions", "Health Potion", 80),
    ]
    while True:
        index = choose(
            "CLAN TRAVELLER SHOP · SEASON ONE",
            [
                goods_line(bag, item, price, stock["remaining"][i])
                for i, (bag, item, price) in enumerate(goods)
            ],
        )
        if index is None:
            return
        bag, item, price = goods[index]
        if stock["remaining"][index] <= 0:
            print("Sold out until the next 20-wander cycle.")
            continue
        if not pay(p, price):
            print(
                "This purchase requires the displayed souls and an allowed purchasing mode."
            )
            continue
        p.setdefault(bag, []).append(deepcopy(item))
        stock["remaining"][index] -= 1
        print(
            "Bought "
            + (item["name"] if isinstance(item, dict) else item)
            + ". You remain in the village."
        )


def defend_woods(game):
    p = game.player
    q = quest(p)
    if q["complete"]:
        print("Whispering Woods is already defended.")
        return False
    if p.get("source_story", {}).get("season_one_complete") or p.get("chapter", 1) >= 2:
        print(
            "This defence belongs to the Season One invasion. Clan raid contracts remain available."
        )
        return False
    if p["region"] != "Whispering Woods" or not q["prepared"]:
        print("Return to Whispering Woods and prepare the barricades first.")
        return False
    if q["waves"] >= 3:
        print("The three waves are beaten. Report to Elian in Old Village.")
        return False
    assigned = [
        role
        for region, role in q["assignments"].items()
        if region in dict(known_clans(p))
    ]
    repair = assigned.count(ROLES[3])
    defenders = assigned.count(ROLES[0])
    healers = assigned.count(ROLES[2])
    if repair and not pay(p, materials={"Timber": 1}):
        print("Assigned repair volunteers require one Timber for this wave.")
        return False
    p["hp"] = min(p["max_hp"], p["hp"] + 5 * healers)
    wave = q["waves"] + 1
    enemy = dict(
        name=["Dreamscape Woodstalker", "Riftborn Prowler", "Dreamscape Raid Captain"][
            wave - 1
        ],
        hp=18 + 4 * wave + 2 * p["level"],
        atk=max(2, 4 + wave + p["level"] // 2 - 2 * defenders - repair),
        **{"def": wave - 1},
        gold=10,
        xp=10,
    )
    from expansion_combat import encounter

    print(
        "WHISPERING WOODS · INVASION WAVE "
        + str(wave)
        + "/3. Volunteers: "
        + str(q["assignments"])
    )
    enemies = [enemy]
    # More attackers without multiplying the entire introductory wave's stats.
    enemy["hp"] = max(8, int(enemy["hp"] * 0.6))
    enemy["atk"] = max(2, int(enemy["atk"] * 0.65))
    for index in range(wave):
        enemies.append(
            dict(
                name=["Rift-touched Woodling", "Dreamscape Thornling", "Rift Howler"][
                    index
                ],
                hp=max(6, (18 + 4 * wave + 2 * p["level"]) // (wave + 1)),
                atk=max(
                    1, (4 + wave + p["level"] // 2) // (wave + 1) - defenders - repair
                ),
                **{"def": max(0, wave - 2)},
                gold=3,
                xp=3,
            )
        )
    print(
        f"{len(enemies)} monsters are attacking this wave. Defeat them all; use Change target to choose who you attack."
    )
    if not encounter(game, enemies):
        return False
    q["waves"] = wave
    gathered = 2 * assigned.count(ROLES[1])
    if gathered:
        bag = p.setdefault("building_materials", {})
        bag["Timber"] = bag.get("Timber", 0) + gathered
        print("Gathering volunteers delivered " + str(gathered) + " Timber.")
    print(
        "Wave repelled. "
        + (
            "Report to Elian in Old Village."
            if wave == 3
            else "You can rest, gather supplies or adjust clan assignments before the next wave."
        )
    )
    return True


def report(game):
    p = game.player
    q = quest(p)
    if q["complete"] or q["waves"] < 3:
        return (
            False,
            "Defeat all three invasion waves first; completed rewards cannot be repeated.",
        )
    if (
        not ui.village
        or ui.village["name"] != "Old Village"
        or p["region"] != "Whispering Woods"
    ):
        return False, "Report to Elian in Old Village, Whispering Woods."
    q["complete"] = True
    p["gold"] += 100
    game.gain_xp(30)
    p["inventory"].append(
        deepcopy(next(x for x in data.FOOD_ITEMS if x["name"] == "Traveller's Ration"))
    )
    from source_story import clue

    clue(
        p,
        "woods_defended",
        "Whispering Woods held against three waves of the Dreamscape invasion. Any clan volunteers helped without taking their protected cores from home.",
    )
    return (
        True,
        'Elian: "You gave these people a road home. The king still threatens the other regions; carry this hope with you." Main quest complete: 100 souls, 30 XP and a travelling ration.',
    )


def menu(game):
    p = game.player
    q = quest(p)
    if (
        p.get("chapter", 1) >= 2 or p.get("source_story", {}).get("season_one_complete")
    ) and not q["complete"]:
        print(
            "The Season One Woods defence has passed. You can still protect discovered clans through their raid option."
        )
        return
    while True:
        print("\n--- SEASON ONE MAIN QUEST · PROTECT WHISPERING WOODS ---")
        print(
            "Barricades: "
            + ("ready" if q["prepared"] else "need 2 Timber and 1 Stone")
            + f' · Waves beaten {q["waves"]}/3 · '
            + ("Complete" if q["complete"] else "In progress")
        )
        print(
            "The Dreamscape invasion threatens Old Village. Discovered clans may send volunteers, but finding a clan is not required. The four cores stay at home."
        )
        print("Assigned volunteers: " + str(q["assignments"]))
        c = choose(
            "WOODS DEFENCE",
            [
                "Hear Elian’s briefing",
                "Prepare barricades (2 Timber, 1 Stone)",
                "Assign discovered clan volunteers",
                "Fight the next invasion wave",
                "Report victory to Elian",
            ],
        )
        if c is None:
            return
        if c == 0:
            print(
                'Elian: "The monsters are crossing the old roads. Brace the village edge and hold three attacks. Ask any clans you have met for volunteers; we will hold even if no clan can spare help."'
            )
        elif c == 1:
            if q["complete"] or q["prepared"]:
                print("The barricades already stand.")
                continue
            if p["region"] != "Whispering Woods":
                print("Build the barricades in Whispering Woods.")
                continue
            if pay(p, materials={"Timber": 2, "Stone": 1}):
                q["prepared"] = True
                print(
                    "Barricades ready. No clan discovery is required to defend the Woods."
                )
            else:
                print("Gather two Timber and one Stone first.")
        elif c == 2:
            clans = known_clans(p)
            if not clans:
                print(
                    "No clans have been discovered yet. You can still defend the Woods with its local people."
                )
                continue
            index = choose("DISCOVERED CLANS", [v["name"] for _, v in clans])
            if index is None:
                continue
            role = choose(
                "ASSIGN VOLUNTEERS", list(ROLES) + ["Release this clan’s volunteers"]
            )
            if role == 4:
                q["assignments"].pop(clans[index][0], None)
                print("Volunteers released.")
            elif role is not None:
                print(assign(p, clans[index][0], ROLES[role])[1])
        elif c == 3:
            defend_woods(game)
        elif c == 4:
            print(report(game)[1])
