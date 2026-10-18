"""Shared hooks keep original combat, crafting and new activities connected."""

from copy import deepcopy
from expansion_state import state, count


def on_wander(game):
    from legacy_systems import on_wander as legacy
    from food_addons import decay
    from expedition import observe

    p = game.player
    legacy(p)
    decay(p)
    observe(p)
    count(p, "wanders")
    for pet in p.get("companions", []):
        if (
            pet.get("temperament") == "curious"
            and pet.get("hunger", 100) >= 30
            and p.get("wander_count", 0) % 20 == 0
        ):
            import data

            pool = data.REGION_INGREDIENTS.get(p["region"], [])
            if pool:
                p.setdefault("ingredients", []).append(pool[0])
                print(pet["name"] + " scouted an extra " + pool[0] + ".")


def prompt(player, text, snapshot):
    activities = state(player)["activities"]
    enemy = snapshot.get("enemy")
    if enemy and enemy.get("addon_encounter"):
        return
    current = activities.get("current_battle")
    if enemy:
        if not current or current["enemy"] != enemy["name"]:
            if current:
                finish_battle(player, False)
            current = dict(enemy=enemy["name"], turns=[], practice=False, won=False)
            activities["current_battle"] = current
        entry = dict(
            prompt=text,
            hp=player["hp"],
            enemy_hp=enemy["hp"],
            effects=deepcopy(player.get("rune_status", {})),
        )
        if not current["turns"] or current["turns"][-1] != entry:
            current["turns"].append(entry)
            del current["turns"][:-80]
    elif current:
        finish_battle(player, False)


def finish_battle(player, won):
    activities = state(player)["activities"]
    current = activities.pop("current_battle", None)
    if current:
        current["won"] = won
        current["turns"].append(dict(hp=player["hp"], finished=True))
        history = activities.setdefault("battle_replays", [])
        history.append(current)
        del history[:-10]
    if current or won:
        ritual = state(player).get("systems", {}).get("ritual", {})
        if ritual:
            ritual["remaining"] = max(0, ritual.get("remaining", 0) - 1)
    if won:
        count(player, "victories")
        systems = state(player).setdefault("systems", {})
        systems["battle_xp"] = systems.get("battle_xp", 0) + 20


def scale_enemy(player, enemy):
    runs = state(player).get("systems", {}).get("ngplus", 0)
    if not runs and player.get("faction") != "shadow_cult":
        return enemy
    enemy = deepcopy(enemy)
    factor = 1 + 0.5 * min(4, runs)
    enemy["hp"] = int(enemy.get("hp", 50) * factor)
    enemy["max_hp"] = enemy["hp"]
    enemy["atk"] = int(enemy.get("atk", 5) * factor)
    enemy["xp"] = int(enemy.get("xp", 20) * (1.2 if runs else 1))
    enemy["gold"] = int(
        enemy.get("gold", 10)
        * (1.2 if runs else 1)
        * (1.2 if player.get("faction") == "shadow_cult" else 1)
    )
    return enemy
