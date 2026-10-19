"""Finite construction resource sites and peaceful regional watch posts."""

import original_ui as ui
from resource_sites import gather, yield_description


def visit(game, struct, region):
    previous = ui.location
    ui.location = dict(name=struct["name"], kind=struct["type"], region=region)
    try:
        print("\n--- " + struct["name"].upper() + " ---")
        if struct["type"] == "watchpost":
            print(
                "A watchkeeper marks safe settlements on a worn map. The monsters were once peaceful; now the roads need guarding."
            )
            print("1. Ask for a village direction\n2. Read local side quests\n0. Leave")
            choice = input("Watch post > ").strip()
            if choice == "1":
                candidates = [
                    x
                    for x in game.REGION_STRUCTURES.get(region, [])
                    if x["type"] == "village"
                ]
                found = game.player.setdefault("discovered_structures", {}).setdefault(
                    region, []
                )
                unknown = [x for x in candidates if x["name"] not in found]
                if unknown:
                    village = game.random.choice(unknown)
                    found.append(village["name"])
                    print(
                        "The keeper shows you the route to "
                        + village["name"]
                        + ". It is now in your Village Directory."
                    )
                else:
                    print(
                        "You already know every ordinary village here. Hidden elemental settlements are not marked on this map."
                    )
            elif choice == "2":
                game.quest_board(region)
            return
        if struct["type"] == "quarry" and region == "Ironpeak Mountains":
            from regional_forges import dwarven_quarry

            dwarven_quarry(game, struct)
            return
        rewards = yield_description(struct["type"], region)
        print(
            f"1. Work for {rewards}\n0. Leave\nOne gathering trip per site each 20-wander cycle. No charge; supplies are finite."
        )
        if (
            input(
                "Choose 1 to gather building and crafting supplies, or 0 to leave > "
            ).strip()
            != "1"
        ):
            return
        if not gather(game.player, struct, region):
            print("This site needs time to replenish. Return next 20-wander cycle.")
    finally:
        ui.location = previous
