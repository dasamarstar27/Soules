"""Regional work-site yields shared by quarries, timber yards and mining."""

REGIONAL_METALS = {
    "Whispering Woods": "Iron",
    "Ashen Wastes": "Iron",
    "Crimson Depths": "Crimson Steel",
    "Frostbound Tundra": "Froststeel",
    "Crystal Spire": "Crystal Alloy",
    "Sunken Coast": "Iron",
    "Ironpeak Mountains": "Titanium",
    "Blight Swamp": "Iron",
    "Shadow Vale": "Shadow Iron",
    "Infernal Depths": "Infernium",
    "Celestial Expanse": "Celestium",
    "Riftlands": "Riftsteel",
    "Abyss of Souls": "Soulsteel",
    "Shattered Wastes": "Void Alloy",
    "The Dreamscape": "Chronosteel",
    "Creator's Realm": "Creator Alloy",
}
REGIONAL_WOODS = dict(
    zip(
        REGIONAL_METALS,
        (
            "Oak",
            "Ashwood",
            "Emberwood",
            "Frostwood",
            "Crystalwood",
            "Oak",
            "Ironbark",
            "Soulwood",
            "Shadowwood",
            "Dragonwood",
            "Sunwood",
            "Riftwood",
            "Soulwood",
            "Voidwood",
            "Dreamwood",
            "Worldwood",
        ),
    )
)


def yield_description(kind, region):
    if kind == "quarry":
        return "2 Stone + 1 " + REGIONAL_METALS[region]
    return "2 Timber + 1 " + REGIONAL_WOODS[region]


def gather(player, structure, region):
    """One finite trip per named site per cycle; construction and craft bags differ."""
    cycle = player.get("wander_count", 0) // 20
    record = player.setdefault("work_sites", {})
    key = region + "::" + structure["name"]
    if record.get(key) == cycle:
        return False
    quarry = structure["type"] == "quarry"
    material = "Stone" if quarry else "Timber"
    resource = (REGIONAL_METALS if quarry else REGIONAL_WOODS)[region]
    bag = player.setdefault("building_materials", {})
    bag[material] = bag.get(material, 0) + 2
    player.setdefault("metals" if quarry else "woods", []).append(resource)
    record[key] = cycle
    print(
        "Gathered "
        + yield_description(structure["type"], region)
        + ". Stone/Timber go into village building supplies; the metal/wood goes into crafting materials."
    )
    return True
