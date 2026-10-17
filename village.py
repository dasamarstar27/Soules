"""All crafting workstations are available from the village hub."""

from data import STRUCTURES
from copy import deepcopy

COSTS = {
    "forge": {"gold": 25, "shards": 1, "action": "Temper weapon · +2 attack"},
    "loom": {"gold": 25, "shards": 1, "action": "Weave armor reinforcement · +1 defense"},
    "enchantment_tower": {
        "gold": 15,
        "shards": 1,
        "action": "Combine two runes into a castable staff",
    },
    "disenchantry": {
        "gold": 0,
        "shards": 0,
        "action": "Salvage a rune or staff · recover 1 shard and 5 gold",
    },
    "source_temple": {
        "gold": 10,
        "shards": 1,
        "action": "Infuse a staff with another rune’s effects",
    },
}


def catalog():
    return [dict(key=k, **deepcopy(v), work=COSTS.get(k)) for k, v in STRUCTURES.items()]


def craft(g, body, fuse):
    station = body.get("structure")
    if station not in COSTS:
        raise ValueError("Choose a village crafting workstation.")
    if g["enemy"]:
        raise ValueError("Return to the village after the battle to craft.")
    if g["player"]["hp"] <= 0:
        raise ValueError("Rest at the village sanctuary first.")
    price = COSTS[station]
    if g["player"]["gold"] < price["gold"] or g["shards"] < price["shards"]:
        raise ValueError(
            f"You need {price['gold']} gold and {price['shards']} soul shard(s). Explore to earn them."
        )
    owned = {r["id"]: r for r in g["runes"]}
    selected = body.get("rune_ids", [])
    if (
        not isinstance(selected, list)
        or any(not isinstance(i, str) for i in selected)
        or len(set(selected)) != len(selected)
    ):
        raise ValueError("Choose separate runes from your collection.")
    if any(i not in owned for i in selected):
        raise ValueError("A selected rune is no longer in your collection.")
    consumed = []
    result = None
    if station == "enchantment_tower":
        if len(selected) != 2:
            raise ValueError("Choose two different inventory copies to make a staff.")
        result = fuse([owned[i] for i in selected])
        result.update(kind="staff", name=result["name"].removesuffix(" Rune") + " Staff")
        consumed = selected
        message = (
            "Crafted "
            + result["name"]
            + ". Invoke it from the spell list in combat, or bind it to your weapon."
        )
    elif station == "source_temple":
        staff = owned.get(body.get("staff_id"))
        if not staff or staff.get("kind") != "staff":
            raise ValueError("Make a staff at the Enchantment Tower first, then choose it here.")
        if len(selected) != 1 or selected[0] == staff["id"]:
            raise ValueError("Choose a different rune to infuse into the staff.")
        incoming = owned[selected[0]]
        components = list(
            dict.fromkeys(staff["components"] + incoming.get("components", [incoming["effect"]]))
        )
        if components == staff["components"]:
            raise ValueError("That staff already holds all of this rune’s effects.")
        result = deepcopy(staff)
        result["components"] = components
        consumed = [staff["id"], incoming["id"]]
        message = (
            "Infused "
            + staff["name"]
            + ". The source rune was consumed; its new powers are retained in the staff."
        )
    elif station == "disenchantry":
        if len(selected) != 1:
            raise ValueError("Choose one rune or staff to salvage.")
        if len(g["runes"]) <= 1:
            raise ValueError("Keep at least one rune in your collection.")
        consumed = selected
        message = "Salvaged " + owned[selected[0]]["name"] + ". Recovered 1 soul shard and 5 gold."
    elif station == "forge":
        message = "Tempered your weapon. Attack permanently increased by 2."
    else:
        message = "Wove an armor reinforcement. Defense permanently increased by 1."
    g["player"]["gold"] -= price["gold"]
    g["shards"] -= price["shards"]
    if station == "forge":
        g["player"]["atk"] += 2
    elif station == "loom":
        g["player"]["def"] += 1
    elif station == "disenchantry":
        g["shards"] += 1
        g["player"]["gold"] += 5
    g["runes"] = [r for r in g["runes"] if r["id"] not in consumed]
    g["equipped"] = [
        i for i in g["equipped"] if i not in consumed or (result and i == result["id"])
    ]
    if result:
        g["runes"].append(result)
    g["log"].append(message)
