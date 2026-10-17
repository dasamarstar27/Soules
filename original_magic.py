"""Connect the complete effect registry to the original combat loop."""

import effects
from rune_pairs import register


def proxy(entity):
    for key in list(entity.setdefault("rune_status", {})):
        if key not in effects.EFFECTS:
            names = entity.get("rune_abilities", {}).get(key, {}).get("inputs", [])
            try:
                from rune_pairs import BASE, fusion

                result = fusion(*[BASE[name] for name in names])
                if result["pair_ability"] != key:
                    raise ValueError
                register(result)
            except (KeyError, TypeError, ValueError):
                entity["rune_status"].pop(key, None)
    copy = dict(entity)
    copy["status"] = entity.setdefault("rune_status", {})
    copy.setdefault("name", "Adventurer")
    copy.setdefault("max_hp", copy.get("hp", 100))
    copy.setdefault("mana", 0)
    copy["max_mana"] = max(100, copy["mana"])
    return copy


def sync(entity, copy):
    for key in ("hp", "mana"):
        entity[key] = copy[key]


def emit(log):
    for line in log:
        print(line)


def apply(rune, user, enemy):
    source = proxy(user)
    target = source if enemy is user else proxy(enemy)
    log = []
    for key in register(rune):
        destination = source if effects.EFFECTS[key]["target"] == "self" else target
        owner = user if destination is source else enemy
        owner.setdefault("rune_abilities", {})[key] = dict(
            effects.EFFECTS[key], inputs=rune.get("inputs", [])
        )
        before = destination["hp"]
        multiplier = (
            max(1, effects.total(source, "fusion_multiplier"))
            if rune.get("effect") == "fusion"
            else 1
        )
        effects.apply(destination, key, log, source)
        if destination is not source and before > destination["hp"] and multiplier > 1:
            effects.hurt(destination, (before - destination["hp"]) * (multiplier - 1), log)
    sync(user, source)
    if enemy is not user:
        sync(enemy, target)
    emit(log)


def turn(entity, opponent):
    current = proxy(entity)
    other = proxy(opponent)
    log = []
    effects.expire(current, entity.get("_rune_previous", []))
    entity["_rune_previous"] = list(current["status"])
    can_act = effects.tick(current, other, log)
    sync(entity, current)
    sync(opponent, other)
    emit(log)
    return can_act


def damage(source, target, amount):
    actor = proxy(source)
    victim = proxy(target)
    ratio = effects.stat(actor, "atk") / max(1, actor.get("atk", 1))
    return max(1, int(amount * ratio + target.get("def", 0) - effects.stat(victim, "def")))


def strike(source, target, amount, magical=False):
    actor = proxy(source)
    victim = proxy(target)
    log = []
    # Original damage calculation already accounts for equipment and defence.
    dealt = effects.hit(actor, victim, amount, log, piercing=True, magical=magical)
    for _ in range(max(0, int(effects.total(actor, "attack_count")) - 1)):
        if victim["hp"] > 0:
            dealt += effects.hit(actor, victim, amount, log, piercing=True, magical=magical)
    sync(source, actor)
    sync(target, victim)
    emit(log)
    return dealt


def can_flee(entity):
    return not effects.total(proxy(entity), "trap_in_battle")


def silenced(entity):
    return bool(effects.total(proxy(entity), "silenced"))
