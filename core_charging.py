"""Sacrifice a compatible loose normal rune or fusion into a Crimson weapon core."""

from copy import deepcopy
import data
import effects
from expansion_state import choose


# Opposing elemental families cannot charge each other. Other normal runes
# remain valid; this restriction does not alter two-normal-rune fusion recipes.
CORE_ELEMENTS = dict(
    zip(
        data.CORES,
        (
            "fire",
            "nature",
            "ice",
            "soul",
            "shadow",
            "astral",
            "water",
            "metal",
            "poison",
            "rift",
            "inferno",
            "dream",
            "crystal",
            "ember",
            "prism",
            "celestial",
            "abyss",
            "dragon",
            "phoenix",
            "cosmic",
        ),
    )
)
HOT = frozenset(("fire", "ember", "inferno", "magma", "solar", "phoenix"))
COLD = frozenset(("ice", "frost", "glacial"))
WET = frozenset(("water", "tide"))
DARK = frozenset(("shadow", "abyss", "void", "necrotic", "death", "demon"))
LIGHT = frozenset(("light", "radiant", "celestial", "angel"))
BLOCKED = {name: frozenset() for name in data.CORES}
for name in (
    "Molten Core",
    "Hellfire Core",
    "Ember Core",
    "Dragon Core",
    "Phoenix Core",
):
    BLOCKED[name] = WET | COLD
BLOCKED["Glacier Core"] = HOT
BLOCKED["Ocean Core"] = HOT
for name in ("Shadow Core", "Abyss Core"):
    BLOCKED[name] = LIGHT
BLOCKED["Celestial Core"] = DARK
BLOCKED["Nature Core"] = frozenset(("death", "necrotic", "inferno"))
BLOCKED["Blight Core"] = frozenset(("life", "harmony"))


FUSION_ENERGIES = {
    **{
        name: HOT | {"dragon"}
        for name in (
            "Molten Core",
            "Hellfire Core",
            "Ember Core",
            "Dragon Core",
            "Phoenix Core",
        )
    },
    "Glacier Core": COLD,
    "Ocean Core": WET,
    "Nature Core": frozenset(("nature", "forest", "life")),
    "Soul Core": frozenset(("soul", "spirit", "spectral", "ethereal", "blood")),
    "Shadow Core": frozenset(("shadow", "nightmare", "void")),
    "Star Core": frozenset(("astral", "cosmic", "solar", "lunar", "celestial")),
    "Iron Core": frozenset(("metal", "iron", "steel", "magnetic")),
    "Blight Core": frozenset(("poison", "venom", "necrotic")),
    "Anomaly Core": frozenset(("rift", "space", "time", "gravity", "chaos")),
    "Lucid Core": frozenset(("dream", "nightmare")),
    "Spire Core": frozenset(("crystal", "quartz", "prism", "glimmer")),
    "Prism Core": frozenset(("prism", "crystal", "quartz", "glimmer")),
    "Celestial Core": LIGHT | {"solar"},
    "Abyss Core": frozenset(("abyss", "void", "death", "necrotic", "shadow")),
    "Omnipotent Core": frozenset(("cosmic", "ancient", "eternal", "eternity", "fate")),
}


def fusion_components(rune):
    from rune_pairs import BASE, fusion

    names = rune.get("inputs")
    if (
        not isinstance(names, list)
        or len(names) != 2
        or any(not isinstance(n, str) or n not in BASE for n in names)
    ):
        return None
    parts = [BASE[name] for name in names]
    canonical = fusion(*parts)
    if not all(rune.get(key) == value for key, value in canonical.items()):
        return None
    return parts


def compatible(core, rune):
    if not isinstance(core, str) or core not in BLOCKED or not isinstance(rune, dict):
        return False
    if rune.get("effect") == "fusion":
        parts = fusion_components(rune)
        return bool(parts) and all(
            part["element"] in FUSION_ENERGIES[core] for part in parts
        )
    return (
        rune in data.RUNES
        and rune.get("effect") in effects.EFFECTS
        and rune.get("element") not in BLOCKED[core]
    )


def rune_description(rune):
    if rune.get("effect") == "fusion":
        return (
            " + ".join(rune["inputs"])
            + " · both components match this core's energy; retains both abilities and fusion synergy"
        )
    return effects.EFFECTS[rune["effect"]]["description"]


def limits(core):
    blocked = ", ".join(sorted(BLOCKED.get(core, ())))
    return (
        (
            "Normal runes reject: " + blocked
            if blocked
            else "Normal runes: every element allowed"
        )
        + ". Fusion requires BOTH components from: "
        + ", ".join(sorted(FUSION_ENERGIES[core]))
    )


def make_charged(core, rune, region):
    if not compatible(core, rune):
        raise ValueError("Incompatible rune and weapon core")
    return dict(
        name="Charged " + core + " · " + rune["name"],
        core_name=core,
        rune=deepcopy(rune),
        element=CORE_ELEMENTS[core] if rune["effect"] == "fusion" else rune["element"],
        charged=True,
        source_region=region,
    )


def charge(player, core, rune_index):
    runes = player.get("runes", [])
    if core not in data.CORES or core not in player.get("cores", []):
        return (
            False,
            "Carry an ordinary weapon core; protected clan cores cannot be charged.",
        )
    if type(rune_index) is not int or not 0 <= rune_index < len(runes):
        return False, "Choose a carried loose rune."
    rune = runes[rune_index]
    if not compatible(core, rune):
        return (
            False,
            core
            + " cannot accept "
            + rune.get("name", "that rune")
            + ". "
            + limits(core)
            + ". Supplies kept.",
        )
    player["cores"].remove(core)
    runes.pop(rune_index)
    item = make_charged(core, rune, player["region"])
    player.setdefault("charged_cores", []).append(item)
    return (
        True,
        "Charged "
        + core
        + " by sacrificing "
        + rune["name"]
        + ". The rune and ordinary core are consumed into one charged core. Only the reclaimed Crimson Forge can use it to make an elemental weapon.",
    )


def menu(game):
    p = game.player
    cores = list(dict.fromkeys(x for x in p.get("cores", []) if x in data.CORES))
    first = choose(
        "CHARGE WEAPON CORE · CONSUMES ONE CORE AND ONE LOOSE RUNE",
        [core + " · " + limits(core) for core in cores],
    )
    if first is None:
        return
    print(cores[first] + " · " + limits(cores[first]))
    runes = [
        (i, r) for i, r in enumerate(p.get("runes", [])) if compatible(cores[first], r)
    ]
    second = choose(
        "SACRIFICE A COMPATIBLE LOOSE RUNE · MATCHING-ENERGY FUSIONS ALLOWED",
        [r["name"] + " · " + rune_description(r) for _, r in runes],
    )
    if second is None:
        return
    print(charge(p, cores[first], runes[second][0])[1])
