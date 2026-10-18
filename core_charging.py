"""Sacrifice a loose normal rune into an ordinary core for the Crimson hearth."""

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


def compatible(core, rune):
    return (
        core in BLOCKED
        and isinstance(rune, dict)
        and rune in data.RUNES
        and rune.get("effect") in effects.EFFECTS
        and rune.get("effect") != "fusion"
        and rune.get("element") not in BLOCKED[core]
    )


def limits(core):
    blocked = ", ".join(sorted(BLOCKED.get(core, ())))
    return "Rejects: " + blocked if blocked else "Accepts every normal rune element"


def make_charged(core, rune, region):
    if not compatible(core, rune):
        raise ValueError("Incompatible rune and weapon core")
    return dict(
        name="Charged " + core + " · " + rune["name"],
        core_name=core,
        rune=deepcopy(rune),
        element=rune["element"],
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
    if rune.get("effect") == "fusion" or rune.get("effect") not in effects.EFFECTS:
        return (
            False,
            "Charge cores with one normal loose rune. Bound runes and fusions cannot be sacrificed.",
        )
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
        "CHARGE WEAPON CORE · CONSUMES ONE CORE AND ONE NORMAL RUNE",
        [core + " · " + limits(core) for core in cores],
    )
    if first is None:
        return
    print(cores[first] + " · " + limits(cores[first]))
    runes = [
        (i, r) for i, r in enumerate(p.get("runes", [])) if compatible(cores[first], r)
    ]
    second = choose(
        "SACRIFICE A LOOSE NORMAL RUNE",
        [
            r["name"] + " · " + effects.EFFECTS[r["effect"]]["description"]
            for _, r in runes
        ],
    )
    if second is None:
        return
    print(charge(p, cores[first], runes[second][0])[1])
