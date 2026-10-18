"""Readable records, map annotations, routes and equipment comparison."""

import data
from expansion_state import state, mark, choose


def character_sheet(player):
    return dict(
        name=player["name"],
        level=player["level"],
        class_id=player.get("class_id"),
        region=player["region"],
        hp=player["hp"],
        max_hp=player["max_hp"],
        gold=player["gold"],
        chapter=player.get("chapter", 1),
        weapon=(player.get("weapon") or {}).get("name"),
        armour=(player.get("armour") or {}).get("name"),
        bosses=list(player.get("bosses_defeated", [])),
        companions=[
            x.get("form_name", x["name"]) for x in player.get("companions", [])
        ],
    )


def activity(game, feature):
    p = game.player
    s = state(p)
    if feature == 91:
        rows = s["activities"].get("battle_replays", [])
        index = choose(
            "COMBAT REPLAY",
            [
                f"Battle {i+1} · {'practice' if x['practice'] else 'journey'} · {'won' if x['won'] else 'withdrawn / defeated'}"
                for i, x in enumerate(rows)
            ],
        )
        if index is None:
            return
        for turn in rows[index]["turns"]:
            print(turn)
        mark(p, 91)
    elif feature == 92:
        print(
            "Saves now contains the five most recent explicit save checkpoints. Each can be restored independently of your six main slots."
        )
        mark(p, 92)
    elif feature == 93:
        print(
            "Customise → Keyboard controls lets you remap Focus, Latest and Back without changing numbered game choices."
        )
        mark(p, 93)
    elif feature == 94:
        print(
            "Customise → Screen-reader combat mode enables concise HP, enemy and current-question announcements."
        )
        mark(p, 94)
    elif feature == 95:
        r = p["region"]
        known = p.get("discovered_structures", {}).get(r, [])
        entries = [x for x in data.REGION_STRUCTURES.get(r, []) if x["name"] in known]
        index = choose("KNOWN ORDINARY MAP MARKERS", [x["name"] for x in entries])
        if index is None:
            return
        note = input("Map marker note (blank clears) > ").strip()[:240]
        s["notes"][r + "::" + entries[index]["name"]] = note
        mark(p, 95)
    elif feature == 96:
        routes = {}
        for quest in p.get("quests", []):
            if not quest.get("completed"):
                routes.setdefault(quest.get("region", p["region"]), []).append(
                    quest.get("desc", "Quest")
                )
        from addon_quests import QUESTS

        for key, q in s["quests"].items():
            if not q.get("complete"):
                region = QUESTS[int(key)][0 if q["stage"] == 0 else 1]
                routes.setdefault(region, []).append("Story " + key)
        for region, quests in routes.items():
            print(
                region
                + (" [unlocked]" if region in p["unlocked_regions"] else " [locked]")
                + ": "
                + ", ".join(quests)
            )
        if not routes:
            print("No active quest routes.")
        mark(p, 96)
    elif feature == 97:
        weapons = p.get("weapons", [])
        armours = p.get("armours", [])
        wi = choose("HYPOTHETICAL WEAPON", [x["name"] for x in weapons])
        if wi is None:
            return
        ai = choose("HYPOTHETICAL ARMOUR", ["No armour"] + [x["name"] for x in armours])
        if ai is None:
            return
        armour = None if ai == 0 else armours[ai - 1]
        print(
            "Planned ATK "
            + str(p["atk"] + weapons[wi].get("atk", 0))
            + " · DEF "
            + str(p["def"] + (armour or {}).get("def", 0))
            + ". Your equipped gear and supplies have not changed."
        )
        print("Weapon rune: " + str(weapons[wi].get("rune", {}).get("name", "none")))
        mark(p, 97)
    elif feature == 98:
        for key, value in character_sheet(p).items():
            print(str(key) + ": " + str(value))
        print(
            "Use Export character sheet on the Saves page to download this readable summary."
        )
        mark(p, 98)
    elif feature == 99:
        stats = s["statistics"]
        if stats.get("hidden"):
            print("Journey statistics are hidden.")
        else:
            favourites = sorted(
                (
                    (key, value)
                    for key, value in stats.items()
                    if key.startswith("addon_")
                ),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            print("Most selected activities: " + str(favourites))
            for key, value in stats.items():
                print(str(key) + ": " + str(value))
        if input("Toggle statistics visibility? (y/n) > ").strip().lower() == "y":
            stats["hidden"] = not stats.get("hidden", False)
        mark(p, 99)
    elif feature == 100:
        print(
            "Completed and fallen run chronicles are stored locally in Saves. New Game+ also carries a short written chronicle without carrying old supplies."
        )
        for entry in s.get("chronicles", []):
            print(entry)
        mark(p, 100)
