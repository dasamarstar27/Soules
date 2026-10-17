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
        "An elemental civilisation once stood in every region. Eleven cores were destroyed, stripping their civilisations of their powers and leaving them vulnerable. Only Ignar, Glacien, Voltis and Sylvar survived. Their warriors entered the temple and gave their lives to stabilise the power and banish the king."
    )
    print(
        "The four clans keep their surviving cores at home; the Riftlands temple holds only the stabiliser. For generations the clans hid behind their wards. Now the rift has opened again. The Dreamscape has fallen back into the world, and the corrupted king's monsters are overrunning the roads."
    )
    print("Seek shelter in a village. Someone there may know how to help you face this invasion.")
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
        return "Repair the stabiliser using the four clans’ harmonic knowledge. Their cores stay in their villages."
    if s.get("season_one_complete") and player.get("chapter", 1) < 2:
        return f"Rebuild the world: {min(20,interlude_progress(player))}/20 side quests after Season One. Season Two begins five months later in lore."
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
        if s.get("season_one_complete") and p.get("chapter", 1) < 2:
            print(
                f"7. Side quest board · 8. Begin Season Two ({min(20,interlude_progress(p))}/20 side quests)"
            )
        print("0. Back")
        c = input("Journal > ").strip()
        if c == "0":
            return
        if c == "8":
            begin_season_two(game)
        elif c == "7":
            game.quest_board(p["region"])
        elif c == "1":
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
            if len(s["witnesses"]) < 4:
                print(
                    "Ask all four clans for their harmonic knowledge. The cores themselves stay in their villages."
                )
                continue
            if (
                input("Repair the stabiliser using the clans’ harmonic instructions? (y/n) > ")
                .strip()
                .lower()
                != "y"
            ):
                continue
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
        "Vael falls before the second activation completes. The bridge is broken, but the stabiliser can be repaired using the four clans’ harmonic knowledge. Their cores stay guarded in their villages.",
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


def sidequest_total(player):
    return (
        sum(bool(q.get("completed")) for q in player.get("quests", []))
        + sum(
            record.get("errands_completed", 0)
            for record in player.get("village_records", {}).values()
        )
        + sum(value == "complete" for value in player.get("elemental_quests", {}).values())
    )


def interlude_progress(player):
    s = state(player)
    return max(0, sidequest_total(player) - s.get("sidequest_baseline", sidequest_total(player)))


def season_one_ending(player):
    s = state(player)
    if s.get("season_one_complete"):
        return
    s["season_one_complete"] = True
    s["sidequest_baseline"] = sidequest_total(player)
    player["season_one_complete"] = True
    # The original ending is complete; the next season has not started yet.
    player["chapter"] = 1
    print("\n--- SEASON ONE COMPLETE · A WORLD SAVED? ---")
    print(
        "Elian, your elderly mentor and the grandson of a fallen warrior, joins you as the battle falls silent."
    )
    print('You: "The king is gone. The world is finally saved."')
    print(
        'Elian: "Not really. The Dreamscape did not connect itself back to our world. Someone—or something—made that happen."'
    )
    print(
        'Elian: "Whoever did it understands core energy. The king is defeated, but that knowledge is still out there. We have to be ready for what comes next."'
    )
    clue(
        player,
        "elians_warning",
        "Elian warned that someone or something must have reopened the rift, and that they understand core energy. The true cause remains unknown.",
    )
    print('1. "Then we find them."\n2. "What should we do now?"\n0. Leave with Elian')
    answer = input("Elian > ").strip()
    if answer == "1":
        print(
            'Elian: "We will. First, help the people rebuild. A world worth saving needs more than one victory."'
        )
    elif answer == "2":
        print(
            'Elian: "The villages need help. Repair their lives while I follow the traces left at the temple."'
        )
    print(
        "INTERLUDE · Help rebuild the world: complete 20 side quests after this victory. Season Two opens five months later in the story; there is no real-time wait."
    )


def begin_season_two(game):
    p = game.player
    s = state(p)
    if p.get("chapter", 1) >= 2:
        print("Season Two has already begun.")
        return
    if not s.get("season_one_complete"):
        print("Finish Season One by defeating the Dreamscape King first.")
        return
    progress = interlude_progress(p)
    if progress < 20:
        print(
            f"Help rebuild the world first: {min(progress,20)}/20 side quests completed since the victory."
        )
        return
    if input("Begin Season Two, five months after Season One? (y/n) > ").strip().lower() != "y":
        return
    p["chapter"] = 2
    s["months_since_season_one"] = 5
    clue(
        p,
        "five_months_later",
        "Five months after the king's defeat, Elian returns with reports of a new imbalance at the Sacred Temple. The four surviving cores remain guarded in their villages; only the stabiliser stands at the temple.",
    )
    print(
        'SEASON TWO · FIVE MONTHS LATER\nElian: "The stabiliser has been tampered with. This time we have a trail to follow."'
    )


def meet_mentor(player, village):
    s = state(player)
    if s.get("mentor_village"):
        return
    s["mentor_village"] = dict(id=village["id"], name=village["name"], region=village["region"])
    print("\nAn old man named Elian welcomes you to the first village you find.")
    print(
        'Elian: "My grandmother Miren was one of the warriors who gave their lives at the Sacred Temple. I cannot swing a sword as I once did, but I can help you find your way."'
    )
    print(
        "He becomes your mentor. Speak to him here for advice, and he will help you understand the old war."
    )
    clue(
        player,
        "mentor_met",
        f'You met Elian in {village["name"]}. He is an old man and the grandson of Miren, one of the fallen warriors.',
    )


def mentor_talk(game, village):
    p = game.player
    s = state(p)
    home = s.get("mentor_village")
    if not home:
        meet_mentor(p, village)
        home = s["mentor_village"]
    if home["id"] != village["id"]:
        print(f'Elian is waiting in {home["name"]}, {home["region"]}.')
        return
    print(
        "\n--- ELIAN · YOUR MENTOR ---\n1. Ask about his grandmother\n2. Ask for advice\n3. Discuss the next season\n0. Back"
    )
    c = input("Mentor > ").strip()
    if c == "1":
        print(
            'Elian: "Miren of Sylvar anchored the seal to the living world. Her warband never came home. The four surviving clans kept their cores safe, because eleven destroyed cores had already left their people powerless."'
        )
        clue(
            p,
            "mentors_family",
            "Elian is Miren of Sylvar’s grandson. The Sacred Temple contains the stabiliser, not the four surviving cores.",
        )
    elif c == "2":
        print(
            'Elian: "Keep food for the road. Learn which villages have good workshops. Free each region and stop the king. Courage is useful; preparation keeps you alive."'
        )
    elif c == "3":
        if p.get("chapter", 1) >= 2:
            print(
                'Elian: "Someone tampered with the stabiliser. Listen to the four clans, and follow the evidence."'
            )
        elif s.get("season_one_complete"):
            begin_season_two(game)
        else:
            print(
                'Elian: "The invasion comes first. We cannot build a future while the king is taking our world."'
            )
