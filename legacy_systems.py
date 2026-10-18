"""Playable replacements for the original catalogue-only optional menus."""

from copy import deepcopy
import data
from expansion_state import state, pay, choose, count


def systems(player):
    return state(player).setdefault("systems", {})


def menu(game, kind):
    p = game.player
    s = systems(p)
    if kind == "daily":
        from daily_rewards import menu as daily

        daily(game)
    elif kind == "cosmetics":
        rows = [
            (category, key, value)
            for category, items in data.COSMETICS_SHOP.items()
            for key, value in items.items()
        ]
        owned = s.setdefault("cosmetics", [])
        currency = p.setdefault("cosmetics", {}).get("currency", 0)
        index = choose(
            f"COSMETICS · {currency} CURRENCY",
            [
                f'{x[2]["name"]} · {"owned" if x[0]+":"+x[1] in owned else x[2]["price"]}'
                for x in rows
            ],
        )
        if index is None:
            return
        category, key, item = rows[index]
        token = category + ":" + key
        if token not in owned:
            if currency < item["price"]:
                print("Not enough cosmetic currency.")
                return
            p["cosmetics"]["currency"] -= item["price"]
            owned.append(token)
        s.setdefault("equipped_cosmetics", {})[category] = key
        if category == "titles":
            p["title"] = item["name"]
        print("Equipped " + item["name"] + ".")
    elif kind == "guild":
        from community_store import guilds, create_guild, join_guild, guild_level

        if not p.get("guild"):
            option = choose(
                "GUILDS · SHARED ON THIS HOSTED INSTANCE",
                ["Create a guild (500 souls)", "Join an existing guild"],
            )
            if option == 0:
                print(create_guild(p, input("Guild name (blank cancels) > "))[1])
            elif option == 1:
                rows = guilds()
                index = choose(
                    "OPEN GUILDS",
                    [x["name"] + " · Level " + str(x["level"]) for x in rows],
                )
                if index is not None:
                    print(join_guild(p, rows[index]["id"])[1])
            return
        level = guild_level(p)
        print(f"Guild {p['guild']} · Level {level}")
        index = choose(
            "GUILD",
            [
                "Donate 100 souls: improve shared guild supplies (max level 5)",
                "Claim guild expedition supplies once per 20 wanders",
            ],
        )
        if index == 0:
            if s.get("shared_guild"):
                print("Guild level: " + str(guild_level(p, donate=True)))
            elif level < 5 and pay(p, 100):
                s["guild_level"] = level + 1
        elif index == 1:
            cycle = p.get("wander_count", 0) // 20
            if s.get("guild_supply_cycle") == cycle:
                print("Already supplied this cycle.")
                return
            s["guild_supply_cycle"] = cycle
            p.setdefault("building_materials", {})["Timber"] = (
                p.get("building_materials", {}).get("Timber", 0) + level
            )
            print("Guild Timber delivered.")
    elif kind == "events":
        from daily_rewards import today

        names = list(data.SEASONAL_EVENTS)
        active = names[(today().toordinal() // 30) % len(names)]
        event = data.SEASONAL_EVENTS[active]
        print("Current 30-day festival: " + event["name"])
        cycle = str(today().toordinal() // 30)
        if s.get("festival_claims", {}).get(cycle):
            print("Festival champion reward already collected.")
            return
        enemies = [
            dict(
                name=name,
                hp=80 + p["level"] * 8,
                atk=8 + p["level"],
                **{"def": 3},
                gold=40,
                xp=35,
            )
            for name in event["unique_bosses"]
        ]
        from expansion_combat import encounter

        if encounter(game, enemies):
            s.setdefault("festival_claims", {})[cycle] = True
            p.setdefault("cosmetics", {})["currency"] = (
                p.get("cosmetics", {}).get("currency", 0) + 80
            )
            s.setdefault("festival_materials", []).extend(event["unique_materials"])
            s.setdefault("cosmetics", []).extend(
                "character_skins:" + x for x in event["exclusive_cosmetics"]
            )
            print(
                "Festival won: materials, an event appearance and 80 cosmetic currency."
            )
    elif kind == "modes":
        modes = ["speedrun", "ironman", "budget_run", "solo_challenge"]
        index = choose("RUN MODE", modes + ["End current mode (forfeit its record)"])
        if index is None:
            return
        if index == 4:
            s.pop("mode", None)
            return
        if s.get("mode"):
            print("End your current mode first.")
            return
        from datetime import datetime, timezone

        s["mode"] = dict(
            id=modes[index],
            started=datetime.now(timezone.utc).isoformat(),
            start_level=p["level"],
            start_wander=p.get("wander_count", 0),
        )
        print(
            "Mode active: "
            + modes[index]
            + ". Budget blocks purchases; Solo disables companion combat support; Ironman already ends on death. Speedrun records elapsed time when you reach level 10."
        )
    elif kind == "ngplus":
        if not p.get("source_story", {}).get("season_one_complete"):
            print("Finish the original Dreamscape campaign before beginning New Game+.")
            return
        if (
            input(
                "Start a fresh harder character? All carried supplies reset; your chronicle is kept. (yes/no) > "
            )
            .strip()
            .lower()
            != "yes"
        ):
            return
        from original_worker import initial_player
        from journal_addons import character_sheet

        history = state(p).get("chronicles", []) + [character_sheet(p)]
        fresh = initial_player({"name": p["name"], "cls": p.get("class_id", "warrior")})
        runs = s.get("ngplus", 0) + 1
        p.clear()
        p.update(fresh)
        state(p)["chronicles"] = history[-10:]
        systems(p)["ngplus"] = runs
        import original_ui as ui

        ui.init_ui(p)
        game.visit_village({"name": "Old Village"}, data.REGIONS[0])
    elif kind == "battle_pass":
        xp = s.get("battle_xp", 0)
        claimed = s.setdefault("pass_claims", [])
        rows = list(data.BATTLE_PASS_TIERS.items())
        index = choose(
            f"ADVENTURE PASS · {xp} XP",
            [
                key
                + " · "
                + str(value["required_xp"])
                + " XP · "
                + ("claimed" if key in claimed else str(value["rewards"]))
                for key, value in rows
            ],
        )
        if index is None:
            return
        key, entry = rows[index]
        if key in claimed or xp < entry["required_xp"]:
            print("Not eligible or already claimed.")
            return
        reward = entry["rewards"]
        p["gold"] += reward.get("gold", 0)
        p.setdefault("cosmetics", {})["currency"] = p.get("cosmetics", {}).get(
            "currency", 0
        ) + reward.get("cosmetic_currency", 0)
        for material, amount in reward.get("materials", {}).items():
            s.setdefault("pass_materials", {})[material] = (
                s.setdefault("pass_materials", {}).get(material, 0) + amount
            )
        s["prestige_tokens"] = s.get("prestige_tokens", 0) + reward.get(
            "prestige_token", 0
        )
        if reward.get("legendary_skin"):
            s.setdefault("cosmetics", []).append("character_skins:legendary_hero")
        if reward.get("exclusive_title"):
            p["title"] = "Worldkeeper"
        claimed.append(key)
        print("Reward claimed.")
    elif kind == "rituals":
        rows = [
            ("Blessing of Strength", {"Iron fittings": 2}, [], {"atk": 3}, 5),
            ("Shield of Resilience", {"Timber": 2}, [], {"def": 3}, 5),
            ("Swiftness Ritual", {}, ["Dew Blossom"], {"spd": 2}, 5),
            (
                "Grand Ceremony",
                {"Iron fittings": 4},
                ["Dew Blossom", "Thorn Petal"],
                {"atk": 5, "def": 5, "spd": 3},
                10,
            ),
        ]
        index = choose(
            "RITUALS · ONE ACTIVE AT A TIME",
            [
                f"{name}: 30 souls, {materials}, {ingredients}; {bonus}, {duration} encounters"
                for name, materials, ingredients, bonus, duration in rows
            ],
        )
        if index is None:
            return
        name, materials, ingredients, bonus, duration = rows[index]
        if pay(p, 30, materials, ingredients):
            s["ritual"] = dict(name=name, bonus=bonus, remaining=duration)
            print(
                "Ritual active: "
                + name
                + ". Combat encounters consume duration; menus do not."
            )
        else:
            print("Bring the displayed supplies and souls.")
    elif kind == "arena":
        from community_store import register, ghosts

        index = choose(
            "ARENA",
            [
                "Fight an NPC opponent (nonlethal)",
                "Publish/update my ghost on this hosted instance",
                "Challenge a shared ghost",
                "View arena record",
            ],
        )
        if index == 1:
            register(p)
            s["ghost_published"] = True
            print(
                "Your public character name and combat statistics were registered on this instance. No save file or password is published."
            )
            return
        if index == 3:
            print("Arena points: " + str(p.get("arena_points", 0)))
            return
        enemy = dict(
            name="Arena Duelist",
            hp=55 + p["level"] * 6,
            atk=6 + p["level"],
            **{"def": 3},
            intelligent=True,
        )
        if index == 2:
            rows = ghosts(p)
            selected = choose(
                "SHARED ARENA GHOSTS",
                [x["name"] + " · level " + str(x["level"]) for x in rows],
            )
            if selected is None:
                return
            row = rows[selected]
            enemy = dict(
                name=row["name"] + " · ghost",
                hp=row["hp"],
                atk=row["atk"],
                **{"def": row["defence"]},
                intelligent=True,
            )
        elif index != 0:
            return
        cycle = p.get("wander_count", 0) // 20
        from expansion_combat import encounter

        if encounter(game, [enemy], True) and s.get("arena_cycle") != cycle:
            s["arena_cycle"] = cycle
            p["arena_points"] = p.get("arena_points", 0) + 20
            if s.get("ghost_published"):
                register(p)
            print("Arena victory: +20 points. One ranked reward per exploration cycle.")
    elif kind == "market":
        from community_store import publish, offers, buy, settle

        print(
            "Shared offers exist only on this hosted instance; a separate offline computer has a separate market. Posting removes the item into escrow."
        )
        c = choose(
            "TRADING POST",
            [
                "Post a spare weapon",
                "Browse and buy offers",
                "Collect sale proceeds",
                "Cancel my active offer",
                "Post spare armour",
                "Post a spare staff",
            ],
        )
        if c in (0, 4, 5):
            bag = {0: "weapons", 4: "armours", 5: "staffs"}[c]
            pool = p.get(bag, [])
            index = choose("SPARE EQUIPMENT", [x["name"] for x in pool])
            if index is None:
                return
            try:
                price = int(input("Asking price (1–100000) > "))
            except ValueError:
                return
            print(publish(p, bag, index, price)[1])
        elif c == 1:
            rows = offers()
            index = choose(
                "MARKET",
                [json_item(x) + " · " + str(x["price"]) + " souls" for x in rows],
            )
            if index is not None:
                print(buy(p, rows[index]["id"])[1])
        elif c == 2:
            print("Collected " + str(settle(p)[0]) + " souls.")
        elif c == 3:
            rows = [x for x in offers() if x["owner"] == state(p)["character_id"]]
            index = choose("CANCEL OFFER", [json_item(x) for x in rows])
            if index is not None:
                print(
                    "Item returned."
                    if settle(p, cancel=rows[index]["id"])[1]
                    else "Offer already sold or unavailable."
                )
    elif kind == "town":
        buildings = s.setdefault("town", {})
        rows = list(data.TOWN_STRUCTURES.items())
        index = choose(
            "TOWN BUILDINGS",
            [
                value["name"]
                + " · Level "
                + str(buildings.get(key, 0))
                + "/3 · next "
                + str(value["cost"] * (buildings.get(key, 0) + 1))
                + " souls"
                for key, value in rows
            ]
            + ["Collect this cycle’s town income"],
        )
        if index is None:
            return
        if index == len(rows):
            cycle = p.get("wander_count", 0) // 20
            if s.get("town_cycle") == cycle:
                print("Already collected this cycle.")
                return
            s["town_cycle"] = cycle
            income = buildings.get("tavern", 0) * 40
            p["gold"] += income
            p["mana"] = p.get("mana", 0) + buildings.get("shrine", 0) * 5
            print(f"Collected {income} souls and shrine mana.")
            return
        key, item = rows[index]
        level = buildings.get(key, 0)
        if level < 3 and pay(p, item["cost"] * (level + 1)):
            buildings[key] = level + 1
            print(
                "Building upgraded. Market levels discount commissions; Tower levels add adventure pass XP."
            )
    elif kind == "factions":
        if p.get("faction"):
            faction_services(game)
            return
        rows = list(data.FACTIONS.items())
        index = choose(
            "FACTIONS", [x[1]["name"] + " · " + str(x[1]["bonuses"]) for x in rows]
        )
        if index is None:
            return
        key, entry = rows[index]
        p["faction"] = key
        for stat, amount in entry["bonuses"].items():
            if stat == "atk":
                p["atk"] += amount
            elif stat == "def":
                p["def"] += amount
            elif stat == "spd":
                p["speed"] += amount
            elif stat == "hp":
                p["max_hp"] += amount
                p["hp"] += amount
        print(
            "Faction joined. Combat stats applied once; gathering/crafting/economy bonuses apply through activity hooks."
        )
    elif kind == "treasure":
        maps = s.setdefault("treasure_maps", [])
        c = choose(
            "TREASURE HUNTING",
            ["Buy an ordinary map (40 souls)", "Follow a carried map"],
        )
        if c == 0:
            if len(maps) >= 5:
                print("Carry at most five maps.")
                return
            destinations = [x for x in data.REGIONS if x in p["unlocked_regions"]]
            if pay(p, 40):
                maps.append(
                    dict(
                        region=game.random.choice(destinations),
                        accepted=p.get("wander_count", 0),
                        reward=90,
                    )
                )
                print("Map acquired: " + maps[-1]["region"])
        elif c == 1:
            index = choose("MAPS", [x["region"] for x in maps])
            if index is None:
                return
            item = maps[index]
            if (
                p["region"] != item["region"]
                or p.get("wander_count", 0) <= item["accepted"]
            ):
                print("Reach its region and scout at least once.")
                return
            claims = s.setdefault("treasure_claims", {})
            cycle = p.get("wander_count", 0) // 20
            if claims.get(p["region"]) == cycle:
                print("This region’s treasure grounds need the next 20-wander cycle.")
                return
            claims[p["region"]] = cycle
            p["gold"] += item["reward"]
            p["inventory"].append(
                deepcopy(game.random.choice(game.regional_loot(p["region"])))
            )
            maps.pop(index)
            print("Treasure recovered: 90 souls and a native trinket.")
    elif kind == "mounts":
        owned = p.setdefault("mounts", [])
        rows = list(data.MOUNTS.items())
        index = choose(
            "MOUNTS",
            [
                v["name"]
                + " · "
                + ("owned" if k in owned else str(v["cost"]) + " souls")
                for k, v in rows
            ],
        )
        if index is None:
            return
        key, item = rows[index]
        if key not in owned:
            if not pay(p, item["cost"]):
                print("Not enough souls.")
                return
            owned.append(key)
        s["mount"] = key
        print(
            "Mounted "
            + item["name"]
            + ". Travel restores 2 hunger and escort completion earns a 10-soul transport bonus."
        )
    elif kind == "recipes":
        from food_addons import food_state

        print("Known tested brews: " + str(food_state(p).get("discovered", [])))
        print(
            "Potion Dictionary lists all ingredient recipes. Textile Patterns and specialties add equipment recipes."
        )
        choices = [("crafting_shard", "Iron fittings"), ("essence_dust", "Dew Blossom")]
        index = choose(
            "REWARD SUPPLY EXCHANGE",
            [
                first + " → " + second + " (one daily/pass supply)"
                for first, second in choices
            ],
        )
        if index is None:
            return
        resource, result = choices[index]
        ledgers = [
            state(p).get("daily", {}).get("materials", {}),
            s.get("pass_materials", {}),
        ]
        ledger = next((bag for bag in ledgers if bag.get(resource, 0) > 0), None)
        if ledger is None:
            print("No unspent reward supplies of this kind.")
            return
        ledger[resource] -= 1
        if resource == "crafting_shard":
            p.setdefault("building_materials", {})["Iron fittings"] = (
                p.get("building_materials", {}).get("Iron fittings", 0) + 1
            )
        else:
            p.setdefault("ingredients", []).append(result)
        print("Converted one " + resource + " into " + result + ".")


def json_item(row):
    import json

    return json.loads(row["item"])["name"]


def on_wander(player):
    s = systems(player)
    s["battle_xp"] = s.get("battle_xp", 0) + 5 + s.get("town", {}).get("tower", 0)
    mode = s.get("mode", {})
    if (
        mode.get("id") == "speedrun"
        and player["level"] >= 10
        and not mode.get("completed")
    ):
        from datetime import datetime, timezone

        mode["seconds"] = (
            datetime.now(timezone.utc) - datetime.fromisoformat(mode["started"])
        ).total_seconds()
        mode["completed"] = True
        print(
            "Speedrun reached level 10 in "
            + str(round(mode["seconds"], 1))
            + " seconds."
        )


def ritual_bonus(player, stat):
    ritual = systems(player).get("ritual", {}) if player.get("expansion") else {}
    return ritual.get("bonus", {}).get(stat, 0) if ritual.get("remaining", 0) > 0 else 0


def faction_services(game):
    p = game.player
    s = systems(p)
    key = p["faction"]
    progress = s.setdefault("faction_progress", {})
    index = choose(
        data.FACTIONS[key]["name"]
        + " · FACTION HALL · "
        + str(progress.get("reputation", 0))
        + " reputation",
        [
            "Accept/complete an expedition contract: scout three times, 45 souls and 1 reputation",
            "Buy a faction healing draught: 25 souls, reputation 1 required",
            "Buy faction equipment: 120 souls, reputation 3 required",
        ],
    )
    cycle = p.get("wander_count", 0) // 20
    if index == 0:
        if progress.get("contract_cycle") == cycle:
            print("Contract already completed this cycle.")
            return
        if "started" not in progress:
            progress["started"] = p.get("wander_count", 0)
            print("Scout three times, then return to the faction hall.")
            return
        if p.get("wander_count", 0) - progress["started"] < 3:
            print("Scout three times first.")
            return
        progress.pop("started")
        progress["contract_cycle"] = cycle
        progress["reputation"] = progress.get("reputation", 0) + 1
        p["gold"] += 45
        print("Contract complete: 45 souls, 1 faction reputation.")
    elif index == 1:
        if progress.get("reputation", 0) < 1:
            print("Earn faction reputation first.")
            return
        if progress.get("potion_cycle") == cycle:
            print("Draught stock returns next exploration cycle.")
            return
        if pay(p, 25):
            p["potions"].append("Forest Salve")
            progress["potion_cycle"] = cycle
            print("Forest Salve received.")
    elif index == 2:
        if progress.get("reputation", 0) < 3:
            print("Earn 3 faction reputation first.")
            return
        if progress.get("equipment_cycle") == cycle:
            print("Equipment stock returns next exploration cycle.")
            return
        if pay(p, 120):
            p["weapons"].append(
                dict(
                    name=data.FACTIONS[key]["name"] + " Service Blade",
                    atk=16 + progress["reputation"],
                    value=50,
                    provenance=p["region"],
                    maker=data.FACTIONS[key]["name"],
                )
            )
            progress["equipment_cycle"] = cycle
            print("Faction blade received.")
