"""Four regional monster forms and level-based stats, without reading player gear."""

from copy import deepcopy
import data

LEVELS = (1, 5, 10, 15)
HP_FACTORS = (1, 2.4, 4.5, 7)
ATK_FACTORS = (1, 2, 3.2, 4.5)
DEF_BONUS = (0, 3, 7, 12)


def stage(level):
    level = max(1, int(level))
    return max(index for index, minimum in enumerate(LEVELS) if level >= minimum)


def form(region, species, level):
    level = max(1, int(level))
    tier = stage(level)
    base = data.NORMAL_MONSTERS[region][species]
    evolved = data.EVOLVED_MONSTERS.get(region, [])
    advanced = evolved[species] if species < len(evolved) else base
    advanced_name = (
        advanced["name"]
        if advanced["name"] != base["name"]
        else "Ascended " + base["name"]
    )
    names = (
        base["name"],
        "Empowered " + base["name"],
        advanced_name,
        "Apex " + advanced_name,
    )
    enemy = deepcopy(advanced if tier >= 2 else base)
    delta = level - LEVELS[tier]
    enemy.update(
        name=names[tier],
        hp=max(
            1,
            round(
                base["hp"]
                * HP_FACTORS[tier]
                * (1 + (0.12 if tier == 0 else 0.08) * delta)
            ),
        ),
        atk=max(1, round(base["atk"] * ATK_FACTORS[tier] + delta)),
        **{"def": max(0, round(base.get("def", 0) + DEF_BONUS[tier] + 0.4 * delta))},
        evolution=dict(
            base=base["name"],
            region=region,
            stage=tier + 1,
            minimum_level=LEVELS[tier],
            level=level,
        ),
        evolution_rewards=dict(
            xp=(20, 30, 45, 65)[tier] + 2 * delta, gold=(20, 28, 40, 55)[tier] + delta
        ),
    )
    enemy["max_hp"] = enemy["hp"]
    return enemy


def champion(enemy, level):
    enemy = deepcopy(enemy)
    level = max(10, int(level))
    factor = 1 + 0.08 * (level - 10)
    for key in ("hp", "atk"):
        enemy[key] = max(1, round(enemy[key] * factor))
    enemy["def"] = max(0, round(enemy.get("def", 0) + 0.5 * (level - 10)))
    enemy["max_hp"] = enemy["hp"]
    enemy["evolution"] = dict(
        base=enemy["name"],
        stage=stage(level) + 1,
        minimum_level=10,
        level=level,
        champion=True,
    )
    enemy["evolution_rewards"] = dict(
        xp=60 + 3 * (level - 10), gold=70 + 2 * (level - 10)
    )
    return enemy


def pool(region, level):
    regular = [
        form(region, index, level)
        for index in range(len(data.NORMAL_MONSTERS.get(region, [])))
    ]
    champions = (
        [champion(enemy, level) for enemy in data.MINI_BOSSES.get(region, [])]
        if level >= 10
        else []
    )
    # Existing mini-bosses stay occasional: 25% with the usual two/two pools.
    return regular * 3 + champions if champions and regular else regular or champions


def tracked(enemy, region, level):
    for index, base in enumerate(data.NORMAL_MONSTERS.get(region, [])):
        if base["name"] == enemy["name"]:
            return form(region, index, level)
    return deepcopy(enemy)


def attack_range(enemy):
    if enemy.get("evolution") and enemy["evolution"]["level"] > 1:
        high = max(1, round(enemy["atk"]))
        return max(1, round(high * 0.65)), high
    if enemy.get("_story_boss"):
        return max(5, enemy["atk"] // 3), max(10, enemy["atk"] // 2)
    return 5, 15


def reference_entries():
    entries = []
    for region, bases in data.NORMAL_MONSTERS.items():
        for index, base in enumerate(bases):
            forms = [form(region, index, level) for level in LEVELS]
            chain = " → ".join(
                f"Lv {level}: {enemy['name']}" for level, enemy in zip(LEVELS, forms)
            )
            for enemy in forms:
                entries.append(
                    dict(
                        name=enemy["name"],
                        type="Creatures",
                        source="MONSTER_EVOLUTION",
                        description=f"{region} · Stage {enemy['evolution']['stage']}/4. {chain}. At level {enemy['evolution']['level']} before night, world events and Easy modifiers: HP {enemy['hp']}, ATK {enemy['atk']}, DEF {enemy['def']}, XP {enemy['evolution_rewards']['xp']}, souls {enemy['evolution_rewards']['gold']}. Stats grow with player level between forms and after level 15; carried gear is not used. Ordinary attacks use 65–100% of scaled ATK above level 1, before defence, evasion and effects. Easy keeps 25% less enemy HP and 40% less incoming direct damage. A normal species has equal selection weight to the other normal species; at level 10+, mini-bosses occupy 25% of the usual two-species/two-mini-boss pool. Night elite rolls still apply.",
                    )
                )
    return entries
