import random
import json
import os
import hashlib

import original_ui as _ui

from status_effects import (
    RUNE_EFFECTS,
    OFFENSIVE_STATUS,
    DEFENSIVE_STATUS,
    UTILITY_STATUS,
    STATUS_SYNERGIES,
    STATUS_CURES,
    BOSS_EXCLUSIVE_STATUS,
)

from data import (
    BOSS_DROPS,
    REGIONS,
    SECRET_REGION,
    NORMAL_MONSTERS,
    EVOLVED_MONSTERS,
    MINI_BOSSES,
    REGION_BOSSES,
    WEAPONS,
    ARMOURS,
    RUNES,
    STAFFS,
    SCROLLS,
    LOOT_ITEMS,
    MERCHANT_ITEMS,
    COMPANIONS,
    REGION_ITEM_ELEMENTS,
    ELEMENTAL_VILLAGES,
    ELEMENTAL_BOSSES,
    ELEMENTAL_CORES,
    CORE_STABILISER,
    REGION_STRUCTURES,
    FOOD_ITEMS,
    VILLAGE_STOCK,
    CLASSES,
    SKILLS,
    QUEST_TEMPLATES,
    COMPANION_MOVES,
    WEATHER_EFFECTS,
    WANDER_EVENTS,
    ACHIEVEMENTS,
    ACHIEVEMENT_TITLES,
    BOUNTY_MONSTERS,
    POTION_RECIPES,
    WORLD_EVENTS,
    GEAR_SETS,
    FUSION_RECIPES,
    REGION_INGREDIENTS,
    INGREDIENT_COMBOS,
    TOWER_MONSTERS,
    DUNGEON_MONSTERS,
    LIBRARY_TOMES,
    GRAVEYARD_LOOT,
    METALS,
    WOODS,
    CORES,
    CLOTHS,
    LEATHERS,
    STRUCTURES,
    ARMOR_RECIPES,
    STAFF_RECIPES,
    EQUIPMENT_SETS,
    DAILY_CHALLENGES,
    WEEKLY_CHALLENGES,
    BOSS_RUSH_CONFIGURATIONS,
    SKILL_TREES,
    COSMETICS_SHOP,
    GUILD_BONUSES,
    SEASONAL_EVENTS,
    CHALLENGE_MODES,
    STORY_QUESTS,
    ENCHANTMENTS,
    NEWGAME_PLUS_CONFIG,
    SOUL_BINDINGS,
    BATTLE_PASS_TIERS,
    RITUAL_CEREMONIES,
    ARENA_RANKS,
    ARENA_REWARDS,
    RECIPE_DISCOVERY,
    TRADING_CONFIG,
    TOWN_STRUCTURES,
    LOGIN_BONUSES,
    FACTIONS,
    TREASURE_MAPS,
    MOUNTS,
    ARTIFACTS,
)

SAVE_FILE = "soulcrypt_save.json"

# =========================
# COMPANION SYSTEM
# =========================

ELEMENT_RUNES = {
    "fire": ["Flame Rune", "Demon Rune", "Magma Rune", "Solar Rune", "Phoenix Rune"],
    "ice": ["Ice Rune", "Frostfire Rune"],
    "water": ["Water Rune", "Ocean Rune"],
    "earth": ["Earth Rune", "Stone Rune", "Mountain Rune", "Root Rune"],
    "poison": ["Poison Rune", "Venom Rune"],
    "shadow": ["Shadow Rune", "Nightmare Rune", "Abyss Rune"],
    "void": ["Void Rune", "Abyss Rune", "Rift Rune"],
    "light": ["Light Rune", "Celestial Rune", "Lunar Rune"],
    "nature": ["Nature Rune", "Forest Rune", "Life Rune"],
    "soul": ["Soul Rune", "Death Rune"],
}


def find_companion_rune(element):
    rune_names = ELEMENT_RUNES.get(element, [])
    choices = [r.copy() for r in RUNES if r["name"] in rune_names]
    return random.choice(choices) if choices else None


def is_region_rune(rune, region):
    allowed = REGION_ITEM_ELEMENTS.get(region, [])
    return not allowed or rune.get("element") in allowed


def is_region_staff(staff, region):
    allowed = REGION_ITEM_ELEMENTS.get(region, [])
    return not allowed or staff.get("element") in allowed


def get_region_companion_candidates(region):
    owned_names = {c["name"] for c in player.get("companions", []) + player.get("home_companions", [])}
    return [c for c in COMPANIONS.get(region, []) if c["name"] not in owned_names]


def get_ordered_unlocked_regions():
    ordered = [r for r in REGIONS if r in player["unlocked_regions"]]
    if SECRET_REGION in player["unlocked_regions"]:
        ordered.append(SECRET_REGION)
    return ordered


def unlock_secret_region():
    if SECRET_REGION in player["unlocked_regions"]:
        return

    if "Abyss of Souls" not in player["unlocked_regions"]:
        player["secret_gate_ready"] = True
        print(
            "A hidden gateway has been forged, but it will remain sealed until the Abyss of Souls is reached."
        )
        return

    player["unlocked_regions"].add(SECRET_REGION)
    print(f"Secret region unlocked: {SECRET_REGION}!")


def update_companion_evolution():
    from companion_care import evolve

    for companion in player.get("companions", []):
        if evolve(companion):
            print(f"✨ Evolved into {companion['form_name']}!")


def apply_companion_support(enemy):
    from companion_care import ready, form_name, normalise

    from expansion_state import state as expansion_state
    if expansion_state(player).get("systems", {}).get("mode", {}).get("id") == "solo_challenge": return
    for companion in player.get("companions", []):
        normalise(companion, player['region'])
        if companion['hunger'] < 30:
            continue
        if not companion.get('can_battle'):
            if player['hp'] < player['max_hp']:
                player['hp'] = min(player['max_hp'], player['hp']+1+companion.get('stage',0)+int(companion.get('temperament')=='gentle'))
                companion['helped_this_battle'] = True
            continue
        if not ready(companion):
            continue
        if enemy.get('hp',0)<=0:
            continue
        if companion.get('stage',0)>0 and companion.get('element') in ('nature','light') and player['hp']>=player['max_hp']:continue
        if companion.get('stage',0)>0 and companion.get('element')=='water' and enemy.get('def',0)<=0:continue
        companion['helped_this_battle'] = True
        if companion.get('stage',0) == 0:
            enemy['hp'] -= 1
            print(companion['name']+' helps with a small strike (1 damage).')
            continue
        enemy.setdefault("status", {})
        enemy.setdefault("active_buffs", {})
        elem = companion["element"]
        strength = (2 if companion.get("stage", 0) >= 2 else 1) + (1 if companion.get("accessory") else 0) + (1 if companion.get("temperament")=="bold" else 0)
        print(f"✨ {form_name(companion)} assists in battle with {elem} power!")
        if elem == "fire":
            enemy["hp"] -= 3 * strength
            enemy.setdefault("status", {})["burn"] = max(enemy["status"].get("burn", 0), strength)
        elif elem == "ice":
            enemy["hp"] -= 2 * strength
            enemy.setdefault("status", {})["freeze"] = max(enemy["status"].get("freeze", 0), strength)
        elif elem == "water":
            enemy["def"] = max(0, enemy.get("def", 0) - strength)
        elif elem == "earth":
            buffs = player.setdefault("active_buffs", {})
            buffs["fortress"] = max(buffs.get("fortress", 0), strength)
        elif elem == "poison":
            enemy.setdefault("status", {})["poison"] = max(enemy["status"].get("poison", 0), 1 + strength)
        elif elem == "shadow":
            enemy.setdefault("active_buffs", {})["blind"] = strength
        elif elem == "void":
            enemy.setdefault("status", {})["void"] = max(enemy["status"].get("void", 0), strength)
        elif elem == "light":
            player["hp"] = min(player["max_hp"], player["hp"] + 3 * strength + int(companion.get('temperament')=='gentle'))
        elif elem == "nature":
            player["hp"] = min(player["max_hp"], player["hp"] + 2 * strength + int(companion.get('temperament')=='gentle'))
        elif elem == "soul":
            enemy["hp"] -= 2 * strength
            player["hp"] = min(player["max_hp"], player["hp"] + 2 * strength + int(companion.get('temperament')=='gentle'))
        elif elem == "arcane":
            enemy["hp"] -= 3 * strength
        elif elem == "crystal":
            enemy["hp"] -= 2 * strength
            enemy["def"] = max(0, enemy.get("def", 0) - strength)
        elif elem == "storm":
            enemy["hp"] -= 3 * strength
            enemy.setdefault("status", {})["shock"] = strength


def recruit_companion(companion):
    from copy import deepcopy
    if any(c["name"] == companion["name"] for c in player.get("companions", []) + player.get("home_companions", [])):
        print("That companion is already with your party or staying in Old Village.")
        return False
    if len(player.get("companions", [])) >= 3:
        recruit=deepcopy(companion)
        from companion_care import normalise
        normalise(recruit, player["region"])
        player.setdefault("home_companions", []).append(recruit)
        print(recruit["name"] + " is staying safely in Old Village; change your party at its sanctuary.")
        return True
    recruit = companion.copy()
    recruit["stage"] = 0
    recruit["xp"] = 0
    from companion_care import normalise

    normalise(recruit, player["region"])
    player.setdefault("companions", []).append(recruit)
    print(f"🐾 {recruit['name']} has joined your party!")
    return True


def view_companion_status():
    import sys
    from companion_care import menu

    menu(sys.modules[__name__])


# SPECIAL FUSION RECIPES
# =========================

SPECIAL_FUSION_RECIPES = {
    frozenset({"Nightmare Rune", "Demon Rune"}): {
        "name": "Infernal Nightmare Rune",
        "effect": "infernal_nightmare",
        "components": ["fear", "hellfire"],
    },
    frozenset({"Dream Rune", "Abyss Rune"}): {
        "name": "Abyssal Dream Rune",
        "effect": "abyssal_dream",
        "components": ["sleep", "curse"],
    },
    frozenset({"Light Rune", "Shadow Rune"}): {
        "name": "Eclipse Rune",
        "effect": "eclipse",
        "components": ["blind", "heal_tick"],
    },
    frozenset({"Dragon Rune", "Phoenix Rune"}): {
        "name": "Rebirth Flame Rune",
        "effect": "rebirth_flame",
        "components": ["rebirth", "burn"],
    },
    frozenset({"Cosmic Rune", "Eternity Rune"}): {
        "name": "Cosmic Eternity Rune",
        "effect": "cosmic_eternity",
        "components": ["reality_bend", "time_lock"],
    },
    frozenset({"Cosmic Eternity Rune", "Eternity Rune"}): {
        "name": "Creator Rune",
        "effect": "creation",
        "components": ["creation"],
    },
    frozenset({"Fire Rune", "Earth Rune", "Storm Rune"}): {
        "name": "Rune of Elements",
        "effect": "element_synthesis",
        "components": ["elemental_balance", "supercharge", "fusion_boost"],
    },
    frozenset({"Fire Rune", "Water Rune"}): {
        "name": "Steam Cataclysm Rune",
        "effect": "steam_burst",
        "components": ["burn", "soak", "blind"],
    },
    frozenset({"Ice Rune", "Fire Rune"}): {
        "name": "Volcanic Frost Rune",
        "effect": "volcanic_freeze",
        "components": ["magma", "freeze", "shock"],
    },
    frozenset({"Earth Rune", "Water Rune"}): {
        "name": "Mud Titan Rune",
        "effect": "mud_titan",
        "components": ["root", "slow_time", "crush"],
    },
    frozenset({"Shadow Rune", "Fire Rune"}): {
        "name": "Doomflame Rune",
        "effect": "doomflame",
        "components": ["fear", "burn", "curse"],
    },
    frozenset({"Light Rune", "Fire Rune"}): {
        "name": "Solar Judgment Rune",
        "effect": "solar_judgment",
        "components": ["sun_blast", "holy_barrier", "execute"],
    },
    frozenset({"Void Rune", "Light Rune"}): {
        "name": "Null Radiance Rune",
        "effect": "null_radiance",
        "components": ["void", "blind", "reality_bend"],
    },
    frozenset({"Void Rune", "Fire Rune"}): {
        "name": "Voidflame Rune",
        "effect": "voidflame",
        "components": ["void_burn", "fear", "burn"],
    },
    frozenset({"Nature Rune", "Light Rune"}): {
        "name": "World Tree Rune",
        "effect": "world_tree",
        "components": ["heal_tick", "nature_blessing", "regen"],
    },
    frozenset({"Soul Rune", "Shadow Rune"}): {
        "name": "Grave Whisper Rune",
        "effect": "grave_whisper",
        "components": ["soul_drain", "fear", "curse"],
    },
    frozenset({"Soul Rune", "Light Rune"}): {
        "name": "Ascended Spirit Rune",
        "effect": "ascended_spirit",
        "components": ["heal_tick", "divine_luck", "rebirth"],
    },
    frozenset({"Time Rune", "Void Rune"}): {
        "name": "Chrono Void Rune",
        "effect": "chrono_void",
        "components": ["time_lock", "void", "slow_time"],
    },
    frozenset({"Time Rune", "Fire Rune"}): {
        "name": "Temporal Flame Rune",
        "effect": "temporal_flame",
        "components": ["burn", "time_lock", "double_cast"],
    },
    frozenset({"Cosmic Rune", "Void Rune"}): {
        "name": "Dark Universe Rune",
        "effect": "dark_universe",
        "components": ["dimension_break", "void", "reality_bend"],
    },
    frozenset({"Cosmic Rune", "Light Rune"}): {
        "name": "Big Bang Rune",
        "effect": "big_bang",
        "components": ["starfall", "sun_blast", "creation"],
    },
    frozenset({"Dragon Rune", "Void Rune"}): {
        "name": "Void Dragon Rune",
        "effect": "void_dragon",
        "components": ["dragon_fury", "void_burn", "fear"],
    },
    frozenset({"Phoenix Rune", "Void Rune"}): {
        "name": "Eternal Ash Rune",
        "effect": "eternal_ash",
        "components": ["rebirth", "void", "burn"],
    },
    frozenset({"Eternity Rune", "Time Rune"}): {
        "name": "Infinite Loop Rune",
        "effect": "infinite_loop",
        "components": ["time_loop", "stability", "double_cast"],
    },
    frozenset({"Reality Rune", "Void Rune"}): {
        "name": "Broken Reality Rune",
        "effect": "broken_reality",
        "components": ["dimension_break", "random_effect", "curse"],
    },
    frozenset({"Berserk Rune", "Blood Rune"}): {
        "name": "Bloodlust Rune",
        "effect": "bloodlust",
        "components": ["bloodlust"],
    },
    frozenset({"Thunder God Rune", "Earth Rune"}): {
        "name": "Earthquake Rune",
        "effect": "earthquake",
        "components": ["earthquake"],
    },
    frozenset({"Ice Rune", "Shadow Rune"}): {
        "name": "Frostshade Rune",
        "effect": "frostshade",
        "components": ["frostshade"],
    },
    frozenset({"Soul Rune", "Void Rune"}): {
        "name": "Abyssal Soul Rune",
        "effect": "abyssal_soul",
        "components": ["abyssal_soul"],
    },
    frozenset({"Dragon Rune", "Fire Rune"}): {
        "name": "Dragon Flame Rune",
        "effect": "dragon_flame",
        "components": ["dragon_flame"],
    },
    frozenset({"Phoenix Rune", "Light Rune"}): {
        "name": "Dawn Rebirth Rune",
        "effect": "dawn_rebirth",
        "components": ["dawn_rebirth"],
    },
    frozenset({"Titan Rune", "Earth Rune"}): {
        "name": "Colossus Rune",
        "effect": "colossus",
        "components": ["colossus"],
    },
    frozenset({"Mirror Rune", "Echo Rune"}): {
        "name": "Phantom Rune",
        "effect": "phantom",
        "components": ["phantom"],
    },
    frozenset({"Chaos Rune", "Void Rune"}): {
        "name": "Entropy Rune",
        "effect": "entropy",
        "components": ["entropy"],
    },
    frozenset({"Nature Rune", "Water Rune"}): {
        "name": "Tide of Life Rune",
        "effect": "tide_of_life",
        "components": ["tide_of_life"],
    },
    frozenset({"Ancient Rune", "Cosmic Rune"}): {
        "name": "Primordial Rune",
        "effect": "ancient_power",
        "components": ["ancient_power", "reality_bend", "giant_strength"],
    },
    frozenset({"Wraith Rune", "Shadow Rune"}): {
        "name": "Spectre Rune",
        "effect": "spectre",
        "components": ["wraith_form", "blind", "soul_drain"],
    },
    frozenset({"Sacrifice Rune", "Phoenix Rune"}): {
        "name": "Martyr Rune",
        "effect": "martyr",
        "components": ["sacrifice", "rebirth", "sun_blast"],
    },
    frozenset({"Shatter Rune", "Thunder God Rune"}): {
        "name": "Obliteration Rune",
        "effect": "obliteration",
        "components": ["shatter", "lightning_storm", "dragon_fury"],
    },
    frozenset({"Blood Moon Rune", "Soul Rune"}): {
        "name": "Eclipse of Souls Rune",
        "effect": "eclipse_of_souls",
        "components": ["blood_moon", "soul_drain", "curse", "void"],
    },
}


# =========================
# RUNE EFFECTS
# =========================


def apply_rune_effect(rune, user, enemy):
    from original_magic import apply

    return apply(rune, user, enemy)


# =========================
# PLAYER
# =========================

player = {
    "hp": 120,
    "max_hp": 120,
    "atk": 15,
    "def": 5,
    "speed": 5,
    "mana": 0,
    "level": 1,
    "xp": 0,
    "gold": 50,
    "region": REGIONS[0],
    "weapon": None,
    "weapons": [],
    "armour": None,
    "armours": [],
    "runes": [],
    "staffs": [],
    "inventory": [],
    "metals": [],
    "cores": [],
    "woods": [],
    "companions": [],
    "wander_count": 0,
    "scrolls": {},
    "status": {},
    "active_buffs": {},
    "unlocked_regions": {REGIONS[0]},
    "secret_gate_ready": False,
    "forge_cores": [],
    "hunger": 100,
    "discovered_structures": {},
    "elemental_cores": [],
    "class_id": None,
    "skills": [],
    "skill_points": 0,
    "quests": [],
    "class_skill_cooldown": 0,
    "luck": 0,
    "title": None,
    "bosses_defeated": [],
    "achievements": [],
    "bounties_claimed": [],
    "weather": "Clear",
    "is_night": False,
    "potions": [],
    "potion_atk_boost": 0,
    "potion_atk_turns": 0,
    "luck_boost_explores": 0,
    "kill_counts": {},
    "corruption": 0,
    "resonance_streak": 0,
    "resonance_ready": False,
    "prestige_level": 0,
    "prestige_bonus": 0,
    "world_event_idx": 0,
    "active_set": None,
    "set_crit_counter": 0,
    "companion_xp": {},
    "companion_levels": {},
}


def _check_level_up():
    if player["xp"] >= player["level"] * 50:
        player["xp"] -= player["level"] * 50
        player["level"] += 1
        player["max_hp"] += 5
        player["atk"] += 0.5
        player["def"] += 0.2
        player["speed"] += 1
        player["mana"] += 2
        player["hp"] = player["max_hp"]
        player["skill_points"] += 1
        print(f"🎉 LEVEL UP! You are now level {player['level']}!")


# =========================
# INVENTORY
# =========================


def view_inventory():
    import sys
    from inventory_tools import inventory_menu

    inventory_menu(sys.modules[__name__])


# =========================
# SAVE / LOAD
# =========================


def _read_all_saves():
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # new multi-save format  { username: {...} }
            # but guard against the OLD format (has "hp" key at top level)
            if "hp" in data:
                name = data.get("name", "Unknown")
                return {name: data}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def _write_all_saves(saves):
    with open(SAVE_FILE, "w") as f:
        json.dump(saves, f, indent=4)


def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def save_game():
    saves = _read_all_saves()
    data = player.copy()
    data["unlocked_regions"] = list(data["unlocked_regions"])
    # preserve existing password hash — never overwrite it on plain save
    existing = saves.get(player["name"], {})
    if "password_hash" in existing and "password_hash" not in data:
        data["password_hash"] = existing["password_hash"]
    saves[player["name"]] = data
    _write_all_saves(saves)
    print(f"💾 Saved as '{player['name']}'")


def load_game():
    global player

    saves = _read_all_saves()

    default_player = {
        "hp": 120,
        "max_hp": 120,
        "atk": 15,
        "def": 5,
        "speed": 5,
        "mana": 0,
        "level": 1,
        "xp": 0,
        "gold": 50,
        "region": REGIONS[0],
        "weapon": None,
        "weapons": [],
        "armour": None,
        "armours": [],
        "runes": [],
        "staffs": [],
        "inventory": [],
        "companions": [],
        "wander_count": 0,
        "scrolls": {},
        "status": {},
        "active_buffs": {},
        "unlocked_regions": {REGIONS[0]},
        "secret_gate_ready": False,
        "forge_cores": [],
        "elemental_cores": [],
        "hunger": 100,
        "discovered_structures": {},
        "class_id": None,
        "skills": [],
        "skill_points": 0,
        "quests": [],
        "class_skill_cooldown": 0,
        "luck": 0,
        "title": None,
        "bosses_defeated": [],
        "achievements": [],
        "bounties_claimed": [],
        "weather": "Clear",
        "is_night": False,
        "potions": [],
        "potion_atk_boost": 0,
        "potion_atk_turns": 0,
        "luck_boost_explores": 0,
        "kill_counts": {},
        "corruption": 0,
        "resonance_streak": 0,
        "resonance_ready": False,
        "prestige_level": 0,
        "prestige_bonus": 0,
        "world_event_idx": 0,
        "active_set": None,
        "set_crit_counter": 0,
        "companion_xp": {},
        "companion_levels": {},
        "metals": [],
        "cores": [],
        "woods": [],
    }

    if saves:
        print("\n=== SAVE FILES ===")
        names = list(saves.keys())
        for i, n in enumerate(names):
            s = saves[n]
            lvl = s.get("level", 1)
            reg = s.get("region", "?")
            lock = "🔒" if "password_hash" in s else "🔓"
            print(f"{i}. {lock} {n}  (Lv.{lvl} — {reg})")
        print(f"{len(names)}. New game")

        try:
            choice = int(input("> "))
        except ValueError:
            choice = len(names)

        if 0 <= choice < len(names):
            chosen_name = names[choice]
            data = saves[chosen_name]

            # ── password check ──────────────────────────────────────
            stored_hash = data.get("password_hash")
            if stored_hash:
                for attempt in range(3):
                    pw = input("🔑 Password: ").strip()
                    if _hash_pw(pw) == stored_hash:
                        break
                    remaining = 2 - attempt
                    if remaining > 0:
                        print(f"❌ Wrong password. {remaining} attempt(s) left.")
                    else:
                        print("❌ Access denied. Returning to menu.")
                        load_game()
                        return
            else:
                # old save — no password yet, invite them to set one
                print("⚠  This save has no password. Set one now to protect it.")
                pw1 = input("New password (or press Enter to skip): ").strip()
                if pw1:
                    pw2 = input("Confirm password: ").strip()
                    if pw1 == pw2:
                        data["password_hash"] = _hash_pw(pw1)
                        saves[chosen_name] = data
                        _write_all_saves(saves)
                        print("✅ Password set!")
                    else:
                        print("⚠  Passwords didn't match — skipping.")
            # ────────────────────────────────────────────────────────

            default_player.update(data)
            player = default_player
            # strip password_hash from live player dict — no need in memory
            player.pop("password_hash", None)
            if isinstance(player.get("unlocked_regions"), list):
                player["unlocked_regions"] = set(player["unlocked_regions"])
            print(f"✅ Loaded '{player['name']}'")
            return
        # fall through to new game

    # new game — ask for name then password
    name = input("Enter your character name: ").strip() or "Wanderer"
    player["name"] = name

    print("Set a password to protect your save (others can't load it without it).")
    pw1 = input("Password (or press Enter to skip): ").strip()
    if pw1:
        pw2 = input("Confirm password: ").strip()
        if pw1 == pw2:
            player["password_hash"] = _hash_pw(pw1)
            print("🔒 Password set — your save is protected!")
        else:
            print("⚠  Passwords didn't match — no password set.")

    # ── Class selection ──────────────────────────────────────
    print("\n╔══════════════════════════════════╗")
    print("║      CHOOSE YOUR CLASS           ║")
    print("╚══════════════════════════════════╝")
    class_keys = list(CLASSES.keys())
    for i, key in enumerate(class_keys):
        cls = CLASSES[key]
        print(f"\n  {i}. {cls['icon']} {cls['name']}")
        print(f"     {cls['desc']}")
        print(f"     Passive: {cls['passive_desc']}")
        print(f"     Skill:   [{cls['skill_name']}] — {cls['skill_desc']}")
    try:
        ci = int(input("\nChoose class (0-4) > "))
        if not (0 <= ci < len(class_keys)):
            ci = 0
    except ValueError:
        ci = 0
    chosen_key = class_keys[ci]
    chosen_cls = CLASSES[chosen_key]
    player["class_id"] = chosen_key
    for stat, val in chosen_cls["bonus"].items():
        player[stat] = player.get(stat, 0) + val
    print(f"\n⭐ You are a {chosen_cls['icon']} {chosen_cls['name']}!")
    print(f"   Passive: {chosen_cls['passive_desc']}")
    # ──────��──────────────────────────────────────────────────

    print(f"⚔  New game started as '{name}'")


# =========================
# STATUS
# =========================


def apply_status(entity):
    """Apply all status effects for one combat turn with print feedback."""
    s = entity.setdefault("status", {})
    ab = entity.setdefault("active_buffs", {})
    is_player = entity is player
    lbl = "You" if is_player else entity.get("name", "Enemy")
    lbl_lower = "you" if is_player else entity.get("name", "enemy")

    # ── Damage-over-time ──
    DOT = {
        "burn": (5, f"  🔥 {lbl} burn{'s' if not is_player else ''} for 5 damage!"),
        "poison": (4, f"  ☠ {lbl} take{'s' if not is_player else ''} 4 poison damage!"),
        "bleed": (6, f"  🩸 {lbl} bleed{'s' if not is_player else ''} for 6 damage!"),
        "void": (8, f"  🌀 Void gnaws {lbl_lower} for 8 damage!"),
        "magma": (10, f"  🌋 Magma scorches {lbl_lower} for 10 damage!"),
        "shock": (4, f"  ⚡ Shock zaps {lbl_lower} for 4 damage!"),
        "curse": (3, f"  💀 Curse saps {lbl_lower} for 3 damage!"),
        "root": (2, f"  🌿 Roots tear at {lbl_lower} for 2 damage!"),
        "necrosis": (7, f"  🖤 Necrosis rots {lbl_lower} for 7 damage!"),
    }
    for effect, (dmg, msg) in DOT.items():
        if effect in s:
            entity["hp"] -= dmg
            print(msg)

    # ── Heal-over-time ──
    HOT = {
        "regen": (5, f"  💚 {lbl} regenerate{'s' if not is_player else ''} 5 HP!"),
        "heal_tick": (3, f"  ✨ {lbl} recover{'s' if not is_player else ''} 3 HP!"),
        "creation": (4, f"  ⭐ Creation restores 4 HP to {lbl_lower}!"),
        "life_sap": (
            6,
            f"  💚 {lbl} drain{'s' if not is_player else ''} 6 HP from the wound!",
        ),
    }
    for effect, (amt, msg) in HOT.items():
        if effect in s:
            entity["hp"] = min(entity.get("max_hp", 9999), entity["hp"] + amt)
            print(msg)

    # ── Control effects → convert to active_buffs or display ──

    # Freeze: 55% chance to stun (skip turn), otherwise weaken
    if "freeze" in s:
        if random.random() < 0.55:
            ab["stun"] = max(ab.get("stun", 0), 1)
            print(f"  ❄ {lbl} {'are' if is_player else 'is'} frozen solid — turn skipped!")
        else:
            print(f"  ❄ {lbl} struggle{'s' if not is_player else ''} against the ice!")
            if not is_player:
                ab["root"] = max(ab.get("root", 0), 1)

    # Sleep: always stun for 1 turn
    if "sleep" in s:
        ab["stun"] = max(ab.get("stun", 0), 1)
        print(f"  💤 {lbl} fall{'s' if not is_player else ''} asleep — turn lost!")

    # Fear: 45% chance to cause miss (blind)
    if "fear" in s:
        if random.random() < 0.45:
            ab["blind"] = max(ab.get("blind", 0), 1)
            print(f"  😱 {lbl} {'are' if is_player else 'is'} overwhelmed by fear!")
        else:
            print(f"  😱 {lbl} push{'es' if not is_player else ''} through the fear…")

    # Slow: apply to enemy active_buffs so fight loop reduces their damage
    if "slow" in s and not is_player:
        ab["slow_time"] = max(ab.get("slow_time", 0), 1)
        print(f"  ⌛ {lbl} is slowed!")

    # Silence: prevent scrolls/staffs (flag in active_buffs)
    if "silence" in s:
        ab["silenced"] = max(ab.get("silenced", 0), 1)
        print(f"  🔇 {lbl} {'are' if is_player else 'is'} silenced — magic weakened!")

    # Weaken: reduce ATK for this turn via active_buffs
    if "weaken" in s:
        ab["weakened"] = max(ab.get("weakened", 0), 1)
        print(f"  💢 {lbl} {'are' if is_player else 'is'} weakened!")

    # ── Tick down all statuses and remove expired ──
    to_remove = []
    for k in list(s.keys()):
        s[k] -= 1
        if s[k] <= 0:
            to_remove.append(k)
    for k in to_remove:
        del s[k]
        EXPIRE_MSG = {
            "burn": f"  ✓ {lbl_lower.capitalize()} stop{'s' if not is_player else ''} burning.",
            "poison": f"  ✓ Poison fades from {lbl_lower}.",
            "bleed": f"  ✓ {lbl_lower.capitalize()} stop{'s' if not is_player else ''} bleeding.",
            "void": f"  ✓ Void dissipates.",
            "magma": f"  ✓ Magma cools.",
            "shock": f"  ✓ Shock disperses.",
            "curse": f"  ✓ Curse lifted from {lbl_lower}.",
            "freeze": f"  ✓ {'You thaw' if is_player else lbl + ' thaws'} out.",
            "sleep": f"  ✓ {'You wake' if is_player else lbl + ' wakes'} up.",
            "fear": f"  ✓ {'Your' if is_player else lbl + chr(39) + 's'} fear fades.",
            "root": f"  ✓ Roots release {lbl_lower}.",
            "slow": f"  ✓ {lbl} regain{'s' if not is_player else ''} full speed.",
            "silence": f"  ✓ Silence lifts from {lbl_lower}.",
            "weaken": f"  ✓ {lbl} {'feel' if is_player else 'feels'} strength returning.",
            "necrosis": f"  ✓ Necrosis halts.",
        }
        if k in EXPIRE_MSG:
            print(EXPIRE_MSG[k])


# =========================
# XP
# =========================


def equip_armour():
    if not player["armours"]:
        print("No armour available.")
        return

    print("\n=== EQUIP ARMOUR ===")
    for i, a in enumerate(player["armours"]):
        eq = " [EQUIPPED]" if player["armour"] == a else ""
        elem = f" [{a['element']}]" if a.get("element") else ""
        print(f"{i}. {a['name']} (DEF {a['def']}){elem}{eq}")

    try:
        idx = int(input("> "))
        if 0 <= idx < len(player["armours"]):
            player["armour"] = player["armours"][idx]
            print(f"🛡 Equipped {player['armour']['name']}")
        else:
            print("Invalid index.")
    except ValueError:
        print("Invalid input.")


def equip_weapon():
    if not player["weapons"]:
        print("No weapons available.")
        return

    print("\n=== EQUIP WEAPON ===")

    for i, w in enumerate(player["weapons"]):
        eq = " [EQUIPPED]" if player["weapon"] == w else ""
        print(f"{i}. {w['name']} (ATK {w['atk']}){eq}")

    try:
        idx = int(input("> "))

        if 0 <= idx < len(player["weapons"]):
            player["weapon"] = player["weapons"][idx]
            print(f"⚔ Equipped {player['weapon']['name']}")
        else:
            print("Invalid index.")

    except ValueError:
        print("Invalid input.")


def gain_xp(x):
    update_challenge_progress("xp_gain", x)
    player["xp"] += x
    need = player["level"] * 50

    if player["xp"] >= need:
        player["xp"] = 0
        player["level"] += 1
        player["max_hp"] += 5
        player["atk"] += 0.5
        player["def"] += 0.2
        player["speed"] += 1
        player["hp"] = player["max_hp"]
        player["skill_points"] = player.get("skill_points", 0) + 1
        cls = CLASSES.get(player.get("class_id") or "", {})
        icon = cls.get("icon", "⭐")
        print(f"{icon} LEVEL UP! You are now level {player['level']}!")
        print(f"   +1 Skill Point (total: {player['skill_points']}) — spend via option 19")
        update_challenge_progress("level_reach", player["level"])
        _check_achievements()


# =========================
# BUFFS
# =========================


def process_buffs():
    buffs = player["active_buffs"]

    expired = []
    for k in list(buffs.keys()):
        buffs[k] -= 1
        if buffs[k] <= 0:
            expired.append(k)

    for k in expired:
        del buffs[k]


def blacksmith():
    from expansion_state import state as expansion_state
    if expansion_state(player).get('systems',{}).get('mode',{}).get('id')=='budget_run':
        print('Budget Run blocks purchases. End the mode to use this service.')
        return
    import sys
    from village_life import require_service, smith

    if require_service("forge"):
        smith(sys.modules[__name__], _ui.village)


# =========================
# DAMAGE
# =========================


def calculate_damage(player_obj, enemy, mode="weapon"):
    weapon = player_obj.get("weapon") or {}
    staff = player_obj.get("staffs")[0] if player_obj.get("staffs") else {}
    runes = []  # Carried runes are supplies, not permanent passive bonuses.
    buffs = player_obj.get("active_buffs") or {}

    base_atk = 0
    element_bonus = 0
    flat_bonus = 0
    crit = 1

    if mode == "weapon":
        base_atk = weapon.get("atk", 0) + player_obj["atk"]
    elif mode == "staff":
        base_atk = staff.get("power", 0)

    for rune in runes:
        effects = [rune.get("effect")]
        if rune.get("effect") == "fusion":
            effects = rune.get("components", [])

        for effect in effects:
            if effect in ["giant_strength", "atk_up", "massive_atk_up"]:
                flat_bonus += rune.get("value", 5)

            if effect == "crit_up" and random.random() < 0.2:
                crit = 2

            if effect in ["burn", "hellfire", "sun_blast"]:
                element_bonus += 5
            elif effect in ["freeze", "ice"]:
                element_bonus += 4
            elif effect in ["shock", "chain_shock"]:
                element_bonus += 6
            elif effect in ["void", "void_burn"]:
                element_bonus += 8
            elif effect in ["poison", "deadly_poison"]:
                element_bonus += 4

        # FIX: buff bonuses are independent checks, not chained as elif under element effects
        if buffs.get("supercharge"):
            flat_bonus *= 1.5
            element_bonus += 2

        if buffs.get("elemental_balance"):
            element_bonus += 10

        if buffs.get("fusion_boost"):
            flat_bonus += 10

    base_atk += buffs.get("atk_up", 0)
    base_atk += buffs.get("massive_atk_up", 0)
    base_atk += buffs.get("giant_strength", 0)

    damage = (base_atk + flat_bonus + element_bonus) * crit
    damage -= enemy.get("def", 0)

    from original_magic import damage as rune_damage

    return rune_damage(player_obj, enemy, max(1, int(damage)))


FORGE_DATABASE = {}
# format:
# {("core","metal","wood"): {"name": "Excalibur", "creator": "player"}}


def forge_weapon():
    from village_life import require_service, quality

    if not require_service("forge"):
        return
    cores = [i for i in player["cores"] if i in CORES]
    metals = [i for i in player["metals"] if i in METALS]
    woods = [i for i in player["woods"] if i in WOODS]

    if not cores:
        print("You have no weapon cores.")
        return
    if not metals:
        print("You have no metals.")
        return
    if not woods:
        print("You have no woods.")
        return

    print("\n=== SELECT CORE ===")
    for i, core in enumerate(cores, 1):
        print(f"{i}. {core}")
    core = cores[int(input("> ")) - 1]

    print("\n=== SELECT METAL ===")
    for i, metal in enumerate(metals, 1):
        print(f"{i}. {metal}")
    metal = metals[int(input("> ")) - 1]

    print("\n=== SELECT WOOD ===")
    for i, wood in enumerate(woods, 1):
        print(f"{i}. {wood}")
    wood = woods[int(input("> ")) - 1]

    combo_key = (core, metal, wood)

    # CHECK IF COMBO EXISTS
    if combo_key in FORGE_DATABASE:
        existing = FORGE_DATABASE[combo_key]
        print(f"\nThis weapon already exists!")
        print(f"Name: {existing['name']}")
        print(f"Forged by: {existing['creator']}")
        return

    print("\nName your weapon:")
    weapon_name = input("> ").strip()

    if not weapon_name:
        weapon_name = "Unnamed Weapon"

    # Consume the selected materials and create the actual weapon, not only a registry entry.
    player["cores"].remove(core)
    player["metals"].remove(metal)
    player["woods"].remove(wood)
    crafted = {
        "name": weapon_name,
        "tier": "crafted",
        "atk": METALS[metal].get("atk", 0)
        + WOODS[wood].get("atk", 0)
        + 10
        + (quality("forge") - 1) * 2,
        "cores": {},
        "materials": {"core": core, "metal": metal, "wood": wood},
    }
    from source_story import rank, craft_xp

    crafted["atk"] += rank(player, "smithing") - 1
    from artisan_addons import apply_traits
    apply_traits(player, crafted, "smithing")
    player["weapons"].append(crafted)
    craft_xp(player, "smithing")
    # STORE NEW COMBINATION
    FORGE_DATABASE[combo_key] = {
        "name": weapon_name,
        "creator": player.get("name", "Unknown"),
    }

    print("\nWeapon forged successfully!")
    print(f"{weapon_name} has been added to the forge database.")


# =========================
# STAFF
# =========================


def choose_staff():
    if not player["staffs"]:
        return None

    if len(player["staffs"]) == 1:
        return player["staffs"][0]

    print("\n=== SELECT STAFF ===")
    for i, staff in enumerate(player["staffs"]):
        rune = staff.get("rune")
        rune_name = rune["name"] if isinstance(rune, dict) else "None"
        print(f"{i}. {staff['name']} (Power {staff['power']}) Rune: {rune_name}")

    try:
        idx = int(input("Select staff > "))
        if idx < 0 or idx >= len(player["staffs"]):
            print("Invalid staff selection.")
            return None
    except ValueError:
        print("Invalid input.")
        return None

    return player["staffs"][idx]


def use_staff(enemy):
    staff = choose_staff()

    if staff is None:
        print("No staff selected.")
        return

    dmg = staff.get("power", 5 + len(staff.get("effects", [])) * 3)
    print(f"\n✨ You use {staff['name']}")

    from original_magic import strike, damage

    strike(player, enemy, damage(player, enemy, dmg), magical=True)
    if staff.get('paired_effects'):
        for effect in staff['paired_effects']:
            apply_rune_effect({'name':'Paired channel','effect':effect},player,enemy)
        print('The paired staff channels its permanent inscription.')
        return
    bound = staff.pop("rune", None)
    if bound:
        apply_rune_effect(bound, player, enemy)
        print(f"Used up the bound {bound['name']}.")
    for stored in staff.pop("stored_runes", []):
        apply_rune_effect(stored, player, enemy)
        print(f"Used up the stored {stored['name']}.")
    staff.pop("effects", None)


# =========================
# runes and forge and items
# =========================


def crimson_forge():
    import sys
    from regional_forges import forge_menu
    forge_menu(sys.modules[__name__])


def _reinforce_crimson_gear():
    if player["region"] != "Crimson Depths":
        print("🔥 You must travel to Crimson Forge.")
        return

    if not player["forge_cores"]:
        print("No forge cores available.")
        return

    print("\n🔥 CRIMSON FORGE 🔥")

    print("Forge Cores:")
    for i, core in enumerate(player["forge_cores"]):
        print(f"{i}. {core}")

    try:
        idx = int(input("Choose core > "))
        core = player["forge_cores"][idx]
    except:
        print("Invalid selection.")
        return

    print("\n1. Upgrade Weapon")
    print("2. Upgrade Staff")

    choice = input("> ")

    if choice == "1":
        if not player["weapons"]:
            print("No weapons.")
            return

        for i, weapon in enumerate(player["weapons"]):
            print(f"{i}. {weapon['name']} (ATK {weapon['atk']})")

        try:
            w = int(input("> "))
            weapon = player["weapons"][w]
        except:
            print("Invalid weapon.")
            return

        bonus = random.randint(5, 15)

        if "Creator" in core:
            bonus += 25
        elif "Soul" in core:
            bonus += 15
        elif "Celestial" in core:
            bonus += 12
        elif "Void" in core:
            bonus += 10

        weapon["atk"] += bonus
        player["forge_cores"].remove(core)

        print(f"⚔ {weapon['name']} gained +{bonus} ATK!")

    elif choice == "2":
        if not player["staffs"]:
            print("No staffs.")
            return

        for i, staff in enumerate(player["staffs"]):
            print(f"{i}. {staff['name']} (Power {staff['power']})")

        try:
            s = int(input("> "))
            staff = player["staffs"][s]
        except:
            print("Invalid staff.")
            return

        bonus = random.randint(3, 10)

        if "Creator" in core:
            bonus += 20
        elif "Soul" in core:
            bonus += 12
        elif "Celestial" in core:
            bonus += 10
        elif "Void" in core:
            bonus += 8

        staff["power"] += bonus
        player["forge_cores"].remove(core)

        print(f"✨ {staff['name']} gained +{bonus} power!")


def use_scroll():
    scrolls = [i for i in player["inventory"] if "turns" in i]
    if not scrolls:
        print("No scrolls.")
        return

    for i, s in enumerate(scrolls):
        print(i, s["name"])

    idx = int(input("> "))
    scroll = scrolls[idx]

    player["active_buffs"][scroll["effect"]] = scroll["turns"]

    player["inventory"].remove(scroll)
    print(f"📜 Used {scroll['name']}")


def merge_runes():
    if len(player["runes"]) < 2:
        print("You need at least two runes to merge.")
        return

    print("\n=== MERGE RUNES ===")
    for i, rune in enumerate(player["runes"]):
        components = (
            ", ".join(rune.get("components", [rune["effect"]]))
            if rune.get("effect") == "fusion"
            else rune["effect"]
        )
        print(f"{i}. {rune['name']} ({components})")

    try:
        first = int(input("Select first rune > "))
        second = int(input("Select second rune > "))
    except ValueError:
        print("Invalid selection.")
        return

    if (
        first == second
        or first < 0
        or second < 0
        or first >= len(player["runes"])
        or second >= len(player["runes"])
    ):
        print("Invalid rune choice.")
        return

    if first > second:
        first, second = second, first

    rune_one = player["runes"][first]
    rune_two = player["runes"][second]

    from rune_pairs import fusion

    try:
        fusion_rune = fusion(rune_one, rune_two)
    except ValueError as error:
        print(str(error))
        return
    recipe = None
    player["runes"].pop(second)
    player["runes"].pop(first)
    from magic_addons import record_fusion
    record_fusion(player, fusion_rune)
    player["runes"].append(fusion_rune)

    print(f"🔮 Created {fusion_rune['name']}!")
    print(f"✦ {fusion_rune['ability']['name']}: {fusion_rune['ability']['description']}")


def use_combat_rune(enemy):
    from original_magic import silenced

    if silenced(player):
        print("Silence prevents rune use this turn.")
        return False
    """Choose and consume one rune. Ordinary attacks never consume your whole pouch."""
    if not player.get("runes"):
        print("No runes left. Find or buy more; your sword still works.")
        return False
    for index, rune in enumerate(player["runes"]):
        print(f"{index}. {rune['name']} — one use")
    try:
        index = int(input("Choose a rune (-1 cancel) > "))
    except ValueError:
        return False
    if not 0 <= index < len(player["runes"]):
        return False
    rune = player["runes"].pop(index)
    apply_rune_effect(rune, player, enemy)
    print(f"Used up {rune['name']}. {len(player['runes'])} rune(s) remaining.")
    return True


def cast_spell():
    if not player["runes"]:
        print("No runes to cast.")
        return

    print("\n=== CAST SPELL ===")
    for i, rune in enumerate(player["runes"]):
        eff = rune.get("effect")
        if eff == "fusion":
            eff = ", ".join(rune.get("components", []))
        print(f"{i}. {rune['name']} ({eff})")

    try:
        idx = int(input("Select rune to cast > "))
        if not 0 <= idx < len(player["runes"]):
            raise IndexError
        rune = player["runes"][idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    allowed = {
        "regen",
        "greater_regen",
        "heal_tick",
        "defense_up",
        "speed_up",
        "crit_up",
        "holy_barrier",
        "nature_blessing",
        "warp",
        "moon_guard",
        "fortress",
        "stability",
        "divine_luck",
        "mana_regen",
        "rebirth",
        "double_cast",
        "reflect",
    }

    effects = rune.get("components") if rune.get("effect") == "fusion" else [rune["effect"]]

    if any(effect not in allowed for effect in effects):
        print("That rune can only be used in combat.")
        return

    apply_rune_effect(rune, player, player)
    player["runes"].remove(rune)
    print(f"✨ Cast {rune['name']}.")


def merchant():
    from expansion_state import state as expansion_state
    if expansion_state(player).get('systems',{}).get('mode',{}).get('id')=='budget_run':
        print('Budget Run blocks purchases. End the mode to use this service.')
        return
    from copy import deepcopy

    region = player["region"]
    stock = []
    for name in MERCHANT_ITEMS.get(region, []):
        offer = None
        for key, catalog, stat in [
            ("weapons", WEAPONS, "atk"),
            ("staffs", STAFFS, "power"),
            ("runes", RUNES, None),
            ("armours", ARMOURS, "def"),
        ]:
            item = next((x for x in catalog if x["name"] == name), None)
            if item:
                price = item.get(stat, 10) * 10 if stat else random.randint(100, 550)
                offer = (key, deepcopy(item), price)
                break
        if offer is None:
            for key, catalog, limits in [
                ("woods", WOODS, (50, 150)),
                ("metals", METALS, (70, 200)),
                ("cores", CORES, (100, 300)),
            ]:
                if name in catalog:
                    offer = (key, name, random.randint(*limits))
                    break
        if offer:
            from village_life import quality

            key, item, price = offer
            stock.append((key, item, max(1, round(price * (1 - (quality("trade") - 1) * 0.05)))))
    while True:
        print(f"\n=== {region} MERCHANT ===\nSouls: {player['gold']}")
        for i, (key, item, price) in enumerate(stock, 1):
            name = item["name"] if isinstance(item, dict) else item
            print(f"{i}. {name} — {price} souls")
        print("0. Leave")
        choice = input("Buy item number > ").strip().lower()
        if choice in ("0", "x"):
            return
        try:
            index = int(choice) - 1
            if not 0 <= index < len(stock):
                raise ValueError
        except ValueError:
            print("Choose a listed item number.")
            continue
        key, item, price = stock[index]
        name = item["name"] if isinstance(item, dict) else item
        if input(f"Buy {name} for {price} souls? (y/n) > ").lower() != "y":
            continue
        if player["gold"] < price:
            print("Not enough souls.")
            continue
        player["gold"] -= price
        player.setdefault(key, []).append(deepcopy(item))
        stock.pop(index)
        print(f"Purchased {name}!")


def _use_class_skill(cls, enemy):
    skill = cls.get("skill_name", "")
    passive = cls.get("passive", "")
    print(f"\n✨ {skill}!")
    if passive == "counter":  # Shield Bash
        enemy.setdefault("active_buffs", {})["stun"] = 1
        print("   Enemy is STUNNED for 1 turn!")
    elif passive == "spell_boost":  # Arcane Surge
        player.setdefault("active_buffs", {})["arcane_surge"] = 1
        print("   Your next attack will strike twice!")
    elif passive == "crit":  # Expose Weakness
        enemy["def"] = max(0, enemy.get("def", 0) - 6)
        enemy.setdefault("active_buffs", {})["exposed"] = 3
        print(f"   Enemy DEF reduced by 6 for 3 turns!")
    elif passive == "ranger_shot":  # Volley
        total = 0
        for _ in range(3):
            dmg = 5 + min(10, player.get("level", 1))
            enemy["hp"] -= dmg
            total += dmg
        print(f"   3-arrow volley! {total} total damage!")
    elif passive == "lifesteal":  # Soul Rip
        drain = min(35, 10 + player.get("level", 1) * 2)
        enemy["hp"] -= drain
        player["hp"] = min(player["max_hp"], player["hp"] + drain)
        print(f"   Drained {drain} HP directly from the enemy!")


def _use_companion_move(companions, enemy):
    from expansion_state import state as expansion_state
    if expansion_state(player).get('systems',{}).get('mode',{}).get('id')=='solo_challenge':
        print('Solo mode disables companion battle moves.');return False
    from companion_care import active_ready

    battle_ready = [c for c in companions if active_ready(c)]
    if not battle_ready:
        print("🐾 Companions need stage 1 and at least 30 hunger to use battle moves. Feed them through Character → Companions.")
        return False
    print("\n🐾 Companion moves:")
    for i, c in enumerate(battle_ready):
        elem = c.get("element", "?")
        move = COMPANION_MOVES.get(elem, {})
        print(f"  {i}. {c.get('form_name', c['name'])} [{elem}] — {move.get('name', '?')}: {move.get('desc', '?')}")
    try:
        idx = int(input("  Use which? (-1 cancel) > "))
    except ValueError:
        return False
    if not (0 <= idx < len(battle_ready)):
        return False
    chosen = battle_ready[idx]
    chosen['helped_this_battle'] = True
    elem = chosen.get("element", "")
    move = COMPANION_MOVES.get(elem, {})
    print(f"\n💫 {chosen.get('form_name', chosen['name'])} uses {move.get('name', '?')}!")
    bond = "companion_bond" in player.get("skills", [])
    mult = 2 if bond else 1
    if elem == "fire":
        dmg = 30 * mult
        enemy["hp"] -= dmg
        enemy.setdefault("status", {})["burn"] = 3
        print(f"   🔥 {dmg} fire damage + burn 3!")
    elif elem == "ice":
        dmg = 25 * mult
        enemy["hp"] -= dmg
        enemy.setdefault("status", {})["freeze"] = 2
        print(f"   ❄️ {dmg} ice damage + freeze 2!")
    elif elem == "water":
        dmg = 20 * mult
        enemy["hp"] -= dmg
        enemy["def"] = max(0, enemy.get("def", 0) - 4)
        print(f"   🌊 {dmg} damage + enemy DEF -4!")
    elif elem == "earth":
        player.setdefault("active_buffs", {})["fortress"] = 3
        print("   🪨 Stone Wall! Your DEF boosted for 3 turns!")
    elif elem == "poison":
        dmg = 15 * mult
        enemy["hp"] -= dmg
        enemy.setdefault("status", {})["poison"] = 4
        print(f"   ☠️ {dmg} damage + poison 4!")
    elif elem == "shadow":
        dmg = 20 * mult
        enemy["hp"] -= dmg
        enemy.setdefault("active_buffs", {})["blind"] = 2
        print(f"   🌑 {dmg} damage + blind 2!")
    elif elem == "void":
        dmg = 28 * mult
        enemy["hp"] -= dmg
        enemy.setdefault("status", {})["void"] = 3
        print(f"   🌀 {dmg} void damage + void 3!")
    elif elem == "light":
        heal = 30 * mult
        player["hp"] = min(player["max_hp"], player["hp"] + heal)
        print(f"   ✨ Holy Light heals you for {heal} HP!")
    elif elem == "nature":
        enemy.setdefault("active_buffs", {})["root"] = 2
        print("   🌿 Entangle! Enemy rooted for 2 turns!")
    elif elem == "soul":
        drain = 25 * mult
        enemy["hp"] -= drain
        player["hp"] = min(player["max_hp"], player["hp"] + drain)
        print(f"   💀 Soul Drain: {drain} HP stolen!")
    elif elem == "storm":
        dmg = 35 * mult
        enemy["hp"] -= dmg
        print(f"   ⚡ Chain Lightning: {dmg} damage!")
    elif elem == "arcane":
        dmg = 30 * mult
        enemy["hp"] -= dmg
        debuffs = ["burn", "freeze", "shock", "poison"]
        enemy.setdefault("status", {})[random.choice(debuffs)] = 2
        print(f"   🔮 Arcane Bolt: {dmg} damage + random debuff!")

    elif elem == "crystal":
        dmg = 24 * mult
        enemy["hp"] -= dmg
        enemy["def"] = max(0, enemy.get("def", 0) - 3)
        print(f"   💎 Prism Lance: {dmg} damage + enemy DEF -3!")

    return True


# =========================
# QUEST SYSTEM
# =========================


def advance_quest(quest_type, region=None):
    completed_any = False
    for q in player.get("quests", []):
        if q.get("completed"):
            continue
        if q["type"] != quest_type:
            continue
        if q.get("region") and q["region"] != region:
            continue
        q["progress"] = q.get("progress", 0) + 1
        if q["progress"] >= q["target"]:
            q["completed"] = True
            completed_any = True
            souls = q.get("reward_souls", 0)
            item_name = q.get("reward_item")
            player["gold"] += souls
            print(f"\n🎯 QUEST COMPLETE: {q['desc']}")
            print(f"   Reward: {souls} souls", end="")
            if item_name and item_name in _FOOD_BY_NAME:
                fd = _FOOD_BY_NAME[item_name]
                player.setdefault("inventory", []).append({"name": item_name, "value": fd["value"]})
                print(f" + {item_name}", end="")
            print()
    return completed_any


def quest_board(region):
    active = [q for q in player.get("quests", []) if not q.get("completed")]
    done = [q for q in player.get("quests", []) if q.get("completed")]

    print("\n📋═══════════════════════════════📋")
    print("          QUEST BOARD")
    print("📋═══════════════════════════════📋")

    if done:
        print(f"  ✅ Completed quests: {len(done)}")

    if active:
        print(f"\n  Active quests ({len(active)}):")
        for q in active:
            print(f"  • {q['desc']}  [{q.get('progress', 0)}/{q['target']}]")

    if len(active) >= 3:
        print("\n  (Max 3 active quests — complete some first)")
        return

    # Generate new quests for this region
    import copy

    all_other_regions = [
        r for r in REGIONS if r != region and r in player.get("unlocked_regions", set())
    ]
    new_quests = []
    templates = QUEST_TEMPLATES[:]
    random.shuffle(templates)
    for tpl in templates[:4]:
        n = random.randint(*tpl["n_range"])
        if tpl["type"] == "reach_region" and not all_other_regions:
            continue
        target_region = random.choice(all_other_regions) if all_other_regions else region
        if tpl["type"] == "reach_region":
            desc = tpl["desc"].format(n=n, region=region, target_region=target_region)
            q = {
                "type": "reach_region",
                "desc": desc,
                "target": 1,
                "progress": 0,
                "region": target_region,
                "reward_souls": tpl["reward_souls"],
                "reward_item": tpl.get("reward_item"),
                "completed": False,
            }
        else:
            desc = tpl["desc"].format(n=n, region=region, target_region=target_region)
            q = {
                "type": tpl["type"],
                "desc": desc,
                "target": n,
                "progress": 0,
                "region": region,
                "reward_souls": tpl["reward_souls"],
                "reward_item": tpl.get("reward_item"),
                "completed": False,
            }
        new_quests.append(q)

    if not new_quests:
        print("\n  No new quests available right now.")
        return

    slots = 3 - len(active)
    print(f"\n  Available quests (can take {slots} more):")
    for i, q in enumerate(new_quests):
        print(
            f"  {i}. {q['desc']}  → {q['reward_souls']} souls"
            + (f" + {q['reward_item']}" if q.get("reward_item") else "")
        )
    print(f"  {len(new_quests)}. Leave board")

    try:
        c = int(input("> "))
    except ValueError:
        return
    if 0 <= c < len(new_quests) and slots > 0:
        player.setdefault("quests", []).append(new_quests[c])
        print(f"  📋 Quest accepted: {new_quests[c]['desc']}")


# =========================
# SKILL TREE
# =========================


def skill_tree():
    pts = player.get("skill_points", 0)
    owned = player.get("skills", [])
    cls = CLASSES.get(player.get("class_id") or "", {})

    print("\n🌟═══════════════════════════════🌟")
    print("          SKILL TREE")
    print("🌟═══════════════════════════════🌟")
    if cls:
        print(f"  Class: {cls['icon']} {cls['name']}  |  Passive: {cls['passive_desc']}")
    print(f"  Skill Points available: {pts}\n")

    available = {k: v for k, v in SKILLS.items() if k not in owned}
    if not available:
        print("  You've learned all available skills!")
        return

    skill_list = list(available.items())
    for i, (key, sk) in enumerate(skill_list):
        print(f"  {i}. {sk['name']}  ({sk['pts']} pt{'s' if sk['pts'] > 1 else ''}) — {sk['desc']}")

    print(f"\n  {len(skill_list)}. Cancel")
    if owned:
        print(f"\n  Already learned: {', '.join(SKILLS[k]['name'] for k in owned if k in SKILLS)}")

    try:
        c = int(input("> "))
    except ValueError:
        return
    if not (0 <= c < len(skill_list)):
        return

    key, sk = skill_list[c]
    cost = sk["pts"]
    if pts < cost:
        print(f"  Not enough skill points ({cost} needed, you have {pts}).")
        return

    player["skill_points"] = pts - cost
    player.setdefault("skills", []).append(key)
    print(f"  ✨ Learned {sk['name']}! ({player['skill_points']} points remaining)")

    # Apply immediate stat bonuses
    if key == "iron_skin":
        player["def"] += 4
        print(f"  DEF is now {player['def']}")
    elif key == "battle_hardened":
        player["max_hp"] += 20
        player["hp"] = min(player["hp"] + 20, player["max_hp"])
        print(f"  Max HP is now {player['max_hp']}")
    elif key == "swift_feet":
        player["speed"] += 8
        print(f"  Speed is now {player['speed']}")


def fight(enemy, boss=False):
    from expansion_hooks import scale_enemy
    enemy = scale_enemy(player, enemy)
    enemy = enemy.copy()
    enemy["boss"] = bool(boss)
    player.pop("_rune_previous", None)
    enemy.pop("_rune_previous", None)
    enemy.setdefault("status", {})
    enemy.setdefault("active_buffs", {})
    if not enemy.get("max_hp"):
        enemy["max_hp"] = enemy["hp"]

    # ── Feature 1: Apply World Event modifiers to enemy ──
    ev = get_current_world_event()
    enemy["hp"] = int(enemy["hp"] * ev["enemy_hp_mod"])
    enemy["max_hp"] = int(enemy["max_hp"] * ev["enemy_hp_mod"])
    enemy["atk"] = int(enemy["atk"] * ev["enemy_atk_mod"])
    if ev["enemy_hp_mod"] != 1.0 or ev["enemy_atk_mod"] != 1.0:
        print(f"  {ev['icon']} {ev['name']} — enemy modifiers active!")

    # ── Feature 7: Show active gear set bonus ──
    active_set = player.get("active_set")
    if active_set:
        print(f"  {GEAR_SETS[active_set]['icon']} Gear Set: {active_set} active!")

    ui = _ui.get_ui()
    if ui:
        ui.set_enemy(enemy)

    if boss and not enemy.get("_story_boss") and enemy.get("name") == "The Dreaming God":
        print(
            'THE DREAMSCAPE KING · The corrupted ruler returns. "Their sacrifice held me outside this world. Now the rift is open, and your world will dream as I command."'
        )
    print("⚔", enemy["name"])
    if enemy.get("evolution"):
        evolution = enemy["evolution"]
        print(f"Stage {evolution['stage']}/4 · Level {evolution['level']} · HP {enemy['hp']} · ATK {enemy['atk']} · DEF {enemy.get('def',0)}")

    for pet in player.get('companions', []):
        pet.pop('helped_this_battle', None)
    companion_move_used = False  # reset per fight
    player["resonance_streak"] = player.get("resonance_streak", 0)  # persist across turns

    while player["hp"] > 0 and enemy["hp"] > 0:
        process_buffs()
        apply_status(player)
        apply_status(enemy)
        from original_magic import turn as rune_turn

        if not rune_turn(player, enemy):
            player["active_buffs"]["stun"] = 1
        if player["hp"] <= 0 or enemy["hp"] <= 0:
            break
        if not rune_turn(enemy, player):
            enemy["active_buffs"]["stun"] = 1
        if player["hp"] <= 0 or enemy["hp"] <= 0:
            break

        # ── Setup (always done before stun check) ──
        cls = CLASSES.get(player.get("class_id") or "", {})
        cd = player.get("class_skill_cooldown", 0)
        if cd > 0:
            player["class_skill_cooldown"] = cd - 1
        companions = player.get("companions", [])
        wx = player.get("weather", "Clear")
        wx_data = WEATHER_EFFECTS.get(wx, WEATHER_EFFECTS["Clear"])

        # ── Player stun check (set by apply_status for freeze/sleep) ──
        if player["active_buffs"].pop("stun", None):
            print("  🛑 You cannot act this turn!")
            c = ""  # skip all player actions below
        else:
            skill_label = ""
            if cls:
                sn = cls["skill_name"]
                skill_label = f" | 5 {sn}" + (f" (CD {cd})" if cd > 0 else " (ready)")
            comp_label = " | 6 Companion" if companions else ""
            potion_label = (
                f" | 7 Potion({len(player.get('potions', []))})" if player.get("potions") else ""
            )
            night_str = " 🌙" if player.get("is_night") else ""
            print(f"{wx_data['icon']} {wx}{night_str}  |  {player['hp']} vs {enemy['hp']}")
            c = input(
                f"1 atk 2 scroll 3 staff 4 run{skill_label}{comp_label}{potion_label} | 8 Rune({len(player.get('runes',[]))}) | 9 Elemental art > "
            ).strip()

        if c == "9":
            from season_two import use_art

            if not use_art(player, enemy):
                continue

        if c == "4" and not boss:
            from original_magic import can_flee

            if can_flee(player):
                return
            print("This effect prevents fleeing.")
            continue

        if c == "7":
            potions = player.get("potions", [])
            if not potions:
                print("  No potions!")
                continue
            print("\n🧪 Potions:")
            for i, p in enumerate(potions):
                print(f"  {i}. {p}")
            try:
                pidx = int(input("  Use which? (-1 cancel) > "))
            except ValueError:
                continue
            if 0 <= pidx < len(potions):
                pname = potions.pop(pidx)
                print(f"  You drink the {pname}!")
                recipe = next(
                    (
                        r
                        for r in list(INGREDIENT_COMBOS.values()) + POTION_RECIPES
                        if r["name"] == pname
                    ),
                    None,
                )
                from food_addons import food_state
                if pname in food_state(player).get("blends",{}):
                    _apply_potion_effect("blend",pname)
                elif recipe:
                    _apply_potion_effect(recipe["effect"], pname)
                elif pname == "Health Potion":
                    player["hp"] = min(player["max_hp"], player["hp"] + 50)
                    print("  +50 HP!")
                elif pname == "Greater Elixir":
                    player["hp"] = min(player["max_hp"], player["hp"] + 120)
                    print("  +120 HP!")
                elif pname == "Antidote":
                    for s in ["poison", "burn"]:
                        player["status"].pop(s, None)
                    print("  Status effects cured!")
                elif pname == "Strength Draught":
                    boost = 10
                    player["atk"] += boost
                    player["potion_atk_boost"] = player.get("potion_atk_boost", 0) + boost
                    player["potion_atk_turns"] = 3
                    print("  +10 ATK for 3 turns!")
                elif pname == "Elixir of Fortune":
                    player["luck_boost_explores"] = 5
                    print("  +20% loot quality for next 5 explores!")
            continue

        if c == "1":
            dmg = calculate_damage(player, enemy, "weapon")

            # ── Feature 4: Soul Resonance burst ──
            resonance_mult = consume_resonance()
            if resonance_mult > 1.0:
                dmg = int(dmg * resonance_mult)

            # ── Feature 2: Bestiary weakness bonus ──
            bestiary_mult = bestiary_bonus_for(enemy["name"])
            if bestiary_mult > 1.0:
                dmg = int(dmg * bestiary_mult)
                print(f"  📖 Bestiary weakness! x{bestiary_mult}")

            # ── Feature 7: Gear Set ATK bonus ──
            set_bonus = get_set_atk_bonus()
            if set_bonus > 0:
                dmg += set_bonus
                # Death's Herald: every 4th hit is guaranteed crit
                if player.get("active_set") == "Death's Herald":
                    player["set_crit_counter"] = player.get("set_crit_counter", 0) + 1
                    if player["set_crit_counter"] % 4 == 0:
                        dmg *= 2
                        print(f"  💀 Death's Herald: guaranteed crit!")

            # ── Cursed weapon self-damage ─��
            cur_weapon = player.get("weapon")
            if cur_weapon and cur_weapon.get("cursed"):
                self_dmg = 5
                player["hp"] = max(1, player["hp"] - self_dmg)
                print(f"☠ Cursed weapon bites back! -{self_dmg} HP to you!")

            # ── Weather damage modifier ──
            wx_mod = wx_data.get("player_dmg_mod", 1.0)
            if player.get("is_night"):
                wx_mod *= 1.0
            if wx_mod != 1.0:
                dmg = int(dmg * wx_mod)

            # ── Class crit passive ──
            crit_chance = 0.0
            passive = cls.get("passive", "")
            if passive == "crit":
                crit_chance += 0.15
            if "assassin" in player.get("skills", []):
                crit_chance += 0.10
            if crit_chance > 0 and random.random() < crit_chance:
                dmg *= 2
                print(f"💥 CRITICAL HIT! ({int(crit_chance * 100)}% chance)")

            # ── Berserk skill passive ──
            if "berserk" in player.get("skills", []) and player["hp"] < player["max_hp"] * 0.30:
                dmg = int(dmg * 1.5)
                print("🔴 Berserk! Low HP fury — damage x1.5!")

            from original_magic import strike

            dmg = strike(player, enemy, dmg)

            # ── Lifesteal (necromancer passive or vampiric_strike skill) ──
            lifesteal_pct = 0.0
            if passive == "lifesteal":
                lifesteal_pct += 0.20
            if "vampiric_strike" in player.get("skills", []):
                lifesteal_pct += 0.15
            from expansion_state import state as expansion_state
            lifesteal_pct += expansion_state(player).get('systems',{}).get('equipment_collection_bonus',{}).get('lifesteal',0)
            if lifesteal_pct > 0:
                heal = max(1, int(dmg * lifesteal_pct))
                player["hp"] = min(player["max_hp"], player["hp"] + heal)
                print(f"🩸 Drained {heal} HP!")

            _apply_charged_weapon_effect(enemy)

            if player["active_buffs"].get("double_cast"):
                print("✨ Double Cast doubles your strike!")
                enemy["hp"] -= dmg

            # ── Arcane Surge (mage skill buff) ──
            if player["active_buffs"].get("arcane_surge"):
                print("🔮 Arcane Surge fires again!")
                enemy["hp"] -= dmg
                player["active_buffs"].pop("arcane_surge", None)

            # ── Ranger shot passive ──
            if passive == "ranger_shot" and random.random() < 0.25:
                shot = 4 + min(11, player.get("level", 1))
                enemy["hp"] -= shot
                print(f"🏹 Ranger free shot! {shot} bonus damage!")

            bound = player.get("weapon", {}).get("rune") if player.get("weapon") else None
            if bound:
                apply_rune_effect(bound, player, enemy)
                print(f"The permanent {bound['name']} activates.")

            apply_companion_support(enemy)

        elif c == "2":
            use_scroll()

        elif c == "3":
            use_staff(enemy)

            apply_companion_support(enemy)

        elif c == "8":
            if not use_combat_rune(enemy):
                continue

        elif c == "5" and cls:
            if player.get("class_skill_cooldown", 0) > 0:
                print(
                    f"⏳ {cls['skill_name']} is on cooldown ({player['class_skill_cooldown']} turns)."
                )
            else:
                _use_class_skill(cls, enemy)
                player["class_skill_cooldown"] = cls.get("skill_cd", 3)

        elif c == "6" and companions:
            if companion_move_used:
                print("🐾 Companions already acted this fight.")
            else:
                if not _use_companion_move(companions, enemy):
                    continue
                companion_move_used = True

        if enemy["hp"] <= 0:
            break

        if enemy["active_buffs"].get("stun"):
            print("🛑 Enemy is stunned and cannot attack!")
            enemy["active_buffs"].pop("stun", None)
            enemy_dmg = 0
        else:
            from monster_evolution import attack_range
            base_enemy_dmg = random.randint(*attack_range(enemy))
            armour_def = (
                player.get("armour", {}) and player["armour"].get("def", 0)
                if player.get("armour")
                else 0
            )
            base_enemy_dmg = max(1, base_enemy_dmg - player.get("def", 0) // 3 - armour_def // 4)
            enemy_dmg = base_enemy_dmg
            if player["active_buffs"].get("warp"):
                print("✨ You warp away the attack!")
                enemy_dmg = 0
            if enemy["active_buffs"].get("blind"):
                if random.random() < 0.35:
                    print("✨ Enemy misses due to blind!")
                    enemy_dmg = 0
            from original_magic import proxy
            from effects import stat

            dodge_chance = min(stat(proxy(player), "speed") * 0.005, 0.40)
            if enemy_dmg > 0 and random.random() < dodge_chance:
                print(
                    f"💨 You dodge the attack! (speed {player.get('speed', 5)}, {int(dodge_chance * 100)}% chance)"
                )
                enemy_dmg = 0
            if player["active_buffs"].get("moon_guard"):
                enemy_dmg = max(0, enemy_dmg - 4)
            if player["active_buffs"].get("fortress"):
                enemy_dmg = max(0, enemy_dmg - 3)
            if player["active_buffs"].get("stability"):
                enemy_dmg = max(0, enemy_dmg - 2)
            if enemy["active_buffs"].get("root"):
                enemy_dmg = max(1, enemy_dmg - 3)
            if enemy["active_buffs"].get("slow_time"):
                enemy_dmg = max(1, enemy_dmg - 3)

            if player["active_buffs"].get("reflect") and enemy_dmg > 0:
                print("✨ Reflect sends damage back to the enemy!")
                enemy["hp"] -= enemy_dmg

            if player["active_buffs"].get("thorns") and enemy_dmg > 0:
                thorn_dmg = max(1, enemy_dmg // 3)
                enemy["hp"] -= thorn_dmg
                print(f"🌵 Thorns reflects {thorn_dmg} damage!")

            if player["active_buffs"].get("wraith_form"):
                print("👻 Wraith Form: Attack passes through you!")
                enemy_dmg = 0
                player["active_buffs"]["wraith_form"] -= 1
                if player["active_buffs"]["wraith_form"] <= 0:
                    player["active_buffs"].pop("wraith_form", None)

        # ── Resilience skill (flat damage reduction) ──
        if "resilience" in player.get("skills", []) and enemy_dmg > 0:
            reduction = max(1, int(enemy_dmg * 0.10))
            enemy_dmg = max(0, enemy_dmg - reduction)

        if enemy_dmg > 0:
            from original_magic import strike, damage as rune_damage

            enemy_dmg = strike(enemy, player, rune_damage(enemy, player, enemy_dmg))

        # ── Feature 4: Update Soul Resonance streak ──
        update_resonance(enemy_dmg > 0)

        # ── Warrior counter-attack passive ──
        if enemy_dmg > 0 and cls.get("passive") == "counter" and random.random() < 0.15:
            counter_dmg = max(1, int(calculate_damage(player, enemy, "weapon") * 0.5))
            enemy["hp"] -= counter_dmg
            print(f"⚔ Counter-attack! {counter_dmg} damage back!")

        if player["hp"] <= 0 and player["active_buffs"].get("rebirth"):
            player["hp"] = max(1, player["max_hp"] // 2)
            player["active_buffs"].pop("rebirth", None)
            print("✨ Rebirth activated! You return to half health.")

    if player["hp"] > 0:
        from expansion_hooks import finish_battle
        finish_battle(player, True)
        # ── Feature 2: Bestiary kill tracking ──
        record_kill(enemy["name"])
        # ── Feature 10: Companion XP ──
        award_companion_xp(10 if boss else 5)
        from companion_care import battle_credit

        battle_credit(player, 10 if boss else 5)
        if enemy.get("_story_boss"):
            from source_story import victory

            victory(player)
            gain_xp(150)
            player["gold"] += 150
            if _ui.get_ui():
                _ui.get_ui().clear_enemy()
            return
        if boss:
            advance_quest("boss_kill", player["region"])
            print(f"You defeated the boss of {player['region']}!")
            if player.get("secret_gate_ready", False):
                unlock_secret_region()
            if player["region"] == SECRET_REGION:
                print("🏆 You have conquered the hidden Creator's Realm!")
                gain_xp(200)
                player["gold"] += 200
                drop_loot()
                drop_loot()
                drop_loot()
            else:
                region_order = [
                    "Whispering Woods",
                    "Ashen Wastes",
                    "Crimson Depths",
                    "Frostbound Tundra",
                    "Crystal Spire",
                    "Sunken Coast",
                    "Ironpeak Mountains",
                    "Blight Swamp",
                    "Shattered Wastes",
                    "Shadow Vale",
                    "Infernal Depths",
                    "Celestial Expanse",
                    "Riftlands",
                    "Abyss of Souls",
                    "The Dreamscape",
                ]
                try:
                    current_index = region_order.index(player["region"])
                except ValueError:
                    current_index = -1
                if current_index >= 0 and current_index < len(region_order) - 1:
                    next_region = region_order[current_index + 1]
                    player["unlocked_regions"].add(next_region)
                    print(f"🌍 {next_region} has been unlocked!")
                if player["region"] not in player.setdefault("bosses_defeated", []):
                    player["bosses_defeated"].append(player["region"])
                update_challenge_progress("boss_kill")
                update_challenge_progress("region_boss_clear", player["region"])
                if player["region"] == "The Dreamscape" and all(
                    r in player["unlocked_regions"] for r in REGIONS
                ):
                    from source_story import season_one_ending

                    season_one_ending(player)
                gain_xp(100)
                player["gold"] += 100
                drop_loot()
                drop_loot()
                drop_loot()
                drop_loot()
                item = random.choice(BOSS_DROPS[player["region"]])
                print(f"Special Boss Drop: {item} this can be used in the crimson realm's forge")
                player["forge_cores"].append(item)
                ui = _ui.get_ui()
                if ui:
                    ui.show_boss_drop_popup(item, player["region"])
        else:
            print("yay u won")
            rewards = enemy.get("evolution_rewards", {})
            xp_gain = rewards.get("xp", 20)
            gold_gain = rewards.get("gold", 20)
            if "soul_harvest" in player.get("skills", []):
                xp_gain = int(xp_gain * 1.5)
            if "dungeon_delver" in player.get("skills", []):
                gold_gain = int(gold_gain * 1.3)
            # ── Feature 1: World Event XP/gold multipliers ──
            ev = get_current_world_event()
            xp_gain = int(xp_gain * ev["xp_mod"])
            gold_gain = int(gold_gain * ev["gold_mod"])
            # ── Feature 5: Elite monster bonus loot ──
            if enemy.get("_elite"):
                gold_gain *= 2
                print(f"  ★ Elite defeated! Double gold reward!")
                drop_loot()
            gain_xp(xp_gain)
            player["gold"] += gold_gain
            advance_quest("kill_enemies", player["region"])
            drop_loot()
    # FIX: death message moved to outer else so it actually triggers when player dies
    else:
        print("Your character has fallen.")
        raise _ui.RunEnded()

    ui = _ui.get_ui()
    if ui:
        ui.clear_enemy()


# =========================
# LOOT
# =========================


def regional_loot(region):
    """Common trinkets plus finds native to this region; never the global rare pool."""
    return [item for item in LOOT_ITEMS if not item.get("regions") or region in item["regions"]]


def drop_loot():
    luck_bonus = 10 if player["active_buffs"].get("divine_luck") else 0
    roll = min(100, random.randint(1, 100) + luck_bonus)
    ui = _ui.get_ui()

    if roll <= 60:
        item = random.choice(regional_loot(player["region"])).copy()
        player["inventory"].append(item)
        print(f"\n📦 Loot Found: {item['name']}")
        if ui:
            ui.show_loot_popup(item["name"], player["region"])
    elif roll <= 65:
        if player["level"] < 5:
            pool = [a for a in ARMOURS if a["tier"] == "basic"]
        elif player["level"] < 10:
            pool = [a for a in ARMOURS if a["tier"] == "mid"]
        elif player["level"] < 15:
            pool = [a for a in ARMOURS if a["tier"] in ["mid", "high"]]
        else:
            pool = [a for a in ARMOURS if a["tier"] in ["high", "legendary"]]
        item = random.choice(pool).copy()
        player["armours"].append(item)
        print(f"🛡 Armour Found: {item['name']} (DEF {item['def']})")
        if ui:
            ui.show_loot_popup(f"🛡 {item['name']}", player["region"])
    elif roll <= 75:
        if player["level"] < 5:
            pool = [w for w in WEAPONS if w["tier"] == "basic"]
        elif player["level"] < 10:
            pool = [w for w in WEAPONS if w["tier"] == "mid"]
        elif player["level"] < 15:
            pool = [w for w in WEAPONS if w["tier"] in ["mid", "high"]]
        else:
            pool = [w for w in WEAPONS if w["tier"] in ["high", "legendary"]]
        item = random.choice(pool)
        player["weapons"].append(item)
        print(f"⚔ Weapon Found: {item['name']}")
        if ui:
            ui.show_loot_popup(f"⚔ {item['name']}", player["region"])
    elif roll <= 90:
        item = random.choice(SCROLLS)
        player["inventory"].append(item)
        print(f"\n📜 Scroll Found: {item['name']}")
        if ui:
            ui.show_loot_popup(f"📜 {item['name']}", player["region"])
    elif roll <= 97:
        pool = [r for r in RUNES if is_region_rune(r, player["region"])] or RUNES
        item = random.choice(pool).copy()
        player["runes"].append(item)
        print(f"\n🔮 Rune Found: {item['name']}")
        if ui:
            ui.show_loot_popup(f"🔮 {item['name']}", player["region"])
    else:
        pool = [s for s in STAFFS if is_region_staff(s, player["region"])] or STAFFS
        item = random.choice(pool).copy()
        player["staffs"].append(item)
        print(f"\n✨ Staff Found: {item['name']}")
        if ui:
            ui.show_loot_popup(f"✨ {item['name']}", player["region"])


# =========================
# EXPLORATION
# =========================


def _check_achievements():
    """Check all achievements and award new ones."""
    earned = player.setdefault("achievements", [])
    for ach in ACHIEVEMENTS.values():
        if ach.get("id", ach["name"]) in earned:
            continue
        if "type" not in ach:
            continue
        t = ach["type"]
        threshold = ach["threshold"]
        unlocked = False
        if t == "wander_count" and player.get("wander_count", 0) >= threshold:
            unlocked = True
        elif t == "unlocked_count" and len(player.get("unlocked_regions", set())) >= threshold:
            unlocked = True
        elif t == "boss_count" and len(player.get("bosses_defeated", [])) >= threshold:
            unlocked = True
        elif t == "gold" and player.get("gold", 0) >= threshold:
            unlocked = True
        elif t == "level" and player.get("level", 1) >= threshold:
            unlocked = True
        elif t == "weapon_count" and len(player.get("weapons", [])) >= threshold:
            unlocked = True
        elif t == "struct_count":
            total = sum(len(v) for v in player.get("discovered_structures", {}).values())
            if total >= threshold:
                unlocked = True
        elif t == "core_count" and len(player.get("elemental_cores", [])) >= threshold:
            unlocked = True
        elif t == "skill_count" and len(player.get("skills", [])) >= threshold:
            unlocked = True

        if unlocked:
            earned.append(ach.get("id", ach["name"]))
            title = ACHIEVEMENT_TITLES.get(ach.get("id", ach["name"]))
            print(
                f"\n🏆 ACHIEVEMENT UNLOCKED: {ach['name']} — {ach.get('desc', ach.get('description', ''))}"
            )
            if title:
                player["title"] = title
                print(f"   🎖 Title earned: [{title}]")


def _show_achievements():
    """Display all achievements and player title."""
    print("\n🏆 ═══════ ACHIEVEMENTS ═══════ 🏆")
    title = player.get("title")
    if title:
        print(f"  🎖 Current Title: [{title}]")
    earned = player.get("achievements", [])
    for ach in ACHIEVEMENTS.values():
        status = "✅" if ach.get("id", ach["name"]) in earned else "⬜"
        print(f"  {status} {ach['name']}  — {ach.get('desc', ach.get('description', ''))}")
    print(f"\n  Progress: {len(earned)}/{len(ACHIEVEMENTS)} achievements")
    n_bounties = len(player.get("bounties_claimed", []))
    print(f"  Bounties claimed: {n_bounties}")
    lk = player.get("luck", 0)
    if lk > 0:
        print(f"  Luck: +{lk} (from helping travellers & blessings)")
    print()


def _handle_wander_event(event_id, region):
    """Handle a random wander event."""
    if event_id == "wandering_merchant":
        from expansion_state import state as expansion_state
        if expansion_state(player).get('systems',{}).get('mode',{}).get('id')=='budget_run':
            print('Budget Run: you pass the merchant without buying.')
            return
        print("\n🛒 The merchant spreads out a small collection of goods.")
        pool = MERCHANT_ITEMS.get(region, [])
        if not pool:
            print("  They have nothing of interest today.")
            return
        items_shown = random.sample(pool, min(3, len(pool)))
        all_gear = {
            **{w["name"]: w for w in WEAPONS},
            **{a["name"]: a for a in ARMOURS},
            **{r["name"]: r for r in RUNES},
            **{s["name"]: s for s in STAFFS},
        }
        for i, name in enumerate(items_shown):
            g = all_gear.get(name)
            if g:
                price = int(g.get("atk", g.get("def", g.get("power", 10))) * 6)
                print(f"  {i}. {name}  — {price} souls")
        try:
            c = int(input("  Buy which? (-1 to pass) > "))
        except ValueError:
            return
        if 0 <= c < len(items_shown):
            name = items_shown[c]
            g = all_gear.get(name)
            if g:
                price = int(g.get("atk", g.get("def", g.get("power", 10))) * 6)
                if player["gold"] >= price:
                    player["gold"] -= price
                    if "atk" in g:
                        player.setdefault("weapons", []).append(g.copy())
                    elif "def" in g:
                        player.setdefault("armours", []).append(g.copy())
                    elif "effect" in g:
                        player.setdefault("runes", []).append(g.copy())
                    else:
                        player.setdefault("staffs", []).append(g.copy())
                    print(f"  Bought {name}.")
                else:
                    print("  Not enough souls.")

    elif event_id == "mysterious_altar":
        print("\n🗿 The altar hums with power. You sense three possible gifts...")
        options = ["Restore 30 HP", "Gain 100 souls", "Gain 1 Skill Point"]
        for i, o in enumerate(options):
            print(f"  {i + 1}. {o}")
        try:
            c = int(input("  Choose your boon (1-3) > "))
        except ValueError:
            return
        if c == 1:
            player["hp"] = min(player["max_hp"], player["hp"] + 30)
            print("  The altar mends your wounds. +30 HP.")
        elif c == 2:
            player["gold"] += 100
            print("  Coins materialise in your hand. +100 souls.")
        elif c == 3:
            player["skill_points"] = player.get("skill_points", 0) + 1
            print("  Knowledge floods your mind. +1 Skill Point.")

    elif event_id == "lucky_cache":
        gold_found = random.randint(50, 200)
        player["gold"] += gold_found
        print(f"\n💰 You found {gold_found} souls in the satchel!")
        if random.random() < 0.4:
            drop_loot()

    elif event_id == "cursed_chest":
        print("\n⚠  The chest rattles as you approach.")
        choice = input("  Open it? This might be dangerous. (y/n) > ").lower()
        if choice == "y":
            roll = random.randint(1, 3)
            if roll == 1:
                dmg = random.randint(20, 50)
                player["hp"] = max(1, player["hp"] - dmg)
                print(f"  A trap! You take {dmg} damage from the curse!")
            elif roll == 2:
                drop_loot()
                drop_loot()
                print("  Riches spill out! You grab the loot.")
            else:
                print("  The chest was empty. The runes fade silently.")
        else:
            print("  You back away cautiously.")

    elif event_id == "bandit_ambush":
        bandit = {
            "name": "Road Bandit",
            "hp": 40 + player["level"] * 5,
            "atk": 10 + player["level"] * 2,
            "def": 3 + player["level"],
        }
        print(f"\n🗡 Road Bandit springs from the shadows!")
        fight(bandit)
        if player["hp"] > 0:
            bonus = random.randint(40, 120)
            player["gold"] += bonus
            print(f"  You search the body — found {bonus} souls.")

    elif event_id == "wounded_traveller":
        print("\n💬 The traveller is badly hurt. You can:")
        print("  1. Help them (lose 20 souls, gain +15 HP and good karma)")
        print("  2. Leave them")
        choice = input("  > ").strip()
        if choice == "1":
            if player["gold"] >= 20:
                player["gold"] -= 20
                player["hp"] = min(player["max_hp"], player["hp"] + 15)
                player["luck"] = player.get("luck", 0) + 1
                print("  They bless you for your kindness. +15 HP, +1 Luck.")
            else:
                print("  You don't have enough souls to spare...")
        else:
            print("  You walk on, trying not to think about it.")


def regenerate_from_full_hunger():
    """One small recovery before a wander spends hunger; never revive a dead run."""
    if player.get("hunger", 100) < 100 or player["hp"] <= 0:
        return 0
    recovered = max(0, min(3, player["max_hp"] - player["hp"]))
    if recovered:
        player["hp"] += recovered
        print(f"🍎 Full hunger: you recover {recovered} HP before continuing your journey.")
    return recovered


def explore():
    from wander_reference import WEATHER_RESELECT
    r = player["region"]

    # ── Day / Night cycle (every 7 wanders = night for 3 wanders) ──
    wc = player.get("wander_count", 0)
    cycle_pos = wc % 10
    was_night = player.get("is_night", False)
    player["is_night"] = cycle_pos >= 7
    if player["is_night"] and not was_night:
        print("\n🌙 Night falls. Enemies grow stronger, but rewards improve...")
    elif not player["is_night"] and was_night:
        print("\n☀  Dawn breaks. The land feels safer.")

    night = player["is_night"]

    # ── Weather update (20% chance to change each explore) ──
    weather_keys = list(WEATHER_EFFECTS.keys())
    if random.random() < WEATHER_RESELECT:
        player["weather"] = random.choice(weather_keys)
    wx = player.get("weather", "Clear")
    wx_data = WEATHER_EFFECTS[wx]
    print(f"\n🌍 Exploring {r}...  {wx_data['icon']} {wx} — {wx_data['desc']}")
    if night:
        print("   🌙 Night — enemies are +15% stronger, loot is better.")

    player["wander_count"] = player.get("wander_count", 0) + 1
    from companion_care import wander as companion_hunger

    companion_hunger(player)
    from village_jobs import advance_all
    advance_all(player)
    from expansion_hooks import on_wander
    on_wander(__import__(__name__))

    from source_story import anomaly

    anomaly(__import__(__name__))

    if player["wander_count"] % 20 == 0:
        advance_world_event()

    # ── Potion ATK boost decay ──
    if player.get("potion_atk_turns", 0) > 0:
        player["potion_atk_turns"] -= 1
        if player["potion_atk_turns"] == 0:
            player["atk"] = max(0, player["atk"] - player.get("potion_atk_boost", 0))
            player["potion_atk_boost"] = 0
            print("  (Strength Draught has worn off.)")

    # ── Luck boost decay ──
    if player.get("luck_boost_explores", 0) > 0:
        player["luck_boost_explores"] -= 1

    regenerate_from_full_hunger()

    # ── Hunger decreases each wander ──
    drain = 1 if "hunger_resist" in player.get("skills", []) else 5
    player["hunger"] = max(0, player.get("hunger", 100) - drain)
    h = player["hunger"]
    if h <= 0:
        dmg = 10
        player["hp"] = max(0, player["hp"] - dmg)
        if player["hp"] <= 0:
            raise _ui.RunEnded()
        print(f"🍖 You are STARVING! You take {dmg} damage. Find a village and eat!")
    elif h < 30:
        print(f"🍖 You are hungry ({h}/100). Find a village before you weaken further.")

    from expedition import before_wander
    if before_wander(__import__(__name__)):
        return

    from wander_roll import resolve
    resolve(__import__(__name__))



def _wander_monster(r, night):
    from wander_reference import NIGHT_ELITE
    from monster_evolution import pool
    enemy_pool = pool(r, player["level"])
    if not enemy_pool:
        print("No creatures inhabit this path.")
        return
    from copy import deepcopy

    enemy = deepcopy(random.choice(enemy_pool))
    if night:
        enemy["hp"] = int(enemy["hp"] * 1.15)
        enemy["max_hp"] = enemy["hp"]
        enemy["atk"] = int(enemy["atk"] * 1.15)
        if random.random() < NIGHT_ELITE:
            enemy = make_elite(enemy)
            print(f"\n★ AN ELITE MONSTER APPEARS! {enemy['name']} — beware!")
        if r in _DARK_REGIONS:
            add_corruption(5)
    fight(enemy)
    _check_achievements()


# =========================
# TRAVEL
# =========================


def travel():
    print("\n=== TRAVEL ===")
    print("Current region: " + player["region"])
    ordered = get_ordered_unlocked_regions()
    for i, region in enumerate(ordered, 1):
        print(f"{i}. {region}")
    print(
        "F. Crimson Forge" + ("" if "Crimson Depths" in player["unlocked_regions"] else " [locked]")
    )
    print("0. Back")
    choice = input("Destination > ").strip().lower()
    if choice == "0":
        return
    if choice == "f":
        if "Crimson Depths" not in player["unlocked_regions"]:
            print("Crimson Depths is still locked.")
            return
        region = "Crimson Depths"
    else:
        try:
            index = int(choice) - 1
        except ValueError:
            print("Choose a listed destination.")
            return
        if not 0 <= index < len(ordered):
            print("Choose a listed destination.")
            return
        region = ordered[index]
    player["region"] = region
    player["current_location"] = region
    from expansion_state import state as expansion_state
    if expansion_state(player).get("systems", {}).get("mount"):
        player["hunger"] = min(100, player.get("hunger",100)+2)
    print("Travelled to " + region)
    advance_quest("reach_region", region)
    if choice == "f":
        crimson_forge()


# =========================
# STRUCTURES
# =========================

_FOOD_BY_NAME = {f["name"]: f for f in FOOD_ITEMS}


def _eat_food():
    """Let the player eat food from inventory to restore hunger."""
    from food_addons import is_food, catalog
    foods = [i for i in player.get("inventory", []) if is_food(i) or i.get("name") in _FOOD_BY_NAME]
    if not foods:
        print("  (You have no food in your inventory.)")
        return
    print("\n🍖 Your food:")
    for idx, item in enumerate(foods):
        fd = _FOOD_BY_NAME.get(item["name"], catalog(item))
        print(f"  {idx}. {item['name']}  (+{fd['hunger']} hunger)")
    try:
        c = int(input("  Eat which? (-1 to cancel) > "))
    except ValueError:
        return
    if 0 <= c < len(foods):
        chosen = foods[c]
        fd = _FOOD_BY_NAME.get(chosen["name"], catalog(chosen))
        player["hunger"] = min(100, player.get("hunger", 100) + fd["hunger"])
        player["hp"] = min(player["max_hp"], player["hp"]+fd.get("also_heal",0))
        player["inventory"].remove(chosen)
        print(f"  You eat the {chosen['name']}. Hunger: {player['hunger']}/100")


def _apply_potion_effect(effect, name):
    from food_addons import toxicity, food_state
    toxicity(player)
    if effect=='blend':
        blend=food_state(player).get('blends',{}).get(name)
        if blend:
            amount=max(0,min(120,blend.get('heal',0)))
            player['hp']=min(player['max_hp'],player['hp']+amount)
            print(f'The blended potion restores up to {amount} HP.')
        return
    if player.get('faction')=='light_clergy' and effect.startswith('heal_') and effect[5:].isdigit():
        player['hp']=min(player['max_hp'],player['hp']+int(effect[5:])//4)
    for status in {'Frost Tonic':['freeze'],'Stone Balm':['bleed'],'Dream Tonic':['sleep','fear']}.get(name,[]):
        player.setdefault('status',{}).pop(status,None)
        player.setdefault('rune_status',{}).pop(status,None)
    if effect == "heal_20":
        player["hp"] = min(player["max_hp"], player["hp"] + 20)
        print(f"  ✨ +20 HP!")
    elif effect == "heal_25":
        player["hp"] = min(player["max_hp"], player["hp"] + 25)
        print(f"  ✨ +25 HP!")
    elif effect == "heal_30":
        player["hp"] = min(player["max_hp"], player["hp"] + 30)
        print(f"  ✨ +30 HP!")
    elif effect == "heal_35":
        player["hp"] = min(player["max_hp"], player["hp"] + 35)
        print(f"  ✨ +35 HP!")
    elif effect == "heal_40":
        player["hp"] = min(player["max_hp"], player["hp"] + 40)
        print(f"  ✨ +40 HP!")
    elif effect == "heal_50":
        player["hp"] = min(player["max_hp"], player["hp"] + 50)
        print(f"  ✨ +50 HP!")
    elif effect == "heal_60":
        player["hp"] = min(player["max_hp"], player["hp"] + 60)
        print(f"  ✨ +60 HP!")
    elif effect == "heal_70_atk_10":
        player["hp"] = min(player["max_hp"], player["hp"] + 70)
        player["atk"] += 10
        player["potion_atk_boost"] = player.get("potion_atk_boost", 0) + 10
        player["potion_atk_turns"] = 2
        print(f"  ✨ +70 HP and +10 ATK for 2 fights!")
    elif effect == "heal_80":
        player["hp"] = min(player["max_hp"], player["hp"] + 80)
        print(f"  ✨ +80 HP!")
    elif effect == "heal_80_cost10":
        if player["hp"] > 10:
            player["hp"] = min(player["max_hp"], player["hp"] - 10 + 80)
            print(f"  ✨ +70 net HP (cost 10, gained 80)!")
        else:
            print("  ☠ Too risky to drink — not enough HP.")
            return
    elif effect == "heal_100":
        player["hp"] = min(player["max_hp"], player["hp"] + 100)
        print(f"  ✨ +100 HP!")
    elif effect == "def_boost_10":
        player["atk"] = player.get("atk", 0)
        player["def"] = player.get("def", 0) + 10
        player["potion_def_boost"] = player.get("potion_def_boost", 0) + 10
        player["potion_def_turns"] = 3
        print(f"  🛡 +10 DEF for 3 fights!")
    elif effect == "def_boost_12":
        player["def"] = player.get("def", 0) + 12
        player["potion_def_boost"] = player.get("potion_def_boost", 0) + 12
        player["potion_def_turns"] = 3
        print(f"  🛡 +12 DEF for 3 fights!")
    elif effect == "def_boost_15":
        player["def"] = player.get("def", 0) + 15
        player["potion_def_boost"] = player.get("potion_def_boost", 0) + 15
        player["potion_def_turns"] = 3
        print(f"  🛡 +15 DEF for 3 fights!")
    elif effect == "atk_boost_10":
        player["atk"] = player.get("atk", 0) + 10
        player["potion_atk_boost"] = player.get("potion_atk_boost", 0) + 10
        player["potion_atk_turns"] = 3
        print(f"  ⚔ +10 ATK for 3 fights!")
    elif effect == "atk_boost_15":
        player["atk"] = player.get("atk", 0) + 15
        player["potion_atk_boost"] = player.get("potion_atk_boost", 0) + 15
        player["potion_atk_turns"] = 3
        print(f"  ⚔ +15 ATK for 3 fights!")
    elif effect == "atk_boost_20":
        player["atk"] = player.get("atk", 0) + 20
        player["potion_atk_boost"] = player.get("potion_atk_boost", 0) + 20
        player["potion_atk_turns"] = 3
        print(f"  ⚔ +20 ATK for 3 fights!")
    elif effect == "atk_boost_25":
        player["atk"] = player.get("atk", 0) + 25
        player["potion_atk_boost"] = player.get("potion_atk_boost", 0) + 25
        player["potion_atk_turns"] = 4
        print(f"  ⚔ +25 ATK for 4 fights!")
    elif effect == "cure_status":
        player.setdefault("rune_status", {}).clear()
        player.setdefault("status", {}).clear()
        print(f"  💊 All status effects cured!")
    elif effect == "cure_void":
        for s in ["void", "curse"]:
            player.setdefault("status", {}).pop(s, None)
        print(f"  💊 Void and curse lifted!")
    elif effect == "luck_boost":
        player["luck_boost_explores"] = player.get("luck_boost_explores", 0) + 5
        print(f"  🍀 +25% loot quality for 5 explores!")
    elif effect == "mana_full":
        player["mana"] = max(player.get("mana", 0), 50)
        print(f"  ✨ Mana fully restored!")
    elif effect == "skip_fight":
        player["skip_next_fight"] = True
        print(f"  💤 Your next enemy will be asleep — skip one fight!")
    elif effect == "genesis":
        player["hp"] = player["max_hp"]
        player["mana"] = max(player.get("mana", 0), 50)
        print(f"  🌟 HP and MP fully restored!")
    elif effect == "random_wild":
        roll = random.randint(1, 6)
        if roll <= 2:
            player["hp"] = min(player["max_hp"], player["hp"] + 60)
            print(f"  ✨ Wild luck! +60 HP!")
        elif roll <= 4:
            player["atk"] = player.get("atk", 0) + 15
            player["potion_atk_boost"] = player.get("potion_atk_boost", 0) + 15
            player["potion_atk_turns"] = 3
            print(f"  ✨ Wild surge! +15 ATK for 3 fights!")
        else:
            dmg = random.randint(10, 25)
            player["hp"] = max(1, player["hp"] - dmg)
            print(f"  💀 Wild misfire! You take {dmg} damage!")
    elif effect == "random_bad":
        dmg = random.randint(5, 20)
        player["hp"] = max(1, player["hp"] - dmg)
        player.setdefault("status", {})["poison"] = player["status"].get("poison", 0) + 3
        print(f"  ☠ The brew was vile! -{dmg} HP and poisoned!")


def _ingredient_brew_menu():
    from village_life import require_service, quality

    if not require_service("alchemy"):
        return
    print("\n🧪═══════════════════════════════🧪")
    print("   VILLAGE WORKBENCH — Ingredient Brewing")
    print("🧪═══════════════════════════════🧪")
    ings = player.get("ingredients", [])
    if not ings:
        print("  You have no ingredients. Wander regions to gather them (8% chance each explore).")
        return

    print(f"\n  Your ingredient pouch ({len(ings)} total):")
    unique_ings = sorted(set(ings))
    for i, ing in enumerate(unique_ings):
        count = ings.count(ing)
        print(f"    {i}. {ing}  x{count}")

    print("\n  Pick TWO ingredients to mix, or 'c' to cancel.")
    try:
        a_in = input("  First ingredient # > ").strip()
        if a_in.lower() == "c":
            return
        a_idx = int(a_in)
        b_in = input("  Second ingredient # > ").strip()
        if b_in.lower() == "c":
            return
        b_idx = int(b_in)
    except (ValueError, IndexError):
        print("  Invalid choice.")
        return

    if a_idx == b_idx:
        # Check they have 2 of this ingredient
        if not 0 <= a_idx < len(unique_ings):
            print("Invalid selection.")
            return
        ing_a = unique_ings[a_idx]
        if ings.count(ing_a) < 2:
            print(f"  You only have 1 {ing_a}. You need 2 to mix the same ingredient.")
            return
        ing_b = ing_a
    else:
        if not (0 <= a_idx < len(unique_ings) and 0 <= b_idx < len(unique_ings)):
            print("  Invalid selection.")
            return
        ing_a = unique_ings[a_idx]
        ing_b = unique_ings[b_idx]

    combo_key = frozenset([ing_a, ing_b])
    from food_addons import brew_recipe
    result = brew_recipe(player, ing_a, ing_b)

    # Remove ingredients from player pouch
    try:
        ings.remove(ing_a)
        ings.remove(ing_b)
    except ValueError:
        print("  Not enough of those ingredients.")
        return

    print(f"\n  ⚗ Mixing [{ing_a}] + [{ing_b}]...")
    if result:
        from source_story import rank, craft_xp

        chance = (quality("alchemy") - 1) * 0.10 + (rank(player, "alchemy") - 1) * 0.02
        if random.random() < chance:
            ings.append(ing_b)
            print("The skilled lab preserved one ingredient!")
        craft_xp(player, "alchemy")
        update_challenge_progress("craft_count")
        from food_addons import food_state
        discovered = food_state(player).setdefault("discovered", [])
        if result["name"] not in discovered: discovered.append(result["name"])
        print(f"  ✨ You brew: {result['name']}!")
        print(f"     {result['desc']}")
        use_now = input("  Use now? (y/n) > ").strip().lower()
        if use_now == "y":
            _apply_potion_effect(result["effect"], result["name"])
        else:
            player.setdefault("potions", []).append(result["name"])
            print(f"  Bottled! Added to your potion belt.")
    else:
        print(f"  💥 The mixture bubbles violently... nothing useful comes of it.")
        dmg = random.randint(3, 10)
        player["hp"] = max(1, player["hp"] - dmg)
        print(f"  The fumes sting! -{dmg} HP.")


def visit_library(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n📚═══════════════════════════════📚")
    print(f"     {struct['name'].upper()}")
    print(f"📚═══════════════════════════════📚")
    print("Dusty shelves line ancient stone walls. A wealth of forgotten knowledge awaits.\n")
    print("1. Browse the tomes  (random knowledge reward)")
    print("2. Search for ingredients  (may find 1-2 rare ingredients)")
    print("3. Leave")
    c = input("> ").strip()
    if c == "1":
        tome = random.choice(LIBRARY_TOMES)
        print(f'\n  📖 You open: "{tome["title"]}"')
        print(f"  {tome['desc']}")
        eff = tome["effect"]
        if eff == "max_hp_10":
            player["max_hp"] += 10
            player["hp"] = min(player["hp"] + 10, player["max_hp"])
        elif eff == "max_hp_15":
            player["max_hp"] += 15
            player["hp"] = min(player["hp"] + 15, player["max_hp"])
        elif eff == "def_perm_3":
            player["def"] = player.get("def", 0) + 3
        elif eff == "atk_perm_3":
            player["atk"] = player.get("atk", 0) + 3
        elif eff == "xp_boost":
            xp_gain = random.choice([80, 100, 120])
            player["xp"] = player.get("xp", 0) + xp_gain
            print(f"  +{xp_gain} XP!")
            _check_level_up()
        elif eff == "gold_80":
            g = random.randint(60, 100)
            player["gold"] += g
            print(f"  +{g} souls found hidden in the pages!")
        elif eff == "hunger_full":
            player["hunger"] = 100
            print("  Hunger restored!")
        elif eff == "mana_full":
            player["mana"] = max(player.get("mana", 0), 50)
        elif eff == "ingredient":
            r = player["region"]
            pool = REGION_INGREDIENTS.get(r, list(REGION_INGREDIENTS.values())[0])
            new_ing = random.choice(pool)
            player.setdefault("ingredients", []).append(new_ing)
            print(f"  🌿 Found ingredient: [{new_ing}]!")
    elif c == "2":
        if random.random() < 0.65:
            r = player["region"]
            pool = REGION_INGREDIENTS.get(r, list(REGION_INGREDIENTS.values())[0])
            found = [random.choice(pool) for _ in range(random.randint(1, 2))]
            for f in found:
                player.setdefault("ingredients", []).append(f)
            print(f"  🌿 Found: {', '.join(f'[{f}]' for f in found)}!")
        else:
            print("  You search carefully but find no useful materials today.")


def visit_arena(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n⚔═══════════════════════════════⚔")
    print(f"     {struct['name'].upper()}")
    print(f"⚔═══════════════════════════════⚔")
    print("The crowd roars. Three waves of fighters stand between you and glory.\n")
    print("1. Enter the arena (3 consecutive fights, big rewards)")
    print("2. Watch from the stands  (leave)")
    c = input("> ").strip()
    if c != "1":
        return
    lvl = player.get("level", 1)
    wave_names = [
        {
            "name": f"Arena Challenger",
            "hp": 50 + lvl * 10,
            "max_hp": 50 + lvl * 10,
            "atk": 14 + lvl * 2,
            "def": 4 + lvl,
            "xp": 30 + lvl * 5,
            "gold": 40 + lvl * 5,
            "status": {},
            "active_buffs": {},
        },
        {
            "name": f"Arena Veteran",
            "hp": 75 + lvl * 14,
            "max_hp": 75 + lvl * 14,
            "atk": 18 + lvl * 3,
            "def": 6 + lvl,
            "xp": 50 + lvl * 7,
            "gold": 60 + lvl * 8,
            "status": {},
            "active_buffs": {},
        },
        {
            "name": f"Arena Champion",
            "hp": 120 + lvl * 18,
            "max_hp": 120 + lvl * 18,
            "atk": 24 + lvl * 4,
            "def": 9 + lvl,
            "xp": 80 + lvl * 10,
            "gold": 100 + lvl * 12,
            "status": {},
            "active_buffs": {},
        },
    ]
    print("\n  ⚔ The crowd cheers as you step into the pit!")
    for i, enemy in enumerate(wave_names):
        print(f"\n  🥊 Wave {i + 1}: {enemy['name']} enters!")
        fight(enemy, boss=(i == 2))
        if player["hp"] <= 0:
            print("  You were defeated in the arena. The crowd goes silent.")
            return
        if i < 2:
            heal = min(20, player["max_hp"] - player["hp"])
            player["hp"] += heal
            print(f"  A brief rest between rounds. +{heal} HP.")
    print("\n  🏆 ARENA CHAMPION! The crowd erupts!")
    bonus_gold = 80 + lvl * 15
    player["gold"] += bonus_gold
    print(f"  💰 +{bonus_gold} arena prize souls!")
    if LOOT_ITEMS and random.random() < 0.6:
        loot = random.choice(regional_loot(region)).copy()
        player.setdefault("inventory", []).append(loot)
        print(f"  🎁 Bonus prize: {loot['name']}!")


def visit_blacksmith(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n🔨═══════════════════════════════🔨")
    print(f"     {struct['name'].upper()}")
    print(f"🔨═══════════════════════════════🔨")
    print("The blacksmith's hammer rings out. They can improve your gear for a price.\n")
    weapons = player.get("weapons", [])
    armours = player.get("armours", [])
    print("1. Upgrade weapon   (+3 ATK, costs 80 souls)")
    print("2. Upgrade armour   (+4 DEF, costs 80 souls)")
    print("3. Sharpen weapon   (+1 ATK per level × level, costs 40×level souls)")
    print("4. Leave")
    c = input("> ").strip()
    if c == "1":
        if not weapons:
            print("  You have no weapons to upgrade.")
            return
        print("\n  Your weapons:")
        for i, w in enumerate(weapons):
            print(f"    {i}. {w['name']}  ATK {w.get('atk', 0)}")
        try:
            idx = int(input("  Upgrade which? (-1 cancel) > "))
        except ValueError:
            return
        if 0 <= idx < len(weapons):
            if player["gold"] < 80:
                print("  Not enough souls (80 needed).")
            else:
                player["gold"] -= 80
                weapons[idx]["atk"] = weapons[idx].get("atk", 0) + 3
                print(f"  ⚒ {weapons[idx]['name']} upgraded to ATK {weapons[idx]['atk']}!")
    elif c == "2":
        if not armours:
            print("  You have no armour to upgrade.")
            return
        print("\n  Your armours:")
        for i, a in enumerate(armours):
            print(f"    {i}. {a['name']}  DEF {a.get('def', 0)}")
        try:
            idx = int(input("  Upgrade which? (-1 cancel) > "))
        except ValueError:
            return
        if 0 <= idx < len(armours):
            if player["gold"] < 80:
                print("  Not enough souls (80 needed).")
            else:
                player["gold"] -= 80
                armours[idx]["def"] = armours[idx].get("def", 0) + 4
                print(f"  ⚒ {armours[idx]['name']} upgraded to DEF {armours[idx]['def']}!")
    elif c == "3":
        lvl = player.get("level", 1)
        cost = 40 * lvl
        if not weapons:
            print("  You have no weapons.")
            return
        print(f"  Cost: {cost} souls for your current level ({lvl}).")
        print("\n  Your weapons:")
        for i, w in enumerate(weapons):
            print(f"    {i}. {w['name']}  ATK {w.get('atk', 0)}")
        try:
            idx = int(input("  Sharpen which? (-1 cancel) > "))
        except ValueError:
            return
        if 0 <= idx < len(weapons):
            if player["gold"] < cost:
                print(f"  Not enough souls ({cost} needed).")
            else:
                player["gold"] -= cost
                boost = max(1, lvl)
                weapons[idx]["atk"] = weapons[idx].get("atk", 0) + boost
                print(
                    f"  ⚒ {weapons[idx]['name']} sharpened to ATK {weapons[idx]['atk']} (+{boost})!"
                )


def visit_cave(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n🪨═══════════════════════════════🪨")
    print(f"     {struct['name'].upper()}")
    print(f"🪨═══════════════════════════════🪨")
    print("A dark cave mouth gapes before you. Sounds echo from within...\n")
    print("1. Venture inside  (2 fights, loot at the end)")
    print("2. Turn back")
    c = input("> ").strip()
    if c != "1":
        return
    lvl = player.get("level", 1)
    region_dungeon_pool = DUNGEON_MONSTERS.get(region)
    if region_dungeon_pool and len(region_dungeon_pool) >= 2:
        f1 = region_dungeon_pool[0].copy()
        f2 = region_dungeon_pool[1].copy()
    else:
        f1 = {
            "name": "Cave Lurker",
            "hp": 50 + lvl * 8,
            "max_hp": 50 + lvl * 8,
            "atk": 14 + lvl * 2,
            "def": 4 + lvl,
            "xp": 25 + lvl * 5,
            "gold": 35 + lvl * 5,
            "status": {},
            "active_buffs": {},
        }
        f2 = {
            "name": "Cave Warden",
            "hp": 75 + lvl * 12,
            "max_hp": 75 + lvl * 12,
            "atk": 18 + lvl * 3,
            "def": 6 + lvl,
            "xp": 40 + lvl * 7,
            "gold": 55 + lvl * 8,
            "status": {},
            "active_buffs": {},
        }
    for enemy_tmpl in [f1, f2]:
        enemy = dict(enemy_tmpl)
        enemy["hp"] = enemy.get("hp", 60)
        enemy["max_hp"] = enemy["hp"]
        enemy.setdefault("status", {})
        enemy.setdefault("active_buffs", {})
        enemy.setdefault("xp", 30 + lvl * 5)
        enemy.setdefault("gold", 40 + lvl * 5)
        print(f"\n  ⚠ A {enemy['name']} blocks your path!")
        fight(enemy)
        if player["hp"] <= 0:
            return
    print("\n  You reach the back of the cave.")
    if random.random() < 0.7 and LOOT_ITEMS:
        loot = random.choice(regional_loot(region)).copy()
        player.setdefault("inventory", []).append(loot)
        ores = random.choice(list(METALS))
        player.setdefault("metals", []).append(ores)
        print(f"  💎 You find: {loot['name']} gleaming in the dark!")
        print(f"  🪙 You find: {ores}!")
    bonus = 40 + lvl * 10
    player["gold"] += bonus
    print(f"  💰 +{bonus} souls from a crack in the cave wall!")
    # Small chance to find ingredients in cave
    if random.random() < 0.5:
        pool = REGION_INGREDIENTS.get(region, [])
        if pool:
            ing = random.choice(pool)
            player.setdefault("ingredients", []).append(ing)
            print(f"  🌿 Found ingredient growing in the cave: [{ing}]!")


def visit_graveyard(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n🪦═══════════════════════════════🪦")
    print(f"     {struct['name'].upper()}")
    print(f"🪦═══════════════════════════════🪦")
    print(
        "Weathered gravestones stretch into the mist. The dead keep their secrets... or do they?\n"
    )
    print("1. Dig up a grave  (risky — could be loot or a curse)")
    print("2. Search the perimeter  (safer, less reward)")
    print("3. Leave in peace")
    c = input("> ").strip()
    if c == "1":
        roll = random.random()
        loot_entry = random.choice(GRAVEYARD_LOOT)
        print(f"\n  You dig... and find: {loot_entry['name']}.")
        print(f"  {loot_entry['desc']}")
        t = loot_entry["type"]
        if t == "gold":
            player["gold"] += loot_entry["value"]
            print(f"  +{loot_entry['value']} souls!")
        elif t == "weapon" and WEAPONS:
            w = random.choice(WEAPONS).copy()
            player.setdefault("weapons", []).append(w)
            print(f"  ⚔ Got: {w['name']} (ATK {w.get('atk', 0)})")
        elif t == "armour" and ARMOURS:
            a = random.choice(ARMOURS).copy()
            player.setdefault("armours", []).append(a)
            print(f"  🛡 Got: {a['name']} (DEF {a.get('def', 0)})")
        elif t == "ingredient":
            pool = REGION_INGREDIENTS.get(region, [])
            if pool:
                ing = random.choice(pool)
                player.setdefault("ingredients", []).append(ing)
                print(f"  🌿 Ingredient: [{ing}]!")
        elif t == "curse":
            dmg = random.randint(15, 35)
            player["hp"] = max(1, player["hp"] - dmg)
            player.setdefault("status", {})["curse"] = 3
            print(f"  ☠ You are cursed! -{dmg} HP and cursed for 3 turns!")
        elif t == "empty":
            print("  Nothing worth taking.")
        # Random undead encounter (40% when digging)
        if random.random() < 0.4:
            lvl = player.get("level", 1)
            undead = {
                "name": "Grave Revenant",
                "hp": 60 + lvl * 10,
                "max_hp": 60 + lvl * 10,
                "atk": 16 + lvl * 2,
                "def": 5 + lvl,
                "xp": 30 + lvl * 6,
                "gold": 35 + lvl * 5,
                "status": {},
                "active_buffs": {},
            }
            print(f"\n  ⚰ A {undead['name']} rises from the disturbed earth!")
            fight(undead)
    elif c == "2":
        if random.random() < 0.55:
            g = random.randint(20, 55)
            player["gold"] += g
            print(f"\n  You find an old offering left by a mourner. +{g} souls.")
        else:
            print("\n  Nothing but old bones and silence.")


def visit_camp(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n⛺═══════════════════════════════⛺")
    print(f"     {struct['name'].upper()}")
    print(f"⛺═══════════════════════════════⛺")
    print("A rough camp of travellers huddles around a fire. They're cautious but friendly.\n")
    print("1. Rest by the fire  (free rest: +25 HP + +20 hunger)")
    print("2. Trade stories  (may learn a tip — small XP gain)")
    print("3. Trade one ingredient  (15–40 souls; requires an ingredient)")
    print("4. Move on")
    while True:
        c = input("Camp > ").strip()
        if c in ("1", "2", "3", "4"):
            break
        print("Choose 1 Rest, 2 Trade stories, 3 Trade one ingredient, or 4 Move on.")
    if c == "1":
        heal = max(0, min(25, player["max_hp"] - player["hp"]))
        player["hp"] += heal
        hunger_gain = max(0, min(20, 100 - player.get("hunger", 100)))
        player["hunger"] = player.get("hunger", 100) + hunger_gain
        print(f"  You rest warmly. +{heal} HP, +{hunger_gain} hunger.")
    elif c == "2":
        xp = random.randint(20, 50)
        tips = [
            '"Watch out — at night the monsters hit harder."',
            '"Ingredients can be mixed at village workbenches."',
            '"Dungeons have three floors now. The third guardian is deadly."',
            '"Libraries hold permanent stat boosts — seek them out."',
            '"The arena rewards great courage with greater gold."',
        ]
        print(f"\n  A grizzled wanderer shares their experience.")
        print(f"  {random.choice(tips)}")
        print(f"  +{xp} XP from the conversation.")
        gain_xp(xp)
    elif c == "3":
        ings = player.get("ingredients", [])
        if not ings:
            print("  You have no ingredients to offer.")
            return
        trade_ing = random.choice(ings)
        ings.remove(trade_ing)
        gold = random.randint(15, 40)
        player["gold"] += gold
        print(f"  You trade [{trade_ing}] for {gold} souls.")

    elif c == "4":
        print("  You leave the camp. Nearby, you gather wood from a fallen tree.")
        loot = random.choice(list(WOODS))
        player.setdefault("woods", []).append(loot)
        print(f"  You found {loot}.")


def visit_village(struct, region):
    import sys
    from village_life import visit

    visit(sys.modules[__name__], struct, region)


def visit_ruins(struct, region):
    import sys
    from ancient_ruins import visit

    visit(sys.modules[__name__], struct, region)


def visit_shrine(struct):
    print(f"\n⛪═══════════════════════════════⛪")
    print(f"     {struct['name'].upper()}")
    print(f"⛪═══════════════════════════════⛪")
    print("A warm divine light fills the air...\n")

    corruption = player.get("corruption", 0)
    print("1. Bless of Vitality  — +20 max HP        (80 souls)")
    print("2. Bless of Power     — +3 ATK permanent  (80 souls)")
    print("3. Bless of Ward      — +2 DEF permanent  (80 souls)")
    print("4. Restore Hunger     — hunger → 100      (80 souls)")
    print("5. Meditate — tier 1  — +5 ATK, +10 HP    (150 souls)")
    print("6. Meditate — tier 2  — +12 ATK, +30 HP   (400 souls)")
    print("7. Meditate — tier 3  — +25 ATK, +60 HP   (1000 souls)")
    if corruption > 0:
        print(f"8. Cleanse Corruption  — removes {corruption}% corruption (200 souls)")
    print("9. Depart")
    c = input("> ").strip()

    cost = 80
    if c in ("1", "2", "3", "4") and player["gold"] < cost:
        print(f"  The shrine demands {cost} souls.")
        print("while in the shrine you find a weapon core")
        loot = random.choice(list(CORES))
        player["cores"].append(loot)
        print(f"It is a {loot} core ")
        return

    if c == "1":
        player["gold"] -= cost
        player["max_hp"] += 20
        player["hp"] = min(player["hp"] + 20, player["max_hp"])
        print(f"  ✨ Max HP +20! ({player['max_hp']} total)")
    elif c == "2":
        player["gold"] -= cost
        player["atk"] += 3
        print(f"  ⚔ ATK +3! ({player['atk']} total)")
    elif c == "3":
        player["gold"] -= cost
        player["def"] += 2
        print(f"  🛡 DEF +2! ({player['def']} total)")
    elif c == "4":
        player["gold"] -= cost
        player["hunger"] = 100
        print(f"  🍖 The shrine's grace fills you — hunger fully restored!")

    elif c == "5":
        if player["gold"] < 150:
            print("  You need 150 souls to meditate at this level.")
            return
        player["gold"] -= 150
        player["atk"] += 5
        player["max_hp"] += 10
        player["hp"] = min(player["hp"] + 10, player["max_hp"])
        print(f"  🧘 Deep meditation: +5 ATK, +10 Max HP!")
    elif c == "6":
        if player["gold"] < 400:
            print("  You need 400 souls for tier-2 meditation.")
            return
        player["gold"] -= 400
        player["atk"] += 12
        player["max_hp"] += 30
        player["hp"] = min(player["hp"] + 30, player["max_hp"])
        print(f"  🧘 Deep meditation: +12 ATK, +30 Max HP!")
    elif c == "7":
        if player["gold"] < 1000:
            print("  You need 1000 souls for tier-3 meditation.")
            return
        player["gold"] -= 1000
        player["atk"] += 25
        player["max_hp"] += 60
        player["hp"] = min(player["hp"] + 60, player["max_hp"])
        print(f"  🧘 Transcendent meditation: +25 ATK, +60 Max HP! You are reborn.")
    # ─��� Feature 6: Corruption Cleanse ─���
    elif c == "8" and corruption > 0:
        if player["gold"] < 200:
            print("  Cleansing costs 200 souls.")
            return
        player["gold"] -= 200
        cleanse_corruption()
    elif c == "9":
        print("  You bow and leave the shrine.")


def visit_dungeon(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n🏰═══════════════════════����═══════🏰")
    print(f"     {struct['name'].upper()}")
    print(f"🏰═══════════════════════════════🏰")
    print("A damp passage leads into darkness. Three floors of danger await within...\n")

    print("1. Enter  (3 floors — harder each level, boss at the end)")
    print("2. Turn back")
    c = input("> ").strip()
    if c != "1":
        return

    lvl = player.get("level", 1)
    floor_pool = DUNGEON_MONSTERS.get(region)

    if floor_pool and len(floor_pool) >= 3:
        floors = [f.copy() for f in floor_pool]
    else:
        floors = [
            {
                "name": f"Dungeon Crawler",
                "hp": 55 + lvl * 10,
                "atk": 15 + lvl * 2,
                "def": 5 + lvl,
                "xp": 25 + lvl * 5,
                "gold": 35 + lvl * 5,
            },
            {
                "name": f"Dungeon Warden",
                "hp": 80 + lvl * 14,
                "atk": 20 + lvl * 3,
                "def": 7 + lvl,
                "xp": 45 + lvl * 7,
                "gold": 55 + lvl * 8,
            },
            {
                "name": f"{struct['name']} Guardian",
                "hp": 120 + lvl * 20,
                "atk": 26 + lvl * 4,
                "def": 10 + lvl,
                "xp": 75 + lvl * 12,
                "gold": 90 + lvl * 12,
            },
        ]

    for floor_num, ftmpl in enumerate(floors, 1):
        enemy = dict(ftmpl)
        enemy["hp"] = int(enemy.get("hp", 60 + lvl * 10))
        enemy["max_hp"] = enemy["hp"]
        enemy.setdefault("atk", 15 + lvl * 2)
        enemy.setdefault("def", 5 + lvl)
        enemy.setdefault("xp", 30 + lvl * 6)
        enemy.setdefault("gold", 40 + lvl * 6)
        enemy.setdefault("status", {})
        enemy.setdefault("active_buffs", {})

        is_boss_floor = floor_num == len(floors)
        print(f"\n  🏰 Floor {floor_num}: {enemy['name']} lurks here!")
        fight(enemy, boss=is_boss_floor)

        if player["hp"] <= 0:
            return

        if not is_boss_floor:
            mid_loot_chance = 0.35
            if random.random() < mid_loot_chance and LOOT_ITEMS:
                mid_loot = random.choice(regional_loot(region)).copy()
                player.setdefault("inventory", []).append(mid_loot)
                print(f"  💎 Floor {floor_num} loot: {mid_loot['name']}!")
            gold_mid = 20 + lvl * 8
            player["gold"] += gold_mid
            print(f"  💰 +{gold_mid} souls from the floor vault.")
            heal = min(15, player["max_hp"] - player["hp"])
            if heal > 0:
                player["hp"] += heal
                print(f"  You catch your breath. +{heal} HP.")

    print(f"\n  🏆 {struct['name']} CLEARED! You conquer the deepest floor!")
    if LOOT_ITEMS:
        loot = random.choice(regional_loot(region)).copy()
        player.setdefault("inventory", []).append(loot)
        print(f"  🎁 Boss drop: {loot['name']}!")
    souls_bonus = 80 + lvl * 25
    player["gold"] += souls_bonus
    print(f"  💰 +{souls_bonus} bonus souls from the final vault!")
    if random.random() < 0.3:
        pool = REGION_INGREDIENTS.get(region, [])
        if pool:
            ing = random.choice(pool)
            player.setdefault("ingredients", []).append(ing)
            print(f"  🌿 Rare ingredient found in the vault: [{ing}]!")
    cat = random.choice([CORES, WOODS, METALS])
    loot = random.choice(list(cat))
    if loot in CORES:
        player["cores"].append(loot)
        print(f"You found a {loot} core")
    elif loot in WOODS:
        player["woods"].append(loot)
        print(f"You found a {loot} wood")
    elif loot in METALS:
        player["metals"].append(loot)
        print(f"You found a {loot} metal")
    else:
        print("You found nothing else")



def visit_tower(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n🗼═══════════════════════════════🗼")
    print(f"     {struct['name'].upper()}")
    print(f"🗼═══════════════════════════════🗼")
    print("A lone tower rises sharply. Three guardians protect its peak...\n")

    print("1. Climb the tower  (3 guardians, weapon reward at the top)")
    print("2. Leave")
    c = input("> ").strip()
    if c != "1":
        return

    lvl = player.get("level", 1)
    tower_pool = TOWER_MONSTERS.get(region)

    if tower_pool and len(tower_pool) >= 3:
        floors = [f.copy() for f in tower_pool]
    else:
        floors = [
            {
                "name": f"Tower Initiate",
                "hp": 50 + lvl * 10,
                "atk": 16 + lvl * 3,
                "def": 5 + lvl,
                "xp": 22 + lvl * 5,
                "gold": 30 + lvl * 5,
            },
            {
                "name": f"Tower Knight",
                "hp": 75 + lvl * 14,
                "atk": 22 + lvl * 4,
                "def": 7 + lvl,
                "xp": 38 + lvl * 7,
                "gold": 50 + lvl * 7,
            },
            {
                "name": f"{struct['name']} Archon",
                "hp": 110 + lvl * 18,
                "atk": 30 + lvl * 5,
                "def": 10 + lvl,
                "xp": 60 + lvl * 10,
                "gold": 80 + lvl * 10,
            },
        ]

    for floor_num, ftmpl in enumerate(floors, 1):
        enemy = dict(ftmpl)
        enemy["hp"] = int(enemy.get("hp", 60 + lvl * 10))
        enemy["max_hp"] = enemy["hp"]
        enemy.setdefault("atk", 18 + lvl * 3)
        enemy.setdefault("def", 6 + lvl)
        enemy.setdefault("xp", 30 + lvl * 6)
        enemy.setdefault("gold", 40 + lvl * 6)
        enemy.setdefault("status", {})
        enemy.setdefault("active_buffs", {})

        is_top = floor_num == len(floors)
        print(f"\n  🗼 Floor {floor_num}: {enemy['name']} blocks your ascent!")
        fight(enemy, boss=is_top)

        if player["hp"] <= 0:
            return

        if not is_top:
            heal = min(15, player["max_hp"] - player["hp"])
            if heal > 0:
                player["hp"] += heal
                print(f"  You climb to the next floor. +{heal} HP.")

    print(f"\n  🗼 You reach the peak of {struct['name']}!")
    region_weapons = [w for w in WEAPONS if w.get("region") == region]
    pool = region_weapons if region_weapons else WEAPONS
    reward = random.choice(pool).copy()
    player.setdefault("weapons", []).append(reward)
    print(f"  ⚔ Tower reward: {reward['name']} (ATK {reward['atk']})!")
    bonus_gold = 40 + lvl * 12
    player["gold"] += bonus_gold
    print(f"  💰 +{bonus_gold} souls looted from the tower chest!")
    cat = random.choice([CORES, WOODS, METALS])
    loot = random.choice(list(cat))
    if loot in CORES:
        player["cores"].append(loot)
        print(f"You found a {loot} core")
    elif loot in WOODS:
        player["woods"].append(loot)
        print(f"You found a {loot} wood")
    elif loot in METALS:
        player["metals"].append(loot)
        print(f"You found a {loot} metal")
    else:
        print("You found nothing else")


def visit_structures():
    r = player["region"]
    discovered = player.get("discovered_structures", {}).get(r, [])

    print(f"\n🗺═══════════════════════════════🗺")
    print(f"  STRUCTURES — {r}")
    print(f"🗺═══════════════════════════════🗺")

    all_structs = list(REGION_STRUCTURES.get(r, []))
    if r in ELEMENTAL_VILLAGES:
        hidden = ELEMENTAL_VILLAGES[r]
        if hidden["name"] in discovered:
            all_structs.append(dict(name=hidden["name"], type="elemental", icon=hidden["icon"]))
    if not discovered:
        print("  You haven't discovered any structures here yet. Wander to find them!")
        return

    # Special: Source Temple in Riftlands is always accessible via source_temple()
    avail = [s for s in all_structs if s["name"] in discovered]
    for i, s in enumerate(avail):
        print(f"  {i}. {s['icon']} {s['name']}  [{s['type']}]")
    print(f"  {len(avail)}. Leave")

    try:
        c = int(input("> "))
    except ValueError:
        return

    if 0 <= c < len(avail):
        struct = avail[c]
        t = struct["type"]
        if t == "elemental":
            visit_elemental_village()
        elif t == "village":
            visit_village(struct, r)
        elif t == "ruins":
            visit_ruins(struct, r)
        elif t == "shrine":
            visit_shrine(struct)
        elif t == "dungeon":
            visit_dungeon(struct, r)
        elif t == "tower":
            visit_tower(struct, r)
        elif t == "special":
            source_temple()
        elif t == "library":
            visit_library(struct, r)
        elif t == "arena":
            visit_arena(struct, r)
        elif t == "blacksmith":
            visit_blacksmith(struct, r)
        elif t == "cave":
            visit_cave(struct, r)
        elif t == "graveyard":
            visit_graveyard(struct, r)
        elif t == "camp":
            visit_camp(struct, r)
        elif t == "crimsonforge":
            crimson_forge()
        elif t in ("quarry", "lumberyard", "watchpost"):
            from world_sites import visit
            import sys

            visit(sys.modules[__name__], struct, r)


# =========================
# WORLD MAP
# =========================


def show_map():
    print("\n=== WORLD MAP ===")
    current = player["region"]
    unlocked = player["unlocked_regions"]
    symbols = {
        "Whispering Woods": "🌲",
        "Ashen Wastes": "🔥",
        "Frostbound Tundra": "❄️",
        "Sunken Coast": "🌊",
        "Ironpeak Mountains": "⛰️",
        "Blight Swamp": "☠️",
        "Shadow Vale": "🌑",
        "Infernal Depths": "🌋",
        "Celestial Expanse": "✨",
        "Riftlands": "🌌",
        "Abyss of Souls": "🌀",
        "Creator's Realm": "🔱",
    }

    def label(region):
        icon = symbols.get(region, "?")
        if region == current:
            return f"[{icon} {region} (YOU)]"
        if region in unlocked:
            return f" {icon} {region} "
        return f" 🔒 {region} "

    print(
        label("Whispering Woods")
        + " -> "
        + label("Ashen Wastes")
        + " -> "
        + label("Frostbound Tundra")
        + " -> "
        + label("Sunken Coast")
        + " -> "
        + label("Ironpeak Mountains")
    )
    print("                |")
    print("                v")
    path_line = (
        label("Blight Swamp")
        + " -> "
        + label("Shadow Vale")
        + " -> "
        + label("Infernal Depths")
        + " -> "
        + label("Celestial Expanse")
        + " -> "
        + label("Riftlands")
        + " -> "
        + label("Abyss of Souls")
    )
    if SECRET_REGION in unlocked:
        path_line += " -> " + label(SECRET_REGION)
    print(path_line)
    if SECRET_REGION not in unlocked:
        print("A hidden path appears beyond the Abyss, but its gate remains unseen.")
    print(
        "\nLegend: unlocked regions are shown normally, locked regions show 🔒, current region is marked (YOU)"
    )

    # ── Discovered structures ──
    discovered = player.get("discovered_structures", {})
    if any(discovered.get(reg) for reg in unlocked):
        print("\n══ DISCOVERED STRUCTURES ══")
        all_struct_lookup = {
            s["name"]: s for structs in REGION_STRUCTURES.values() for s in structs
        }
        for reg in [r for r in symbols if r in unlocked]:
            names = discovered.get(reg, [])
            if not names:
                continue
            icon = symbols.get(reg, "?")
            print(f"\n  {icon} {reg}:")
            for n in names:
                s = all_struct_lookup.get(n, {})
                si = s.get("icon", "📍")
                st = s.get("type", "?")
                print(f"     {si} {n}  [{st}]")
    else:
        print("\n  (Explore to discover structures — 10% on Normal, 12% on Easy)")


# =========================
# BOSS
# =========================


def boss_fight():
    region = player["region"]
    fight(REGION_BOSSES[region], boss=True)
    # ── Feature 8: Prestige offer after The Dreamscape boss ──
    if player["hp"] > 0:
        try_prestige()


# =========================
# ELEMENTAL CIVILIZATIONS
# =========================

_ELEM_ICONS = {"fire": "🔥", "ice": "❄️", "storm": "⚡", "nature": "🌿"}
_ELEM_EFFECTS = {"fire": "burn", "ice": "freeze", "storm": "shock", "nature": "poison"}


def visit_elemental_village():
    region = player["region"]
    village = ELEMENTAL_VILLAGES.get(region)
    if not village:
        print("There are no elemental civilisations here.")
        return

    found = player.setdefault("discovered_structures", {}).setdefault(region, [])
    if village["name"] not in found:
        found.append(village["name"])
    icon = village["icon"]
    from source_story import meet_mentor
    from village_life import profile

    meet_mentor(player, profile(region, village["name"], True))
    print(f"\n{icon * 5} SECRET ELEMENTAL VILLAGE {icon * 5}")
    print(f"You have stumbled upon the hidden home of the {village['name']}!")
    print(f"{village['desc']}")
    print(f"\nThey tell you about  you their sacred {village['core']}.")
    print(
        "Their core remains guarded here. Destroyed cores once left eleven civilisations powerless."
    )
    from village_life import register_visit, profile
    clan_profile=profile(region,village['name'],True)
    register_visit(player,clan_profile,random)
    while True:
        print("\n1. Ask for the clan’s elemental blessing")
        print("2. Test yourself against their guardian (the core stays here)")
        print("3. Buy clan supplies / visit the expanded halls")
        print("4. Leave quietly")
        print("5. Hear the history of the fallen warriors")
        print("6. Local services, crafting and restaurant")
        print("7. Protect this clan from a raid / assign village defenders")
        print("8. Protect Whispering Woods / assign clan volunteers")
        c=input("Elemental village > ").strip()
        if c in ('4','0'):
            print("You leave the village. Its location remains in Structures.")
            return
        if c=='1':_give_elemental_core(village['core'])
        elif c=='2':
            boss_data=ELEMENTAL_BOSSES[village['boss_key']].copy()
            print(f"\n{icon} {boss_data['name']} rises for your trial!")
            print(f'"{boss_data["taunt"]}"')
            _fight_elemental_boss(boss_data)
        elif c=='3':
            import sys
            from season_two import available, village_services
            if available(player):village_services(sys.modules[__name__],village)
            else:
                from clan_defence import basic_market
                basic_market(sys.modules[__name__],village)
        elif c=='5':
            from source_story import remember_warriors
            remember_warriors(player,clan_profile)
        elif c=='6':
            import sys
            from village_life import visit
            visit(sys.modules[__name__],dict(name=village['name'],elemental=True,same_visit=True),region)
        elif c=='7':
            import sys
            from community_addons import defence
            defence(sys.modules[__name__],clan_profile)
        elif c=='8':
            import sys
            from clan_defence import menu
            menu(sys.modules[__name__])
        else:print("Choose a listed village option; 4 leaves.")


def _give_elemental_core(core_name):
    """Grant a blessing, never remove a civilisation's surviving core."""
    attuned = player.setdefault("core_attunements", [])
    if core_name not in attuned:
        attuned.append(core_name)
    print(
        f"The keepers grant a blessing from {core_name}. The core remains guarded in its village; no core is added to your inventory."
    )


def _fight_elemental_boss(boss_data):
    """Special boss fight that applies elemental status effects every N turns."""
    from expansion_hooks import scale_enemy
    boss = scale_enemy(player, boss_data.copy())
    for pet in player.get('companions', []):
        pet.pop('helped_this_battle', None)
    boss["boss"] = True
    player.pop("_rune_previous", None)
    boss.setdefault("status", {})
    boss.setdefault("active_buffs", {})
    boss.setdefault("max_hp", boss["hp"])

    icon = boss.get("icon", "✨")
    eff = boss["status_effect"]
    eff_dmg = boss["status_dmg"]
    every = boss["status_every"]
    turn = 0

    ui = _ui.get_ui()
    if ui:
        ui.set_enemy(boss)

    print(f"\n⚔ {boss['name']} [{boss['element'].upper()} BOSS]")
    print(f"HP: {boss['hp']}  ATK: {boss['atk']}  DEF: {boss['def']}")
    print(f"⚠  Every {every} turn(s) it applies {eff} to YOU!\n")

    while player["hp"] > 0 and boss["hp"] > 0:
        turn += 1
        process_buffs()
        apply_status(player)
        apply_status(boss)
        from original_magic import turn as rune_turn, strike

        player_can_act = rune_turn(player, boss)
        boss_can_act = rune_turn(boss, player)
        if player["hp"] <= 0 or boss["hp"] <= 0:
            break

        # Phase announcement
        max_hp = boss["max_hp"]
        if boss["hp"] <= max_hp * 0.25:
            print(f"{icon} FINAL PHASE — {boss['name']} burns with desperate fury!")
        elif boss["hp"] <= max_hp * 0.5:
            print(f"{icon} PHASE 3 — {boss['name']} unleashes full elemental power!")
        elif boss["hp"] <= max_hp * 0.75:
            print(f"{icon} PHASE 2 — {boss['name']} grows stronger!")

        print(f"\nYou: {player['hp']} HP  |  {boss['name']}: {boss['hp']} HP")
        c = (
            input("1 atk  2 scroll  3 staff  8 loose rune > ").strip()
            if player_can_act and not player["active_buffs"].pop("stun", None)
            else ""
        )

        if c == "1":
            dmg = calculate_damage(player, boss, "weapon")
            strike(player, boss, dmg)
            print(f"You dealt {dmg} damage!")
            _apply_charged_weapon_effect(boss)
            if player.get("weapon", {}).get("rune"):
                apply_rune_effect(player["weapon"]["rune"], player, boss)
            apply_companion_support(boss)

        elif c == "2":
            use_scroll()

        elif c == "3":
            use_staff(boss)

            apply_companion_support(boss)

        elif c == "8":
            use_combat_rune(boss)

        if boss["hp"] <= 0:
            break

        if not boss_can_act:
            continue

        # Elemental boss status effect on player
        if turn % every == 0:
            if eff == "freeze":
                player["status"]["freeze"] = player["status"].get("freeze", 0) + 2
                print(f"{icon} {boss['name']} freezes you solid! (skip next turn)")
            elif eff == "shock":
                shock_dmg = random.randint(eff_dmg // 2, eff_dmg)
                player["hp"] -= shock_dmg
                print(f"{icon} Lightning strikes you for {shock_dmg} damage!")
            else:
                player["status"][eff] = player["status"].get(eff, 0) + 3
                print(f"{icon} {boss['name']} inflicts {eff} on you! ({eff_dmg} dmg/turn)")

        # Regular boss attack
        armour_def = player["armour"].get("def", 0) if player.get("armour") else 0
        boss_dmg = max(1, boss["atk"] // 4 - player.get("def", 0) // 4 - armour_def // 5)
        boss_dmg = random.randint(max(1, boss_dmg - 5), boss_dmg + 10)
        if player["active_buffs"].get("warp"):
            print("✨ You warp away the boss attack!")
            boss_dmg = 0
        if player["active_buffs"].get("wraith_form"):
            print("👻 Wraith Form: Boss attack passes through you!")
            boss_dmg = 0
            player["active_buffs"]["wraith_form"] -= 1
            if player["active_buffs"]["wraith_form"] <= 0:
                player["active_buffs"].pop("wraith_form", None)
        if boss_dmg > 0:
            strike(boss, player, boss_dmg)
            print(f"{icon} {boss['name']} strikes you for {boss_dmg}!")

        if player["hp"] <= 0 and player["active_buffs"].get("rebirth"):
            player["hp"] = max(1, player["max_hp"] // 2)
            player["active_buffs"].pop("rebirth", None)
            print("✨ Rebirth activated! You return to half health.")

    if ui:
        ui.clear_enemy()

    if player["hp"] > 0:
        print(f"\n🏆 You defeated {boss['name']}!")
        from expansion_hooks import finish_battle
        from companion_care import battle_credit
        finish_battle(player, True)
        award_companion_xp(20)
        battle_credit(player, 10)
        _give_elemental_core(boss["drop"])
        gain_xp(150)
        player["gold"] += 150
        drop_loot()
        drop_loot()
    else:
        print(f"\n☠ {boss['name']} has destroyed you.")
        raise _ui.RunEnded()


# =========================
# INFUSE GEAR WITH ELEMENTAL CORE
# =========================


def source_temple():
    if player["region"] != "Riftlands":
        print("The Source Temple stands in the Riftlands.")
        return
    print("\n--- SOURCE TEMPLE · RIFTLANDS ---")
    print(
        "The ancient stabiliser stands here. The Keeper also prepares portable Core "
        "Stabilisers for binding core energy into equipment."
    )
    print(
        "1. Buy a Core Stabiliser — 300 souls\n"
        "2. Imbue a weapon or staff using core energy and a stabiliser\n"
        "3. Inspect the ancient stabiliser\n4. Story journal\n0. Leave"
    )
    choice = input("Temple > ").strip()
    if choice == "1":
        if player["gold"] < 300:
            print("Not enough souls.")
            return
        player["gold"] -= 300
        player["inventory"].append(dict(
            name="Core Stabiliser", value=150,
            desc="Portable anchor for imbuing core energy into equipment."
        ))
        print("Core Stabiliser added to your inventory.")
    elif choice == "2":
        infuse_gear()
    elif choice == "3":
        print("The fixed stabiliser bears the ancient warriors’ seals. The four surviving cores remain in their civilisations.")
    elif choice == "4":
        view_story()


def infuse_gear():
    if player["region"] != "Riftlands":
        print("⚠  Elemental infusion can only be performed inside the Riftlands Source Temple.")
        print("   Travel to the Riftlands and enter the Source Temple through Structures.")
        return

    cores = list(dict.fromkeys(
        player.get("elemental_cores", []) + player.get("core_attunements", [])
    ))
    has_stabiliser = any(i.get("name") == "Core Stabiliser" for i in player.get("inventory", []))

    if not cores:
        print("You have no core or clan blessing available for imbuing. Broken-core fragments cannot be used.")
        return
    if not has_stabiliser:
        print("You need a Core Stabiliser — purchase one from the Source Temple Keeper.")
        return

    print("\n=== ELEMENTAL INFUSION ===")
    print("Cores available:")
    for i, c in enumerate(cores):
        data = ELEMENTAL_CORES[c]
        print(f"  {i}. {c}  (+{data['bonus_atk']} ATK, on-hit: {data['on_hit_effect']})")

    try:
        core_idx = int(input("Select core > "))
        if not 0 <= core_idx < len(cores):
            raise IndexError
        core_name = cores[core_idx]
    except (ValueError, IndexError):
        print("Invalid choice.")
        return

    core_data = ELEMENTAL_CORES[core_name]
    icon = _ELEM_ICONS.get(core_data["element"], "✨")

    print("\nInfuse into:")
    print("1. Equipped weapon")
    print("2. Equipped staff")
    gear_choice = input("> ").strip()

    target = None
    if gear_choice == "1":
        target = player.get("weapon")
        if not target:
            print("No weapon equipped.")
            return
    elif gear_choice == "2":
        target = player["staffs"][0] if player.get("staffs") else None
        if not target:
            print("No staff equipped.")
            return
    else:
        print("Cancelled.")
        return

    if target.get("elemental_charged"):
        print(f"That gear is already infused with {target.get('element', '?')} energy.")
        return

    # Confirm
    print(f"\n{icon} Infuse {core_name} into {target['name']}?")
    print(f"  +{core_data['bonus_atk']} ATK bonus  |  On-hit: {core_data['on_hit_effect']}")
    print(f"  This uses your Core Stabiliser (consumed).")
    if input("Confirm? (y/n) > ").lower() != "y":
        print("Cancelled.")
        return

    # Apply infusion
    target["elemental_charged"] = True
    target["element"] = core_data["element"]
    target["core_name"] = core_name
    target["bonus_atk"] = core_data["bonus_atk"]
    target["on_hit_effect"] = core_data["on_hit_effect"]
    if gear_choice == "1":
        target["atk"] = target.get("atk", 0) + core_data["bonus_atk"]
    else:
        target["power"] = target.get("power", 0) + core_data["bonus_atk"]

    # Consume core + stabiliser
    if core_name in player.get("elemental_cores", []):
        player["elemental_cores"].remove(core_name)
    # A clan blessing channels energy remotely; its protected core stays in the village.
    for item in player["inventory"]:
        if item.get("name") == "Core Stabiliser":
            player["inventory"].remove(item)
            break

    print(f"\n{icon} {target['name']} is now infused with {core_data['element']} energy!")
    print(f"  Every hit will apply {core_data['on_hit_effect']} to the enemy!")


def _apply_charged_weapon_effect(enemy):
    """Called after a weapon attack — apply elemental on-hit if weapon is infused."""
    w = player.get("weapon")
    if not w or not w.get("elemental_charged"):
        return
    if w.get('forge_core_effect'):
        apply_rune_effect({'name':w.get('elemental_core','Forged core'),'effect':w['forge_core_effect']},player,enemy)
        if w.get('forge_core_rune'):apply_rune_effect(w['forge_core_rune'],player,enemy)
        return
    if w.get('paired_effects'):
        for effect in w['paired_effects'][1:]:
            apply_rune_effect({'name':'Paired channel','effect':effect},player,enemy)
        return
    eff = w.get("on_hit_effect", "burn")
    icon = _ELEM_ICONS.get(w.get("element", "fire"), "✨")
    enemy.setdefault("status", {})[eff] = enemy["status"].get(eff, 0) + 2
    print(f"{icon} Elemental charge inflicts {eff} on the enemy!")


def _sell_all_loot():
    from player_qol import loot as is_loot
    loot = [item for item in player["inventory"] if is_loot(item)]
    if not loot:
        print("No loot to sell.")
        return
    total = sum(item["value"] for item in loot)
    print(f"Selling {len(loot)} items for {total} souls total:")
    for item in loot:
        print(f"  - {item['name']} ({item['value']})")
    player["gold"] += total
    for item in loot:
        player["inventory"].remove(item)
    print(f"💰 Sold everything! +{total} souls.")


def _sell_all_weapons():
    unequipped = [w for w in player["weapons"] if w != player.get("weapon")]
    if not unequipped:
        print("No unequipped weapons to sell.")
        return
    total = sum(w["atk"] * 5 for w in unequipped)
    print(f"Selling {len(unequipped)} weapons for {total} souls total:")
    for w in unequipped:
        print(f"  - {w['name']} ({w['atk'] * 5})")
    player["gold"] += total
    for w in unequipped:
        player["weapons"].remove(w)
    print(f"💰 Sold all unequipped weapons! +{total} souls.")


def _sell_all_runes():
    if not player["runes"]:
        print("No runes to sell.")
        return
    total = len(player["runes"]) * 50
    print(f"Selling {len(player['runes'])} runes for {total} souls total.")
    player["gold"] += total
    player["runes"].clear()
    print(f"💰 Sold all runes! +{total} souls.")


def sell():
    from player_qol import loot as is_loot
    while True:
        loot_count = len([i for i in player["inventory"] if is_loot(i)])
        loot_value = sum(i["value"] for i in player["inventory"] if is_loot(i))
        unequipped_w = [w for w in player["weapons"] if w != player.get("weapon")]
        weapon_value = sum(w["atk"] * 5 for w in unequipped_w)
        rune_value = len(player["runes"]) * 50

        print("\n=== SELL ===")
        print(f"1. Loot         (pick one)")
        print(f"2. Weapons      (pick one)")
        print(f"3. Armour       (pick one)")
        print(f"4. Staffs       (pick one)")
        print(f"5. Runes        (pick one)")
        print(f"6. Scrolls      (pick one)")
        print(f"─────────────────────────")
        print(f"A. Sell ALL loot        ({loot_count} items, {loot_value} souls)")
        print(f"B. Sell ALL unequipped weapons ({len(unequipped_w)} weapons, {weapon_value} souls)")
        print(f"C. Sell ALL runes       ({len(player['runes'])} runes, {rune_value} souls)")
        print(
            f"D. Sell EVERYTHING unequipped ({loot_value + weapon_value + rune_value} souls total)"
        )
        print(f"7. Back")

        choice = input("> ").strip().lower()

        if choice == "7":
            return

        if choice == "a":
            _sell_all_loot()
            continue

        if choice == "b":
            _sell_all_weapons()
            continue

        if choice == "c":
            _sell_all_runes()
            continue

        if choice == "d":
            grand = loot_value + weapon_value + rune_value
            confirm = input(
                f"Sell all loot + unequipped weapons + all runes for {grand} souls? (y/n) > "
            ).lower()
            if confirm == "y":
                _sell_all_loot()
                _sell_all_weapons()
                _sell_all_runes()
            continue

        if choice == "1":
            loot = [item for item in player["inventory"] if is_loot(item)]

            if not loot:
                print("No loot.")
                continue

            for i, item in enumerate(loot):
                print(f"{i}. {item['name']} ({item['value']} souls)")

            try:
                idx = int(input("> "))
                item = loot[idx]
            except:
                print("Invalid.")
                continue

            player["gold"] += item["value"]
            player["inventory"].remove(item)
            print(f"Sold {item['name']} for {item['value']} souls.")

        elif choice == "2":
            if not player["weapons"]:
                print("No weapons.")
                continue

            for i, weapon in enumerate(player["weapons"]):
                print(f"{i}. {weapon['name']} (Sell {weapon['atk'] * 5})")

            try:
                idx = int(input("> "))
                weapon = player["weapons"][idx]
            except:
                print("Invalid.")
                continue

            if player["weapon"] == weapon:
                player["weapon"] = None

            value = weapon["atk"] * 5
            player["gold"] += value
            player["weapons"].remove(weapon)

            print(f"Sold {weapon['name']} for {value} souls.")

        elif choice == "3":
            if not player["armours"]:
                print("No armour.")
                continue

            for i, a in enumerate(player["armours"]):
                print(f"{i}. {a['name']} (Sell {a['def'] * 5})")

            try:
                idx = int(input("> "))
                arm = player["armours"][idx]
            except:
                print("Invalid.")
                continue

            if player["armour"] == arm:
                player["armour"] = None

            value = arm["def"] * 5
            player["gold"] += value
            player["armours"].remove(arm)
            print(f"Sold {arm['name']} for {value} souls.")

        elif choice == "4":
            if not player["staffs"]:
                print("No staffs.")
                continue

            for i, staff in enumerate(player["staffs"]):
                print(f"{i}. {staff['name']} (Sell {staff['power'] * 5})")

            try:
                idx = int(input("> "))
                staff = player["staffs"][idx]
            except:
                print("Invalid.")
                continue

            value = staff["power"] * 5
            player["gold"] += value
            player["staffs"].remove(staff)

            print(f"Sold {staff['name']} for {value} souls.")

        elif choice == "5":
            if not player["runes"]:
                print("No runes.")
                continue

            for i, rune in enumerate(player["runes"]):
                print(f"{i}. {rune['name']} (Sell 50)")

            try:
                idx = int(input("> "))
                rune = player["runes"][idx]
            except:
                print("Invalid.")
                continue

            player["gold"] += 50
            player["runes"].remove(rune)

            print(f"Sold {rune['name']} for 50 souls.")

        elif choice == "6":
            scrolls = [item for item in player["inventory"] if "turns" in item]

            if not scrolls:
                print("No scrolls.")
                continue

            for i, scroll in enumerate(scrolls):
                print(f"{i}. {scroll['name']} (Sell 25)")

            try:
                idx = int(input("> "))
                scroll = scrolls[idx]
            except:
                print("Invalid.")
                continue

            player["gold"] += 25
            player["inventory"].remove(scroll)

            print(f"Sold {scroll['name']} for 25 souls.")


_DARK_REGIONS = {
    "Shadow Vale",
    "Infernal Depths",
    "Abyss of Souls",
    "Shattered Wastes",
    "The Dreamscape",
    "Blight Swamp",
}


def get_current_world_event():
    idx = player.get("world_event_idx", 0) % len(WORLD_EVENTS)
    return WORLD_EVENTS[idx]


def advance_world_event():
    """Called every 20 wanders — cycles to the next world event."""
    player["world_event_idx"] = (player.get("world_event_idx", 0) + 1) % len(WORLD_EVENTS)
    ev = get_current_world_event()
    print(f"\n{'═' * 46}")
    print(f"  🌍 WORLD EVENT CHANGED: {ev['icon']} {ev['name']}")
    print(f"  {ev['desc']}")
    print(f"{'═' * 46}")


def record_kill(enemy_name):
    update_challenge_progress("kill_count")
    from source_story import first_victory

    first_victory(player)
    kc = player.setdefault("kill_counts", {})
    kc[enemy_name] = kc.get(enemy_name, 0) + 1
    count = kc[enemy_name]
    if count == 5:
        print(f"\n📖 BESTIARY: {enemy_name} — weakness discovered! +25% dmg forever.")
    elif count == 20:
        print(f"\n📖 BESTIARY MASTERED: {enemy_name} — this creature holds no secrets from you.")


def bestiary_bonus_for(enemy_name):
    count = player.get("kill_counts", {}).get(enemy_name, 0)
    if count >= 20:
        return 1.4
    if count >= 5:
        return 1.25
    return 1.0


def view_bestiary():
    kc = player.get("kill_counts", {})
    print(f"\n📖{'═' * 42}📖")
    print(f"           BESTIARY")
    print(f"📖{'═' * 42}📖")
    if not kc:
        print("  No creatures catalogued yet. Go explore!")
        return
    for name, count in sorted(kc.items(), key=lambda x: -x[1])[:20]:
        tag = ""
        if count >= 20:
            tag = " ★ MASTERED (+40% dmg)"
        elif count >= 5:
            tag = " ⚡ Weakness known (+25% dmg)"
        print(f"  {name:<30} {count:>4} kills{tag}")
    print(f"\n  Total kills: {sum(kc.values())}")


def update_resonance(took_damage):
    if took_damage:
        player["resonance_streak"] = 0
        player["resonance_ready"] = False
        return
    player["resonance_streak"] = player.get("resonance_streak", 0) + 1
    if player["resonance_streak"] >= 3 and not player.get("resonance_ready"):
        player["resonance_ready"] = True
        print("⚡ SOUL RESONANCE CHARGED! Your next attack deals 3x damage!")


def consume_resonance():
    if player.get("resonance_ready"):
        player["resonance_ready"] = False
        player["resonance_streak"] = 0
        print("⚡ SOUL RESONANCE UNLEASHED!")
        return 3.0
    return 1.0


def make_elite(monster):
    elite = monster.copy()
    elite["name"] = f"★ ELITE {monster['name']}"
    elite["hp"] = int(monster.get("hp", 30) * 2)
    elite["max_hp"] = int(monster.get("hp", 30) * 2)
    elite["atk"] = int(monster.get("atk", 10) * 1.5)
    elite["_elite"] = True
    return elite


def add_corruption(amount=5):
    old = player.get("corruption", 0)
    player["corruption"] = min(100, old + amount)
    new = player["corruption"]
    if old < 100 and new >= 100:
        print("\n☠ CORRUPTION MAXED! Darkness consumes you! -20% ATK, -10 max HP.")
        player["atk"] = max(1, int(player["atk"] * 0.8))
        player["max_hp"] = max(10, player["max_hp"] - 10)
        player["hp"] = min(player["hp"], player["max_hp"])
    elif new >= 75 and old < 75:
        print(f"\n⚠ Corruption: {new}% — the darkness seeps into your soul...")
    elif new >= 50 and old < 50:
        print(f"\n⚠ Corruption: {new}% — you feel unclean.")


def cleanse_corruption():
    amt = player.get("corruption", 0)
    if amt == 0:
        print("  You feel pure — no corruption to cleanse.")
        return
    player["corruption"] = 0
    print(f"  ✨ Divine light burns away your corruption! ({amt}% cleansed)")


def check_gear_set():
    w_name = (player.get("weapon") or {}).get("name", "")
    a_name = (player.get("armour") or {}).get("name", "")
    r_names = [r["name"] for r in player.get("runes", [])]
    current = player.get("active_set")
    for set_name, sdata in GEAR_SETS.items():
        p = sdata["pieces"]
        if p["weapon"] == w_name and p["armour"] == a_name and p["rune"] in r_names:
            if current != set_name:
                player["active_set"] = set_name
                player["set_crit_counter"] = 0
                b = sdata["bonus"]
                print(f"\n{sdata['icon']} SET ACTIVATED: {set_name}!")
                print(f"  {sdata['desc']}  Bonus: {b['label']}")
            return
    if current:
        player["active_set"] = None
        player["set_crit_counter"] = 0


def get_set_atk_bonus():
    s = player.get("active_set")
    if not s:
        return 0
    return GEAR_SETS.get(s, {}).get("bonus", {}).get("atk", 0)


def get_set_def_bonus():
    s = player.get("active_set")
    if not s:
        return 0
    return GEAR_SETS.get(s, {}).get("bonus", {}).get("def", 0)


def try_prestige():
    if player['region']!='The Dreamscape' or player.get('prestige_level',0)>=3:return
    if input('Begin a fresh prestige journey with stronger starting stats? (prestige/cancel) > ').strip().lower()=='prestige':
        import sys
        from legacy_workshops import ascend
        ascend(sys.modules[__name__])


def weapon_fusion():
    print("\n🔥 === WEAPON FUSION ===")
    print("Known Fusion Recipes:")
    for recipe in FUSION_RECIPES:
        a, b = recipe["needs"]
        print(f"  {a} + {b} → {recipe['name']} (ATK {recipe['atk']})")
        print(f'    "{recipe["desc"]}"')
    print()
    weapon_names = [w["name"] for w in player["weapons"]]
    available = [
        r for r in FUSION_RECIPES if r["needs"][0] in weapon_names and r["needs"][1] in weapon_names
    ]
    if not available:
        print("You don't have the right weapon pairs yet. Keep exploring!")
        return
    print("Available fusions:")
    for i, recipe in enumerate(available):
        a, b = recipe["needs"]
        print(f"  {i}. {a} + {b}  →  {recipe['name']}")
    print(f"  {len(available)}. Cancel")
    try:
        choice = int(input("> "))
    except ValueError:
        return
    if choice < 0 or choice >= len(available):
        return
    recipe = available[choice]
    a_name, b_name = recipe["needs"]
    w_a = next(w for w in player["weapons"] if w["name"] == a_name)
    w_b = next(w for w in player["weapons"] if w["name"] == b_name)
    player["weapons"].remove(w_a)
    player["weapons"].remove(w_b)
    if player.get("weapon") in (w_a, w_b):
        player["weapon"] = None
    fused = {
        "name": recipe["name"],
        "tier": recipe["tier"],
        "atk": recipe["atk"],
        "cores": recipe.get("cores", {}),
    }
    if recipe.get("cursed"):
        fused["cursed"] = True
    player["weapons"].append(fused)
    player["weapon"] = fused
    print(f"\n🔥 FUSION COMPLETE! {fused['name']} (ATK {fused['atk']}) — auto-equipped!")
    print(f'  "{recipe["desc"]}"')


def award_companion_xp(amount):
    companions = player.get("companions", [])
    if not companions:
        return
    cxp = player.setdefault("companion_xp", {})
    clvl = player.setdefault("companion_levels", {})
    for c in companions:
        if c.get("hunger", 100) < 30 or not c.get("helped_this_battle"):
            continue
        name = c["name"]
        cxp[name] = cxp.get(name, 0) + amount
        clvl[name] = clvl.get(name, 1)
        xp_needed = clvl[name] * 50
        if cxp[name] >= xp_needed and clvl[name] < 5:
            clvl[name] += 1
            cxp[name] -= xp_needed
            c["atk"] = int(c.get("atk", 10) * 1.2)
            print(f"\n🐾 {name} levelled up to Lv.{clvl[name]}! ATK → {c['atk']}")


# =========================
# RUNE BINDING
# =========================


def bind_rune_weapon():
    if not player["weapons"]:
        print("No weapons available.")
        return

    if not player["runes"]:
        print("No runes available.")
        return

    print("\n=== WEAPONS ===")
    for i, w in enumerate(player["weapons"]):
        current = w.get("rune", None)
        rune_name = current["name"] if current else "None"
        print(f"{i}. {w['name']} | Rune: {rune_name}")

    try:
        w_idx = int(input("Select weapon > "))
        weapon = player["weapons"][w_idx]
    except:
        print("Invalid weapon selection.")
        return

    if weapon.get("rune"):
        print("This weapon already has a permanent rune. It cannot be removed or replaced.")
        return

    print("\n=== RUNES ===")
    for i, r in enumerate(player["runes"]):
        print(f"{i}. {r['name']} ({r['effect']})")

    try:
        r_idx = int(input("Select rune > "))
        rune = player["runes"][r_idx]
    except:
        print("Invalid rune selection.")
        return

    weapon["rune"] = rune
    player["runes"].remove(rune)

    print(f"🔮 Bound {rune['name']} to {weapon['name']}")


def bind_rune_staff():
    if not player["staffs"]:
        print("No staffs available.")
        return

    if not player["runes"]:
        print("No runes available.")
        return

    print("\n=== STAFFS ===")
    for i, s in enumerate(player["staffs"]):
        current = s.get("rune", None)
        rune_name = current["name"] if current else "None"
        print(f"{i}. {s['name']} ({s['element']}) | Rune: {rune_name}")

    try:
        s_idx = int(input("Select staff > "))
        staff = player["staffs"][s_idx]
    except:
        print("Invalid staff selection.")
        return

    print("\n=== RUNES ===")
    for i, r in enumerate(player["runes"]):
        print(f"{i}. {r['name']} ({r['effect']})")

    try:
        r_idx = int(input("Select rune > "))
        rune = player["runes"][r_idx]
    except:
        print("Invalid rune selection.")
        return

    if "rune" in staff:
        old = staff["rune"]
        player["runes"].append(old)

    if staff["name"] == "Rift Staff" and rune["name"] == "Creator Rune":
        staff["name"] = "Staff of Creation"
        staff["element"] = "creation"
        staff["power"] = max(staff.get("power", 0), 45)
        staff["rune"] = rune
        player["runes"].remove(rune)
        print(
            f"✨ {staff['name']} has formed as the bound {rune['name']} transformed your Rift Staff!"
        )
        unlock_secret_region()
        return

    staff["rune"] = rune
    player["runes"].remove(rune)

    print(f"✨ Bound {rune['name']} to {staff['name']}")


# =========================
# GAME LOOP
# =========================
def perform_original_action(c):
    from legacy_systems import menu as system_menu
    legacy = {'29':'cosmetics','30':'guild','31':'events','32':'modes','35':'ngplus','36':'battle_pass','37':'rituals','38':'arena','39':'recipes','40':'market','41':'town','42':'daily','43':'factions','44':'treasure','45':'mounts'}
    if c in legacy:
        import sys
        system_menu(sys.modules[__name__], legacy[c])
        return True
    if c == '48':
        import sys
        from addons import hub
        hub(sys.modules[__name__])
        return True
    if c == "1":
        explore()
    elif c == "2":
        travel()
    elif c == "3":
        print(
            "\n--- BLACKSMITH & RUNES ---\n1. Blacksmith\n2. Use scroll\n3. Bind rune\n4. Fuse runes\n5. Cast spell\n6. Weapon fusion\n0. Back"
        )
        x = input("Choose a crafting option > ").strip()
        if x == "2":
            use_scroll()
        elif x == "1":
            blacksmith()
        elif x == "6":
            weapon_fusion()
        elif x == "3":
            y = input("bind to 1. staff or 2. weapon: ")
            if y == "1":
                bind_rune_staff()
            elif y == "2":
                bind_rune_weapon()
        elif x == "4":
            merge_runes()
        elif x == "5":
            cast_spell()
    elif c == "4":
        equip_weapon()
    elif c == "5":
        equip_armour()
    elif c == "6":
        print(player)
    elif c == "7":
        save_game()
    elif c == "8":
        return False
    elif c == "9":
        boss_fight()
    elif c == "49":
        from player_qol import potion_menu
        import sys
        potion_menu(sys.modules[__name__])
    elif c == "10":
        view_inventory()
    elif c == "11":
        sell()
    elif c == "12":
        cast_spell()
    elif c == "13":
        show_map()
    elif c == "14":
        crimson_forge()
    elif c == "15":
        infuse_gear()
    elif c == "16":
        source_temple()
    elif c == "17":
        visit_structures()
    elif c == "18":
        _eat_food()
    elif c == "19":
        skill_tree()
    elif c == "20":
        _show_achievements()
    elif c == "21":
        view_bestiary()
    elif c == "22":
        view_companion_status()
    elif c == "23":
        view_crafting_hub()
    elif c == "24":
        view_daily_challenges()
    elif c == "25":
        view_weekly_challenges()
    elif c == "26":
        start_boss_rush()
    elif c == "27":
        view_boss_rush_stats()
    elif c == "28":
        view_skill_tree()
    elif c == "29":
        view_cosmetics_shop()
    elif c == "30":
        view_guild()
    elif c == "31":
        view_seasonal_events()
    elif c == "32":
        view_challenge_modes()
    elif c == "33":
        view_story()
    elif c == "34":
        enchant_equipment()
    elif c == "35":
        start_newgame_plus()
    elif c == "36":
        view_battle_pass()
    elif c == "37":
        perform_ritual()
    elif c == "38":
        battle_arena()
    elif c == "39":
        discover_recipes()
    elif c == "40":
        trading_post()
    elif c == "41":
        build_town()
    elif c == "42":
        view_login_streak()
    elif c == "43":
        join_faction()
    elif c == "44":
        treasure_hunting()
    elif c == "45":
        ride_mounts()
    elif c == "46":
        view_active_effects()
    elif c == "47":
        import sys
        from village_life import directory

        directory(sys.modules[__name__])
    check_gear_set()
    return True


def game():
    """The original 46 actions with grouped text menus and a status sidebar."""
    from copy import deepcopy
    from original_menus import BY_ID

    load_game()
    _ui.init_ui(player)
    group = ""
    while True:
        _ui.location = None
        if _ui.get_ui():
            _ui.get_ui().clear_enemy()
        if player.get("auto_sell_duplicates"):
            from inventory_tools import sell_duplicates

            sell_duplicates(player, quiet=True)
        _ui.context("category" if group else "main", group)
        if group:
            print("\n--- " + BY_ID[group]["name"].upper() + " ---")
            for number, (_, label) in enumerate(BY_ID[group]["options"], 1):
                print(f"{number}. {label}")
            print("0. Back to main menu")
        else:
            print("\n--- MAIN MENU ---")
            for number, category in enumerate(BY_ID.values(), 1):
                print(f"{number}. {category['name']}")
        try:
            choice = input("Choose an action > " if group else "Choose a category > ").strip()
        except _ui.ReturnToMenu:
            group = ""
            continue
        if choice.upper() == "DAMAR" and not group:
            from beta_testing import grant_collectibles

            grant_collectibles(player)
            continue
        if choice.upper() == "SAMAR":
            from beta_testing import disable_beta

            disable_beta(player)
            continue
        category = next(
            (g["id"] for g in BY_ID.values() if choice.lower() in (g["id"], g["name"].lower())),
            None,
        )
        if choice.startswith("/group:"):
            category = choice.split(":", 1)[1]
        if category in BY_ID:
            group = category
            continue
        if group and choice == "0":
            group = ""
            continue
        try:
            index = int(choice) - 1
            options = BY_ID[group]["options"] if group else list(BY_ID)
            if not 0 <= index < len(options):
                raise ValueError
        except ValueError:
            print("Choose one of the numbers shown above.")
            continue
        if not group:
            group = options[index]
            continue
        choice = str(options[index][0])
        _ui.context("action", group)
        before = deepcopy(player)
        try:
            result = perform_original_action(choice)
            if player["hp"] <= 0:
                raise _ui.RunEnded()
            if not result:
                save_game()
                print("Journey saved. You can continue from the title screen.")
                return
        except _ui.RunEnded:
            raise
        except _ui.ReturnToMenu:
            if player["hp"] <= 0:
                raise _ui.RunEnded()
            print("Returned to the category menu.")
        except Exception as error:
            player.clear()
            player.update(before)
            _ui.init_ui(player)
            print(
                f"This original action could not finish ({type(error).__name__}: {error}). Your character was restored to before this action."
            )


# =========================================================
# ARMOR CRAFTING SYSTEM
# =========================================================


def craft_armor():
    from village_life import require_service, quality

    if not require_service("loom"):
        return
    """Craft armor pieces using the Loom structure"""
    global player

    armor_pieces = ["helmet", "chest", "legs", "feet"]

    print("\n=== ARMOR CRAFTING ===")
    print("Select armor piece to craft:")
    for i, piece in enumerate(armor_pieces, 1):
        print(f"{i}. {piece.title()}")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice not in ["1", "2", "3", "4"]:
        print("Invalid choice.")
        return

    piece_type = armor_pieces[int(choice) - 1]
    recipes = ARMOR_RECIPES.get(piece_type, [])

    if not recipes:
        print(f"No {piece_type} recipes available.")
        return

    print(f"\n=== Available {piece_type.title()} Recipes ===")
    for i, recipe in enumerate(recipes, 1):
        print(f"{i}. {recipe['name']} (Tier: {recipe['tier']})")
        print(
            f"   DEF: +{recipe['def'] + (quality('loom')-1)*2}, HP: +{recipe['hp']}, SPD: {recipe['spd']}"
        )
        print(f"   Materials: {recipe['materials']}, Cost: {recipe['cost']} gold")

    recipe_choice = input(f"\nSelect recipe (1-{len(recipes)}): ").strip()

    if not recipe_choice.isdigit() or int(recipe_choice) < 1 or int(recipe_choice) > len(recipes):
        print("Invalid choice.")
        return

    recipe = recipes[int(recipe_choice) - 1]

    # Check materials
    for material, amount in recipe["materials"].items():
        material_list = (
            player.get("cloths", [])
            if material in CLOTHS
            else player.get("leathers", []) if material in LEATHERS else player.get("metals", [])
        )
        if material_list.count(material) < amount:
            print(f"Not enough {material}. Need {amount}, have {material_list.count(material)}")
            return

    # Check gold
    if player["gold"] < recipe["cost"]:
        print(f"Not enough gold. Need {recipe['cost']}, have {player['gold']}")
        return

    # Consume materials
    for material, amount in recipe["materials"].items():
        if material in CLOTHS:
            for _ in range(amount):
                player["cloths"].remove(material)
        elif material in LEATHERS:
            for _ in range(amount):
                player["leathers"].remove(material)
        else:
            for _ in range(amount):
                player["metals"].remove(material)

    player["gold"] -= recipe["cost"]

    # Create armor piece
    armor_piece = {
        "name": recipe["name"],
        "type": piece_type,
        "level": 1,
        "rarity": recipe["tier"],
        "def": recipe["def"],
        "hp": recipe["hp"],
        "spd": recipe["spd"],
        "materials": recipe["materials"],
    }

    from source_story import rank, craft_xp

    armor_piece["def"] += (quality("loom") - 1) * 2 + rank(player, "weaving") - 1
    craft_xp(player, "weaving")
    from artisan_addons import apply_traits
    apply_traits(player, armor_piece, "weaving")
    player.setdefault("armours", []).append(armor_piece)
    player.setdefault("crafted_armor", []).append(armor_piece)

    # Gain structure XP
    player["structures"]["loom"]["xp"] += 5

    print(f"\n✓ Successfully crafted {recipe['name']}!")
    print(f"  DEF: +{armor_piece['def']}, HP: +{recipe['hp']}, SPD: {recipe['spd']}")


def view_rune_library():
    """Display all available runes and their effects"""
    print("\n=== RUNE LIBRARY ===")
    print("All runes have comprehensive effects:")
    print()

    # RUNES is a list of dicts from data.py with 100+ runes
    for rune in RUNES:
        print(f"{rune['name']} [{rune.get('element', 'unknown').upper()}]")
        print(f"   Effect: {rune.get('effect', 'unknown')}")
        print()

    print("\nEach rune has a unique effect when used in staffs and combat.")


def travel_to_location():
    """Travel to a crafting location"""
    global player

    locations = {
        "1": ("Crimson Depths", "Forge for weapons & staff crafting"),
        "2": ("Infernal Depths", "Ignar Clan - Elemental Village (armor crafting)"),
        "3": ("Frostbound Tundra", "Glacien Tribe - Elemental Village (armor crafting)"),
        "4": ("Crystal Spire", "Voltis Enclave - Elemental Village (armor crafting)"),
        "5": ("Whispering Woods", "Sylvar Circle - Elemental Village (armor crafting)"),
        "6": ("Source Temple", "Ancient temple for staff imbuing with rune energy"),
    }

    print("\n=== TRAVEL TO CRAFTING LOCATIONS ===")
    for key, (location, desc) in locations.items():
        current = " (current)" if player.get("current_location") == location else ""
        print(f"{key}. {location}: {desc}{current}")

    choice = input("\nSelect location (1-6): ").strip()

    if choice in locations:
        location, desc = locations[choice]
        player["current_location"] = location
        print(f"\n✓ Travelled to {location}")
        print(f"  {desc}")
    else:
        print("Invalid choice.")


def init_daily_challenges():
    from challenge_progress import initialise
    initialise(player)


def init_weekly_challenges():
    from challenge_progress import initialise
    initialise(player)


def update_challenge_progress(challenge_type, amount=1):
    from challenge_progress import update
    update(player, challenge_type, amount)


def claim_challenge_reward(challenge, period):
    from challenge_progress import reward
    reward(player,challenge)


def view_daily_challenges():
    """Display and manage daily challenges"""
    init_daily_challenges()

    print("\n=== DAILY CHALLENGES ===")
    print("Complete challenges to earn rewards!\n")

    for challenge in DAILY_CHALLENGES:
        data = player["daily_challenges"][challenge["id"]]
        status = "COMPLETED" if data["completed"] else f"{data['progress']}/{challenge['target']}"
        check = "[✓]" if data["completed"] else "[ ]"
        print(f"{check} {challenge['name']}")
        print(f"   {challenge['description']}")
        print(f"   Progress: {status}")
        print(f"   Reward: {challenge['reward_gold']} gold + materials")
        print()


def view_weekly_challenges():
    """Display and manage weekly challenges"""
    init_weekly_challenges()

    print("\n=== WEEKLY CHALLENGES ===")
    print("Complete challenges for major rewards!\n")

    for challenge in WEEKLY_CHALLENGES:
        data = player["weekly_challenges"][challenge["id"]]
        status = "COMPLETED" if data["completed"] else f"{data['progress']}/{challenge['target']}"
        check = "[✓]" if data["completed"] else "[ ]"
        print(f"{check} {challenge['name']}")
        print(f"   {challenge['description']}")
        print(f"   Progress: {status}")
        print(f"   Reward: {challenge['reward_gold']} gold + materials")
        print()


def start_boss_rush():
    import sys
    from legacy_workshops import boss_rush
    boss_rush(sys.modules[__name__])


def view_boss_rush_stats():
    """Display boss rushing statistics"""
    stats = player.get("boss_rush_stats", {})

    print("\n=== BOSS RUSH STATISTICS ===")
    print(f"Total Runs: {stats.get('total_runs', 0)}")
    print(f"Best Normal Run: {stats.get('best_run_normal', 0)} bosses")
    print(f"Best Hard Run: {stats.get('best_run_hard', 0)} bosses")
    print(f"Best Nightmare Run: {stats.get('best_run_nightmare', 0)} bosses")
    print(f"Leaderboard Score: {stats.get('leaderboard_score', 0)}")


# =========================================================
# SKILL TREES SYSTEM
# =========================================================


def view_skill_tree():
    import sys
    from legacy_workshops import advanced_skills
    advanced_skills(sys.modules[__name__])


def learn_skill(tree_name, skill_name):
    from legacy_workshops import learn
    okay,message=learn(player,tree_name,skill_name)
    print(message)
    return okay


# =========================================================
# COSMETICS SHOP
# =========================================================


def view_cosmetics_shop():
    """Browse and purchase cosmetics"""
    global player

    cosmetic_currency = player.get("cosmetics", {}).get("currency", 0)

    print(f"\n=== COSMETICS SHOP ===")
    print(f"Cosmetic Currency: {cosmetic_currency}\n")

    print("CHARACTER SKINS:")
    for key, cosmetic in COSMETICS_SHOP["character_skins"].items():
        owned = (
            "OWNED"
            if key in player.get("cosmetics", {}).get("owned", [])
            else str(cosmetic["price"])
        )
        print(f"  - {cosmetic['name']}: {owned}")

    print("\nWEAPON SKINS:")
    for key, cosmetic in COSMETICS_SHOP["weapon_skins"].items():
        owned = (
            "OWNED"
            if key in player.get("cosmetics", {}).get("owned", [])
            else str(cosmetic["price"])
        )
        print(f"  - {cosmetic['name']}: {owned}")

    print("\nTITLES:")
    for key, cosmetic in COSMETICS_SHOP["titles"].items():
        owned = (
            "OWNED"
            if key in player.get("cosmetics", {}).get("owned", [])
            else str(cosmetic["price"])
        )
        print(f"  - {cosmetic['name']}: {owned}")


# =========================================================
# GUILD SYSTEM
# =========================================================


def view_guild():
    """Display guild information and options"""
    global player

    guild = player.get("guild")

    print("\n=== GUILD SYSTEM ===")

    if not guild:
        print("You are not in a guild.")
        print("1. Create Guild (Cost: 500 gold)")
        print("2. Join Guild (Enter guild name)")
        choice = input("Select: ").strip()

        if choice == "1":
            if player["gold"] >= 500:
                guild_name = input("Guild name: ").strip()
                player["guild"] = guild_name
                player["guild_rank"] = "Leader"
                player["gold"] -= 500
                print(f"Guild '{guild_name}' created!")
            else:
                print("Not enough gold!")
    else:
        print(f"Guild: {guild}")
        print(f"Rank: {player.get('guild_rank', 'Member')}")
        print(f"Guild XP: {player.get('guild_xp', 0)}")


# =========================================================
# SEASONAL EVENTS
# =========================================================


def view_seasonal_events():
    """Display current seasonal events"""
    print("\n=== SEASONAL EVENTS ===")

    for event_key, event in SEASONAL_EVENTS.items():
        print(f"{event['icon']} {event['name']} ({event['duration']} days)")
        print(f"   Unique Bosses: {', '.join(event['unique_bosses'])}")
        print(f"   Exclusive Materials: {', '.join(event['unique_materials'])}\n")


# =========================================================
# CHALLENGE MODES
# =========================================================


def view_challenge_modes():
    """Display available challenge modes"""
    print("\n=== CHALLENGE MODES ===")
    print("Play special challenge runs for unique rewards!\n")

    for mode_key, mode in CHALLENGE_MODES.items():
        print(f"{mode['name']}")
        print(f"  {mode['description']}")
        print(f"  Leaderboard: {'Yes' if mode['leaderboard'] else 'No'}\n")


# =========================================================
# STORY & LORE
# =========================================================


def view_story():
    import sys
    from source_story import journal

    journal(sys.modules[__name__])


# =========================================================
# EQUIPMENT ENCHANTING
# =========================================================


def enchant_equipment():
    global player
    from expansion_state import state as expansion_state
    if expansion_state(player).get('systems',{}).get('mode',{}).get('id')=='budget_run':
        print('Budget Run blocks purchases. End the mode to use this service.')
        return
    """Enchant gear with permanent bonuses"""

    if not player.get("weapons"):
        print("You have no weapons to enchant.")
        return

    print("\n=== EQUIPMENT ENCHANTING ===")
    print("Enchant weapons with permanent stat bonuses!\n")

    print("Your weapons:")
    for i, weapon in enumerate(player["weapons"], 1):
        enchant_count = len(weapon.get("enchantments", []))
        print(f"{i}. {weapon['name']} ({enchant_count} enchantments)")

    weapon_choice = input(f"\nSelect weapon (1-{len(player['weapons'])}): ").strip()

    if (
        not weapon_choice.isdigit()
        or int(weapon_choice) < 1
        or int(weapon_choice) > len(player["weapons"])
    ):
        print("Invalid choice.")
        return

    weapon = player["weapons"][int(weapon_choice) - 1]

    print("\nAvailable Enchantments:")
    for i, (key, ench) in enumerate(ENCHANTMENTS.items(), 1):
        print(
            f"{i}. {ench['name']} - +{ench['bonus']} {ench['stat']} ({int(ench['success_rate']*100)}% success)"
        )

    ench_choice = input(f"\nSelect enchantment (1-{len(ENCHANTMENTS)}): ").strip()

    if not ench_choice.isdigit():
        print("Invalid choice.")
        return

    ench_list = list(ENCHANTMENTS.values())
    if int(ench_choice) < 1 or int(ench_choice) > len(ench_list):
        print("Invalid choice.")
        return

    enchantment = ench_list[int(ench_choice) - 1]
    success = random.random() < enchantment["success_rate"]

    if success:
        weapon.setdefault("enchantments", []).append(enchantment["name"])
        print(f"Enchantment successful! Added {enchantment['name']}")
    else:
        print("Enchantment failed...")


# =========================================================
# NEW GAME+ MODE
# =========================================================


def start_newgame_plus():
    """Start a new prestige run with enhanced rewards"""
    global player

    if player.get("prestige_level", 0) < NEWGAME_PLUS_CONFIG["prestige_requirements"]:
        print(
            f"You need Prestige {NEWGAME_PLUS_CONFIG['prestige_requirements']} to unlock New Game+"
        )
        return

    print("\n=== NEW GAME+ ===")
    print(NEWGAME_PLUS_CONFIG["unlock_message"])
    print(f"\nDifficulty: 1.5x harder")
    print(f"Rewards: 1.3x more materials, 1.2x more gold")

    confirm = input("\nStart New Game+? (yes/no): ").strip().lower()
    if confirm == "yes":
        print("New Game+ run started!")


def view_battle_pass():
    """Track battle pass progression through seasonal tiers"""
    print("\n=== SEASONAL BATTLE PASS ===")
    current_xp = player.get("battle_pass_xp", 0)
    current_tier = player.get("battle_pass_tier", 0)
    print(f"Current Tier: {current_tier}")
    print(f"Battle Pass XP: {current_xp}\n")

    for tier_key, tier_data in BATTLE_PASS_TIERS.items():
        tier_num = int(tier_key.split("_")[1])
        completed = (
            "✓ CLAIMED" if current_tier >= tier_num else f"{tier_data['required_xp']} XP needed"
        )
        print(f"Tier {tier_num}: {completed}")
        print(f"  Rewards: {tier_data['rewards']}\n")


def perform_ritual():
    """Burn materials at ritual bonfire for temporary powerful buffs"""
    print("\n=== RITUAL BONFIRE CEREMONIES ===")
    print("Perform ceremonies to gain temporary buffs!\n")

    for i, (ritual_key, ritual) in enumerate(RITUAL_CEREMONIES.items(), 1):
        print(f"{i}. {ritual_key.replace('_', ' ').title()}")
        print(f"   Materials needed: {ritual['materials']}")
        print(f"   Duration: {ritual['duration_hours']} hours")
        print(f"   Bonus: {ritual['bonus']}\n")

    choice = input("Select ritual (1-4): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(RITUAL_CEREMONIES):
        ritual_list = list(RITUAL_CEREMONIES.items())
        ritual_key, ritual_data = ritual_list[int(choice) - 1]

        # Check if player has materials
        has_materials = True
        for material, amount in ritual_data["materials"].items():
            if player.get(material, 0) < amount:
                has_materials = False
                print(f"Not enough {material}!")
                break

        if has_materials:
            # Consume materials
            for material, amount in ritual_data["materials"].items():
                player[material] -= amount

            # Apply buff
            for stat, bonus in ritual_data["bonus"].items():
                player[stat] = player.get(stat, 0) + bonus

            player["active_buffs"] = player.get("active_buffs", {})
            player["active_buffs"][ritual_key] = ritual_data["duration_hours"]
            print(f"✨ Ritual performed! Buffs active for {ritual_data['duration_hours']} hours")
            print(f"   Bonuses: {ritual_data['bonus']}")


def battle_arena():
    """Face other players in ranked combat for arena rewards and prestige"""
    print("\n=== ARENA PVP ===")
    print("Climb the ranks through player battles!\n")

    for i, rank in enumerate(ARENA_RANKS, 1):
        print(f"{i}. {rank}")

    player_rank = player.get("arena_rank", ARENA_RANKS[0])
    print(f"\nYour Rank: {player_rank}")
    print(f"Arena Points: {player.get('arena_points', 0)}")


def discover_recipes():
    """Unlock rare crafting recipes through combat and exploration"""
    print("\n=== RECIPE DISCOVERY ===")
    discovered = player.get("discovered_recipes", [])
    print(f"Recipes Discovered: {len(discovered)}\n")

    for recipe_key, recipe in RECIPE_DISCOVERY.items():
        status = (
            "DISCOVERED"
            if recipe_key in discovered
            else f"{int(recipe['discovery_rate']*100)}% chance"
        )
        print(f"{recipe_key}: {status}")


def trading_post():
    """Create trade offers for other players with auto-expiry"""
    print("\n=== PLAYER TRADING ===")
    print(f"Active Offers: {len(player.get('trade_offers', []))}/{TRADING_CONFIG['max_offers']}\n")

    print("1. Create Trade Offer")
    print("2. View Active Offers")
    print("3. Browse Market Offers")


def build_town():
    """Construct and upgrade town structures for passive resource generation"""
    print("\n=== TOWN BUILDING ===")
    print("Build structures to generate passive resources!\n")

    for struct_key, struct in TOWN_STRUCTURES.items():
        level = player.get("town_structures", {}).get(struct_key, 0)
        print(f"{struct['name']} (Level {level})")
        print(f"  Bonus: {struct['bonus']} | Upgrade Cost: {struct['cost']} gold\n")


def view_login_streak():
    """View daily login streak bonuses"""
    print("\n=== DAILY LOGIN STREAK ===")
    streak = player.get("login_streak", 0)
    print(f"Current Streak: {streak} days\n")

    for day, bonus in LOGIN_BONUSES.items():
        day_num = int(day.split("_")[1])
        status = "CLAIMED" if streak >= day_num else "LOCKED"
        print(f"Day {day_num}: {status}")
        print(f"  Rewards: {bonus}\n")


def join_faction():
    """Align with a faction for permanent stat bonuses and exclusive vendors"""
    print("\n=== FACTIONS ===")
    current_faction = player.get("faction", None)
    print(f"Current Faction: {current_faction or 'None'}\n")

    for faction_key, faction in FACTIONS.items():
        print(f"{faction['icon']} {faction['name']}")
        print(f"  Bonuses: {faction['bonuses']}\n")


def treasure_hunting():
    """Find treasure maps with hidden loot stashes"""
    print("\n=== TREASURE MAPS ===")
    maps = player.get("treasure_maps", [])
    print(f"Treasure Maps Found: {len(maps)}\n")

    for map_key, map_data in TREASURE_MAPS.items():
        print(f"{map_data['name']}: {int(map_data['find_chance']*100)}% drop rate")
        print(f"  Treasure Value: {map_data['treasure_value']} gold\n")


def ride_mounts():
    """Collect and ride mounts for fast travel and cosmetic benefits"""
    print("\n=== MOUNTS ===")
    owned_mounts = player.get("mounts", [])
    print(f"Mounts Owned: {len(owned_mounts)}\n")

    for mount_key, mount in MOUNTS.items():
        print(f"{mount['name']}")
        print(f"  Speed: {mount['speed_bonus']}x | Cost: {mount['cost']} gold\n")


def collect_artifacts():
    """Collect legendary artifacts that grant unique bonuses"""
    print("\n=== ARTIFACTS ===")
    artifacts = player.get("artifacts", [])
    print(f"Artifacts Owned: {len(artifacts)}\n")

    for artifact_key, artifact in ARTIFACTS.items():
        status = "OWNED" if artifact_key in artifacts else "LOCKED"
        print(f"{artifact['name']} [{artifact['rarity'].upper()}]")
        print(f"  Stats: {artifact['stats']} | Status: {status}\n")


# =========================================================
# STATUS EFFECTS MANAGEMENT
# =========================================================


def apply_status_effect(target, effect_name, source="combat"):
    """Apply a status effect to a player or enemy"""
    global player

    # Determine effect type
    effect = None
    effect_type = None

    if effect_name in OFFENSIVE_STATUS:
        effect = OFFENSIVE_STATUS[effect_name]
        effect_type = "offensive"
    elif effect_name in DEFENSIVE_STATUS:
        effect = DEFENSIVE_STATUS[effect_name]
        effect_type = "defensive"
    elif effect_name in UTILITY_STATUS:
        effect = UTILITY_STATUS[effect_name]
        effect_type = "utility"
    elif effect_name in BOSS_EXCLUSIVE_STATUS:
        effect = BOSS_EXCLUSIVE_STATUS[effect_name]
        effect_type = "boss"

    if not effect:
        return False

    # Initialize active effects if needed
    if "active_effects" not in target:
        target["active_effects"] = {}

    # Apply effect
    target["active_effects"][effect_name] = {
        "turns_remaining": effect.get("duration", 1),
        "type": effect_type,
        "data": effect,
    }

    return True


def remove_status_effect(target, effect_name):
    """Remove a specific status effect"""
    if "active_effects" in target and effect_name in target["active_effects"]:
        del target["active_effects"][effect_name]
        return True
    return False


def cure_status_effects(target, cure_name):
    """Apply a cure to remove multiple status effects"""
    cure = STATUS_CURES.get(cure_name)
    if not cure:
        return False

    if "all" in cure:
        target["active_effects"] = {}
        return True

    for effect in cure:
        remove_status_effect(target, effect)

    return True


def view_active_effects():
    """Display all active status effects on player"""
    print("\n=== ACTIVE STATUS EFFECTS ===")

    active_effects = player.get("active_effects", {})

    if not active_effects:
        print("No active effects.\n")
        return

    print(f"Active Effects: {len(active_effects)}\n")

    for effect_name, effect_data in active_effects.items():
        effect_info = effect_data["data"]
        turns = effect_data["turns_remaining"]
        print(f"{effect_info['icon']} {effect_info['name']} ({turns} turns)")
        print(f"   {effect_info.get('description', 'Active combat effect')}\n")


def update_status_effects():
    """Decrease status effect duration each turn"""
    global player

    if "active_effects" not in player:
        return

    effects_to_remove = []

    for effect_name, effect_data in player["active_effects"].items():
        effect_data["turns_remaining"] -= 1

        if effect_data["turns_remaining"] <= 0:
            effects_to_remove.append(effect_name)
        else:
            # Apply per-turn damage/healing
            effect_info = effect_data["data"]

            if "damage_per_turn" in effect_info:
                player["hp"] -= effect_info["damage_per_turn"]

            if "hp_restore_per_turn" in effect_info:
                player["hp"] += effect_info["hp_restore_per_turn"]

    # Remove expired effects
    for effect_name in effects_to_remove:
        del player["active_effects"][effect_name]


def check_status_synergies():
    """Check if active effects create synergies"""
    active_effect_names = set(player.get("active_effects", {}).keys())

    for synergy_key, synergy in STATUS_SYNERGIES.items():
        if set(synergy["trigger"]).issubset(active_effect_names):
            print(f"\n⚡ SYNERGY TRIGGERED: {synergy['result']}!")
            print(f"   {synergy['effect']}")


def imbue_staff():
    from village_life import require_service, quality

    if not require_service("temple"):
        return
    """Charge empty staffs with elemental cores at the Source Temple"""
    global player

    player_staffs = player.get("staffs", [])
    player_cores = player.get("core_attunements", [])

    if not player_staffs:
        print("\nYou have no staffs to imbue.")
        return

    if not player_cores:
        print("\nAsk an elemental clan for its blessing first. Their core stays in the village.")
        return

    print("\n=== SOURCE TEMPLE - STAFF IMBUING ===")
    print("Charge your empty staffs with elemental core energy.\n")

    print("Your staffs:")
    for i, staff in enumerate(player_staffs, 1):
        charged = "✓ CHARGED" if staff.get("charged") else "Empty"
        core_used = staff.get("core_used", "None")
        print(f"{i}. {staff['name']} [{charged}] (Core: {core_used})")

    staff_choice = input(f"\nSelect staff to charge (1-{len(player_staffs)}): ").strip()

    if (
        not staff_choice.isdigit()
        or int(staff_choice) < 1
        or int(staff_choice) > len(player_staffs)
    ):
        print("Invalid choice.")
        return

    selected_staff = player_staffs[int(staff_choice) - 1]

    if selected_staff.get("charged"):
        print(f"This staff is already charged with {selected_staff.get('core_used')}!")
        return

    print(f"\nYour elemental cores:")
    for i, core_name in enumerate(player_cores, 1):
        core_data = ELEMENTAL_CORES.get(core_name, {})
        print(f"{i}. {core_name} ({core_data.get('element', 'unknown')})")
        print(f"   Effect: {core_data.get('on_hit_effect', 'unknown')}")

    core_choice = input(f"\nSelect core to imbue (1-{len(player_cores)}): ").strip()

    if not core_choice.isdigit() or int(core_choice) < 1 or int(core_choice) > len(player_cores):
        print("Invalid choice.")
        return

    selected_core_name = player_cores[int(core_choice) - 1]
    selected_core = ELEMENTAL_CORES.get(selected_core_name)

    if not selected_core:
        print("Core not found!")
        return

    if player["gold"] < 50:
        print("Channeling the clan’s blessing costs 50 souls.")
        return
    player["gold"] -= 50
    # Charge the staff
    selected_staff["charged"] = True
    selected_staff["core_used"] = selected_core_name
    selected_staff["element"] = selected_core.get("element")
    selected_staff["on_hit_effect"] = selected_core.get("on_hit_effect")
    selected_staff["bonus_atk"] = selected_core.get("bonus_atk", 0)
    selected_staff["power"] = (
        selected_staff.get("power", 0)
        + selected_core.get("bonus_atk", 0)
        + (quality("temple") - 1) * 2
    )

    # Remove core from inventory
    # The clan core and its blessing stay with their owners; pay for channeling, not extraction.

    # Gain Source Temple XP
    player["structures"].setdefault("source_temple", {"level": 1, "xp": 0})
    player["structures"]["source_temple"]["xp"] += 15

    from source_story import craft_xp

    craft_xp(player, "imbuing")
    # Track imbuement history
    player.setdefault("imbuement_history", []).append(
        {
            "staff": selected_staff["name"],
            "core": selected_core_name,
            "element": selected_core.get("element"),
            "effect": selected_core.get("on_hit_effect"),
        }
    )

    print(f"\n✨ Successfully charged {selected_staff['name']} with {selected_core_name}!")
    print(f"   Element: {selected_core.get('element').title()}")
    print(f"   Effect: {selected_core.get('on_hit_effect')}")
    print(f"   ATK Bonus: +{selected_core.get('bonus_atk', 0)}")


def craft_staff():
    from village_life import require_service, quality

    if not require_service("tower"):
        return
    """Create staffs by combining runes"""
    global player

    print("\n=== STAFF CRAFTING ALTAR ===")
    print("Combine 2-5 runes to create a powerful staff.")

    player_runes = player.get("runes", [])
    if len(player_runes) < 2:
        print("You need at least 2 runes to craft a staff.")
        return

    print(f"\nYour runes ({len(player_runes)} total):")
    for i, rune in enumerate(player_runes, 1):
        rune_name = rune.get("name", "Unknown")
        rune_effect = rune.get("effect", "unknown")
        print(f"  {i}. {rune_name} ({rune_effect})")

    selected_runes = []
    max_runes = min(5, len(player_runes))

    print(f"\nSelect 2-{max_runes} runes to combine (type rune number, then 'done' when finished):")

    while len(selected_runes) < max_runes:
        choice = input(f"Rune {len(selected_runes) + 1} (or 'done'): ").strip()

        if choice.lower() == "done":
            if len(selected_runes) >= 2:
                break
            else:
                print("Need at least 2 runes.")
                continue

        if choice.isdigit() and 1 <= int(choice) <= len(player_runes):
            idx = int(choice) - 1
            selected_rune = player_runes[idx]
            if any(selected_rune is r for r in selected_runes):
                print("Choose another inventory copy; this rune is already selected.")
                continue
            selected_runes.append(selected_rune)
            print(f"  Added: {selected_rune.get('name')}")
        else:
            print("Invalid choice.")

    if len(selected_runes) < 2:
        print("Cancelled staff crafting.")
        return

    # Generate staff name from rune combination
    rune_count = len(selected_runes)
    rune_names = [r.get("name") for r in selected_runes]

    # Check if this matches a special fusion recipe
    staff_name = f"Staff of {' & '.join(rune_names[:3])}"
    recipe_match = SPECIAL_FUSION_RECIPES.get(frozenset(rune_names))
    if recipe_match:
        staff_name = recipe_match.get("name", staff_name).replace(" Rune", " Staff")

    # Create staff with all rune effects
    staff = {
        "name": staff_name,
        "type": "staff",
        "level": 1,
        "rarity": "rare" if recipe_match else "uncommon",
        "runes": rune_names,
        "effects": [r.get("effect") for r in selected_runes],
        "stored_runes": [dict(r) for r in selected_runes],
        "power": 5 + 3 * len(selected_runes) + (quality("tower") - 1) * 3,
        "elements": [r.get("element") for r in selected_runes],
    }

    from source_story import rank, craft_xp

    staff["power"] += rank(player, "enchanting") - 1
    craft_xp(player, "enchanting")
    from artisan_addons import apply_traits
    apply_traits(player, staff, "enchanting")
    player.setdefault("crafted_staffs", []).append(staff)
    player.setdefault("staffs", []).append(staff)

    # Remove runes from inventory
    for rune in selected_runes:
        if rune in player.get("runes", []):
            player["runes"].remove(rune)

    # Gain structure XP
    player["structures"]["enchantment_tower"]["xp"] += 5 * rune_count

    print(f"\n✓ Successfully forged {staff_name}!")
    print(f"  Runes: {', '.join(rune_names)}")
    print(f"  Effects: {', '.join(staff['effects'])}")


def upgrade_structure(structure_key):
    """Upgrade a crafting structure"""
    global player

    if structure_key not in STRUCTURES:
        print("Invalid structure.")
        return

    structure = STRUCTURES[structure_key]
    cost = structure["upgrade_cost"]

    player_struct = player["structures"][structure_key]
    new_level = player_struct["level"] + 1

    print(f"\nUpgrade {structure['name']} to level {new_level}?")
    print(f"Cost: {cost} gold")

    if player["gold"] < cost:
        print(f"Not enough gold. Need {cost}, have {player['gold']}")
        return

    player["gold"] -= cost
    player_struct["level"] = new_level

    print(f"✓ {structure['name']} upgraded to level {new_level}!")


def salvage_equipment():
    import sys
    from village_life import salvage

    salvage(sys.modules[__name__])


def transmute_materials():
    """Convert materials between types"""
    global player

    print("\n=== MATERIAL TRANSMUTATION ===")
    print("Convert materials to upgrade your gear.")

    transmutations = [
        {
            "name": "Copper to Iron (3 copper → 1 iron)",
            "cost": 25,
            "input": {"Copper": 3},
            "output": {"Iron": 1},
        },
        {
            "name": "Linen to Silk (3 linen → 1 silk)",
            "cost": 100,
            "input": {"Linen": 3},
            "output": {"Silk": 1},
        },
        {"name": "Common Cores to Rare (5 cores → 1 rare)", "cost": 500},
    ]

    print("\nAvailable transmutations:")
    for i, tx in enumerate(transmutations[:2], 1):
        print(f"  {i}. {tx['name']} - {tx['cost']} gold")

    choice = input("\nSelect transmutation: ").strip()

    if not choice.isdigit() or int(choice) < 1 or int(choice) > 2:
        print("Invalid choice.")
        return

    tx = transmutations[int(choice) - 1]

    if player["gold"] < tx["cost"]:
        print(f"Not enough gold. Need {tx['cost']}, have {player['gold']}")
        return

    # Check materials
    for material, amount in tx["input"].items():
        if material in CLOTHS:
            inventory = player.get("cloths", [])
        elif material in LEATHERS:
            inventory = player.get("leathers", [])
        else:
            inventory = player.get("metals", [])

        if inventory.count(material) < amount:
            print(f"Not enough {material}. Need {amount}, have {inventory.count(material)}")
            return

    # Consume input
    player["gold"] -= tx["cost"]
    for material, amount in tx["input"].items():
        if material in CLOTHS:
            inventory = player.setdefault("cloths", [])
        elif material in LEATHERS:
            inventory = player.setdefault("leathers", [])
        else:
            inventory = player.setdefault("metals", [])
        for _ in range(amount):
            inventory.remove(material)

    # Add output
    for material, amount in tx["output"].items():
        if material in CLOTHS:
            player.setdefault("cloths", []).extend([material] * amount)
        elif material in LEATHERS:
            player.setdefault("leathers", []).extend([material] * amount)
        else:
            player.setdefault("metals", []).extend([material] * amount)

    print(f"✓ Transmutation complete!")
    print(f"  Gained: {tx['output']}")


# =========================================================
#  SHOPS & MERCHANTS
# =========================================================


def merchant_shop(merchant_type):
    """Interactive merchant shop interface"""
    global player

    merchants = {
        "forge_master": {
            "name": "Forge Master",
            "icon": "🔨",
            "desc": "Rare metals and equipment dealer",
            "buy_items": [
                {"name": "Mythril", "type": "metal", "price": 300},
                {"name": "Adamantine", "type": "metal", "price": 500},
                {"name": "Titanium", "type": "metal", "price": 250},
            ],
            "sell_multiplier": 0.8,
        },
        "weaver": {
            "name": "Weaver",
            "icon": "🧵",
            "desc": "Fine cloths and woven armor",
            "buy_items": [
                {"name": "Silk", "type": "cloth", "price": 150},
                {"name": "Dragon Silk", "type": "cloth", "price": 400},
                {"name": "Starweave", "type": "cloth", "price": 350},
            ],
            "sell_multiplier": 0.75,
        },
        "rune_master": {
            "name": "Rune Master",
            "icon": "✨",
            "desc": "Mysterious elemental runes",
            "buy_items": [
                {"name": "Flame Rune", "type": "rune", "price": 150},
                {"name": "Ice Rune", "type": "rune", "price": 150},
                {"name": "Lightning Rune", "type": "rune", "price": 150},
                {"name": "Void Rune", "type": "rune", "price": 250},
                {"name": "Dragon Rune", "type": "rune", "price": 300},
                {"name": "Phoenix Rune", "type": "rune", "price": 300},
            ],
            "sell_multiplier": 0.7,
        },
    }

    merchant = merchants.get(merchant_type)
    if not merchant:
        return

    while True:
        print(f"\n=== {merchant['icon']} {merchant['name']} ===")
        print(merchant["desc"])
        print(f"\nYour gold: {player['gold']}")
        print("\n1. Buy items")
        print("2. Sell equipment")
        print("3. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            print(f"\n{merchant['icon']} {merchant['name']}'s Stock:")
            for i, item in enumerate(merchant["buy_items"], 1):
                print(f"  {i}. {item['name']} - {item['price']} gold")

            item_choice = input("\nSelect item to buy (or 'back'): ").strip()

            if item_choice.lower() == "back":
                continue

            if item_choice.isdigit() and 1 <= int(item_choice) <= len(merchant["buy_items"]):
                item = merchant["buy_items"][int(item_choice) - 1]

                if player["gold"] < item["price"]:
                    print(f"Not enough gold. Need {item['price']}, have {player['gold']}")
                    continue

                player["gold"] -= item["price"]

                if item["type"] == "metal":
                    player.setdefault("metals", []).append(item["name"])
                elif item["type"] == "cloth":
                    player.setdefault("cloths", []).append(item["name"])
                elif item["type"] == "rune":
                    # Find rune from RUNES list and add to inventory
                    for rune in RUNES:
                        if rune.get("name") == item["name"]:
                            player.setdefault("runes", []).append(rune.copy())
                            break

                print(f"✓ Purchased {item['name']}!")

        elif choice == "2":
            # Sell weapons/armor
            print("\nAvailable equipment to sell:")
            equipment = player.get("weapons", []) + player.get("crafted_armor", [])

            if not equipment:
                print("You have no equipment to sell.")
                continue

            for i, item in enumerate(equipment, 1):
                base_value = item.get("atk", 0) * 10 + item.get("def", 0) * 15
                sell_price = int(base_value * merchant["sell_multiplier"])
                print(f"  {i}. {item['name']} - {sell_price} gold")

            eq_choice = input("\nSelect item to sell (or 'back'): ").strip()

            if eq_choice.lower() == "back":
                continue

            if eq_choice.isdigit() and 1 <= int(eq_choice) <= len(equipment):
                item = equipment[int(eq_choice) - 1]
                base_value = item.get("atk", 0) * 10 + item.get("def", 0) * 15
                sell_price = int(base_value * merchant["sell_multiplier"])

                player["gold"] += sell_price
                equipment.remove(item)

                print(f"✓ Sold {item['name']} for {sell_price} gold!")

        elif choice == "3":
            break


# =========================================================
# PHASE 6: MASTERY & LONG-CAMPAIGN FEATURES
# =========================================================


def view_material_mastery():
    """Display mastery levels for materials and structures"""
    global player

    print("\n=== MATERIAL MASTERY ===")
    print("Level up your crafting by using materials repeatedly.")
    print()

    mastery = player.get("material_mastery", {})

    print("Material Mastery:")
    for material, data in sorted(mastery.items()):
        level = data.get("level", 0)
        xp = data.get("xp", 0)
        xp_needed = (level + 1) * 50  # XP needed for next level
        bar_fill = int((xp / xp_needed) * 10)
        bar = "█" * bar_fill + "░" * (10 - bar_fill)
        print(f"  {material:15} Lvl {level:2} [{bar}] {xp}/{xp_needed} XP")

    print("\nStructure Mastery:")
    for structure_key, struct_data in player.get("structures", {}).items():
        level = struct_data.get("level", 1)
        xp = struct_data.get("xp", 0)
        xp_needed = level * 100
        bar_fill = int((xp / xp_needed) * 10)
        bar = "█" * bar_fill + "░" * (10 - bar_fill)
        struct_name = STRUCTURES[structure_key]["name"]
        print(f"  {struct_name:20} Lvl {level:2} [{bar}] {xp}/{xp_needed} XP")


def view_equipment_sets():
    """Track equipment sets and bonuses"""
    global player

    print("\n=== EQUIPMENT SETS ===")
    print("Collect matching items to unlock set bonuses!")
    print()

    # Check what sets the player is progressing toward
    player_weapons = {item["name"]: item for item in player.get("weapons", [])}
    player_armor = {item["name"]: item for item in player.get("crafted_armor", [])}
    player_staffs = {item["name"]: item for item in player.get("staffs", [])}

    for set_name, set_data in EQUIPMENT_SETS.items():
        pieces = set_data.get("pieces", [])
        collected = sum(
            1
            for piece in pieces
            if piece in player_weapons or piece in player_armor or piece in player_staffs
        )

        print(f"{set_name} ({collected}/{len(pieces)} pieces)")
        for piece in pieces:
            status = (
                "✓"
                if piece in player_weapons or piece in player_armor or piece in player_staffs
                else "✗"
            )
            print(f"  {status} {piece}")

        if collected > 0:
            bonuses = set_data.get("bonuses", {})
            if str(collected) in bonuses:
                bonus = bonuses[str(collected)]
                print(f"  ✓ ACTIVE BONUS: {bonus}")
        print()


def legendary_weapon_quest():
    """Quest to craft a legendary weapon"""
    global player

    print("\n=== LEGENDARY WEAPON QUEST ===")
    print("Collect rare materials to forge a legendary weapon!")
    print()

    quest_requirements = {
        "Abyssium": 3,
        "Dragon Hide": 2,
        "Void Core": 1,
    }

    print("Quest Requirements:")
    for material, needed in quest_requirements.items():
        if material in METALS:
            have = player.get("metals", []).count(material)
        elif material in LEATHERS:
            have = player.get("leathers", []).count(material)
        else:
            have = 0

        status = "✓" if have >= needed else "✗"
        print(f"  {status} {material}: {have}/{needed}")

    # Check if player can complete quest
    has_all = all(
        (player.get("metals", []).count(material) if material in METALS else 0) >= needed
        or (player.get("leathers", []).count(material) if material in LEATHERS else 0) >= needed
        for material, needed in quest_requirements.items()
    )

    if has_all:
        print("\n✓ You can complete this quest!")
        confirm = input("\nForge legendary weapon? (yes/no): ").strip()

        if confirm.lower() == "yes":
            for material, needed in quest_requirements.items():
                if material in METALS:
                    for _ in range(needed):
                        player["metals"].remove(material)
                elif material in LEATHERS:
                    for _ in range(needed):
                        player["leathers"].remove(material)

            legendary = {
                "name": "Blade of the Abyss",
                "type": "weapon",
                "tier": "legendary",
                "atk": 50,
                "rarity": "legendary",
                "materials": quest_requirements,
            }

            player.setdefault("weapons", []).append(legendary)
            print("\n✓ Legendary weapon forged: Blade of the Abyss!")
            print("  ATK: +50 | Rarity: LEGENDARY")
    else:
        print("\n✗ You need to gather more materials.")


def prestige_shop():
    """Prestige-exclusive items and materials"""
    global player

    prestige = player.get("prestige_level", 0)

    if prestige == 0:
        print("\nYou must reach prestige level 1 to access prestige shop.")
        return

    print(f"\n=== PRESTIGE SHOP (Level {prestige}) ===")
    print("Exclusive materials and items for prestige players!")
    print()

    prestige_unlocks = {
        1: ["Mythril", "Sky Core"],
        2: ["Adamantine", "Void Core"],
        3: ["Creator Alloy", "Omnipotent Core"],
    }

    unlocked = prestige_unlocks.get(prestige, [])

    print("Available items:")
    for i, item in enumerate(unlocked, 1):
        if item in METALS:
            price = 200 * prestige
        else:
            price = 500 * prestige
        print(f"  {i}. {item} - {price} gold")


def view_merchants():
    """Visit the merchant trading post"""
    global player

    while True:
        print("\n=== TRADING POST ===")
        print("Welcome to the Trading Post! Meet our merchants:")
        print("\n1. Forge Master 🔨 (Rare metals)")
        print("2. Weaver 🧵 (Fine cloths)")
        print("3. Rune Master ✨ (Elemental runes)")
        print("4. Exit")

        choice = input("\nSelect merchant: ").strip()

        if choice == "1":
            merchant_shop("forge_master")
        elif choice == "2":
            merchant_shop("weaver")
        elif choice == "3":
            merchant_shop("rune_master")
        elif choice == "4":
            break
        else:
            print("Invalid choice.")


def view_crafting_hub():
    import sys
    from village_life import crafting_hub

    crafting_hub(sys.modules[__name__])


if __name__ == "__main__":
    game()
