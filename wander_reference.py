"""Shared wander thresholds and a player-readable reference of exploration rules."""

import data

WEATHER_RESELECT = 0.20
BUILDING_SUPPLY = 0.25
STRUCTURE = 0.12
INGREDIENT = 0.08
ELEMENTAL_VILLAGE = 0.01
BOUNTY = 0.02
SPECIAL_EVENT = 0.08
NIGHT_ELITE = 0.05


def percent(value):
    return f"{value*100:.4f}".rstrip("0").rstrip(".") + "%"


def probabilities(region, undiscovered=True, bounty_available=True):
    """Exclusive outcomes, assuming a living player without a tracking assignment."""
    remaining = 1.0
    outcomes = {}
    for key, chance in [
        (
            "structure",
            STRUCTURE if undiscovered and data.REGION_STRUCTURES.get(region) else 0,
        ),
        (
            "elemental_village",
            ELEMENTAL_VILLAGE if region in data.ELEMENTAL_VILLAGES else 0,
        ),
        (
            "bounty",
            BOUNTY if bounty_available and region in data.BOUNTY_MONSTERS else 0,
        ),
        ("special_event", SPECIAL_EVENT),
    ]:
        outcomes[key] = remaining * chance
        remaining *= 1 - chance
    for key, chance in [
        ("companion", 0.01),
        ("merchant", 0.08),
        ("peaceful", 0.11),
        ("monster", 0.80),
    ]:
        outcomes[key] = remaining * chance
    return outcomes


def reference():
    stages = [
        dict(
            name="How wandering chances work",
            description="Checks happen in order. Structure discovery, a hidden-village visit, a bounty or a special event can end the wander before the ordinary encounter roll. Ingredient and building-supply finds can accompany another outcome. The next-wander estimates assume you survive hunger and have no pending tracked target.",
            type="Read first",
        ),
        dict(
            name="Weather selection",
            description=f"{percent(WEATHER_RESELECT)} each wander to select uniformly from all {len(data.WEATHER_EFFECTS)} weather types, including the current weather. The actual chance of changing weather is {percent(WEATHER_RESELECT*(len(data.WEATHER_EFFECTS)-1)/len(data.WEATHER_EFFECTS))}.",
            type="Before encounters",
        ),
        dict(
            name="Construction supplies",
            description=f"{percent(BUILDING_SUPPLY)} each wander to gain one Timber, Stone or Iron fitting, equally likely. This can happen alongside discoveries and encounters.",
            type="Independent find",
        ),
        dict(
            name="Ordinary structures",
            description=f"{percent(STRUCTURE)} when there are undiscovered ordinary structures in your region. One remaining structure is chosen uniformly. A discovery ends the encounter checks; the new place becomes revisitable through Structures.",
            type="First encounter check",
        ),
        dict(
            name="Regional ingredients",
            description=f"{percent(INGREDIENT)} if this check is reached and the region has ingredients. One native ingredient is selected uniformly. This does not end the wander. A structure discovery or tracked fight bypasses this check.",
            type="Find alongside an encounter",
        ),
        dict(
            name="Hidden elemental village",
            description=f"{percent(ELEMENTAL_VILLAGE)} if reached in one of the four clan regions. This can also revisit an already known clan. The chance is lower per complete wander when earlier checks can end it; the dictionary does not discover the village for you.",
            type="Second encounter check",
        ),
        dict(
            name="Bounty target",
            description=f"{percent(BOUNTY)} if reached, the region has a bounty and you have not claimed it. A bounty encounter ends the remaining checks.",
            type="Third encounter check",
        ),
        dict(
            name="Special wander event",
            description=f"{percent(SPECIAL_EVENT)} if reached. The six events below use their catalogue weights. Night does not increase this event roll.",
            type="Fourth encounter check",
        ),
        dict(
            name="Ordinary encounter roll",
            description="If earlier checks allow it: companion opportunity 1% (roll 1), ordinary merchant 8% (2–9), peaceful wandering 11% (10–20), monster path 80% (21–100). A companion requires an unrecruited eligible species; an empty monster pool produces no fight.",
            type="Last encounter check",
        ),
        dict(
            name="Day and night",
            description="Each ten-wander cycle contains seven day wanders followed by three night wanders. Ordinary night monsters gain 15% HP and attack, with a 5% elite roll after the monster is selected. Night victories add 20% gold; elites add another ×2 gold and an extra loot roll. Dark-region night fights also add corruption.",
            type="Journey cycle",
        ),
        dict(
            name="Monster level pools",
            description="Below level 10 the ordinary monster path uses the regional normal pool. From level 10 it selects uniformly from evolved monsters and mini-bosses, falling back to normal monsters if that pool is empty.",
            type="Combat encounters",
        ),
        dict(
            name="Tracked targets",
            description="A paid tracked target in the current region guarantees that target on your next Wander and replaces all structure/ingredient/clan/bounty/event/ordinary encounter checks. Weather, supply, hunger and journey updates still happen first.",
            type="Tracking exception",
        ),
        dict(
            name="Survival on a wander",
            description="Starting at full hunger restores up to 3 HP before hunger falls by 5 (1 with Hunger Resist). Reaching zero hunger costs 10 HP and can end your run. Companions lose 5 hunger. Toxicity falls by 2. Menus do not trigger these updates.",
            type="Survival",
        ),
        dict(
            name="Exploration timers",
            description="Every 20 wander-count steps, village shops/farms and limited gathering sites enter their next supply cycle, and the world event advances in catalogue order. Source anomalies appear on every tenth eligible Season Two wander until the stabiliser repair; they can give one ordinary Source fragment and your wander continues.",
            type="Supplies and story",
        ),
    ]
    event_details = {
        "wandering_merchant": "A separate merchant with up to three regional wares and visible prices; you can decline.",
        "mysterious_altar": "Choose 30 HP, 100 souls or one skill point.",
        "lucky_cache": "Find 50–200 souls, then a 40% chance of an extra loot roll.",
        "cursed_chest": "Decline safely, or open it: equal 1/3 chances of a 20–50 HP trap (keeps at least 1 HP), two loot rolls, or an empty chest.",
        "bandit_ambush": "Fight a level-scaled Road Bandit; surviving the encounter grants 40–120 additional souls.",
        "wounded_traveller": "Choose whether to help. Helping costs 20 souls and restores up to 15 HP plus one Luck.",
    }
    total = sum(event["weight"] for event in data.WANDER_EVENTS)
    for event in data.WANDER_EVENTS:
        stages.append(
            dict(
                name=event["title"],
                description=f"{event['desc']} {event_details[event['id']]} {percent(event['weight']/total)} of special events; {percent(SPECIAL_EVENT*event['weight']/total)} once the special-event check is reached, before earlier-check reductions.",
                type="Weighted special event",
            )
        )
    stages.append(
        dict(
            name="Clan raids and Whispering Woods defence",
            description="Discovered elemental villages offer a chosen raid defence with worker assignments. Elian offers a Season One main quest to brace Whispering Woods and repel three invasion waves; discovered clans may send volunteers. These are selected missions, not additional random Wander rolls.",
            type="Defence missions",
        )
    )
    stages.append(
        dict(
            name="Ironpeak dwarves and Crimson Forge",
            description="Visit Ironpeak Mountains Quarry for dwarven bulk metal trades, with finite stock refreshing every 20 wanders. The Crimson Forge in Crimson Depths has three monster-held chambers. Sacrifice a normal rune into an ordinary core, then reclaim the forge to create named weapons whose charged core grants permanent abilities. These are chosen structure activities, not extra random encounter rolls.",
            type="Regional activities",
        )
    )
    stages.append(
        dict(
            name="Regional specialist sellers",
            description="Village option 25 opens local specialist stalls: Whispering Woods herbs/woods, Tundra cloth, Crystal Spire runes, Sunken Coast food, Infernal Depths hides, Riftlands ordinary cores. Only Ironpeak’s quarry traders are dwarves. Riftlands has eight of each ordinary core per shipment and a 25% chance of a single charged core. Stocks refresh every 20 wanders; reopening never rerolls the shipment.",
            type="Regional shops",
        )
    )
    regions = {}
    for region in data.REGIONS + [data.SECRET_REGION]:
        bounty = data.BOUNTY_MONSTERS.get(region)
        regions[region] = dict(
            structures=[x["name"] for x in data.REGION_STRUCTURES.get(region, [])],
            bounty=bounty["name"] if bounty else None,
            scenarios={
                f"{int(undiscovered)}:{int(available)}": probabilities(
                    region, undiscovered, available
                )
                for undiscovered in (False, True)
                for available in (False, True)
            },
        )
        normals = [x["name"] for x in data.NORMAL_MONSTERS.get(region, [])]
        advanced = [
            x["name"]
            for x in data.EVOLVED_MONSTERS.get(region, [])
            + data.MINI_BOSSES.get(region, [])
        ]
        stages.append(
            dict(
                name=region,
                description="Normal monsters: "
                + (", ".join(normals) or "none")
                + ". Level 10+ pool: "
                + (", ".join(advanced) or "normal pool fallback")
                + ". Ingredients: "
                + (", ".join(data.REGION_INGREDIENTS.get(region, [])) or "none")
                + ". "
                + (
                    "Bounty: " + bounty["name"] + "."
                    if bounty
                    else "No regional bounty."
                )
                + (
                    " Hidden-clan check available."
                    if region in data.ELEMENTAL_VILLAGES
                    else ""
                ),
                type="Regional encounters",
            )
        )
    weather = [
        dict(
            name=name,
            description=f"{info['icon']} {info['desc']} Weapon damage in original combat: ×{info['player_dmg_mod']:g}. {percent(WEATHER_RESELECT/len(data.WEATHER_EFFECTS))} per wander to select this weather during the reselection roll; selecting the current weather leaves it unchanged.",
            type="Weather",
        )
        for name, info in data.WEATHER_EFFECTS.items()
    ]
    world = [
        dict(
            name=entry["name"],
            description=f"{entry['icon']} {entry['desc']} Original combat modifiers: enemy HP ×{entry['enemy_hp_mod']:g}, enemy attack ×{entry['enemy_atk_mod']:g}, ordinary victory gold ×{entry['gold_mod']:g}, XP ×{entry['xp_mod']:g}. Advances to the next event every 20 wander-count steps; this is a cycle, not a random drop.",
            type="World event",
        )
        for entry in data.WORLD_EVENTS
    ]
    loot = [
        dict(
            name="Loot-roll chances",
            description="Each loot roll: regional/common trinket 60%, armour 5%, weapon 10%, scroll 15%, rune 7%, staff 3%. This is per loot roll, not per wander. Gear pools depend on level; runes/staffs prefer the current region. Sea Pearls are native to Sunken Coast.",
            type="Loot",
        ),
        dict(
            name="Divine Luck loot rolls",
            description="While Divine Luck is active its +10 shifts the roll: trinket 50%, armour 5%, weapon 10%, scroll 15%, rune 7%, staff 13%. Other Luck points do not currently change these category thresholds.",
            type="Loot modifier",
        ),
        dict(
            name="Ancient ruins",
            description="A permitted search rolls 35% protected broken-core fragment, 25% protected tome, 40% nothing. One search per site per 20-wander cycle; each find type is unique to that site. Rolling an already recovered type yields no duplicate. Finds cannot be sold or salvaged.",
            type="Structure activity",
        ),
        dict(
            name="Chosen field activities",
            description="Fishing, mining, surveying, camps, escorts, crossings and peaceful wildlife activities are selected in Adventures → Exploration. They are separate from the automatic Wander roll. Their costs and site limits are printed before use.",
            type="Other exploration",
        ),
    ]
    return dict(
        wandering=stages, weather=weather, world=world, loot=loot, regions=regions
    )
