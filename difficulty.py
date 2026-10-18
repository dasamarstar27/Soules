"""The two adventure difficulties; missing saved choices retain standard balance."""

from copy import deepcopy

DIFFICULTIES = ("normal", "easy")


def validate(value):
    if not isinstance(value, str) or value not in DIFFICULTIES:
        raise ValueError("Choose Easy or Normal difficulty.")
    return value


def easy_enemy(player, enemy):
    """Adjust a fresh encounter copy without changing catalogue enemies or rewards."""
    if player.get("difficulty", "normal") != "easy":
        return enemy
    enemy = deepcopy(enemy)
    health = enemy.get("hp", 40)
    enemy["hp"] = max(1, round(health * 0.75))
    enemy["max_hp"] = max(enemy["hp"], round(enemy.get("max_hp", health) * 0.75))
    return enemy


def incoming_strike(target, amount):
    """Only the player has a difficulty; enemy and player outgoing damage stay intact."""
    return (
        max(1, round(amount * 0.6))
        if target.get("difficulty") == "easy" and amount > 0
        else amount
    )
