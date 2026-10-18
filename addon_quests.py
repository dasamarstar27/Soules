"""Twenty authored side stories with travel, evidence, supplies and choices."""

from copy import deepcopy
import data
from addon_catalog import ADDONS
from expansion_state import state, pay, mark, count

QUESTS = {
    1: (
        "Whispering Woods",
        "Sunken Coast",
        "A courier entrusts you with a fallen warrior’s unsent letter.",
        "Deliver the sealed letter or read it and explain why.",
    ),
    2: (
        "Whispering Woods",
        "Whispering Woods",
        "Elian’s walking staff has split. He asks for repair, not a new weapon.",
        "Use one carried wood and 25 souls to repair it at a village.",
    ),
    3: (
        "Ashen Wastes",
        "Ashen Wastes",
        "An empty chair is kept for every villager who never came home.",
        "Donate two carried foods for their remembrance meal.",
    ),
    4: (
        "Whispering Woods",
        "Whispering Woods",
        "A frightened creature recognises the name it had before the invasion.",
        "Offer Forest Berries, or choose a nonlethal confrontation.",
    ),
    5: (
        "Sunken Coast",
        "Ironpeak Mountains",
        "The lost caravan left broken wheels and a trail of survivors.",
        "Escort it through Sunken Coast, Whispering Woods and Ironpeak Mountains.",
    ),
    6: (
        "Ashen Wastes",
        "Ashen Wastes",
        "Refugee children want to return to the old city without another battle.",
        "Defeat this region’s guardian, then supply four Stone for safe shelter.",
    ),
    7: (
        "Sunken Coast",
        "Sunken Coast",
        "A cook remembers a recipe but not the measurements in her lost book.",
        "Copy a recovered tome and supply one regional ingredient.",
    ),
    8: (
        "Sunken Coast",
        "Sunken Coast",
        "A submerged bell still rings beneath the old civilisation’s stones.",
        "Recover a local ruin find, then choose whether to ring or preserve the bell.",
    ),
    9: (
        "Crystal Spire",
        "Crystal Spire",
        "A self-proclaimed keeper is selling protection that has never worked.",
        "Question two village keepers, then test the supposed blessing.",
    ),
    10: (
        "Ironpeak Mountains",
        "Ironpeak Mountains",
        "A guardian admits its people need help beyond the core’s walls.",
        "Win the regional guardian fight and complete one local work commission.",
    ),
    11: (
        "Riftlands",
        "Riftlands",
        "Eleven memorial stones await records of the civilisations that lost their cores.",
        "Search ruins in eleven different regions; no protected fragment is spent.",
    ),
    12: (
        "Riftlands",
        "Riftlands",
        "A warband memory lets you walk a single moment of the final journey.",
        "Complete the nonlethal memory trial, then choose whose account to preserve.",
    ),
    13: (
        "Crystal Spire",
        "Crystal Spire",
        "A fifth account contradicts a familiar line of the warriors’ history.",
        "Collect two clan testimonies and compare their surviving records.",
    ),
    14: (
        "Shattered Wastes",
        "Shattered Wastes",
        "A torn elemental standard is all that marks a lost settlement.",
        "Supply two cloths and two Timber; restore the banner without recreating its core.",
    ),
    15: (
        "Shadow Vale",
        "Shadow Vale",
        "Repeated marks in the tomes seem to name places, not spells.",
        "Study three different protected tomes to translate the old script.",
    ),
    16: (
        "Riftlands",
        "Riftlands",
        "Temple diagrams explain the stabiliser’s safeguards.",
        "Study two protected fragments and a tome; preserve every original find.",
    ),
    17: (
        "The Dreamscape",
        "The Dreamscape",
        "A portrait shows the Dreamscape King before his transformation.",
        "Recover a Dreamscape tome and decide how to exhibit his hunger for power.",
    ),
    18: (
        "Whispering Woods",
        "Whispering Woods",
        "Household relics describe an ordinary day before the realms merged.",
        "Record three regional field observations and bring one carried food.",
    ),
    19: (
        "Riftlands",
        "Riftlands",
        "Faded inscriptions hide the names of the people who never returned.",
        "Complete Eleven Memorials and spend 30 souls restoring the names.",
    ),
    20: (
        "Celestial Expanse",
        "Celestial Expanse",
        "Each surviving clan preserves a different verse of the same song.",
        "Visit all four hidden elemental villages; choose a shared performance.",
    ),
}


def records(player):
    return state(player)["quests"]


def accept(player, quest_id):
    if quest_id not in QUESTS:
        return False, "Unknown story."
    if str(quest_id) in records(player):
        return False, "This story is already recorded."
    records(player)[str(quest_id)] = dict(
        stage=0,
        accepted_wander=player.get("wander_count", 0),
        visited=[],
        choices=[],
        complete=False,
    )
    return (
        True,
        QUESTS[quest_id][2]
        + " Investigate in "
        + QUESTS[quest_id][0]
        + " after at least two wanders.",
    )


def food_take(player, amount):
    from food_addons import is_food

    foods = [i for i, item in enumerate(player.get("inventory", [])) if is_food(item)]
    if len(foods) < amount:
        return False
    for index in reversed(foods[:amount]):
        player["inventory"].pop(index)
    return True


def progress(game, quest_id, choice="preserve"):
    player = game.player
    q = records(player).get(str(quest_id))
    if not q:
        return False, "Accept this story first."
    if q["complete"]:
        return False, "Already completed. Rewards are not repeated."
    region, destination, intro, task = QUESTS[quest_id]
    if q["stage"] == 0:
        if (
            player["region"] != region
            or player.get("wander_count", 0) - q["accepted_wander"] < 2
        ):
            return False, "Investigate in " + region + " after two more wanders."
        q["stage"] = 1
        return True, intro + " " + task
    if q["stage"] == 1:
        if quest_id == 5:
            route = ["Sunken Coast", "Whispering Woods", "Ironpeak Mountains"]
            target = route[len(q["visited"])]
            if player["region"] != target:
                return False, "Escort next to " + target + "."
            if not food_take(player, 1):
                return False, "Supply one carried food per escort leg."
            q["visited"].append(target)
            if len(q["visited"]) < 3:
                return (
                    True,
                    "The caravan safely reached " + target + ". Continue the route.",
                )
        elif player["region"] != destination:
            return False, "Continue this objective in " + destination + "."
        if quest_id == 2:
            import original_ui as ui

            if not ui.village or not player.get("woods") or not pay(player, 25):
                return False, "Bring one wood and 25 souls to a village."
            player["woods"].pop(0)
        elif quest_id == 3 and not food_take(player, 2):
            return False, "Bring two carried foods."
        elif quest_id == 4:
            berry = next(
                (
                    i
                    for i, x in enumerate(player.get("inventory", []))
                    if x["name"] == "Forest Berries"
                ),
                None,
            )
            if berry is not None:
                player["inventory"].pop(berry)
            elif not q.get("trial_won"):
                return (
                    False,
                    "Bring Forest Berries or complete the nonlethal trial from this story’s menu.",
                )
        elif quest_id == 6:
            if region not in player.get("bosses_defeated", []) or not pay(
                player, materials={"Stone": 4}
            ):
                return False, "Free this region and bring four Stone."
        elif quest_id == 7:
            if not any(r["kind"] == "tome" for r in player.get("protected_relics", [])):
                return False, "Recover an ancient tome to study first."
            pool = data.REGION_INGREDIENTS[region]
            ingredient = next(
                (x for x in pool if x in player.get("ingredients", [])), None
            )
            if not ingredient:
                return False, "Bring a regional ingredient."
            player["ingredients"].remove(ingredient)
            state(player)["field"]["family_recipe"] = True
        elif quest_id == 8:
            if not any(
                r["region"] == region for r in player.get("protected_relics", [])
            ):
                return False, "Recover a find from the local ruins first."
        elif quest_id == 9:
            if len(player.get("source_story", {}).get("dialogue", {})) < 2:
                return False, "Question keepers in two villages first."
        elif quest_id == 10:
            if (
                region not in player.get("bosses_defeated", [])
                or state(player)["statistics"].get("commissions_collected", 0) < 1
            ):
                return False, "Defeat the guardian and collect a work commission."
        elif quest_id == 11:
            if (
                len({key.split("::")[0] for key in player.get("ruin_searches", {})})
                < 11
            ):
                return False, "Search ruins in eleven different regions."
        elif quest_id == 12 and not q.get("trial_won"):
            return False, "Complete the warband memory trial first."
        elif quest_id == 13:
            if len(player.get("source_story", {}).get("witnesses", [])) < 2:
                return False, "Collect two elemental keeper testimonies."
        elif quest_id == 14:
            if len(player.get("cloths", [])) < 2 or not pay(
                player, materials={"Timber": 2}
            ):
                return False, "Bring two cloths and two Timber."
            del player["cloths"][:2]
        elif quest_id == 15:
            if (
                len(
                    {
                        r["id"]
                        for r in player.get("protected_relics", [])
                        if r["kind"] == "tome"
                    }
                )
                < 3
            ):
                return False, "Study three different protected tomes."
            state(player)["field"]["translated_words"] = ["home", "seal", "sacrifice"]
        elif quest_id == 16:
            relics = player.get("protected_relics", [])
            if sum(r["kind"] == "fragment" for r in relics) < 2 or not any(
                r["kind"] == "tome" for r in relics
            ):
                return False, "Study two fragments and one tome; none will be consumed."
        elif quest_id == 17:
            if not any(
                r["kind"] == "tome" and r["region"] == region
                for r in player.get("protected_relics", [])
            ):
                return False, "Find a Dreamscape tome first."
        elif quest_id == 18:
            if len(state(player)["field"].get("observations", [])) < 3 or not food_take(
                player, 1
            ):
                return (
                    False,
                    "Record three field observations and bring one carried food.",
                )
        elif quest_id == 19:
            if not records(player).get("11", {}).get("complete") or not pay(player, 30):
                return False, "Complete Eleven Memorials and bring 30 souls."
        elif quest_id == 20:
            if not all(
                v["name"] in player.get("discovered_structures", {}).get(r, [])
                for r, v in data.ELEMENTAL_VILLAGES.items()
            ):
                return False, "Visit all four hidden elemental villages."
        q["stage"] = 2
        return (
            True,
            "The practical work is done. Choose how this story should be remembered.",
        )
    if choice not in ("preserve", "share", "private"):
        return False, "Choose preserve, share or private."
    q.update(stage=3, complete=True)
    q["choices"].append(choice)
    reward = 75 + quest_id * 10
    player["gold"] += reward
    game.gain_xp(15 + quest_id)
    mark(player, quest_id)
    count(player, "side_stories_completed")
    state(player)["relationships"]["public_trust"] = state(player)["relationships"].get(
        "public_trust", 0
    ) + (2 if choice == "share" else 1)
    if quest_id == 1:
        q["ending"] = (
            "The family receives the letter; the warrior’s name is remembered."
        )
    elif quest_id == 4:
        q["ending"] = "The creature is spared and may return as a peaceful visitor."
    elif quest_id == 7:
        state(player).setdefault("food", {})["family_recipe"] = True
        q["ending"] = (
            "The family cookbook is restored. Coastal cooking now prepares its restorative family stew."
        )
    elif quest_id == 17:
        q["ending"] = (
            "The portrait records a king who pursued power and sacrificed others for it."
        )
    else:
        q["ending"] = (
            f'{ADDONS[quest_id]["name"]}: the people record your choice to {choice} their history.'
        )
    return (
        True,
        q["ending"] + f" Reward: {reward} souls. Choice recorded for later chapters.",
    )


def trial(game, quest_id):
    q = records(game.player).get(str(quest_id))
    if quest_id not in (4, 12) or not q or q["stage"] != 1:
        return False, "No trial is ready."
    from expansion_combat import practice

    won = practice(game, "memory" if quest_id == 12 else "mercy")
    if won:
        q["trial_won"] = True
    return won, "Trial completed." if won else "You may try again when ready."


def menu(game, quest_id):
    while True:
        q = records(game.player).get(str(quest_id))
        print("\n--- " + ADDONS[quest_id]["name"].upper() + " ---")
        print(QUESTS[quest_id][2])
        print(QUESTS[quest_id][3])
        print("Progress: " + str(q or "not accepted"))
        print(
            "1. Accept\n2. Advance objective\n3. Final choice: preserve\n4. Final choice: share\n5. Final choice: private\n6. Nonlethal story trial\n0. Back"
        )
        c = input("Story quest > ").strip()
        if c == "0":
            return
        if c == "1":
            print(accept(game.player, quest_id)[1])
        elif c in ("2", "3", "4", "5"):
            choice = {"2": "preserve", "3": "preserve", "4": "share", "5": "private"}[c]
            print(progress(game, quest_id, choice)[1])
        elif c == "6":
            print(trial(game, quest_id)[1])
