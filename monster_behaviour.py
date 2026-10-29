"""Telegraphed, per-round behaviour for ordinary single-enemy fights."""

from math import ceil

INTENTS = {
    "attack": ("Attack", "moves in for a normal strike."),
    "heavy": (
        "Heavy strike",
        "winds up a heavy blow. Guard or Interrupt to answer it.",
    ),
    "pounce": (
        "Pounce",
        "crouches to lunge. Guard reduces the damage; Interrupt cancels the move.",
    ),
    "guard": (
        "Guard",
        "braces defensively: direct strikes deal half damage this round.",
    ),
    "recover": (
        "Recover",
        "tries to recover 8% health instead of attacking. Finish it or use the opening.",
    ),
    "drain": (
        "Life siphon",
        "draws in soul energy: a weaker hit will restore some of its health.",
    ),
    "fumble": ("Mistake", "loses its footing and will miss its next action."),
}


def prepare(enemy, rng):
    if enemy.get("active_buffs", {}).get("stun"):
        enemy["intent"] = dict(
            key="stunned",
            name="Stunned",
            description="cannot act this round because of its status.",
        )
        return enemy["intent"]
    if enemy.get("intent"):
        return enemy["intent"]
    name = enemy["name"].lower()
    if any(
        word in name
        for word in ("spirit", "wraith", "mage", "witch", "lich", "shaman", "spectre")
    ):
        weights = [
            ("attack", 35),
            ("guard", 10),
            ("heavy", 15),
            ("drain", 20),
            ("recover", 13),
            ("fumble", 7),
        ]
    elif any(
        word in name
        for word in ("wolf", "spider", "beast", "hound", "bear", "bat", "lurker")
    ):
        weights = [
            ("attack", 40),
            ("guard", 8),
            ("heavy", 15),
            ("pounce", 25),
            ("recover", 5),
            ("fumble", 7),
        ]
    else:
        weights = [
            ("attack", 45),
            ("guard", 15),
            ("heavy", 15),
            ("pounce", 10),
            ("recover", 8),
            ("fumble", 7),
        ]
    roll = rng.randrange(100)
    for key, weight in weights:
        if roll < weight:
            break
        roll -= weight
    if key == "recover" and (
        enemy["hp"] >= enemy["max_hp"] * 0.6 or enemy.get("_recoveries", 0) >= 2
    ):
        key = "attack"
    label, detail = INTENTS[key]
    enemy["intent"] = dict(key=key, name=label, description=detail)
    return enemy["intent"]


def interrupt(player, enemy):
    if enemy["intent"]["key"] not in ("heavy", "pounce"):
        return False, "There is no charged move to interrupt. Choose another action."
    if player.get("mana", 0) < 3:
        return False, "Interrupt needs 3 mana. Guard is free."
    player["mana"] -= 3
    enemy["_interrupted"] = True
    return True, "You interrupt the charged move! The monster loses its action."


def enemy_action(enemy, base):
    key = enemy["intent"]["key"]
    if enemy.pop("_interrupted", False):
        return 0
    if key == "guard":
        print("The monster holds its guard instead of attacking.")
        return 0
    if key == "fumble":
        print("The monster stumbles and misses its action!")
        return 0
    if key == "recover":
        healed = min(
            enemy["max_hp"] - enemy["hp"], max(1, ceil(enemy["max_hp"] * 0.08))
        )
        enemy["hp"] += healed
        enemy["_recoveries"] = enemy.get("_recoveries", 0) + 1
        print(f"{enemy['name']} recovers {healed} HP instead of attacking.")
        return 0
    return max(
        1, round(base * {"heavy": 1.65, "pounce": 1.2, "drain": 0.85}.get(key, 1))
    )


def guard_damage(enemy, amount):
    if (
        enemy.get("_behaviour_enabled")
        and enemy.get("intent", {}).get("key") == "guard"
        and not enemy.get("active_buffs", {}).get("stun")
    ):
        print("The monster’s guard halves your direct strike.")
        return max(1, ceil(amount * 0.5))
    return amount


def after_hit(enemy, dealt):
    if dealt > 0 and enemy.get("intent", {}).get("key") == "drain":
        healed = min(enemy["max_hp"] - enemy["hp"], max(1, dealt // 4))
        enemy["hp"] += healed
        print(f"Life siphon restores {healed} HP to {enemy['name']}.")
