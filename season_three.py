"""Season Three: Beyond the Broken Bridge. The villain's motive stays unrevealed."""

from copy import deepcopy
import data
import original_ui as ui
from expansion_state import state, pay, mark, choose

STEPS = [
    "Prepare a controlled expedition after repairing the stabiliser.",
    "Meet Sera on the Written Shore and tune two protected core fragments to its ward.",
    "Defeat the Margin Warden and enter the Archive of Beginnings.",
    "Read the archive and uncover the purpose of the repeated rift interference.",
    "Choose an alliance and gather the four clans’ harmonic knowledge.",
    "Prepare a paired-element expedition weapon or staff.",
    "Stop the Hidden Hand in the Hall of Creation.",
    "Decide who may guard the instruments of creation.",
    "The expedition is complete; explore the optional Unwritten Vault.",
]


def progress(player):
    return state(player)["season_three"]


def objective(player):
    s = progress(player)
    return "Season Three · " + STEPS[min(8, s.get("stage", 0))]


def craft_pair(player, recipe):
    s = progress(player)
    if s.get("stage", 0) < 5:
        return False, "Reach the expedition preparation stage first."
    options = [
        ("Flame Rune", "Ice Rune", "Dawn-and-Dusk Blade", "weapons", "atk"),
        ("Nature Rune", "Light Rune", "Living Radiance Staff", "staffs", "power"),
    ]
    if recipe not in (0, 1):
        return False, "Choose a valid paired recipe."
    first, second, name, bag, stat = options[recipe]
    one = next(
        (
            r
            for r in player.get("runes", [])
            if r["name"] == first and r.get("effect") != "fusion"
        ),
        None,
    )
    two = next(
        (
            r
            for r in player.get("runes", [])
            if r["name"] == second and r.get("effect") != "fusion"
        ),
        None,
    )
    if not one or not two or player["gold"] < 75:
        return (
            False,
            f"Need two normal runes: {first} + {second}, and 75 souls. Fusions are not valid ingredients.",
        )
    if not pay(player, 75):
        return False, "This run mode blocks paid crafting."
    player["runes"].remove(one)
    player["runes"].remove(two)
    player.setdefault(bag, []).append(
        dict(
            name=name,
            **{stat: 32},
            value=100,
            elemental_charged=True,
            element="paired",
            rune=deepcopy(one),
            paired_effects=[one["effect"], two["effect"]],
            provenance="Written Shore",
        )
    )
    s["paired_craft"] = True
    return (
        True,
        "Created "
        + name
        + ". Its binding is permanent; neither rune is returned or spent by attacking.",
    )


def advance(game, choice=0):
    p = game.player
    s = progress(p)
    stage = s.get("stage", 0)
    if not p.get("source_story", {}).get("complete"):
        return False, "Finish Season Two and repair the stabiliser first."
    if stage >= 8:
        return False, "Season Three is already complete."
    if stage == 0:
        from addon_quests import food_take

        if p["gold"] < 50 or p.get("building_materials", {}).get("Timber", 0) < 2:
            return False, "Expedition needs 50 souls, two Timber and two carried foods."
        if state(p).get("systems", {}).get("mode", {}).get("id") == "budget_run":
            return False, "End Budget mode before funding the expedition."
        if not food_take(p, 2):
            return False, "Bring two carried foods."
        pay(p, 50, {"Timber": 2})
        p["chapter"] = 3
        p["unlocked_regions"].add(data.SECRET_REGION)
        p["region"] = data.SECRET_REGION
        s.update(area="Written Shore", stage=1)
        return (
            True,
            "The clans open a controlled path. Sera, an exiled archivist, waits on the Written Shore. She asks you to protect the surviving records.",
        )
    if stage == 1:
        fragments = [
            x for x in p.get("protected_relics", []) if x["kind"] == "fragment"
        ]
        if len(fragments) < 2:
            return (
                False,
                "Recover two protected broken-core fragments from ancient ruins first.",
            )
        s["tuned_fragments"] = [x["id"] for x in fragments[:2]]
        s["sera_helped"] = True
        print(
            'Sera: "They are pieces of the eleven lost cores. Their memory can hold this ward without destroying either fragment. My home was erased; I will not let these records vanish too."'
        )
    elif stage == 2:
        from expansion_combat import encounter

        allies = state(p)["relationships"].get("public_trust", 0) >= 3
        enemy = dict(
            name="Margin Warden",
            hp=95 + p["level"] * 6,
            atk=max(6, 12 + p["level"] - (3 if allies else 0)),
            **{"def": 5},
            xp=80,
            gold=100,
        )
        if not encounter(game, [enemy], terrain="Written Shore"):
            return False, "The Warden still guards the archive."
        s["area"] = "Archive of Beginnings"
    elif stage == 3:
        print(
            "The archive connects the same hidden hand to the reopened Dreamscape rift and the instructions behind the stabiliser sabotage."
        )
        print(
            "Its final objective is written plainly: destroy the Creator and seize his Book and Pen of Creation. Why it wants them is still concealed."
        )
        print(
            "The Creator is a man capable of both kindness and cruelty. One record shows him saving a settlement; another shows him erasing lives to reshape its land. Opposing him does not make theft of creation safe."
        )
        s["reveal_seen"] = True
        s["creator_choice"] = ["seek limits", "demand answers", "protect the records"][
            choice % 3
        ]
    elif stage == 4:
        witnesses = p.get("source_story", {}).get("witnesses", [])
        if len(witnesses) < 4:
            return (
                False,
                "Collect all four clans’ Source testimonies. Their cores stay at home.",
            )
        s["alliance"] = ["village council", "Sera and the archivists", "clan wardens"][
            choice % 3
        ]
        print(
            "Your alliance will guard the route and witness the Creator’s choices. The four cores are not taken or consumed."
        )
    elif stage == 5:
        if not s.get("paired_craft"):
            return False, "Prepare one of the two paired-element recipes first."
        s["area"] = "Hall of Creation"
    elif stage == 6:
        from expansion_combat import encounter

        enemy = dict(
            name="The Hidden Hand",
            hp=150 + p["level"] * 9,
            atk=12 + p["level"],
            **{"def": 7},
            xp=150,
            gold=200,
            intelligent=True,
        )
        if not encounter(game, [enemy], terrain="Hall of Creation"):
            return False, "The Hidden Hand is still advancing on the Creator."
        s["villain_stopped"] = True
    elif stage == 7:
        s["ending"] = [
            "The Creator retains the Book and Pen under witnessed limits; the clans preserve a record of every promise.",
            "A council of the surviving villages guards the Book and Pen; the Creator must answer to those whose lives he shapes.",
            "The instruments are sealed behind a ward maintained by the clans; no single ruler may wield them.",
        ][choice % 3]
        s["complete"] = True
        s["sera_quest_complete"] = True
        p["gold"] += 300
        print(s["ending"])
        print(
            "Sera preserves the archive. The villain’s deeper motive remains a mystery for a later story; it has not been invented as established canon."
        )
    s["stage"] = stage + 1
    return True, objective(p)


def menu(game):
    p = game.player
    s = progress(p)
    while True:
        print("\n--- SEASON THREE · BEYOND THE BROKEN BRIDGE ---")
        print(objective(p))
        if s.get("ending"):
            print(s["ending"])
        print(
            "1. Advance expedition\n2. Make paired-element equipment\n3. Choose expedition dialogue / alliance / ending\n4. Optional Unwritten Vault\n0. Back"
        )
        c = input("Expedition > ").strip()
        if c == "0":
            return
        if c == "1":
            print(advance(game)[1])
        elif c == "2":
            index = choose(
                "PAIRED RECIPES · 75 SOULS",
                [
                    "Flame Rune + Ice Rune → Dawn-and-Dusk Blade",
                    "Nature Rune + Light Rune → Living Radiance Staff",
                ],
            )
            if index is not None:
                print(craft_pair(p, index)[1])
        elif c == "3":
            stage = s.get("stage", 0)
            options = (
                [
                    "Seek limits on the Creator",
                    "Demand answers for his cruelty",
                    "Protect the records",
                ]
                if stage == 3
                else (
                    ["Village council", "Sera and the archivists", "Clan wardens"]
                    if stage == 4
                    else (
                        [
                            "Creator with witnessed limits",
                            "Village council custody",
                            "Seal the instruments",
                        ]
                        if stage == 7
                        else []
                    )
                )
            )
            if not options:
                print("No expedition decision is waiting.")
                continue
            index = choose("EXPEDITION DECISION", options)
            if index is not None:
                print(advance(game, index)[1])
        elif c == "4":
            if not s.get("complete"):
                print("Finish the expedition first.")
                continue
            cycle = p.get("wander_count", 0) // 20
            if s.get("vault_cycle") == cycle:
                print("The Vault needs the next exploration cycle to settle.")
                continue
            from expansion_combat import encounter

            enemies = [
                dict(
                    name="Unwritten Sentinel",
                    hp=90 + p["level"] * 5,
                    atk=8 + p["level"],
                    **{"def": 4},
                ),
                dict(
                    name="Archive Shadow",
                    hp=70 + p["level"] * 4,
                    atk=7 + p["level"],
                    **{"def": 3},
                ),
            ]
            if encounter(game, enemies, terrain="Unwritten Vault"):
                s["vault_cycle"] = cycle
                p["gold"] += 150
                print("Optional Vault cleared; +150 souls.")
