"""Every unordered pair of two catalogued normal runes, including two copies."""

from copy import deepcopy
from hashlib import sha256
from itertools import combinations_with_replacement
import data
from recipes import SPECIAL_FUSION_RECIPES
from effects import EFFECTS

BASE = {r["name"]: deepcopy(r) for r in data.RUNES if r.get("effect") != "fusion"}
PAIR_COUNT = len(BASE) * (len(BASE) + 1) // 2


def fusion(first, second):
    if any(r.get("effect") == "fusion" or r.get("name") not in BASE for r in (first, second)):
        raise ValueError("Fuse exactly two normal runes. Fused runes cannot be ingredients.")
    names = sorted([first["name"], second["name"]])
    a, b = [BASE[name] for name in names]
    digest = sha256("|".join(names).encode()).hexdigest()
    number = int(digest[:8], 16)
    power = 5 + number % 7
    elements = {a.get("element"), b.get("element")}
    families = [
        ("Resonant Strike", dict(damage=power + 5)),
        ("Renewing Echo", dict(hp_restore_per_turn=2 + power // 3)),
        ("Woven Guard", dict(damage_reduction=0.12 + number % 9 / 100)),
        ("Battle Chorus", dict(atk_modifier=1.15 + number % 11 / 100)),
        ("Soul Current", dict(damage=power, attacker_heal=0.5)),
        ("Mind Spring", dict(mana_restore_per_turn=2 + power // 3)),
        ("Fracture", dict(def_modifier=0.65)),
        ("Binding Pulse", dict(spd_modifier=0.55)),
        ("Precise Echo", dict(crit_chance=0.12 + number % 9 / 100)),
        ("Return Ward", dict(reflect_damage=0.15 + number % 11 / 100)),
    ]
    label, mechanics = families[number % len(families)]
    if elements == {"fire", "ice"}:
        label, mechanics = "Thermal Shock", dict(damage=power + 7, stun_chance=0.2)
    elif elements == {"water", "storm"}:
        label, mechanics = "Conductive Surge", dict(damage=power + 4, stun_chance=0.3)
    elif elements == {"fire", "nature"}:
        label, mechanics = "Ashen Renewal", dict(hp_restore_per_turn=3, atk_modifier=1.2)
    beneficial = any(
        key in mechanics
        for key in (
            "hp_restore_per_turn",
            "mana_restore_per_turn",
            "atk_modifier",
            "damage_reduction",
            "crit_chance",
            "reflect_damage",
        )
    )
    ability = dict(
        name=f'{names[0].removesuffix(" Rune")} × {names[1].removesuffix(" Rune")} · {label}',
        icon="✦",
        duration=3,
        target="self" if beneficial else "enemy",
        **mechanics,
    )
    key = "pair_" + digest[:20]
    from effects import effect_description

    ability["description"] = effect_description(ability)
    recipe = SPECIAL_FUSION_RECIPES.get(frozenset(names))
    # Preserve old recipes whose historical Fire Rune is now called Flame Rune.
    if not recipe:
        recipe = SPECIAL_FUSION_RECIPES.get(
            frozenset(name.replace("Flame Rune", "Fire Rune") for name in names)
        )
    components = list(
        dict.fromkeys([a["effect"], b["effect"]] + (recipe["components"] if recipe else []))
    )
    if any(effect not in EFFECTS for effect in components):
        raise ValueError("A fusion component has no registered ability.")
    return dict(
        name=(
            recipe["name"]
            if recipe
            else " + ".join(name.removesuffix(" Rune") for name in names) + " Rune"
        ),
        effect="fusion",
        element="fusion",
        inputs=names,
        components=components,
        pair_ability=key,
        ability=ability,
    )


def register(rune):
    if rune.get("effect") == "fusion" and len(rune.get("inputs", [])) == 2:
        result = fusion(*[BASE[name] for name in rune["inputs"]])
        EFFECTS[result["pair_ability"]] = result["ability"]
        return result["components"] + [result["pair_ability"]]
    return rune.get("components", []) if rune.get("effect") == "fusion" else [rune["effect"]]


def all_pairs():
    for a, b in combinations_with_replacement(BASE.values(), 2):
        yield fusion(a, b)
