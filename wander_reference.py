"""Shared wander thresholds and a player-readable reference of exploration rules."""

import data

from wander_roll import CHANCES, TOTAL, GATHER_MONSTER_CHANCE, ticket_table

WEATHER_RESELECT = 0.20
NIGHT_ELITE = 0.05


def percent(value):
    return f"{value*100:.4f}".rstrip("0").rstrip(".") + "%"


def probabilities(
    region, undiscovered=True, bounty_available=True, difficulty="normal"
):
    """Primary ticket ranges; exhausted ordinary structures become monsters."""
    outcomes = dict.fromkeys(
        (
            "monster",
            "bounty",
            "ingredient",
            "building_supply",
            "structure",
            "elemental_village",
            "special_event",
            "merchant",
            "companion",
            "peaceful",
        ),
        0,
    )
    for key, tickets in ticket_table(
        region, undiscovered, bounty_available, difficulty
    ):
        key = "special_event" if key.startswith("event:") else key
        outcomes[key] += tickets / TOTAL
    return outcomes


def encounter_probabilities(
    region, undiscovered=True, bounty_available=True, difficulty="normal"
):
    """Encounter chances after gathering; item finds overlap this second table."""
    odds = probabilities(region, undiscovered, bounty_available, difficulty)
    gathered = odds.pop("ingredient") + odds.pop("building_supply")
    structure_share = (
        1 - GATHER_MONSTER_CHANCE / 100
        if undiscovered and data.REGION_STRUCTURES.get(region)
        else 0
    )
    odds["structure"] += gathered * structure_share
    odds["monster"] += gathered * (1 - structure_share)
    return odds


def reference():
    stages = [
        dict(
            name="How wandering chances work",
            description="One weighted main roll chooses the starting outcome. An ingredient or building-supply find now keeps its reward and triggers one follow-up: 70% ordinary monster, 30% undiscovered ordinary structure. If all ordinary structures are known, that follow-up is always a monster. It cannot roll another ingredient, supply, merchant or quiet result. Rare bounties, hidden clans and the six event types already occupy their own ranges in this same roll. Item/species selection, combat, event choices and loot can have their own detail rolls. Weather and survival timers continue independently. Paid tracking replaces the random outcome; scheduled story scenes and companion perks remain explicit bonuses.",
            type="Read first",
        ),
        *[
            dict(
                name=mode.title() + " wander table",
                description=" · ".join(
                    name.replace("_", " ").title() + ": " + str(chance) + "%"
                    for name, chance in chances.items()
                )
                + ". Gathering gives one regional ingredient or one building supply, equally likely where ingredients exist, then adds a 70% monster / 30% ordinary structure encounter. Normal totals are 65% combat and 16% structures (including clans); Easy totals are 57% and 21%, while ordinary discoveries remain. Both have only 3% base peaceful wandering. Special events can also lead to fights.",
                type="One main roll",
            )
            for mode, chances in CHANCES.items()
        ],
        dict(
            name="Weather selection",
            description=f"{percent(WEATHER_RESELECT)} each wander to select uniformly from all {len(data.WEATHER_EFFECTS)} weather types, including the current weather. The actual chance of changing weather is {percent(WEATHER_RESELECT*(len(data.WEATHER_EFFECTS)-1)/len(data.WEATHER_EFFECTS))}. Weather is an environment update, not an extra loot encounter.",
            type="Environment",
        ),
        dict(
            name="Construction supplies",
            description="Half the gathering range gives one Timber, Stone or Iron fitting: 10% per Normal wander, 15% per Easy wander. If a region has no ingredients, its entire gathering range gives a building supply. After keeping this supply, roll 70% monster / 30% undiscovered ordinary structure. This does not start a second wander or advance survival/work timers again.",
            type="Gathering outcome",
        ),
        dict(
            name="Regional ingredients",
            description="Half the gathering range gives one native ingredient: 10% per Normal wander, 15% per Easy wander in regions with ingredients. After keeping the ingredient, roll 70% monster / 30% undiscovered ordinary structure. If no ordinary structures remain, fight a monster. You may also receive combat loot after winning that fight.",
            type="Gathering outcome",
        ),
        dict(
            name="Ordinary structures",
            description="Structures occupy 10% of Normal wanders or 12% on Easy. In a clan region, 1% of this structure range belongs to a hidden-clan visit. One undiscovered ordinary structure is otherwise selected uniformly. If all ordinary sites are known, their range becomes ordinary monsters. Gathering adds more ordinary discoveries through its 30% follow-up branch, and exhausted follow-up discoveries also become monsters. Sites remain revisitable through Structures.",
            type="Structure outcome",
        ),
        dict(
            name="Hidden elemental village",
            description="Clan visits occupy 1% of the structure range: 0.1% of a full Normal wander, 0.12% on Easy, in the four clan regions only. These are ranges in the same main roll, not another roll. Already discovered villages can be revisited this way or through Structures.",
            type="Rare structure subtype",
        ),
        dict(
            name="Bounty target",
            description="An unclaimed regional bounty occupies 2% of the monster range: 1.02% per full Normal wander, 0.72% on Easy. The rest is ordinary monsters. After claiming it, those tickets become ordinary monsters. With ordinary discoveries still available, combat totals including gathering follow-ups are 65% Normal / 57% Easy before special-event fights. Follow-up monsters and exhausted-structure replacements do not add bounty tickets.",
            type="Rare monster subtype",
        ),
        dict(
            name="Special wander event",
            description="The special-event ranges total 10% per Normal wander, 12% on Easy. The six catalogue events split that range by their weights within the same roll. A bandit event can lead to a fight and a wandering-merchant event can open a shop; these are event subtypes, not extra main outcomes.",
            type="Event outcome",
        ),
        dict(
            name="Day and night",
            description="Each ten-wander cycle contains seven day wanders followed by three night wanders. Ordinary night monsters gain 15% HP and attack, with a 5% elite detail roll. Night victories add 20% gold; elites add another ×2 gold and an extra loot roll. Night does not change the main outcome weights.",
            type="Journey cycle",
        ),
        dict(
            name="Monster level pools",
            description="Each ordinary species has four forms at player levels 1, 5, 10 and 15. HP, ATK and DEF grow within each stage and continue after level 15. Original level-1 names and existing evolved names at level 10 are retained. From level 10, regional mini-bosses occupy 25% of the usual two-species/two-mini-boss pool. Their stats also grow with level. Evolved direct attacks use scaled ATK; player gear does not set enemy strength. See Dictionary → Evolutions for each chain.",
            type="Combat details",
        ),
        dict(
            name="Tracked targets",
            description="A paid tracked target in the current region guarantees that target on your next Wander and replaces the weighted outcome entirely. Weather, hunger, recovery and work shifts still update. No random gathering or discovery is added.",
            type="Explicit tracking exception",
        ),
        dict(
            name="Survival on a wander",
            description="Starting at full hunger restores up to 3 HP before hunger falls by 5 (1 with Hunger Resist). Reaching zero hunger costs 10 HP and can end your run. Companions lose 5 hunger. Toxicity falls by 2. Menus do not trigger these updates.",
            type="Survival",
        ),
        dict(
            name="Exploration timers",
            description="Every 20 wander-count steps, village shops/farms and limited gathering sites enter their next supply cycle, and the world event advances. Scheduled Season Two anomalies can appear every tenth eligible wander until repair; these story scenes and existing companion scouting bonuses are separate from the random outcome, not extra discovery rolls.",
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
                description=f"{event['desc']} {event_details[event['id']]} {percent(event['weight']/total)} of special events; {percent(.10*event['weight']/total)} per complete Normal wander, {percent(.12*event['weight']/total)} on Easy. The event subtype is part of the same main roll.",
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
            description="Visit Ironpeak Mountains Quarry for dwarven bulk metal trades, with finite stock refreshing every 20 wanders. The Crimson Forge in Crimson Depths has three monster-held chambers. Sacrifice a compatible normal rune or matching-energy fusion into an ordinary core, then reclaim the forge to create named weapons whose charged core grants permanent abilities. These are chosen structure activities, not extra random encounter rolls.",
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
            difficulty_scenarios={
                mode: {
                    f"{int(undiscovered)}:{int(available)}": probabilities(
                        region, undiscovered, available, mode
                    )
                    for undiscovered in (False, True)
                    for available in (False, True)
                }
                for mode in CHANCES
            },
            encounter_scenarios={
                mode: {
                    f"{int(undiscovered)}:{int(available)}": encounter_probabilities(
                        region, undiscovered, available, mode
                    )
                    for undiscovered in (False, True)
                    for available in (False, True)
                }
                for mode in CHANCES
            },
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
                + ". Existing evolved / mini-boss names: "
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
                    " Rare hidden-clan tickets available."
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
        wandering=stages,
        weather=weather,
        world=world,
        loot=loot,
        regions=regions,
        difficulty_chances=CHANCES,
    )
