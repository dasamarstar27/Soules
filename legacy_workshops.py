"""Finish the original advanced skills, collections and prestige workshops."""

from collections import Counter
from copy import deepcopy
import data
import original_ui as ui
from expansion_state import choose, pay, state


def learn(player, tree_name, skill_name):
    tree = data.SKILL_TREES.get(tree_name, {})
    skill = tree.get("skills", {}).get(skill_name)
    learned = player.setdefault("skill_tree", {}).setdefault(tree_name, {})
    if not skill:
        return False, "Unknown skill."
    if learned.get(skill_name):
        return False, "Already learned; points kept."
    if (
        player["level"] < skill["level"]
        or player.get("skill_points", 0) < skill["cost"]
    ):
        return False, "Meet the displayed level and skill-point cost."
    player["skill_points"] -= skill["cost"]
    learned[skill_name] = True
    stat = skill["stat"]
    bonus = skill["bonus"]
    if stat == "hp":
        player["max_hp"] += bonus
        player["hp"] += bonus
    else:
        stat = "speed" if stat == "spd" else stat
        player[stat] = player.get(stat, 0) + bonus
    return True, "Learned " + skill_name + "."


def advanced_skills(game):
    p = game.player
    trees = list(data.SKILL_TREES)
    index = choose("ADVANCED SKILL TREES", trees)
    if index is None:
        return
    tree = trees[index]
    skills = list(data.SKILL_TREES[tree]["skills"].items())
    selected = choose(
        "SKILLS · " + str(p.get("skill_points", 0)) + " POINTS",
        [
            f'{name}: level {info["level"]}, {info["cost"]} points, +{info["bonus"]} {info["stat"]}'
            + (" · learned" if p.get("skill_tree", {}).get(tree, {}).get(name) else "")
            for name, info in skills
        ],
    )
    if selected is not None:
        print(learn(p, tree, skills[selected][0])[1])


def ascend(game):
    p = game.player
    if not p.get("source_story", {}).get("season_one_complete"):
        print("Complete the original invasion first.")
        return False
    if ui.village:
        print("Leave the village before beginning a fresh prestige journey.")
        return False
    level = p.get("prestige_level", 0)
    if level >= 3:
        print("Maximum prestige reached.")
        return False
    from original_worker import initial_player
    from journal_addons import character_sheet

    history = state(p).get("chronicles", []) + [character_sheet(p)]
    old = dict(title=p.get("title"), achievements=list(p.get("achievements", [])))
    fresh = initial_player({"name": p["name"], "cls": p.get("class_id", "warrior"), "difficulty": p.get("difficulty", "normal")})
    p.clear()
    p.update(fresh)
    p.update(old)
    p["prestige_level"] = level + 1
    multiplier = 1 + 0.1 * (level + 1)
    for stat in ("max_hp", "atk", "def"):
        p[stat] = round(p[stat] * multiplier, 1)
    p["hp"] = p["max_hp"]
    state(p)["chronicles"] = history[-10:]
    ui.village = None
    ui.location = None
    ui.init_ui(p)
    print(
        "Prestige ascension: a fresh journey, Rusty Sword only, +"
        + str((level + 1) * 10)
        + "% starting health, attack and defence."
    )
    game.visit_village({"name": "Old Village"}, data.REGIONS[0])
    return True


def collections(game):
    p = game.player
    s = state(p).setdefault("systems", {})
    while True:
        c = choose(
            "ORIGINAL WORKSHOPS & COLLECTIONS",
            [
                "Advanced skills",
                "Material mastery",
                "Equipment collections",
                "Legendary weapon commission",
                "Prestige supply shop",
                "Artifacts",
                "Prestige ascension (fresh journey)",
                "Material transmutation",
            ],
        )
        if c is None:
            return
        if c == 0:
            advanced_skills(game)
        elif c == 1:
            game.view_material_mastery()
        elif c == 2:
            sync_sets(p)
            owned = {
                x["name"]
                for bag in ("weapons", "armours", "staffs")
                for x in p.get(bag, [])
            }
            for name, entry in data.EQUIPMENT_SETS.items():
                print(
                    name
                    + ": "
                    + str(sum(x in owned for x in entry["pieces"]))
                    + "/"
                    + str(len(entry["pieces"]))
                    + " · "
                    + str(entry["bonuses"])
                )
            print(
                "Collection stat bonuses follow owned pieces; selling pieces removes the matching bonus. Lifesteal applies to weapon attacks."
            )
        elif c == 3:
            import original_ui as ui

            if not ui.village or "forge" not in ui.village["services"]:
                print("Visit a village with a forge.")
                continue
            needed = {
                "Abyssium": ("metals", 3),
                "Dragon Hide": ("leathers", 2),
                "Shadow Core": ("cores", 1),
            }
            print(
                "Blade of the Abyss: 3 Abyssium, 2 Dragon Hide, 1 ordinary Shadow Core. No protected elemental core is used."
            )
            if s.get("legendary_forged"):
                print("This legendary commission is already complete.")
                continue
            if any(
                p.get(bag, []).count(name) < amount
                for name, (bag, amount) in needed.items()
            ):
                print("Gather the required materials first.")
                continue
            if input("Forge it? (yes/no) > ").strip().lower() != "yes":
                continue
            for name, (bag, amount) in needed.items():
                for _ in range(amount):
                    p[bag].remove(name)
            item = dict(
                name="Blade of the Abyss",
                atk=50,
                value=250,
                materials={name: amount for name, (_, amount) in needed.items()},
                tier="legendary",
            )
            from artisan_addons import apply_traits

            apply_traits(p, item, "smithing")
            p["weapons"].append(item)
            s["legendary_forged"] = True
            print("Blade of the Abyss forged.")
        elif c == 4:
            prestige = p.get("prestige_level", 0)
            if prestige < 1:
                print("Requires prestige 1.")
                continue
            stock = [("Titanium", "metals", 200), ("Star Core", "cores", 500)]
            if prestige >= 2:
                stock += [
                    ("Dragonsteel", "metals", 400),
                    ("Shadow Core", "cores", 1000),
                ]
            if prestige >= 3:
                stock += [
                    ("Creator Alloy", "metals", 600),
                    ("Omnipotent Core", "cores", 1500),
                ]
            cycle = p.get("wander_count", 0) // 20
            claims = s.setdefault("prestige_stock", {})
            index = choose(
                "PRESTIGE SUPPLIES · ONE EACH PER EXPLORATION CYCLE",
                [name + " · " + str(price) + " souls" for name, _, price in stock],
            )
            if index is None:
                continue
            name, bag, price = stock[index]
            if claims.get(name) == cycle:
                print("Sold out until the next 20-wander cycle.")
                continue
            if pay(p, price):
                p.setdefault(bag, []).append(name)
                claims[name] = cycle
                print("Purchased " + name + ".")
        elif c == 5:
            entries = list(data.ARTIFACTS.items())
            owned = p.setdefault("artifacts", [])
            index = choose(
                "ARTIFACT COLLECTION",
                [
                    info["name"]
                    + f" · {5+min(10,i*4)} main guardians, {100+i*50} souls · "
                    + ("owned" if key in owned else str(info["stats"]))
                    for i, (key, info) in enumerate(entries)
                ],
            )
            if index is None:
                continue
            key, info = entries[index]
            if key in owned:
                print("Already owned. Bonuses cannot be stacked.")
                continue
            defeated = len(set(p.get("bosses_defeated", [])) & set(data.REGIONS))
            if defeated < 5 + min(10, index * 4) or not pay(p, 100 + index * 50):
                print("Meet the displayed guardian and soul requirements.")
                continue
            for stat, amount in info["stats"].items():
                p[stat] = p.get(stat, 0) + amount
            owned.append(key)
            print("Recovered " + info["name"] + ". Its displayed stats apply once.")
        elif c == 7:
            options = [("Iron", "Steel", 25), ("Steel", "Crimson Steel", 100)]
            index = choose(
                "TRANSMUTATION · THREE METALS BECOME ONE",
                [
                    first + " ×3 → " + second + " · " + str(price) + " souls"
                    for first, second, price in options
                ],
            )
            if index is None:
                continue
            first, second, price = options[index]
            if p.get("metals", []).count(first) < 3 or not pay(p, price):
                print("Bring the displayed metals and souls.")
                continue
            for _ in range(3):
                p["metals"].remove(first)
            p["metals"].append(second)
            print("Created " + second + ".")
        elif c == 6:
            if (
                input(
                    "Begin a fresh prestige journey? All carried supplies reset. (prestige/cancel) > "
                )
                .strip()
                .lower()
                == "prestige"
            ):
                ascend(game)
                return


def sync_sets(player):
    systems = state(player).setdefault("systems", {})
    owned = {
        x["name"]
        for bag in ("weapons", "armours", "staffs")
        for x in player.get(bag, [])
    }
    bonus = {"atk": 0, "def": 0, "lifesteal": 0}
    for entry in data.EQUIPMENT_SETS.values():
        pieces = sum(name in owned for name in entry["pieces"])
        applicable = [
            (int(n), value) for n, value in entry["bonuses"].items() if int(n) <= pieces
        ]
        if applicable:
            for key, amount in max(applicable, key=lambda x: x[0])[1].items():
                bonus[key] = bonus.get(key, 0) + amount
    previous = systems.get("equipment_collection_bonus", {})
    for stat in ("atk", "def"):
        player[stat] += bonus[stat] - previous.get(stat, 0)
    systems["equipment_collection_bonus"] = bonus


def boss_rush(game):
    p = game.player
    eligible = [
        region for region in data.REGIONS if region in p.get("bosses_defeated", [])
    ]
    if not eligible:
        print("Defeat at least one regional guardian before attempting boss rush.")
        return
    rows = list(data.BOSS_RUSH_CONFIGURATIONS.items())
    index = choose(
        "BOSS RUSH · LIVE COMBAT, CARRIED SUPPLIES",
        [
            entry["name"]
            + ": "
            + str(entry["bosses_count"])
            + " fights · "
            + entry["description"]
            for _, entry in rows
        ],
    )
    if index is None:
        return
    key, config = rows[index]
    systems = state(p).setdefault("systems", {})
    cycle = p.get("wander_count", 0) // 20
    if systems.get("rush_cycle") == cycle:
        print("One boss-rush attempt per 20-wander cycle.")
        return
    systems["rush_cycle"] = cycle
    stats = p.setdefault("boss_rush_stats", {})
    stats["total_runs"] = stats.get("total_runs", 0) + 1
    wins = 0
    gold = 0
    from expansion_combat import encounter

    for i in range(config["bosses_count"]):
        enemy = deepcopy(data.REGION_BOSSES[eligible[i % len(eligible)]])
        enemy["name"] += " · Rush " + str(i + 1)
        for stat in ("hp", "atk", "def"):
            enemy[stat] = max(
                1, int(enemy.get(stat, 0) * config["difficulty_multiplier"])
            )
        enemy["gold"] = int(enemy.get("gold", 50) * config["reward_multiplier"])
        enemy["boss"] = True
        print("Rush wave " + str(i + 1) + "/" + str(config["bosses_count"]))
        if not encounter(game, [enemy]):
            break
        wins += 1
        gold += enemy["gold"]
        if (
            i + 1 < config["bosses_count"]
            and input("Continue the rush with current health? (y/n) > ").strip().lower()
            != "y"
        ):
            break
    stats["best_run_" + key] = max(stats.get("best_run_" + key, 0), wins)
    stats["leaderboard_score"] = max(
        stats.get("leaderboard_score", 0), wins * 100 + gold // 10
    )
    print(
        "Rush ended: "
        + str(wins)
        + " victories. Record saved. Guardian unlocks and chapter endings are unaffected."
    )
