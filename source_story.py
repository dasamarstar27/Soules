"""A story seeded at awakening, with expandable dialogue and profession hooks."""

from copy import deepcopy
import data

PROFESSIONS = ("smithing", "weaving", "enchanting", "alchemy", "salvaging", "imbuing")


def state(player):
    defaults = dict(
        opened=False,
        clues=[],
        witnesses=[],
        dialogue={},
        profession_xp={},
        rumours=[],
        anomaly_wanders=[],
        fragments=0,
        vael_defeated=False,
        complete=False,
    )
    current = player.setdefault("source_story", {})
    for key, value in defaults.items():
        current.setdefault(key, deepcopy(value))
    return current


def opening(player):
    s = state(player)
    if s.get("opened"):
        return
    s["opened"] = True
    if player.get("chapter", 1) >= 2:
        print(
            "CHAPTER TWO · The monster invasion is over. After the victory, the elemental villages report Source channels falling out of balance."
        )
        clue(
            player,
            "invasion_ended",
            "The Dreaming God has fallen. The villages need help investigating a new Source imbalance.",
        )
        return
    print("\n--- CHAPTER ONE · THE DREAMSCAPE INVASION ---")
    print(
        "Long ago, the Riftlands separated the Dreamscape from the main world. Monsters were much rarer, and lived peacefully beside its people."
    )
    print(
        "The Dreamscape King entered the Sacred Temple in the Riftlands and corrupted its core energy. The realms merged. New monsters rose, and the king himself became a monster and their ruler."
    )
    print(
        "An elemental civilisation once stood in every region. They fought the invasion until only Ignar, Glacien, Voltis and Sylvar remained. Their warriors entered the temple and gave their lives to stabilise the power and banish the king."
    )
    print(
        "For generations the surviving clans hid behind their wards. Now the rift has opened again. The Dreamscape has fallen back into the world, and the corrupted king's monsters are overrunning the roads."
    )
    print(
        "You awaken in Whispering Woods with a Rusty Sword. Survive, find shelter, free the regions and confront the Dreamscape King—known in the old game as The Dreaming God."
    )
    clue(
        player,
        "invasion",
        "The rift has reopened. The Dreamscape King has returned with his monster invasion. Free the regions and reach the Dreamscape.",
    )
    clue(
        player,
        "ancient_war",
        "The king corrupted core energy at the Sacred Temple. The realms merged, monsters rose, and all but four elemental civilisations were destroyed.",
    )
    clue(
        player,
        "warriors_sacrifice",
        "Warriors from Ignar, Glacien, Voltis and Sylvar gave their lives to stabilise the temple and banish the king. Nobody knows why the rift opened again.",
    )


def clue(player, key, text):
    s = state(player)
    if any(c["id"] == key for c in s["clues"]):
        return False
    s["clues"].append(dict(id=key, text=text))
    print("\nJOURNAL UPDATED: " + text)
    return True


def objective(player):
    s = state(player)
    if s.get("complete"):
        return "Season Two complete: Source balance restored. The far side of the bridge has noticed you."
    if s.get("vael_defeated"):
        return "Repair the broken bridge using one core from each elemental village."
    if player.get("chapter", 1) < 2:
        if not any(c["id"] == "first_victory" for c in s["clues"]):
            return "Survive your first encounter; find shelter and ask villagers about the monster invasion."
        return "Free the main regions from the invading monsters, unlock the road to the Dreamscape and defeat the Dreaming God."
    if len(s["witnesses"]) < 4:
        return f'Investigate the sabotage: speak to all four elemental keepers about the Source ({len(s["witnesses"])}/4).'
    return (
        "Follow the evidence to the Source Temple. Confront the former keeper at the Broken Bridge."
    )


def rank(player, profession):
    return min(5, 1 + state(player)["profession_xp"].get(profession, 0) // 5)


def craft_xp(player, profession):
    xp = state(player)["profession_xp"]
    old = rank(player, profession)
    xp[profession] = xp.get(profession, 0) + 1
    if rank(player, profession) > old:
        print(f"PROFESSION: {profession.title()} reached rank {rank(player,profession)}!")


def first_victory(player):
    clue(
        player,
        "first_victory",
        "The defeated monster bears the mark of the Dreamscape. Its invasion is spreading through the woods. Reclaim the roads to the other regions.",
    )


def rumour(player, village):
    s = state(player)
    region = village["region"]
    undiscovered = [
        x
        for x in data.REGION_STRUCTURES.get(region, [])
        if x["name"] not in player.get("discovered_structures", {}).get(region, [])
    ]
    if undiscovered:
        target = undiscovered[0]
        message = f"{target['name']} may be found in {region}. Follow the old paths; its exact location is still unknown."
    else:
        message = (
            f"The people of {region} need the monster invasion stopped. Defeat the guardians and reach the Dreamscape."
            if player.get("chapter", 1) < 2
            else f"Travellers in {region} speak of unusual pulses near the Riftlands. The elemental keepers may know why."
        )
    if message not in s["rumours"]:
        s["rumours"].append(message)
    print("RUMOUR: " + message)
    print("Recorded in your journal. This does not automatically discover the location.")


def talk(game, village):
    p = game.player
    s = state(p)
    while True:
        print(f"\n--- CONVERSATION · {village['name']} keeper ---")
        print(
            (
                "1. Ask about the monster invasion"
                if p.get("chapter", 1) < 2
                else "1. Ask about the unstable Source"
            )
            + "\n2. Ask about local craftsmanship\n3. Offer to help the people\n4. Ask for a rumour\n5. Remember the fallen warriors\n0. Leave"
        )
        choice = input("Conversation > ").strip()
        if choice == "0":
            return
        topics = s["dialogue"].setdefault(village["id"], [])
        if choice in ("1", "2", "3", "4", "5") and choice not in topics:
            topics.append(choice)
        if choice == "1":
            if p.get("chapter", 1) < 2:
                print(
                    '"There used to be far fewer monsters, and they were not hostile. The king corrupted the temple long ago; our ancestors banished him with their lives. The rift has opened again and his monsters are returning."'
                )
                clue(
                    p,
                    "village_warning",
                    "The villagers confirm that monsters used to be rare and peaceful. The Dreamscape King, also called The Dreaming God, returned when the rift reopened.",
                )
            elif village.get("elemental"):
                if village["id"] not in s["witnesses"]:
                    s["witnesses"].append(village["id"])
                print(
                    '"Someone reversed our core channel. The stabiliser is being forced to become a bridge. Only a keeper could have known these controls."'
                )
                clue(
                    p,
                    "witness_" + village["id"],
                    village["name"] + " confirmed deliberate tampering with its Source channel.",
                )
                if len(s["witnesses"]) == 4:
                    clue(
                        p,
                        "vael_identity",
                        "The four accounts identify Vael, a former keeper. He wants to force open the Creator's Realm and remake the world.",
                    )
            else:
                print(
                    '"Seek the four elemental keepers. Their core channels will reveal who has changed the stabiliser."'
                )
        elif choice == "2":
            print(
                '"Our workshops have their own strengths. Practice at real benches to gain profession ranks; opening a menu teaches no mastery."'
            )
            for service, detail in (
                __import__("village_life").snapshot(p, village)["service_details"].items()
            ):
                print(service + ": " + detail)
        elif choice == "3":
            s["stance"] = "helpful"
            print(
                '"Then start with the local errand board. Trust is earned through supplies and deeds." Your journal records your promise.'
            )
        elif choice == "4":
            rumour(p, village)
        elif choice == "5":
            remember_warriors(p, village)


def anomaly(game):
    p = game.player
    s = state(p)
    wander = p.get("wander_count", 0)
    if wander == 3 and p.get("chapter", 1) < 2:
        clue(
            p,
            "early_pulse",
            "The woods fall silent as another pack approaches from the Dreamscape. The invasion is growing; peaceful roads are becoming dangerous.",
        )
    if (
        p.get("chapter", 1) < 2
        or wander % 10
        or wander in s["anomaly_wanders"]
        or s.get("complete")
    ):
        return
    s["anomaly_wanders"].append(wander)
    print("\nSOURCE ANOMALY: a loose thread of energy trembles beside the path.")
    if input("Carefully collect a fragment? (y/n) > ").strip().lower() == "y":
        s["fragments"] += 1
        print("Collected one Source fragment. The anomaly settles; your wander continues.")


def journal(game):
    p = game.player
    s = state(p)
    while True:
        print(
            "\n--- STORY JOURNAL · "
            + ("THE BROKEN BRIDGE" if p.get("chapter", 1) >= 2 else "THE ORIGINAL JOURNEY")
            + " ---"
        )
        print(objective(p))
        print("1. Evidence and memories\n2. Professions\n3. Rumours")
        if p.get("chapter", 1) >= 2:
            print(
                "4. Investigate the Source Temple / Broken Bridge\n5. Repair the bridge\n6. Use a Source fragment (up to 15 HP, +5 mana)"
            )
        print("0. Back")
        c = input("Journal > ").strip()
        if c == "0":
            return
        if c == "1":
            for entry in s["clues"]:
                print("• " + entry["text"])
            print("Your approach: " + s.get("stance", "undecided"))
        elif c == "2":
            for name in PROFESSIONS:
                print(
                    f'{name.title()}: rank {rank(p,name)}/5 · {s["profession_xp"].get(name,0)} successful actions. Five actions per rank.'
                )
            print(
                "Higher crafting ranks add small forge/loom/tower bonuses and improve ingredient preservation. Future specialties will branch from these ranks."
            )
        elif c == "3":
            for message in s["rumours"]:
                print("• " + message)
            if not s["rumours"]:
                print("Ask village keepers for directions and rumours.")
        elif c == "4":
            if p.get("chapter", 1) < 2:
                print("The dream wards still block a full investigation. Complete Chapter 1 first.")
                continue
            if len(s["witnesses"]) < 4:
                print("Gather the testimony of all four elemental keepers first.")
                continue
            if s.get("vael_defeated"):
                print("Vael has already fallen. The broken stabiliser still needs repair.")
                continue
            if "Riftlands" not in p["unlocked_regions"]:
                print("Riftlands is still locked.")
                continue
            p["region"] = "Riftlands"
            p["current_location"] = "Riftlands"
            clue(
                p,
                "broken_bridge",
                "At the Source Temple you find reversed conduits. Vael has turned the Core Stabiliser into an unfinished bridge to the Creator's Realm.",
            )
            print(
                'Vael: "The Creator left us to suffer. I will cross this bridge and take the power to make a better world."'
            )
            if input("Confront Vael? (y/n) > ").strip().lower() != "y":
                continue
            level = p.get("level", 1)
            enemy = dict(
                name="Vael, the Severed Keeper",
                hp=180 + level * 10,
                atk=30 + level,
                **{"def": 8 + level // 2},
                speed=10,
                _story_boss=True,
            )
            import original_ui as ui

            previous = ui.location
            ui.location = dict(name="Sacred Temple · Broken Bridge", kind="temple")
            try:
                game.fight(enemy, boss=True)
            finally:
                ui.location = previous
        elif c == "5":
            if not s.get("vael_defeated"):
                print("Stop the second activation before attempting repairs.")
                continue
            if s.get("complete"):
                print("The Source is already balanced.")
                continue
            needed = [v["core"] for v in data.ELEMENTAL_VILLAGES.values()]
            for core in needed:
                print(f'{core}: {p.get("elemental_cores",[]).count(core)}/1')
            if not all(core in p.get("elemental_cores", []) for core in needed):
                print("Bring one core from each elemental village.")
                continue
            if (
                input("Bind these four cores into the repaired stabiliser? (y/n) > ")
                .strip()
                .lower()
                != "y"
            ):
                continue
            for core in needed:
                p["elemental_cores"].remove(core)
            s["complete"] = True
            p["chapter_2_complete"] = True
            clue(
                p,
                "source_restored",
                "The four villages guide your repairs. Source energy returns to balance and the unfinished bridge closes. Something on the far side noticed you.",
            )
            print(
                "SEASON TWO COMPLETE · The Creator is not a required boss. A new story may follow beyond the bridge."
            )
        elif c == "6":
            if s.get("fragments", 0) < 1:
                print("No Source fragments. Investigate postgame anomalies while wandering.")
                continue
            s["fragments"] -= 1
            p["hp"] = min(p["max_hp"], p["hp"] + 15)
            p["mana"] = p.get("mana", 0) + 5
            print("The fragment steadies you: up to 15 HP and +5 mana.")


def victory(player):
    state(player)["vael_defeated"] = True
    clue(
        player,
        "vael_defeated",
        "Vael falls before the second activation completes. The bridge is broken, but the Core Stabiliser can still be repaired with the four elemental cores.",
    )


ANCESTORS = {
    "fire": (
        "Ilyra of Ignar",
        "held the burning breach open so the other warriors could reach the core",
    ),
    "ice": ("Tovan of Glacien", "slowed the corrupted current long enough to change its course"),
    "storm": ("Kael of Voltis", "bound the fractured currents into one stabilising circuit"),
    "nature": (
        "Miren of Sylvar",
        "anchored the seal to the living world so it could endure after the warriors were gone",
    ),
}


def remember_warriors(player, village):
    element = next(
        (
            v["element"]
            for region, v in data.ELEMENTAL_VILLAGES.items()
            if v["name"] == village["name"]
        ),
        None,
    )
    if element:
        name, deed = ANCESTORS[element]
        text = f'{name} led a warband from {village["name"]} and {deed}. They gave their lives with the other clans to stabilise the core and banish the king.'
        print(text)
        clue(player, "ancestor_" + element, text)
    else:
        text = "Every region once held an elemental civilisation. Only four survived the old war. Their warriors entered the Sacred Temple together and paid for the seal with their lives."
        print(text)
        clue(player, "old_war_memory", text)
    print(
        "The four surviving villages stayed hidden to protect their people and the memory of that sacrifice. Their wards make them difficult to find."
    )
