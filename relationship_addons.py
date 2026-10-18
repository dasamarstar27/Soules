"""Personal companion stories, rest sanctuaries and persistent village relationships."""

from copy import deepcopy
import hashlib
import data
import original_ui as ui
from expansion_state import state, mark, pay, choose


def relationships(player):
    return state(player)["relationships"]


def activity(game, feature):
    p = game.player
    rel = relationships(p)
    pets = p.get("companions", [])
    if feature in (81, 82, 83, 84, 85):
        if feature == 85:
            stored = rel.setdefault("sanctuary", [])
            index = choose(
                "COMPANION SANCTUARY",
                ["Rest an active companion", "Recall a resting companion"],
            )
            if index == 0:
                pet = choose("REST COMPANION", [x["name"] for x in pets])
                if pet is not None:
                    stored.append(pets.pop(pet))
                    print(
                        "Companion rests safely; its hunger and progress are preserved."
                    )
                    mark(p, 85)
            elif index == 1:
                pet = choose("RECALL COMPANION", [x["name"] for x in stored])
                if pet is not None and len(pets) < 3:
                    pets.append(stored.pop(pet))
                    mark(p, 85)
                elif pet is not None:
                    print("Your active party already has three companions.")
            return
        index = choose(
            "CHOOSE COMPANION", [x.get("form_name", x["name"]) for x in pets]
        )
        if index is None:
            return
        pet = pets[index]
        if feature == 81:
            quest = rel.setdefault("companion_quests", {}).setdefault(
                pet["name"],
                dict(accepted=pet.get("helped_victories", 0), complete=False),
            )
            if quest["complete"]:
                print("This companion’s personal story is complete.")
                return
            print(
                pet["name"]
                + " wants to protect its home instead of merely fleeing danger. Help in three victories together, then return home with it."
            )
            if (
                pet.get("helped_victories", 0) - quest["accepted"] >= 3
                and p["region"] == pet["home_region"]
            ):
                quest["complete"] = True
                pet["keepsake"] = "Homebound charm"
                pet["bond_xp"] = pet.get("bond_xp", 0) + 10
                p["gold"] += 75
                mark(p, 81)
                print(
                    "Their home is safer. Personal quest completed; +10 combat bond XP and 75 souls."
                )
        elif feature == 82:
            stories = rel.setdefault("camp_dialogue", {}).setdefault(pet["name"], [])
            milestone = state(p)["statistics"].get("tactical_victories", 0) // 2
            if str(milestone) not in stories:
                stories.append(str(milestone))
                print(
                    pet["name"]
                    + " watches the road home. You choose to promise protection, respect its caution, or share a memory."
                )
                answer = choose(
                    "CAMP CONVERSATION",
                    [
                        "Promise to protect its home",
                        "Respect its caution",
                        "Share a memory",
                    ],
                )
                if answer is not None:
                    rel.setdefault("camp_choices", {})[pet["name"]] = answer
            else:
                print(
                    "You sit together quietly; new memories follow further victories."
                )
            mark(p, 82)
        elif feature == 83:
            temperament = ["bold", "gentle", "curious"][
                int(hashlib.sha256(pet["name"].encode()).hexdigest()[:4], 16) % 3
            ]
            pet["temperament"] = temperament
            print(
                pet["name"]
                + " is "
                + temperament
                + ". Bold companions strike harder, gentle companions heal more, curious companions help scout ingredients."
            )
            mark(p, 83)
        elif feature == 84:
            if pet.get("accessory"):
                print("This companion already wears " + pet["accessory"])
                return
            if not p.get("cloths") or not pay(p, 30, {"Iron fittings": 1}):
                print("Bring 30 souls, one Iron fitting and one cloth.")
                return
            p["cloths"].pop(0)
            pet["accessory"] = "Woven guardian charm"
            mark(p, 84)
            print(
                "Accessory equipped: support strength +1 (hunger requirements still apply)."
            )
    elif feature == 86:
        from source_story import state as story_state

        mentor = story_state(p).get("mentor_village")
        if not mentor:
            print("Meet Elian first.")
            return
        if not ui.village or ui.village["id"] != mentor["id"]:
            print("Elian waits in " + mentor["name"] + ".")
            return
        print(
            'Elian: "Miren’s letters never called her fearless. She was afraid and went anyway. I kept her ordinary stories because sacrifice should not erase the person."'
        )
        rel.setdefault("mentor_memories", [])
        if "Miren" not in rel["mentor_memories"]:
            rel["mentor_memories"].append("Miren")
        mark(p, 86)
    elif feature == 87:
        if not ui.village:
            print("Visit a village to meet its people.")
            return
        people = [
            ui.village["name"] + " Cook",
            ui.village["name"] + " Smith",
            ui.village["name"] + " Trader",
        ]
        index = choose("VILLAGE FRIENDSHIPS", people)
        if index is None:
            return
        person = people[index]
        entry = rel.setdefault("friends", {}).setdefault(
            person, dict(rank=0, topics=[], gift_cycle=-1)
        )
        topic = choose(
            person,
            [
                "Ask about their work",
                "Ask about their family",
                "Give a regional ingredient",
            ],
        )
        if topic is None:
            return
        if topic < 2:
            if topic not in entry["topics"]:
                entry["topics"].append(topic)
            print(
                person
                + ": "
                + [
                    '"Our work keeps travellers alive. Every workshop has its own strengths."',
                    '"My family remembers when the roads were quieter. I want the next children to know that world."',
                ][topic]
            )
        else:
            cycle = p.get("wander_count", 0) // 20
            native = next(
                (
                    x
                    for x in data.REGION_INGREDIENTS.get(p["region"], [])
                    if x in p.get("ingredients", [])
                ),
                None,
            )
            if not native or entry["gift_cycle"] == cycle:
                print("Bring a local ingredient; only one friendship gift per cycle.")
                return
            p["ingredients"].remove(native)
            entry["gift_cycle"] = cycle
            entry["rank"] = min(3, entry["rank"] + 1)
            print(
                "Friendship rank "
                + str(entry["rank"])
                + ". Rank 3 improves local commissions."
            )
        mark(p, 87)
    elif feature == 88:
        if rel.get("partner"):
            print(
                "Travelling with "
                + rel["partner"]["name"]
                + " for "
                + str(rel["partner"]["remaining"])
                + " more encounters."
            )
            return
        if not state(p)["field"].get("escort") and not state(p)["quests"].get(
            "5", {}
        ).get("stage"):
            print("Accept an escort or Lost Caravan quest first.")
            return
        rel["partner"] = dict(name="Caravan Scout", remaining=3, quest="escort")
        mark(p, 88)
        print(
            "The scout joins for three tactical encounters, offering +1 temporary defence."
        )
    elif feature == 89:
        if not state(p)["quests"].get("5", {}).get("complete"):
            print("Rescue the Lost Caravan first.")
            return
        if rel.get("reunion"):
            if rel.get("reunion_supplied"):
                print(
                    "The caravan families greet you again, their medicine packs full."
                )
                return
            print(
                "The families ask for two regional ingredients to restock their travel medicine. Reward: 75 souls; one request."
            )
            from collections import Counter

            native = [
                x
                for x in p.get("ingredients", [])
                if x in data.REGION_INGREDIENTS.get(p["region"], [])
            ]
            if len(native) < 2:
                print("Gather two local ingredients first.")
                return
            if (
                input("Donate two regional ingredients? (y/n) > ").strip().lower()
                == "y"
            ):
                for item in native[:2]:
                    p["ingredients"].remove(item)
                p["gold"] += 75
                rel["reunion_supplied"] = True
                print("The caravan leaves with medicine. +75 souls.")
            return
        rel["reunion"] = True
        p["gold"] += 50
        mark(p, 89)
        print(
            "The rescued caravan returns with news and 50 souls. Its scout can help future escorts."
        )
    elif feature == 90:
        if not any(q.get("complete") for q in state(p)["quests"].values()):
            print("Finish a personal side story first.")
            return
        if rel.get("farewell_keepsake"):
            print("You still carry the Farewell Thread.")
            return
        rel["farewell_keepsake"] = "Farewell Thread"
        mark(p, 90)
        print(
            "A villager gives you a Farewell Thread. It stays in your story collection and cannot be sold."
        )
