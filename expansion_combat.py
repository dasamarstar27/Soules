"""Tactical addon encounters: explicit targets, intent, hazards and safe practice."""

from copy import deepcopy
import data
import original_ui as ui
from expansion_state import state, mark, pay, count, choose


def encounter(game, enemies, practice_mode=False, terrain=None, rules=None):
    p = game.player
    rules = rules or []
    from difficulty import easy_enemy

    enemies = [easy_enemy(p, enemy) for enemy in deepcopy(enemies)]
    for e in enemies:
        e["addon_encounter"] = True
        e.setdefault("max_hp", e.get("hp", 40))
        e.setdefault("status", {})
        e.setdefault("active_buffs", {})
        e.setdefault("def", 0)
        e.setdefault("atk", 5)
    saved = {
        k: deepcopy(p.get(k))
        for k in (
            "hp",
            "mana",
            "status",
            "rune_status",
            "rune_abilities",
            "active_buffs",
            "def",
            "atk",
            "_rune_previous",
            "potion_atk_boost",
            "potion_atk_turns",
            "potion_def_boost",
            "potion_def_turns",
        )
    }
    records = []
    turn = 0
    target = 0
    won = False
    companion_move_used = False
    for pet in p.get("companions", []):
        pet.pop("helped_this_battle", None)
    prepared = state(p)["activities"].pop("prepared", False)
    try:
        while p["hp"] > 0 and any(e["hp"] > 0 for e in enemies):
            alive = [i for i, e in enumerate(enemies) if e["hp"] > 0]
            if target not in alive:
                target = alive[0]
            e = enemies[target]
            if ui.get_ui():
                ui.get_ui().set_enemy(e)
            print(
                "\n--- TACTICAL ENCOUNTER"
                + (" · NONLETHAL PRACTICE" if practice_mode else "")
                + " ---"
            )
            for i, foe in enumerate(enemies, 1):
                intention = (
                    "charging a heavy strike"
                    if (turn + 1) % 3 == 0
                    else "ordinary attack"
                )
                studied = p.get("kill_counts", {}).get(foe["name"], 0) >= 3 or state(p)[
                    "magic"
                ].get("intent_training")
                print(
                    f"{i}. {foe['name']} · HP {foe['hp']}/{foe['max_hp']}"
                    + (" · next: " + intention if studied else "")
                )
            print(
                f"You: {p['hp']} HP, {p.get('mana',0)} mana. Target {target+1}. Terrain: {terrain or 'stable'}. Rules: {rules}"
            )
            print(
                "1. Attack\n2. Change target\n3. Loose rune\n4. Elemental art\n5. Potion\n6. Companion move\n7. Interrupt (3 mana; stops a charged strike)\n8. Counterspell (5 mana; training required)\n9. Offer mercy (intelligent enemy below 25% HP)\n10. Withdraw\n0. Withdraw"
            )
            c = input("Tactical action > ").strip()
            if c in ("0", "10"):
                return False
            if c == "2":
                index = choose("TARGET", [foe["name"] for foe in enemies])
                if index is not None and enemies[index]["hp"] > 0:
                    target = index
                continue
            interrupted = False
            counter = False
            ticked_player = False
            stunned = p.setdefault("active_buffs", {}).pop("stun", False)
            game.process_buffs()
            if stunned:
                c = "disabled"
            if c in ("3", "4") and p.get("active_buffs", {}).get("silenced"):
                print("Silence prevents magic. Choose another action.")
                continue
            if p.get("rune_status"):
                from original_magic import turn as tick_magic

                ticked_player = True
                if not tick_magic(p, e):
                    print("Your active effects prevent this action.")
                    c = "disabled"
            if c == "1":
                ritual = state(p).get("systems", {}).get("ritual", {})
                from original_magic import strike, damage as adjust_damage

                damage = max(1, game.calculate_damage(p, e, "weapon"))
                dealt = strike(p, e, adjust_damage(p, e, damage))
                drain = (
                    state(p)
                    .get("systems", {})
                    .get("equipment_collection_bonus", {})
                    .get("lifesteal", 0)
                )
                if drain:
                    p["hp"] = min(p["max_hp"], p["hp"] + int(dealt * drain))
                bound = p.get("weapon", {}).get("rune") if p.get("weapon") else None
                if bound:
                    game.apply_rune_effect(bound, p, e)
                game._apply_charged_weapon_effect(e)
                game.apply_companion_support(e)
            elif c == "3":
                if "no runes" in rules:
                    print("This contract forbids loose runes.")
                    continue
                if not game.use_combat_rune(e):
                    continue
            elif c == "4":
                from season_two import use_art

                if not use_art(p, e):
                    continue
            elif c == "5":
                if "no potions" in rules:
                    print("This contract forbids potions.")
                    continue
                from food_addons import use_potion

                before = len(p.get("potions", []))
                use_potion(game)
                if len(p.get("potions", [])) == before:
                    continue
            elif c == "6":
                if companion_move_used:
                    print("One companion special move per encounter.")
                    continue
                if not game._use_companion_move(p.get("companions", []), e):
                    continue
                companion_move_used = True
            elif c in ("7", "8"):
                cost = 3 if c == "7" else 5
                if c == "8" and not state(p)["magic"].get("counterspell"):
                    print("Learn Counterspell Training first.")
                    continue
                if p.get("mana", 0) < cost:
                    print("Not enough mana.")
                    continue
                p["mana"] -= cost
                interrupted = (turn + 1) % 3 == 0
                counter = interrupted and c == "8"
                print(
                    "Charged move interrupted!"
                    if interrupted
                    else "No charged move to stop this turn."
                )
                mark(p, 56 if c == "7" else 66)
            elif c == "9":
                if not e.get("intelligent") or e["hp"] > e["max_hp"] * 0.25:
                    print("This enemy is not ready to surrender.")
                    continue
                e["hp"] = 0
                e["spared"] = True
                state(p)["relationships"].setdefault("spared_enemies", []).append(
                    e["name"]
                )
                state(p)["relationships"].setdefault("mercy_visitors", {})[
                    e["name"]
                ] = dict(wander=p.get("wander_count", 0), returned=False)
                mark(p, 58)
            elif c != "disabled":
                continue
            turn += 1
            from original_magic import (
                turn as magic_turn,
                strike,
                damage as adjust_damage,
            )

            game.apply_status(p)
            for foe in enemies:
                game.apply_status(foe)
            if not ticked_player:
                magic_turn(p, e)
            for index, foe in enumerate(enemies):
                if (
                    foe["hp"] <= 0
                    or not magic_turn(foe, p)
                    or foe.setdefault("active_buffs", {}).pop("stun", False)
                ):
                    continue
                if index == target and interrupted:
                    if counter:
                        foe["hp"] -= 8
                    continue
                ritual = state(p).get("systems", {}).get("ritual", {})
                partner = state(p)["relationships"].get("partner")
                amount = max(
                    1,
                    foe["atk"]
                    - p.get("def", 0)
                    - (p.get("armour") or {}).get("def", 0)
                    - (3 if prepared and turn <= 3 else 0)
                    - (1 if partner else 0),
                )
                if turn % 3 == 0:
                    amount += max(2, foe["atk"] // 2)
                strike(foe, p, adjust_damage(foe, p, amount))
            if state(p)["magic"].get("philosophy") == "precision" and c == "4":
                e["hp"] -= 1
            if terrain and turn % 2 == 0 and not state(p)["magic"].get("terrain_ward"):
                p["hp"] = max(0, p["hp"] - 2)
                print("Terrain hazard: 2 HP.")
            records.append(
                dict(
                    turn=turn,
                    action=c,
                    hp=p["hp"],
                    enemies=[dict(name=x["name"], hp=x["hp"]) for x in enemies],
                    effects=deepcopy(p.get("rune_status", {})),
                )
            )
        won = p["hp"] > 0
        if won and not practice_mode:
            for foe in enemies:
                if not foe.get("spared"):
                    game.record_kill(foe["name"])
            if any(x.get("boss") for x in enemies):
                game.update_challenge_progress(
                    "boss_kill", sum(bool(x.get("boss")) for x in enemies)
                )
            game.gain_xp(sum(x.get("xp", 15) for x in enemies))
            p["gold"] += sum(x.get("gold", 10) for x in enemies)
            from companion_care import battle_credit

            game.award_companion_xp(5)
            battle_credit(p, 5)
            count(p, "tactical_victories")
            from expansion_hooks import finish_battle

            finish_battle(p, True)
        return won
    finally:
        ritual = state(p).get("systems", {}).get("ritual", {})
        if ritual and not practice_mode and not won:
            ritual["remaining"] = max(0, ritual.get("remaining", 0) - 1)
        partner = state(p)["relationships"].get("partner")
        if partner and not practice_mode:
            partner["remaining"] -= 1
            if partner["remaining"] <= 0:
                state(p)["relationships"].pop("partner", None)
        if practice_mode:
            for key, value in saved.items():
                if value is None:
                    p.pop(key, None)
                else:
                    p[key] = value
            for pet in p.get("companions", []):
                pet.pop("helped_this_battle", None)
        elif p["hp"] <= 0:
            ui.context("dead")
        if ui.get_ui():
            ui.get_ui().clear_enemy()
        history = state(p)["activities"].setdefault("battle_replays", [])
        history.append(dict(practice=practice_mode, won=won, turns=records))
        del history[:-10]


def practice(game, kind="duel"):
    lvl = game.player["level"]
    hp = 25 + lvl * 5
    return encounter(
        game,
        [
            dict(
                name={
                    "memory": "Warband Echo",
                    "mercy": "Remembering Creature",
                    "arcane": "Arcane Partner",
                }.get(kind, "Friendly Duelist"),
                hp=hp,
                atk=4 + lvl,
                **{"def": 1},
                intelligent=True,
            )
        ],
        True,
    )


def activity(game, feature):
    p = game.player
    activities = state(p)["activities"]
    r = p["region"]
    pool = data.NORMAL_MONSTERS.get(r) or data.NORMAL_MONSTERS[data.REGIONS[0]]
    if feature == 51:
        for e in pool:
            print(
                e["name"]
                + ": "
                + str(p.get("kill_counts", {}).get(e["name"], 0))
                + " studied defeats. Tactical fights reveal charging every third turn."
            )
        mark(p, 51)
    elif feature == 52:
        dummy = dict(name="Training Dummy", hp=100, **{"def": 5})
        print(
            "Estimated weapon damage: "
            + str(game.calculate_damage(p, dummy, "weapon"))
            + ". No XP, items, turns or battle progress are awarded."
        )
        mark(p, 52)
    elif feature in (53, 69):
        print(
            "Nonlethal practice restores HP, mana and effects; no drops, kills or XP."
        )
        if practice(game, "arcane" if feature == 69 else "duel"):
            mark(p, feature)
    elif feature == 54:
        if r not in p.get("bosses_defeated", []):
            print("Defeat the original regional guardian first.")
            return
        c = choose("BOSS REMATCH RESTRICTION", ["No potions", "No runes"])
        if c is None:
            return
        boss = deepcopy(data.REGION_BOSSES[r])
        boss["name"] += " · Rematch"
        if encounter(game, [boss], True, rules=[["no potions", "no runes"][c]]):
            activities.setdefault("rematches", []).append(dict(region=r, restriction=c))
            mark(p, 54)
    elif feature == 55:
        if encounter(game, [pool[0]], terrain=r):
            mark(p, 55)
    elif feature == 56:
        state(p)["magic"]["intent_training"] = True
        if encounter(
            game,
            [
                dict(
                    name="Charging Raider", hp=45, atk=6, **{"def": 2}, intelligent=True
                )
            ],
            True,
        ):
            mark(p, 56)
    elif feature == 57:
        print("Two enemies, separate targets. Use Change target before an action.")
        if encounter(game, [pool[0], pool[-1]]):
            mark(p, 57)
    elif feature == 58:
        visitors = state(p)["relationships"].get("mercy_visitors", {})
        pending = [
            (name, entry) for name, entry in visitors.items() if not entry["returned"]
        ]
        if pending:
            name, entry = pending[0]
            if p.get("wander_count", 0) - entry["wander"] < 2:
                print(
                    "The spared traveller needs time to find a safer road. Scout twice before seeking them again."
                )
                return
            print(
                name
                + ' returns without a weapon. "You let me leave. I want to help guard a village now."'
            )
            if not ui.village:
                print("Meet them again from this activity inside a village.")
                return
            choice = choose(
                "A SECOND CHANCE",
                [
                    "Share one carried food and introduce them to the village watch",
                    "Wish them a peaceful journey",
                ],
            )
            if choice is None:
                return
            if choice == 0:
                from addon_quests import food_take

                if not food_take(p, 1):
                    print("Bring one carried food.")
                    return
                from community_addons import project

                local = project(p, ui.village)
                local["watch_training"] = min(3, local.get("watch_training", 0) + 1)
            entry["returned"] = True
            mark(p, 58)
            print("Their return is recorded.")
            return
        if visitors:
            print("The people you spared are rebuilding their lives.")
            return
        print(
            "An intelligent raider can surrender below 25% HP. Mercy is not available for mindless monsters."
        )
        enemy = dict(
            name="Cornered Raider", hp=45, atk=6, **{"def": 2}, intelligent=True
        )
        encounter(game, [enemy])
    elif feature == 59:
        from addon_quests import food_take

        if not food_take(p, 1):
            print("Bring one carried food to prepare for battle.")
            return
        activities["prepared"] = True
        mark(p, 59)
        print(
            "Prepared: +3 temporary defence for the first three turns of your next tactical encounter."
        )
    elif feature == 60:
        cycle = p.get("wander_count", 0) // 20
        if activities.get("contract_cycle") == cycle:
            print("One paid contract per exploration cycle.")
            return
        c = choose(
            "CHALLENGE CONTRACT",
            ["No potions: 90 souls on victory", "No runes: 90 souls on victory"],
        )
        if c is None:
            return
        if encounter(game, [pool[0]], rules=[["no potions", "no runes"][c]]):
            p["gold"] += 90
            activities["contract_cycle"] = cycle
            mark(p, 60)
