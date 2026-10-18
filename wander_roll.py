"""One weighted draw selects a wander outcome, including rare discoveries/events."""

from math import lcm
import data

CHANCES = {
    "normal": dict(
        monster=45,
        gather=20,
        structure=10,
        special_event=10,
        merchant=5,
        companion=1,
        peaceful=9,
    ),
    "easy": dict(
        monster=30,
        gather=30,
        structure=12,
        special_event=12,
        merchant=6,
        companion=1,
        peaceful=9,
    ),
}
# Exact integer tickets preserve both event catalogue weights and rare subtypes.
TOTAL = lcm(10000, 100 * sum(event["weight"] for event in data.WANDER_EVENTS))


def ticket_table(region, undiscovered=True, bounty_available=True, difficulty="normal"):
    chances = CHANCES.get(difficulty, CHANCES["normal"])
    counts = {key: value * TOTAL // 100 for key, value in chances.items()}
    table = []
    bounty = (
        counts["monster"] * 2 // 100
        if bounty_available and region in data.BOUNTY_MONSTERS
        else 0
    )
    table.extend([("monster", counts["monster"] - bounty), ("bounty", bounty)])
    ingredients = counts["gather"] // 2 if data.REGION_INGREDIENTS.get(region) else 0
    table.extend(
        [
            ("ingredient", ingredients),
            ("building_supply", counts["gather"] - ingredients),
        ]
    )
    clan = counts["structure"] // 100 if region in data.ELEMENTAL_VILLAGES else 0
    ordinary = counts["structure"] - clan
    available = undiscovered and bool(data.REGION_STRUCTURES.get(region))
    table.extend(
        [("elemental_village", clan), ("structure", ordinary if available else 0)]
    )
    event_total = sum(event["weight"] for event in data.WANDER_EVENTS)
    table.extend(
        (
            "event:" + event["id"],
            counts["special_event"] * event["weight"] // event_total,
        )
        for event in data.WANDER_EVENTS
    )
    table.extend((key, counts[key]) for key in ("merchant", "companion"))
    table.append(("peaceful", counts["peaceful"] + (0 if available else ordinary)))
    assert sum(count for _, count in table) == TOTAL
    return [(key, count) for key, count in table if count]


def pick(player, rng):
    region = player["region"]
    found = player.get("discovered_structures", {}).get(region, [])
    undiscovered = any(
        s["name"] not in found for s in data.REGION_STRUCTURES.get(region, [])
    )
    bounty = data.BOUNTY_MONSTERS.get(region)
    available = bool(
        bounty and bounty["name"] not in player.get("bounties_claimed", [])
    )
    roll = rng.randrange(TOTAL)
    for key, count in ticket_table(
        region, undiscovered, available, player.get("difficulty", "normal")
    ):
        if roll < count:
            return key
        roll -= count
    raise AssertionError("Wander ticket outside table")


def resolve(game):
    p = game.player
    region = p["region"]
    outcome = pick(p, game.random)
    if outcome == "monster":
        game._wander_monster(region, p.get("is_night", False))
    elif outcome == "bounty":
        bounty = data.BOUNTY_MONSTERS[region]
        print(f"\n☠ BOUNTY TARGET SPOTTED: {bounty['name']}!")
        game.fight(bounty.copy())
        if p["hp"] > 0:
            p.setdefault("bounties_claimed", []).append(bounty["name"])
            p["gold"] += bounty["reward"]
            print(f"🏴 Bounty claimed! +{bounty['reward']} souls!")
        game._check_achievements()
    elif outcome == "ingredient":
        ingredient = game.random.choice(data.REGION_INGREDIENTS[region])
        p.setdefault("ingredients", []).append(ingredient)
        print(f"\n🌿 Gathered 1 {ingredient}. Added to your pouch.")
    elif outcome == "building_supply":
        from village_life import gather_building_material

        gather_building_material(p, game.random)
    elif outcome == "structure":
        found = p.setdefault("discovered_structures", {}).setdefault(region, [])
        pool = [s for s in data.REGION_STRUCTURES[region] if s["name"] not in found]
        structure = game.random.choice(pool)
        found.append(structure["name"])
        print(
            f"\n🗺 You've discovered a new location: {structure['icon']} {structure['name']}!"
        )
        print("Visit it through Explore → Structures.")
        game._check_achievements()
    elif outcome == "elemental_village":
        village = data.ELEMENTAL_VILLAGES[region]
        print(
            f"\n✨ A faint {village['icon']} glow reveals a hidden elemental village..."
        )
        game.visit_elemental_village()
    elif outcome.startswith("event:"):
        event = next(
            e for e in data.WANDER_EVENTS if e["id"] == outcome.split(":", 1)[1]
        )
        print(f"\n✦ {event['title']}: {event['desc']}")
        game._handle_wander_event(event["id"], region)
        game._check_achievements()
    elif outcome == "merchant":
        game.merchant()
    elif outcome == "companion":
        candidates = game.get_region_companion_candidates(region)
        if candidates:
            companion = game.random.choice(candidates)
            print(f"\n🐾 You encounter {companion['name']}!")
            if input("Recruit? (y/n) > ").strip().lower() == "y":
                game.recruit_companion(companion)
        else:
            print("No new companion answers your call here. You continue peacefully.")
    else:
        print("Peaceful wandering...")
