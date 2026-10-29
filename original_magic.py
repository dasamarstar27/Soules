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
    components = register(rune)
    if "region" in user:
        from magic_addons import record_cast

        record_cast(user, rune, components)
    for key in components:
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
            effects.hurt(
                destination, (before - destination["hp"]) * (multiplier - 1), log
            )
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
    return max(
        1, int(amount * ratio + target.get("def", 0) - effects.stat(victim, "def"))
    )


def strike(source, target, amount, magical=False):
    from monster_behaviour import guard_damage
    amount = guard_damage(target, amount)
    actor = proxy(source)
    victim = proxy(target)
    log = []
    # Ritual swiftness improves evasion only while its encounter counter lasts.
    from legacy_systems import ritual_bonus
    import random

    if ritual_bonus(target, "spd") and random.random() < 0.04 * ritual_bonus(
        target, "spd"
    ):
        print("Ritual swiftness carries you clear of the strike.")
        return 0
    # Equipment wards and rituals modify the already calculated strike once.
    armour = target.get("armour") or {}
    amount = max(1, round(amount * (1 - min(0.4, armour.get("damage_reduction", 0)))))
    if (target.get("weapon") or {}).get("slow_strikes"):
        amount = round(amount * 1.12)
    if magical:
        amount = max(
            1, round(amount * (1 - min(0.5, armour.get("element_resistance", 0))))
        )
    amount = max(1, amount + ritual_bonus(source, "atk") - ritual_bonus(target, "def"))
    from difficulty import incoming_strike

    amount = incoming_strike(target, amount)
    # Original damage calculation already accounts for equipment and defence.
    dealt = effects.hit(actor, victim, amount, log, piercing=True, magical=magical)
    for _ in range(max(0, int(effects.total(actor, "attack_count")) - 1)):
        if victim["hp"] > 0:
            dealt += effects.hit(
                actor, victim, amount, log, piercing=True, magical=magical
            )
    sync(source, actor)
    sync(target, victim)
    emit(log)
    return dealt


def can_flee(entity):
    return not effects.total(proxy(entity), "trap_in_battle")


def silenced(entity):
    return bool(effects.total(proxy(entity), "silenced"))
