import random
import json
import os
import hashlib

import ui as _ui

from status_effects import (
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
    owned_names = {c["name"] for c in player.get("companions", [])}
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
    for companion in player.get("companions", []):
        if companion.get("stage", 0) >= 2:
            continue
        companion["xp"] += 1
        if companion["stage"] == 0 and companion["xp"] >= 3:
            companion["stage"] = 1
            print(f"✨ {companion['name']} has advanced to stage 1!")
        elif companion["stage"] == 1 and companion["xp"] >= 6:
            companion["stage"] = 2
            print(f"✨ {companion['name']} is now fully evolved!")


def apply_companion_support(enemy):
    for companion in player.get("companions", []):
        if not companion.get("can_battle") or companion.get("stage", 0) == 0:
            continue
        elem = companion["element"]
        print(f"✨ {companion['name']} assists in battle with {elem} power!")
        if elem == "fire":
            enemy["hp"] -= 3
            enemy.setdefault("status", {})["burn"] = max(
                enemy["status"].get("burn", 0), 1
            )
        elif elem == "ice":
            enemy["hp"] -= 2
            enemy.setdefault("status", {})["freeze"] = max(
                enemy["status"].get("freeze", 0), 1
            )
        elif elem == "water":
            enemy["def"] = max(0, enemy.get("def", 0) - 1)
        elif elem == "earth":
            player["def"] += 1
        elif elem == "poison":
            enemy.setdefault("status", {})["poison"] = max(
                enemy["status"].get("poison", 0), 2
            )
        elif elem == "shadow":
            enemy.setdefault("active_buffs", {})["blind"] = 1
        elif elem == "void":
            enemy.setdefault("status", {})["void"] = max(
                enemy["status"].get("void", 0), 1
            )
        elif elem == "light":
            player["hp"] = min(player["max_hp"], player["hp"] + 3)
        elif elem == "nature":
            player["hp"] = min(player["max_hp"], player["hp"] + 2)
        elif elem == "soul":
            enemy["hp"] -= 2
            player["hp"] += 2


def recruit_companion(companion):
    if len(player.get("companions", [])) >= 3:
        print("You already have 3 companions and cannot recruit another.")
        return False
    recruit = companion.copy()
    recruit["stage"] = 0
    recruit["xp"] = 0
    player.setdefault("companions", []).append(recruit)
    print(f"🐾 {recruit['name']} has joined your party!")
    return True
def view_companion_status():
    companions = player.get("companions", [])

    if not companions:
        print("You have no companions.")
        return

    print("\n=== COMPANION STATUS ===")

    for i, companion in enumerate(companions, 1):
        print(f"\n{i}. {companion['name']}")
        print(f"   Element: {companion['element'].title()}")
        print(f"   Stage: {companion.get('stage', 0)}")
        print(f"   XP: {companion.get('xp', 0)}")
        print(f"   Battle Companion: {'Yes' if companion.get('can_battle') else 'No'}")

        if companion.get("stage", 0) == 0:
            print("   Evolution Progress: "
                  f"{companion.get('xp', 0)}/3 XP")
        elif companion.get("stage", 0) == 1:
            print("   Evolution Progress: "
                  f"{companion.get('xp', 0)}/6 XP")
        else:
            print("   Evolution Progress: Fully Evolved")
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
    user.setdefault("active_buffs", {})
    enemy.setdefault("active_buffs", {})
    effect = rune.get("effect")

    if effect == "fusion":
        special = rune.get("special_effect")
        if special:
            print(f"✨ Special fusion effect activated: {special}")
        for component in rune.get("components", []):
            apply_rune_effect({"effect": component}, user, enemy)
        return

    if effect == "burn":
        enemy.setdefault("status", {})["burn"] = 3
    elif effect == "poison":
        enemy.setdefault("status", {})["poison"] = 4
    elif effect == "bleed":
        enemy.setdefault("status", {})["bleed"] = 3
    elif effect == "shock":
        enemy.setdefault("status", {})["shock"] = 2
    elif effect == "freeze":
        enemy.setdefault("status", {})["freeze"] = 2
    elif effect == "void":
        enemy.setdefault("status", {})["void"] = 3
    elif effect == "void_burn":
        enemy.setdefault("status", {})["void"] = 2
        enemy.setdefault("status", {})["burn"] = 2
        enemy["hp"] -= 4
    elif effect == "curse":
        enemy.setdefault("status", {})["curse"] = 3
    elif effect == "fear":
        enemy.setdefault("status", {})["fear"] = 2
    elif effect == "sleep":
        enemy.setdefault("status", {})["sleep"] = 1
    elif effect == "stun":
        enemy.setdefault("active_buffs", {})["stun"] = 1
    elif effect == "hellfire":
        enemy.setdefault("status", {})["burn"] = 3
        enemy["hp"] -= 5
    elif effect == "sun_blast":
        enemy.setdefault("status", {})["burn"] = 2
        enemy["hp"] -= 8
    elif effect == "magma":
        enemy.setdefault("status", {})["magma"] = 3
        enemy["hp"] -= 4
    elif effect == "chain_shock":
        enemy.setdefault("status", {})["shock"] = 3
        enemy["hp"] -= 4
    elif effect == "deadly_poison":
        enemy.setdefault("status", {})["poison"] = 5
        enemy["def"] = max(0, enemy.get("def", 0) - 1)
    elif effect == "giant_strength":
        user.setdefault("active_buffs", {})["giant_strength"] = 3
    elif effect == "regen":
        user["hp"] += 5
    elif effect == "greater_regen":
        user["hp"] += 10
    elif effect == "heal_tick":
        user["active_buffs"]["heal_tick"] = 3
    elif effect == "armor_break":
        enemy["def"] = max(0, enemy.get("def", 0) - 2)
    elif effect == "defense_up":
        user["def"] += 2
    elif effect == "speed_up":
        user["active_buffs"]["speed_up"] = 3
    elif effect == "crit_up":
        user["active_buffs"]["crit_up"] = 3
    elif effect == "elemental_balance":
        user["active_buffs"]["elemental_balance"] = 3
    elif effect == "supercharge":
        user["active_buffs"]["supercharge"] = 3
    elif effect == "fusion_boost":
        user["active_buffs"]["fusion_boost"] = 3
    elif effect == "life_drain":
        drain = 5
        enemy["hp"] -= drain
        user["hp"] += drain
    elif effect == "dragon_fury":
        enemy["hp"] -= 15
    elif effect == "rebirth":
        user["active_buffs"]["rebirth"] = 1
    elif effect == "holy_barrier":
        user["active_buffs"]["barrier"] = 2
    elif effect == "nature_blessing":
        user["hp"] += 8
    elif effect == "time_lock":
        enemy["active_buffs"]["stun"] = 1
    elif effect == "reality_bend":
        enemy["hp"] -= random.randint(5, 20)
    elif effect == "soak":
        enemy["def"] = max(0, enemy.get("def", 0) - 1)
    elif effect == "blind":
        enemy["active_buffs"]["blind"] = 2
    elif effect == "mana_regen":
        user["mana"] = min(user.get("mana", 0) + 5, 20)
    elif effect == "burn_freeze":
        enemy.setdefault("status", {})["burn"] = 3
        enemy.setdefault("status", {})["freeze"] = 2
    elif effect == "root":
        enemy["active_buffs"]["root"] = 2
    elif effect == "divine_luck":
        user["active_buffs"]["divine_luck"] = 3
    elif effect == "starfall":
        enemy["hp"] -= 8
    elif effect == "moon_guard":
        user["active_buffs"]["moon_guard"] = 3
    elif effect == "slow_time":
        enemy["active_buffs"]["slow_time"] = 3
    elif effect == "warp":
        user["active_buffs"]["warp"] = 1
    elif effect == "crush":
        enemy["def"] = max(0, enemy.get("def", 0) - 4)
    elif effect == "random_effect":
        sub_effect = random.choice(
            [
                "burn",
                "poison",
                "freeze",
                "shock",
                "life_drain",
                "greater_regen",
                "armor_break",
                "defense_up",
                "speed_up",
            ]
        )
        apply_rune_effect({"effect": sub_effect}, user, enemy)
    elif effect == "stability":
        user["active_buffs"]["stability"] = 3
    elif effect == "soul_drain":
        enemy["hp"] -= 10
        user["hp"] += 10
    elif effect == "execute":
        if enemy["hp"] <= 15:
            enemy["hp"] = 0
        else:
            enemy["hp"] -= 2
    elif effect == "double_cast":
        user["active_buffs"]["double_cast"] = 1
    elif effect == "reflect":
        user["active_buffs"]["reflect"] = 1
    elif effect == "tidal_wave":
        enemy["hp"] -= 5
        enemy.setdefault("status", {})["shock"] = 2
    elif effect == "fortress":
        user["active_buffs"]["fortress"] = 3
    elif effect == "dimension_break":
        enemy["hp"] -= 10
        if "status" in enemy:
            enemy["status"].clear()
    elif effect == "creation":
        user.setdefault("status", {})["creation"] = 3
    elif effect == "berserk":
        user.setdefault("active_buffs", {})["berserk"] = 3
        user["atk"] += 10
        user["def"] = max(0, user.get("def", 0) - 3)
        print("💢 Berserk! ATK +10, DEF -3")
    elif effect == "sacrifice":
        sacrifice_dmg = min(user["hp"] - 1, 20)
        user["hp"] -= sacrifice_dmg
        enemy["hp"] -= sacrifice_dmg * 2
        print(
            f"💀 Sacrifice! Lost {sacrifice_dmg} HP, dealt {sacrifice_dmg * 2} to enemy!"
        )
    elif effect == "shatter":
        enemy["def"] = 0
        print("💥 Shatter! Enemy defense destroyed!")
    elif effect == "overload":
        burst = 10 + user.get("mana", 0) * 2
        enemy["hp"] -= burst
        user["mana"] = 0
        print(f"⚡ Overload! Spent all mana for {burst} damage!")
    elif effect == "thorns":
        user.setdefault("active_buffs", {})["thorns"] = 4
        print("🌵 Thorns! Attackers will take reflected damage!")
    elif effect == "banish":
        enemy.setdefault("status", {}).clear()
        enemy.setdefault("active_buffs", {}).clear()
        enemy["hp"] -= 12
        print("✨ Banish! Stripped all enemy status effects + 12 damage!")
    elif effect == "lightning_storm":
        enemy.setdefault("status", {})["shock"] = 4
        enemy["hp"] -= 10
        enemy["def"] = max(0, enemy.get("def", 0) - 2)
        print("⚡ Lightning Storm! Shock x4, 10 damage, DEF -2!")
    elif effect == "blood_moon":
        user.setdefault("active_buffs", {})["blood_moon"] = 3
        print("🌑 Blood Moon rises! All damage effects intensified!")
    elif effect == "ancient_power":
        user["atk"] += 5
        user["def"] += 3
        user["max_hp"] += 10
        user["hp"] = min(user["hp"] + 10, user["max_hp"])
        print("🏛 Ancient Power! ATK +5, DEF +3, Max HP +10!")
    elif effect == "wraith_form":
        user.setdefault("active_buffs", {})["wraith_form"] = 2
        print("👻 Wraith Form! You become ethereal for 2 turns!")
    elif effect == "bloodlust":
        user["atk"] += 8
        enemy.setdefault("status", {})["bleed"] = 4
        enemy["hp"] -= 8
        print("🩸 Bloodlust! ATK +8, enemy bleeds!")
    elif effect == "earthquake":
        enemy["hp"] -= 12
        enemy["def"] = max(0, enemy.get("def", 0) - 3)
        enemy.setdefault("active_buffs", {})["root"] = 2
        print("🌋 Earthquake! 12 damage, DEF -3, enemy rooted!")
    elif effect == "frostshade":
        enemy.setdefault("status", {})["freeze"] = 2
        enemy.setdefault("active_buffs", {})["blind"] = 2
        enemy.setdefault("status", {})["fear"] = 2
        print("🌑 Frostshade! Freeze + blind + fear applied!")
    elif effect == "abyssal_soul":
        drain = 15
        enemy["hp"] -= drain
        user["hp"] += drain
        enemy.setdefault("status", {})["void"] = 3
        enemy.setdefault("status", {})["curse"] = 2
        print(f"🌀 Abyssal Soul! Drained {drain} HP, applied void + curse!")
    elif effect == "dragon_flame":
        enemy["hp"] -= 20
        enemy.setdefault("status", {})["burn"] = 3
        print("🐉 Dragon Flame! 20 damage + burn!")
    elif effect == "dawn_rebirth":
        user.setdefault("active_buffs", {})["rebirth"] = 1
        user.setdefault("active_buffs", {})["heal_tick"] = 3
        enemy.setdefault("status", {})["burn"] = 2
        print("🌅 Dawn Rebirth! Rebirth ready, healing active, enemy burned!")
    elif effect == "colossus":
        user["atk"] += 12
        user.setdefault("active_buffs", {})["fortress"] = 3
        enemy["def"] = max(0, enemy.get("def", 0) - 4)
        print("🗿 Colossus! ATK +12, fortress up, enemy DEF crushed!")
    elif effect == "entropy":
        enemy["hp"] -= 10
        enemy.setdefault("status", {}).clear()
        for _ in range(3):
            sub = random.choice(["burn", "poison", "void", "shock", "freeze"])
            enemy.setdefault("status", {})[sub] = 2
        print("🌌 Entropy! 10 damage + 3 random chaos effects!")
    elif effect == "tide_of_life":
        user["hp"] = min(user["max_hp"], user["hp"] + 15)
        enemy["hp"] -= 8
        enemy.setdefault("status", {})["shock"] = 2
        print("🌊 Tide of Life! Healed 15, enemy takes 8 damage + shock!")
    elif effect == "phantom":
        user.setdefault("active_buffs", {})["reflect"] = 2
        user.setdefault("active_buffs", {})["double_cast"] = 1
        user.setdefault("active_buffs", {})["warp"] = 1
        print("👻 Phantom! Reflect + double cast + warp active!")

    # ---- basic rune effects (previously unhandled) ----
    elif effect == "enhance_fusion":
        user.setdefault("active_buffs", {})["fusion_boost"] = 3
        print("✨ Enhance Fusion! Next fusion rune hits harder!")
    elif effect == "plasma_surge":
        enemy["hp"] -= 9
        enemy.setdefault("status", {})["shock"] = 2
        print("⚡ Plasma Surge! 9 damage + shock!")
    elif effect == "sonic_shock":
        enemy["hp"] -= 8
        enemy.setdefault("active_buffs", {})["stun"] = 1
        print("🔊 Sonic Shock! 8 damage + stun!")
    elif effect == "ember_blade":
        enemy["hp"] -= 7
        enemy.setdefault("status", {})["burn"] = 3
        print("🔥 Ember Blade! 7 damage + burn!")
    elif effect == "glacial_chill":
        enemy.setdefault("status", {})["freeze"] = 2
        enemy.setdefault("active_buffs", {})["slow_time"] = 2
        print("🧊 Glacial Chill! Freeze + slow!")
    elif effect == "steel_guard":
        user["def"] += 6
        user.setdefault("active_buffs", {})["defense_up"] = 3
        print("🛡 Steel Guard! DEF +6!")
    elif effect == "radiant_glow":
        user["hp"] = min(user["max_hp"], user["hp"] + 12)
        user.setdefault("active_buffs", {})["heal_tick"] = 2
        print("🌟 Radiant Glow! Healed 12 + healing aura!")
    elif effect == "ethereal_wisp":
        user.setdefault("active_buffs", {})["warp"] = 2
        user.setdefault("active_buffs", {})["defense_up"] = 1
        print("👻 Ethereal Wisp! Evasion + shield for 2 turns!")
    elif effect == "necrotic_decay":
        decay = max(5, enemy.get("max_hp", enemy["hp"]) // 10)
        enemy["hp"] -= decay
        enemy["max_hp"] = max(1, enemy.get("max_hp", enemy["hp"]) - decay // 2)
        print(f"☠ Necrotic Decay! {decay} damage + enemy max HP reduced!")
    elif effect == "primal_roar":
        enemy.setdefault("active_buffs", {})["fear"] = 2
        user["atk"] += 5
        print("🦁 Primal Roar! ATK +5, enemy feared!")
    elif effect == "vortex_pull":
        enemy["def"] = max(0, enemy.get("def", 0) - 5)
        enemy.setdefault("active_buffs", {})["root"] = 1
        print("🌀 Vortex Pull! Enemy DEF -5 + rooted!")
    elif effect == "quartz_barrier":
        user.setdefault("active_buffs", {})["fortress"] = 3
        user.setdefault("active_buffs", {})["stability"] = 2
        print("💎 Quartz Barrier! Fortress + stability shield!")
    elif effect == "arcane_burn":
        dmg = 8 + user.get("mana", 0) // 5
        enemy["hp"] -= dmg
        enemy.setdefault("status", {})["burn"] = 2
        print(f"🔮 Arcane Burn! {dmg} arcane damage + burn!")
    elif effect == "plasma_chain":
        enemy["hp"] -= 6
        enemy.setdefault("status", {})["shock"] = 3
        enemy["def"] = max(0, enemy.get("def", 0) - 2)
        print("⚡ Plasma Chain! 6 damage + chain shock + DEF -2!")
    elif effect == "sonic_echo":
        enemy["hp"] -= 5
        user.setdefault("active_buffs", {})["double_cast"] = 1
        print("🔊 Sonic Echo! 5 damage + next hit echoes!")
    elif effect == "ember_crystal":
        enemy["hp"] -= 8
        enemy.setdefault("status", {})["burn"] = 2
        user.setdefault("active_buffs", {})["crit_up"] = 2
        print("💎🔥 Ember Crystal! 8 damage + burn + crit up!")
    elif effect == "glacial_tide":
        enemy.setdefault("status", {})["freeze"] = 2
        user["hp"] = min(user["max_hp"], user["hp"] + 8)
        print("🌊🧊 Glacial Tide! Enemy frozen + healed 8!")
    elif effect == "steel_root":
        enemy.setdefault("active_buffs", {})["root"] = 3
        user["def"] += 4
        print("🌿🛡 Steel Root! Enemy rooted + DEF +4!")
    elif effect == "radiant_aura":
        user["hp"] = min(user["max_hp"], user["hp"] + 10)
        user.setdefault("active_buffs", {})["heal_tick"] = 3
        user.setdefault("active_buffs", {})["moon_guard"] = 2
        print("✨ Radiant Aura! Heal 10 + healing aura + guard!")
    elif effect == "phase_shift":
        user.setdefault("active_buffs", {})["warp"] = 3
        user.setdefault("active_buffs", {})["reflect"] = 1
        print("👻 Phase Shift! Phased for 3 turns + reflect!")
    elif effect == "blood_decay":
        drain = 10
        enemy["hp"] -= drain
        enemy.setdefault("status", {})["bleed"] = 3
        user["hp"] = min(user["max_hp"], user["hp"] + drain // 2)
        print(f"🩸☠ Blood Decay! {drain} drain + bleed, healed {drain // 2}!")
    elif effect == "primal_force":
        dmg = 16
        enemy["hp"] -= dmg
        print(f"🦁 Primal Force! Raw {dmg} damage!")
    elif effect == "vortex_storm":
        enemy["hp"] -= 12
        enemy.setdefault("status", {})["shock"] = 3
        enemy["def"] = max(0, enemy.get("def", 0) - 3)
        print("🌀⚡ Vortex Storm! 12 damage + shock + DEF -3!")
    elif effect == "quartz_shine":
        user.setdefault("active_buffs", {})["fortress"] = 2
        enemy.setdefault("active_buffs", {})["blind"] = 2
        print("💎 Quartz Shine! Your barrier blinds the enemy!")
    elif effect == "spectral_lash":
        raw = 14
        enemy["hp"] -= raw
        print(f"👻 Spectral Lash! {raw} ghost damage (ignores armour)!")
    elif effect == "inferno_wave":
        enemy["hp"] -= 15
        enemy.setdefault("status", {})["burn"] = 4
        print("��� Inferno Wave! 15 damage + burn x4!")
    elif effect == "frost_nova":
        enemy["hp"] -= 10
        enemy.setdefault("status", {})["freeze"] = 3
        print("❄ Frost Nova! 10 damage + freeze x3!")
    elif effect == "thunder_clap":
        enemy["hp"] -= 12
        enemy.setdefault("active_buffs", {})["stun"] = 1
        enemy.setdefault("status", {})["shock"] = 2
        print("⚡ Thunder Clap! 12 damage + stun + shock!")
    elif effect == "tide_blast":
        enemy["hp"] -= 11
        enemy.setdefault("status", {})["shock"] = 2
        user["hp"] = min(user["max_hp"], user["hp"] + 5)
        print("🌊 Tide Blast! 11 damage + shock, healed 5!")
    elif effect == "iron_skin":
        user["def"] += 8
        print("🛡 Iron Skin! DEF +8!")
    elif effect == "aurora_surge":
        user["hp"] = min(user["max_hp"], user["hp"] + 15)
        enemy["hp"] -= 8
        print("🌅 Aurora Surge! Healed 15 + 8 light damage!")
    elif effect == "lunar_flame":
        enemy.setdefault("status", {})["burn"] = 3
        user.setdefault("active_buffs", {})["moon_guard"] = 2
        print("🌙🔥 Lunar Flame! Burn + moon guard!")
    elif effect == "shadow_flame":
        enemy.setdefault("status", {})["burn"] = 2
        enemy.setdefault("active_buffs", {})["blind"] = 2
        enemy["hp"] -= 7
        print("🌑🔥 Shadow Flame! 7 damage + burn + blind!")
    elif effect == "prism_shard":
        hits = random.randint(2, 4)
        total = 0
        for _ in range(hits):
            h = random.randint(3, 7)
            enemy["hp"] -= h
            total += h
        print(f"💎 Prism Shard! {hits} hits for {total} total damage!")
    elif effect == "magnetic_pull":
        enemy["def"] = max(0, enemy.get("def", 0) - 6)
        enemy.setdefault("active_buffs", {})["root"] = 2
        print("🧲 Magnetic Pull! Enemy DEF -6 + locked in place!")
    elif effect == "tempest_charge":
        user.setdefault("active_buffs", {})["supercharge"] = 2
        user.setdefault("active_buffs", {})["speed_up"] = 2
        print("🌪 Tempest Charge! Supercharged + speed up!")
    elif effect == "void_fire":
        enemy["hp"] -= 8
        enemy.setdefault("status", {})["burn"] = 2
        enemy.setdefault("status", {})["void"] = 2
        print("🌑🔥 Void Fire! 8 damage + burn + void!")
    elif effect == "eternal_light":
        user["hp"] = min(user["max_hp"], user["hp"] + 8)
        user.setdefault("active_buffs", {})["heal_tick"] = 4
        print("✨ Eternal Light! Healed 8 + long healing aura!")
    elif effect == "fate_seal":
        user.setdefault("active_buffs", {})["fate_seal"] = 5
        print("🔮 Fate Seal! Enemy will be executed if below 20% HP!")
    elif effect == "harmony_wave":
        heal = 6
        user["hp"] = min(user["max_hp"], user["hp"] + heal)
        user["atk"] += 3
        user["def"] += 3
        print(f"🌊 Harmony Wave! Healed {heal}, ATK +3, DEF +3!")
    elif effect == "ruin_blast":
        dmg = 18
        enemy["hp"] -= dmg
        print(f"💥 Ruin Blast! {dmg} raw damage!")
    elif effect == "glimmer_shield":
        user.setdefault("active_buffs", {})["moon_guard"] = 3
        user.setdefault("active_buffs", {})["heal_tick"] = 2
        print("✨ Glimmer Shield! Guarded + healing for 3 turns!")
    elif effect == "ember_wing":
        enemy.setdefault("status", {})["burn"] = 2
        user.setdefault("active_buffs", {})["speed_up"] = 3
        print("🔥🦅 Ember Wing! Burn + speed up x3!")
    elif effect == "seismic_tremor":
        enemy["hp"] -= 10
        enemy["def"] = max(0, enemy.get("def", 0) - 4)
        enemy.setdefault("active_buffs", {})["stun"] = 1
        print("🌋 Seismic Tremor! 10 damage + DEF -4 + stun!")
    elif effect == "stormheart":
        enemy.setdefault("status", {})["shock"] = 3
        user["hp"] = min(user["max_hp"], user["hp"] + 8)
        print("⛈ Stormheart! Shock x3 + healed 8!")
    elif effect == "soulflare":
        drain = 10
        enemy["hp"] -= drain
        user["hp"] = min(user["max_hp"], user["hp"] + drain // 2)
        enemy.setdefault("status", {})["burn"] = 2
        print(f"🔥👻 Soulflare! {drain} drain + burn, healed {drain // 2}!")
    elif effect == "frostbrand":
        enemy.setdefault("status", {})["freeze"] = 2
        user.setdefault("active_buffs", {})["crit_up"] = 3
        print("❄🔥 Frostbrand! Freeze + crit up x3!")
    elif effect == "radiant_dawn":
        user["hp"] = min(user["max_hp"], user["hp"] + 20)
        enemy.setdefault("status", {})["burn"] = 2
        print("🌅 Radiant Dawn! Healed 20 + burned enemy!")
    elif effect == "silence_field":
        enemy.setdefault("active_buffs", {})["silenced"] = 3
        enemy.setdefault("active_buffs", {})["blind"] = 2
        print("🤫 Silence Field! Enemy silenced for 3 turns + blinded!")

    # ---- fusion rune effects (previously unhandled) ----
    elif effect == "infernal_nightmare":
        enemy["hp"] -= 18
        enemy.setdefault("status", {})["burn"] = 3
        enemy.setdefault("active_buffs", {})["fear"] = 2
        print("😈🔥 Infernal Nightmare! 18 damage + burn + fear!")
    elif effect == "abyssal_dream":
        enemy.setdefault("status", {})["void"] = 3
        enemy.setdefault("active_buffs", {})["sleep"] = 2
        enemy["hp"] -= 10
        print("🌑💤 Abyssal Dream! 10 damage + void + sleep!")
    elif effect == "eclipse":
        enemy.setdefault("active_buffs", {})["blind"] = 3
        enemy["hp"] -= 14
        user.setdefault("active_buffs", {})["moon_guard"] = 2
        print("🌑☀ Eclipse! 14 damage + blind + moon guard!")
    elif effect == "rebirth_flame":
        user.setdefault("active_buffs", {})["rebirth"] = 1
        enemy.setdefault("status", {})["burn"] = 4
        enemy["hp"] -= 10
        print("🐉🔥 Rebirth Flame! Rebirth ready + 10 damage + burn x4!")
    elif effect == "cosmic_eternity":
        user["atk"] += 8
        user["def"] += 5
        user["max_hp"] += 20
        user["hp"] = min(user["hp"] + 20, user["max_hp"])
        user.setdefault("active_buffs", {})["divine_luck"] = 4
        print("🌌 Cosmic Eternity! All stats up + divine luck!")
    elif effect == "element_synthesis":
        for st in ["burn", "shock", "freeze", "poison"]:
            enemy.setdefault("status", {})[st] = 2
        print("🌍 Element Synthesis! All four elements applied!")
    elif effect == "steam_burst":
        enemy["hp"] -= 13
        enemy.setdefault("status", {})["burn"] = 2
        enemy.setdefault("status", {})["shock"] = 2
        print("💨🔥 Steam Burst! 13 damage + burn + shock!")
    elif effect == "volcanic_freeze":
        enemy["hp"] -= 12
        enemy.setdefault("status", {})["burn"] = 2
        enemy.setdefault("status", {})["freeze"] = 2
        print("🌋❄ Volcanic Freeze! 12 damage + burn + freeze!")
    elif effect == "mud_titan":
        user["def"] += 7
        enemy.setdefault("active_buffs", {})["root"] = 3
        enemy["def"] = max(0, enemy.get("def", 0) - 4)
        print("🪨💧 Mud Titan! DEF +7, enemy rooted + DEF -4!")
    elif effect == "doomflame":
        enemy["hp"] -= 16
        enemy.setdefault("status", {})["burn"] = 3
        enemy.setdefault("status", {})["void"] = 2
        print("💀🔥 Doomflame! 16 damage + burn + void!")
    elif effect == "solar_judgment":
        dmg = 20
        enemy["hp"] -= dmg
        enemy.setdefault("status", {})["burn"] = 2
        print(f"☀ Solar Judgment! {dmg} holy damage + burn!")
    elif effect == "null_radiance":
        enemy.setdefault("status", {}).clear()
        enemy.setdefault("active_buffs", {}).clear()
        enemy["hp"] -= 12
        print("✨ Null Radiance! 12 damage + all enemy effects wiped!")
    elif effect == "voidflame":
        enemy["hp"] -= 14
        enemy.setdefault("status", {})["burn"] = 3
        enemy.setdefault("status", {})["void"] = 3
        print("🌑🔥 Voidflame! 14 damage + burn x3 + void x3!")
    elif effect == "world_tree":
        user["hp"] = min(user["max_hp"], user["hp"] + 18)
        user.setdefault("active_buffs", {})["regen"] = 4
        print("🌳 World Tree! Healed 18 + regen x4!")
    elif effect == "grave_whisper":
        drain = 12
        enemy["hp"] -= drain
        user["hp"] = min(user["max_hp"], user["hp"] + drain)
        enemy.setdefault("status", {})["curse"] = 3
        print(f"💀 Grave Whisper! Drained {drain} HP + curse x3!")
    elif effect == "ascended_spirit":
        user["hp"] = min(user["max_hp"], user["hp"] + 15)
        user["mana"] = min(20, user.get("mana", 0) + 8)
        user.setdefault("active_buffs", {})["divine_luck"] = 2
        print("👼 Ascended Spirit! Healed 15, mana +8, divine luck!")
    elif effect == "chrono_void":
        enemy.setdefault("active_buffs", {})["slow_time"] = 4
        enemy.setdefault("status", {})["void"] = 3
        enemy["hp"] -= 10
        print("⏳🌑 Chrono Void! 10 damage + slow x4 + void x3!")
    elif effect == "temporal_flame":
        enemy["hp"] -= 14
        enemy.setdefault("status", {})["burn"] = 2
        enemy.setdefault("active_buffs", {})["slow_time"] = 3
        print("⏳🔥 Temporal Flame! 14 damage + burn + slow x3!")
    elif effect == "dark_universe":
        dmg = 22
        enemy["hp"] -= dmg
        enemy.setdefault("status", {})["void"] = 4
        enemy.setdefault("status", {})["curse"] = 2
        print(f"🌌 Dark Universe! {dmg} darkness damage + void x4 + curse!")
    elif effect == "big_bang":
        dmg = 25
        enemy["hp"] -= dmg
        enemy.setdefault("status", {}).clear()
        print(f"💥 Big Bang! {dmg} cosmic explosion damage!")
    elif effect == "void_dragon":
        enemy["hp"] -= 20
        enemy.setdefault("status", {})["void"] = 4
        enemy["def"] = max(0, enemy.get("def", 0) - 6)
        print("🐉🌑 Void Dragon! 20 damage + void x4 + DEF -6!")
    elif effect == "eternal_ash":
        user.setdefault("active_buffs", {})["rebirth"] = 1
        enemy.setdefault("status", {})["burn"] = 4
        user["atk"] += 6
        print("🔥🐦 Eternal Ash! Rebirth + burn x4 + ATK +6!")
    elif effect == "infinite_loop":
        user.setdefault("active_buffs", {})["double_cast"] = 3
        user.setdefault("active_buffs", {})["stability"] = 3
        print("🔄 Infinite Loop! Double cast x3 + stability x3!")
    elif effect == "broken_reality":
        enemy["hp"] -= 15
        enemy.setdefault("status", {}).clear()
        for _ in range(4):
            sub = random.choice(["burn", "poison", "void", "shock", "freeze", "curse"])
            enemy.setdefault("status", {})[sub] = 2
        print("💥 Broken Reality! 15 damage + 4 random chaos effects!")
    elif effect == "spectre":
        user.setdefault("active_buffs", {})["wraith_form"] = 3
        drain = 10
        enemy["hp"] -= drain
        user["hp"] = min(user["max_hp"], user["hp"] + drain // 2)
        enemy.setdefault("active_buffs", {})["blind"] = 3
        print("👻 Spectre! Wraith form x3 + soul drain + blind x3!")
    elif effect == "martyr":
        sacrifice_dmg = min(user["hp"] - 1, 30)
        user["hp"] -= sacrifice_dmg
        enemy["hp"] -= sacrifice_dmg * 3
        user.setdefault("active_buffs", {})["rebirth"] = 1
        print(
            f"✝ Martyr! Sacrificed {sacrifice_dmg} HP → dealt {sacrifice_dmg * 3} + rebirth ready!"
        )
    elif effect == "obliteration":
        enemy["def"] = 0
        enemy["hp"] -= 18
        enemy.setdefault("status", {})["shock"] = 4
        print("💥⚡ Obliteration! Defense destroyed + 18 damage + shock x4!")
    elif effect == "eclipse_of_souls":
        for st in list(enemy.get("status", {}).keys()):
            enemy["status"][st] = min(6, enemy["status"][st] + 2)
        enemy.setdefault("status", {})["curse"] = 4
        enemy.setdefault("status", {})["void"] = 3
        drain = 14
        enemy["hp"] -= drain
        user["hp"] = min(user["max_hp"], user["hp"] + drain // 2)
        print(f"🌑🌙 Eclipse of Souls! All DoTs amplified + {drain} soul drain!")


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
    print("\n===== INVENTORY =====")

    print("\n📦 Loot & Consumables")
    loot = [item for item in player["inventory"] if "value" in item]
    if loot:
        for item in loot:
            print("-", item["name"])
    else:
        print("Empty")

    print("\n📜 Scrolls")
    scrolls = [item for item in player["inventory"] if "turns" in item]
    if scrolls:
        for scroll in scrolls:
            print("-", scroll["name"])
    else:
        print("Empty")

    print("\n⚔ Weapons")
    if player["weapons"]:
        for weapon in player["weapons"]:
            equipped = " [EQUIPPED]" if player["weapon"] == weapon else ""
            print(f"- {weapon['name']} (ATK {weapon['atk']}){equipped}")
    else:
        print("None")

    print("\n🛡 Armour")
    if player["armours"]:
        for armour in player["armours"]:
            equipped = " [EQUIPPED]" if player["armour"] == armour else ""
            elem = f" [{armour['element']}]" if armour.get("element") else ""
            print(f"- {armour['name']} (DEF {armour['def']}){elem}{equipped}")
    else:
        print("None")

    print("\n✨ Staffs")
    if player["staffs"]:
        for staff in player["staffs"]:
            rune = staff.get("rune", None)
            rune_name = rune["name"] if isinstance(rune, dict) else "None"
            print(f"- {staff['name']} (Power {staff['power']}) Rune: {rune_name}")
    else:
        print("None")

    print("\n🔮 Runes")
    if player["runes"]:
        for rune in player["runes"]:
            print(f"- {rune['name']} ({rune['effect']})")
    else:
        print("None")


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
            print(
                f"  ❄ {lbl} {'are' if is_player else 'is'} frozen solid — turn skipped!"
            )
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
        print(
            f"   +1 Skill Point (total: {player['skill_points']}) — spend via option 19"
        )
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
    if not player["weapons"]:
        print("No weapons available.")
        return

    print("\n🔧 === BLACKSMITH ===")

    for i, w in enumerate(player["weapons"]):
        cost = w["atk"] * 10
        print(f"{i}. {w['name']} | ATK {w['atk']} | Upgrade Cost: {cost}")

    try:
        idx = int(input("Select weapon > "))
        if idx < 0 or idx >= len(player["weapons"]):
            print("Invalid selection.")
            return

        weapon = player["weapons"][idx]
    except ValueError:
        print("Invalid input.")
        return

    cost = weapon["atk"] * 10

    if player["gold"] < cost:
        print("Not enough gold.")
        return

    confirm = input(f"Upgrade {weapon['name']} for {cost} gold? (y/n) > ").lower()
    if confirm != "y":
        print("Cancelled.")
        return

    player["gold"] -= cost
    weapon["atk"] += 3

    print(f"🔧 {weapon['name']} upgraded to ATK {weapon['atk']}")


# =========================
# DAMAGE
# =========================


def calculate_damage(player_obj, enemy, mode="weapon"):
    weapon = player_obj.get("weapon") or {}
    staff = player_obj.get("staffs")[0] if player_obj.get("staffs") else {}
    runes = player_obj.get("runes") or []
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

    return max(1, int(damage))



FORGE_DATABASE = {}
# format:
# {("core","metal","wood"): {"name": "Excalibur", "creator": "player"}}


def forge_weapon():
    if player["region"] != "Crimson Depths":
        print("You must be in Crimson Forge.")
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

    dmg = staff["power"]
    print(f"\n✨ You use {staff['name']}")

    enemy["hp"] -= dmg


# =========================
# runes and forge and items
# =========================


def crimson_forge():
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

    components = []
    for base in (rune_one, rune_two):
        if base.get("effect") == "fusion":
            components.extend(base.get("components", []))
        else:
            components.append(base.get("effect"))

    recipe = SPECIAL_FUSION_RECIPES.get(frozenset({rune_one["name"], rune_two["name"]}))

    if recipe:
        fusion_name = recipe["name"]
        fusion_rune = {
            "name": fusion_name,
            "effect": "fusion",
            "components": recipe["components"],
            "special_effect": recipe["effect"],
        }
    else:
        components = list(dict.fromkeys(components))
        fusion_name = f"Fusion Rune ({rune_one['name']} + {rune_two['name']})"
        fusion_rune = {
            "name": fusion_name,
            "effect": "fusion",
            "components": components,
        }

    player["runes"].pop(second)
    player["runes"].pop(first)
    player["runes"].append(fusion_rune)

    print(f"🔮 Created {fusion_rune['name']}!")
    if recipe:
        print(f"✨ New effect made: {recipe['effect']}")


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

    effects = (
        rune.get("components") if rune.get("effect") == "fusion" else [rune["effect"]]
    )

    if any(effect not in allowed for effect in effects):
        print("That rune can only be used in combat.")
        return

    apply_rune_effect(rune, player, player)
    player["runes"].remove(rune)
    print(f"✨ Cast {rune['name']}.")


def merchant():
    region = player["region"]
    items = MERCHANT_ITEMS.get(region, [])

    while True:
        print(f"\n=== {region} MERCHANT ===")
        print(f"Souls: {player['gold']}")

        for i, item_name in enumerate(items):
            print(f"{i}. {item_name}")

        print("X. Leave")

        choice = input("> ").lower()

        if choice == "x":
            return

        try:
            idx = int(choice)
            item_name = items[idx]
        except:
            print("Invalid choice.")
            continue

        item = None
        item_type = None
        price = 0

        for weapon in WEAPONS:
            if weapon["name"] == item_name:
                item = weapon.copy()
                item_type = "weapon"
                price = weapon["atk"] * 10
                break

        if item is None:
            for staff in STAFFS:
                if staff["name"] == item_name:
                    item = staff.copy()
                    item_type = "staff"
                    price = staff["power"] * 10
                    break

        if item is None:
            for rune in RUNES:
                if rune["name"] == item_name:
                    item = rune.copy()
                    item_type = "rune"
                    price = random.randint(100, 550)
                    break

        if item is None:
            for armour in ARMOURS:
                if armour["name"] == item_name:
                    item = armour.copy()
                    item_type = "armour"
                    price = armour["def"] * 10
                    break
        if item is None:
            for wood in WOODS:
                item = wood.copy()
                item_type = "wood"
                price = random.randint(50, 150)
                break
        if item is None:
            for metal in METALS:
                item = metal.copy()
                item_type = "metal"
                price = random.randint(70, 200)
                break
        if item is None:
            for core in CORES:
                item = core.copy()
                item_type = "core"
                price = random.randint(100, 300)
                break

        if item is None:
            print("Item data missing.")
            continue

        print(f"Buy {item['name']} for {price} souls? (y/n)")

        if input("> ").lower() != "y":
            continue

        if player["gold"] < price:
            print("Not enough souls.")
            continue

        player["gold"] -= price

        if item_type == "weapon":
            player["weapons"].append(item)
        elif item_type == "armour":
            player["armours"].append(item)
        elif item_type == "staff":
            player["staffs"].append(item)
        elif item_type == "rune":
            player["runes"].append(item)
        elif item_type == "wood":
            player["woods"].append(item)
        elif item_type == "metal":
            player["metals"].append(item)
        elif item_type == "core":
            player["cores"].append(item)



        print(f"Purchased {item['name']}!")


# =========================
# COMBAT
# =========================


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
            dmg = 15
            enemy["hp"] -= dmg
            total += dmg
        print(f"   3-arrow volley! {total} total damage!")
    elif passive == "lifesteal":  # Soul Rip
        drain = 35
        enemy["hp"] -= drain
        player["hp"] = min(player["max_hp"], player["hp"] + drain)
        print(f"   Drained {drain} HP directly from the enemy!")


def _use_companion_move(companions, enemy):
    battle_ready = [
        c for c in companions if c.get("can_battle") and c.get("stage", 0) > 0
    ]
    if not battle_ready:
        print("🐾 Your companions aren't battle-ready yet (need feeding first).")
        return
    print("\n🐾 Companion moves:")
    for i, c in enumerate(battle_ready):
        elem = c.get("element", "?")
        move = COMPANION_MOVES.get(elem, {})
        print(
            f"  {i}. {c['name']} [{elem}] — {move.get('name', '?')}: {move.get('desc', '?')}"
        )
    try:
        idx = int(input("  Use which? (-1 cancel) > "))
    except ValueError:
        return
    if not (0 <= idx < len(battle_ready)):
        return
    chosen = battle_ready[idx]
    elem = chosen.get("element", "")
    move = COMPANION_MOVES.get(elem, {})
    print(f"\n💫 {chosen['name']} uses {move.get('name', '?')}!")
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
                player.setdefault("inventory", []).append(
                    {"name": item_name, "value": fd["value"]}
                )
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
        target_region = (
            random.choice(all_other_regions) if all_other_regions else region
        )
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
        print(
            f"  Class: {cls['icon']} {cls['name']}  |  Passive: {cls['passive_desc']}"
        )
    print(f"  Skill Points available: {pts}\n")

    available = {k: v for k, v in SKILLS.items() if k not in owned}
    if not available:
        print("  You've learned all available skills!")
        return

    skill_list = list(available.items())
    for i, (key, sk) in enumerate(skill_list):
        print(
            f"  {i}. {sk['name']}  ({sk['pts']} pt{'s' if sk['pts'] > 1 else ''}) — {sk['desc']}"
        )

    print(f"\n  {len(skill_list)}. Cancel")
    if owned:
        print(
            f"\n  Already learned: {', '.join(SKILLS[k]['name'] for k in owned if k in SKILLS)}"
        )

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
    enemy = enemy.copy()
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

    print("⚔", enemy["name"])

    companion_move_used = False  # reset per fight
    player["resonance_streak"] = player.get(
        "resonance_streak", 0
    )  # persist across turns

    while player["hp"] > 0 and enemy["hp"] > 0:
        process_buffs()
        apply_status(player)
        apply_status(enemy)

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
                f" | 7 Potion({len(player.get('potions', []))})"
                if player.get("potions")
                else ""
            )
            night_str = " 🌙" if player.get("is_night") else ""
            print(
                f"{wx_data['icon']} {wx}{night_str}  |  {player['hp']} vs {enemy['hp']}"
            )
            c = input(
                f"1 atk 2 scroll 3 staff 4 run{skill_label}{comp_label}{potion_label} > "
            ).strip()

        if c == "4" and not boss:
            return

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
                if pname == "Health Potion":
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
                    player["potion_atk_boost"] = (
                        player.get("potion_atk_boost", 0) + boost
                    )
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
            if (
                "berserk" in player.get("skills", [])
                and player["hp"] < player["max_hp"] * 0.30
            ):
                dmg = int(dmg * 1.5)
                print("🔴 Berserk! Low HP fury — damage x1.5!")

            print(f"You dealt {dmg} damage!")
            enemy["hp"] -= dmg

            # ── Lifesteal (necromancer passive or vampiric_strike skill) ──
            lifesteal_pct = 0.0
            if passive == "lifesteal":
                lifesteal_pct += 0.20
            if "vampiric_strike" in player.get("skills", []):
                lifesteal_pct += 0.15
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
                shot = 15
                enemy["hp"] -= shot
                print(f"🏹 Ranger free shot! {shot} bonus damage!")

            for rune in player.get("runes", []):
                apply_rune_effect(rune, player, enemy)

            apply_companion_support(enemy)

        elif c == "2":
            use_scroll()

        elif c == "3":
            use_staff(enemy)
            for rune in player.get("runes", []):
                apply_rune_effect(rune, player, enemy)
            apply_companion_support(enemy)

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
                _use_companion_move(companions, enemy)
                companion_move_used = True

        if enemy["hp"] <= 0:
            break

        if enemy["active_buffs"].get("stun"):
            print("🛑 Enemy is stunned and cannot attack!")
            enemy["active_buffs"].pop("stun", None)
            enemy_dmg = 0
        else:
            base_enemy_dmg = random.randint(5, 15)
            armour_def = (
                player.get("armour", {}) and player["armour"].get("def", 0)
                if player.get("armour")
                else 0
            )
            base_enemy_dmg = max(
                1, base_enemy_dmg - player.get("def", 0) // 3 - armour_def // 4
            )
            enemy_dmg = base_enemy_dmg
            if player["active_buffs"].get("warp"):
                print("✨ You warp away the attack!")
                enemy_dmg = 0
            if enemy["active_buffs"].get("blind"):
                if random.random() < 0.35:
                    print("✨ Enemy misses due to blind!")
                    enemy_dmg = 0
            dodge_chance = min(player.get("speed", 5) * 0.005, 0.40)
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
            player["hp"] -= enemy_dmg

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
        # ── Feature 2: Bestiary kill tracking ──
        record_kill(enemy["name"])
        # ── Feature 10: Companion XP ──
        award_companion_xp(10 if boss else 5)
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
                player.setdefault("bosses_defeated", []).append(player["region"])
                gain_xp(100)
                player["gold"] += 100
                drop_loot()
                drop_loot()
                drop_loot()
                drop_loot()
                item = random.choice(BOSS_DROPS[player["region"]])
                print(
                    f"Special Boss Drop: {item} this can be used in the crimson realm's forge"
                )
                player["forge_cores"].append(item)
                ui = _ui.get_ui()
                if ui:
                    ui.show_boss_drop_popup(item, player["region"])
        else:
            print("yay u won")
            xp_gain = 20
            gold_gain = 20
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
        print("you died LOL")

    ui = _ui.get_ui()
    if ui:
        ui.clear_enemy()


# =========================
# LOOT
# =========================


def drop_loot():
    luck_bonus = 10 if player["active_buffs"].get("divine_luck") else 0
    roll = min(100, random.randint(1, 100) + luck_bonus)
    ui = _ui.get_ui()

    if roll <= 60:
        item = random.choice(LOOT_ITEMS)
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
    for ach in ACHIEVEMENTS:
        if ach["id"] in earned:
            continue
        t = ach["type"]
        threshold = ach["threshold"]
        unlocked = False
        if t == "wander_count" and player.get("wander_count", 0) >= threshold:
            unlocked = True
        elif (
            t == "unlocked_count"
            and len(player.get("unlocked_regions", set())) >= threshold
        ):
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
            total = sum(
                len(v) for v in player.get("discovered_structures", {}).values()
            )
            if total >= threshold:
                unlocked = True
        elif t == "core_count" and len(player.get("elemental_cores", [])) >= threshold:
            unlocked = True
        elif t == "skill_count" and len(player.get("skills", [])) >= threshold:
            unlocked = True

        if unlocked:
            earned.append(ach["id"])
            title = ACHIEVEMENT_TITLES.get(ach["id"])
            print(f"\n🏆 ACHIEVEMENT UNLOCKED: {ach['name']} — {ach['desc']}")
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
    for ach in ACHIEVEMENTS:
        status = "✅" if ach["id"] in earned else "⬜"
        print(f"  {status} {ach['name']}  — {ach['desc']}")
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


def explore():
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
    if random.random() < 0.20:
        player["weather"] = random.choice(weather_keys)
    wx = player.get("weather", "Clear")
    wx_data = WEATHER_EFFECTS[wx]
    print(f"\n🌍 Exploring {r}...  {wx_data['icon']} {wx} — {wx_data['desc']}")
    if night:
        print("   🌙 Night — enemies are +15% stronger, loot is better.")

    player["wander_count"] = player.get("wander_count", 0) + 1

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

    # ── Hunger decreases each wander ──
    drain = 1 if "hunger_resist" in player.get("skills", []) else 5
    player["hunger"] = max(0, player.get("hunger", 100) - drain)
    h = player["hunger"]
    if h <= 0:
        dmg = 10
        player["hp"] = max(1, player["hp"] - dmg)
        print(f"🍖 You are STARVING! You take {dmg} damage. Find a village and eat!")
    elif h < 30:
        print(f"🍖 You are hungry ({h}/100). Find a village before you weaken further.")

    # ── Structure discovery (12% chance per wander, undiscovered only) ──
    region_structs = REGION_STRUCTURES.get(r, [])
    found_names = player.setdefault("discovered_structures", {}).get(r, [])
    undiscovered = [s for s in region_structs if s["name"] not in found_names]
    if undiscovered and random.random() < 0.12:
        struct = random.choice(undiscovered)
        player["discovered_structures"].setdefault(r, []).append(struct["name"])
        print(
            f"\n🗺 You've discovered a new location: {struct['icon']} {struct['name']}!"
        )
        print("  (Visit it via option 17 — Structures)")
        _check_achievements()
        return

    # ── Ingredient discovery (8% chance per wander) ──
    region_ings = REGION_INGREDIENTS.get(r, [])
    if region_ings and random.random() < 0.08:
        found_ing = random.choice(region_ings)
        player.setdefault("ingredients", []).append(found_ing)
        print(f"\n🌿 You spot a rare ingredient: [{found_ing}]! Added to your pouch.")

    # ── Elemental village discovery (1% chance in the 4 elemental regions) ──
    if r in ELEMENTAL_VILLAGES and random.random() < 0.01:
        village = ELEMENTAL_VILLAGES[r]
        print(f"\n✨ You notice something hidden between the shadows...")
        print(f"  A faint {village['icon']} glow pulses ahead — a secret place awaits!")
        visit_elemental_village()
        return

    # ── Bounty encounter (2% chance — named rare enemy) ──
    bounty = BOUNTY_MONSTERS.get(r)
    if bounty and bounty["name"] not in player.get("bounties_claimed", []):
        if random.random() < 0.02:
            print(f"\n☠ BOUNTY TARGET SPOTTED: {bounty['name']}!")
            print("  This creature has a price on its head.")
            fight(bounty.copy())
            if player["hp"] > 0:
                player.setdefault("bounties_claimed", []).append(bounty["name"])
                player["gold"] += bounty["reward"]
                print(f"  🏴 Bounty claimed! +{bounty['reward']} souls!")
            _check_achievements()
            return

    # ── Random wander events (8% chance) ──
    if random.random() < 0.08:
        weights = [e["weight"] for e in WANDER_EVENTS]
        total = sum(weights)
        rnd = random.uniform(0, total)
        cumulative = 0
        night_mod = 1.15 if night else 1  # night events are 15% more likely
        chosen_event = WANDER_EVENTS[0]
        for ev in WANDER_EVENTS:
            cumulative += ev["weight"]
            if rnd <= cumulative:
                chosen_event = ev
                break
        print(f"\n✦ {chosen_event['title']}: {chosen_event['desc']}")
        _handle_wander_event(chosen_event["id"], r)
        _check_achievements()
        return

    roll = random.randint(1, 100)

    if roll < 2:
        candidates = get_region_companion_candidates(r)
        if candidates:
            companion = random.choice(candidates)
            print(f"\n🐾 You encounter {companion['name']}!")
            choice = input("Recruit? (y/n) > ").lower()
            if choice == "y":
                recruit_companion(companion)
    elif roll < 10:
        merchant()
    elif roll > 20:
        night_mod = 1.15 if night else 1.0

        region = player["region"]

        if player["level"] > 10:

            enemy_pool = EVOLVED_MONSTERS.get(region, []) + MINI_BOSSES.get(region, [])

        elif player["level"] < 10 :
                enemy_pool = NORMAL_MONSTERS.get(region, [])
        else:
             return


    night_mod = 1.15 if night else 1.0
    if night_mod > 1.0:
        enemy["hp"] = int(enemy["hp"] * night_mod)
        enemy["atk"] = int(enemy["atk"] * night_mod)

        if random.random() < 0.05:
            enemy = make_elite(enemy)
            print(f"\n★ AN ELITE MONSTER APPEARS! {enemy['name']} — beware!")

        if r in _DARK_REGIONS:
            add_corruption(5)
        fight(enemy)
        _check_achievements()
    else:
        print("Peaceful wandering...")


# =========================
# TRAVEL
# =========================


def travel():
    print("\n=== TRAVEL ===")
    print("current region:", player["region"])
    print(
        "travel to CRIMSON FORGE to upgrade your gear with forge cores obtained from bosses, or explore other unlocked regions for new challenges and rewards."
    )
    wish = input("Do you want to travel to the Crimson Forge? (y/n) > ").lower()
    if wish == "y":
        player["region"] = "Crimson Depths"
        print("Travelled to Crimson Forge")
        return
    else:
        print("Where do you want to travel?")

    ordered = get_ordered_unlocked_regions()
    print("\nUnlocked Regions:")
    for i, region in enumerate(ordered):
        print(f"{i}. {region}")

    choice = int(input("> "))
    player["region"] = ordered[choice]
    print(f"Travelled to {player['region']}")
    advance_quest("reach_region", player["region"])


# =========================
# STRUCTURES
# =========================

_FOOD_BY_NAME = {f["name"]: f for f in FOOD_ITEMS}


def _eat_food():
    """Let the player eat food from inventory to restore hunger."""
    foods = [i for i in player.get("inventory", []) if i.get("name") in _FOOD_BY_NAME]
    if not foods:
        print("  (You have no food in your inventory.)")
        return
    print("\n🍖 Your food:")
    for idx, item in enumerate(foods):
        fd = _FOOD_BY_NAME[item["name"]]
        print(f"  {idx}. {item['name']}  (+{fd['hunger']} hunger)")
    try:
        c = int(input("  Eat which? (-1 to cancel) > "))
    except ValueError:
        return
    if 0 <= c < len(foods):
        chosen = foods[c]
        fd = _FOOD_BY_NAME[chosen["name"]]
        player["hunger"] = min(100, player.get("hunger", 100) + fd["hunger"])
        player["inventory"].remove(chosen)
        print(f"  You eat the {chosen['name']}. Hunger: {player['hunger']}/100")


def _apply_potion_effect(effect, name):
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
        player["mp"] = player.get("max_mp", player.get("mp", 50))
        print(f"  ✨ Mana fully restored!")
    elif effect == "skip_fight":
        player["skip_next_fight"] = True
        print(f"  💤 Your next enemy will be asleep — skip one fight!")
    elif effect == "genesis":
        player["hp"] = player["max_hp"]
        player["mp"] = player.get("max_mp", player.get("mp", 50))
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
        player.setdefault("status", {})["poison"] = (
            player["status"].get("poison", 0) + 3
        )
        print(f"  ☠ The brew was vile! -{dmg} HP and poisoned!")
    player.setdefault("potions", []).append(f"_crafted_{name}")


def _ingredient_brew_menu():
    print("\n🧪═══════════════════════════════🧪")
    print("   VILLAGE WORKBENCH — Ingredient Brewing")
    print("🧪═══════════════════════════════🧪")
    ings = player.get("ingredients", [])
    if not ings:
        print(
            "  You have no ingredients. Wander regions to gather them (8% chance each explore)."
        )
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
    result = INGREDIENT_COMBOS.get(combo_key)

    # Remove ingredients from player pouch
    try:
        ings.remove(ing_a)
        ings.remove(ing_b)
    except ValueError:
        print("  Not enough of those ingredients.")
        return

    print(f"\n  ⚗ Mixing [{ing_a}] + [{ing_b}]...")
    if result:
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
    print(
        "Dusty shelves line ancient stone walls. A wealth of forgotten knowledge awaits.\n"
    )
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
            player["mp"] = player.get("max_mp", player.get("mp", 50))
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
        loot = random.choice(LOOT_ITEMS).copy()
        player.setdefault("inventory", []).append(loot)
        print(f"  🎁 Bonus prize: {loot['name']}!")


def visit_blacksmith(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n🔨═══════════════════════════════🔨")
    print(f"     {struct['name'].upper()}")
    print(f"🔨═══════════════════════════════🔨")
    print(
        "The blacksmith's hammer rings out. They can improve your gear for a price.\n"
    )
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
                print(
                    f"  ⚒ {weapons[idx]['name']} upgraded to ATK {weapons[idx]['atk']}!"
                )
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
                print(
                    f"  ⚒ {armours[idx]['name']} upgraded to DEF {armours[idx]['def']}!"
                )
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
        loot = random.choice(LOOT_ITEMS).copy()
        player.setdefault("inventory", []).append(loot)
        ores = random.choice(METALS)
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
    print(
        "A rough camp of travellers huddles around a fire. They're cautious but friendly.\n"
    )
    print("1. Rest by the fire  (free rest: +25 HP + +20 hunger)")
    print("2. Trade stories  (may learn a tip — small XP gain)")
    print("3. Buy/trade ingredients  (if you have any)")
    print("4. Move on")
    c = input("> ").strip()
    if c == "1":
        heal = min(25, player["max_hp"] - player["hp"])
        player["hp"] += heal
        player["hunger"] = min(100, player.get("hunger", 100) + 20)
        print(f"  You rest warmly. +{heal} HP, +20 hunger.")
    elif c == "2":
        xp = random.randint(20, 50)
        player["xp"] = player.get("xp", 0) + xp
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
        check_level_up()
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


def visit_village(struct, region):
    stock = VILLAGE_STOCK.get(region, {})
    food_names = stock.get("food", [])
    gear_names = stock.get("gear", [])

    print(f"\n🏘═══════════════════════════════🏘")
    print(f"     {struct['name'].upper()}")
    print(f"🏘═══════════════════════════════🏘")
    print(f"Souls: {player['gold']}   Hunger: {player.get('hunger', 100)}/100\n")

    print("1. Buy food")
    print("2. Buy gear")
    print("3. Eat from inventory")
    print("4. Rest here  (costs 50 souls, restores 30 HP)")
    print("5. Quest board 📋")
    print("6. Craft potions 🧪")
    print("7. Leave")
    c = input("> ").strip()

    if c == "1":
        if not food_names:
            print("  Nothing for sale here.")
            return
        print("\n🍖 Food for sale:")
        avail = [_FOOD_BY_NAME[n] for n in food_names if n in _FOOD_BY_NAME]
        for i, f in enumerate(avail):
            print(f"  {i}. {f['name']}  +{f['hunger']} hunger  — {f['value']} souls")
        try:
            idx = int(input("  Buy which? (-1 cancel) > "))
        except ValueError:
            return
        if 0 <= idx < len(avail):
            f = avail[idx]
            if player["gold"] < f["value"]:
                print("  Not enough souls.")
            else:
                player["gold"] -= f["value"]
                player.setdefault("inventory", []).append(
                    {"name": f["name"], "value": f["value"]}
                )
                print(f"  Bought {f['name']}. Souls left: {player['gold']}")

    elif c == "2":
        if not gear_names:
            print("  Nothing for sale here.")
            return
        all_gear = {
            **{w["name"]: w for w in WEAPONS},
            **{a["name"]: a for a in ARMOURS},
            **{r["name"]: r for r in RUNES},
        }
        avail = [all_gear[n] for n in gear_names if n in all_gear]
        if not avail:
            print("  Nothing in stock.")
            return
        print("\n⚔ Gear for sale:")
        for i, g in enumerate(avail):
            price = int(g.get("value", g.get("atk", g.get("def", 10)) * 8))
            print(f"  {i}. {g['name']}  — {price} souls")
        try:
            idx = int(input("  Buy which? (-1 cancel) > "))
        except ValueError:
            return
        if 0 <= idx < len(avail):
            g = avail[idx]
            price = int(g.get("value", g.get("atk", g.get("def", 10)) * 8))
            if player["gold"] < price:
                print("  Not enough souls.")
            else:
                player["gold"] -= price
                if "atk" in g:
                    player.setdefault("weapons", []).append(g.copy())
                elif "def" in g:
                    player.setdefault("armours", []).append(g.copy())
                else:
                    player.setdefault("runes", []).append(g.copy())
                print(f"  Bought {g['name']}. Souls left: {player['gold']}")

    elif c == "3":
        _eat_food()

    elif c == "4":
        if player["gold"] < 50:
            print("  You can't afford to rest here (50 souls).")
        else:
            player["gold"] -= 50
            healed = min(30, player["max_hp"] - player["hp"])
            player["hp"] += healed
            print(f"  You rest at the inn. +{healed} HP. Souls left: {player['gold']}")

    elif c == "5":
        quest_board(region)

    elif c == "6":
        _ingredient_brew_menu()

    elif c == "7":
        print("  You leave the village.")


def visit_ruins(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n🗿═══════════════════════════════🗿")
    print(f"     {struct['name'].upper()}")
    print(f"🗿═══════════════════════════════🗿")
    print("Ancient script covers every stone wall...")
    print("you notice rusted metals in the ruins. they may still be usable")
    rust = random.randint(1,3)
    if rust == 1:
        loot + random.choice(METALS)
        print(f" the metal is a {loot}  and is still usable")
        player["metals"].append(loot)
    elif rust == 2:
        print("the metal is too rusted to be used")
    else:
        print("there was nothing there")
    roll = random.randint(1, 100)
    if roll < 30:
        souls = random.randint(40, 120)
        player["gold"] += souls
        print(f"  💀 You find a hidden cache — {souls} souls!")
    elif roll < 55:
        if RUNES:
            rune = random.choice(RUNES).copy()
            player.setdefault("runes", []).append(rune)
            print(f"  ✨ You recover an ancient rune: {rune['name']}!")
    elif roll < 75:
        if SCROLLS:
            scroll_name = random.choice(list(SCROLLS.keys()))
            player.setdefault("scrolls", {})[scroll_name] = (
                player["scrolls"].get(scroll_name, 0) + 1
            )
            print(f"  📜 You find a worn scroll: {scroll_name}!")
    elif roll < 90:
        bonus = random.randint(2, 5)
        player["max_hp"] += bonus
        player["hp"] = min(player["hp"] + bonus, player["max_hp"])
        print(f"  🌟 A rune-inscribed altar pulses — max HP +{bonus}!")
    else:
        trap = random.randint(10, 25)
        player["hp"] = max(1, player["hp"] - trap)
        print(f"  ⚠ A trap sprung! You take {trap} damage.")


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
        loot = random.choice(CORES)
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
    print(
        "A damp passage leads into darkness. Three floors of danger await within...\n"
    )

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
                mid_loot = random.choice(LOOT_ITEMS).copy()
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
        loot = random.choice(LOOT_ITEMS).copy()
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
    loot = random.choice(category)
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


def visit_camp(struct, region):
    advance_quest("explore_structure", region)
    print(f"\n⛺═══════════════════════════════⛺")
    print(f"     {struct['name'].upper()}")
    print(f"⛺═══════════════════════════════⛺")
    print(
        "A rough camp of travellers huddles around a fire. They're cautious but friendly.\n"
    )
    print("1. Rest by the fire  (free rest: +25 HP + +20 hunger)")
    print("2. Trade stories  (may learn a tip — small XP gain)")
    print("3. Buy/trade ingredients  (if you have any)")
    print("4. Move on")
    c = input("> ").strip()
    if c == "1":
        heal = min(25, player["max_hp"] - player["hp"])
        player["hp"] += heal
        player["hunger"] = min(100, player.get("hunger", 100) + 20)
        print(f"  You rest warmly. +{heal} HP, +20 hunger.")
    elif c == "2":
        xp = random.randint(20, 50)
        player["xp"] = player.get("xp", 0) + xp
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
        check_level_up()
    elif c == "3":
        ings = player.get("ingredients", [])
        if not ings:
            print("  You have no ingredients to offer.")
            return
        trade_ing = random.choice(ings)
        ings.remove(trade_ing)
        gold = random.randint(15, 40)
        player["gold"] += gold
    elif c == "4":
        print("  You leave the camp.")
        print("while near the camp you notice a fallen tree")
        print("you harvest wood from the tree")
        loot = random.choice(WOODS)
        player["woods"].append(loot)
        print(f"You found a {loot} wood")



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
    loot = random.choice(category)
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

    all_structs = REGION_STRUCTURES.get(r, [])
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
        if t == "village":
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
        print("\n  (Explore regions to discover structures — 12% chance each wander)")


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

    icon = village["icon"]
    print(f"\n{icon * 5} SECRET ELEMENTAL VILLAGE {icon * 5}")
    print(f"You have stumbled upon the hidden home of the {village['name']}!")
    print(f"{village['desc']}")
    print(f"\nThey tell you about  you their sacred {village['core']}.")
    print("1. Challenge their guardian to claim it by force")
    print("2. buy the core for 200000000 souls")
    print("3. buy special loot from the elemental village")
    print("4. Leave quietly")

    c = input("> ").strip()

    if c == "1":
        if player["gold"] < 200000000:
            print("You don't have enough souls (200000000 required).")
            return
        player["gold"] -= 200000000
        _give_elemental_core(village["core"])

    elif c == "2":
        boss_key = village["boss_key"]
        boss_data = ELEMENTAL_BOSSES[boss_key].copy()
        print(f"\n{icon} {boss_data['name']} rises to defend the village!")
        print(f'"{boss_data["taunt"]}"')
        _fight_elemental_boss(boss_data)
    elif c == "3":
        print("game feature in development")

    elif c == "4":
        print("You slip away unseen.")


def _give_elemental_core(core_name):
    player.setdefault("elemental_cores", [])
    player["elemental_cores"].append(core_name)
    data = ELEMENTAL_CORES[core_name]
    icon = _ELEM_ICONS.get(data["element"], "✨")
    print(f"\n{icon} Obtained {core_name}!")
    print(f"  {data['desc']}")
    print(
        f"  Bonus ATK when infused: +{data['bonus_atk']}  |  On-hit effect: {data['on_hit_effect']}"
    )


def _fight_elemental_boss(boss_data):
    """Special boss fight that applies elemental status effects every N turns."""
    boss = boss_data.copy()
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

        # Phase announcement
        max_hp = boss["max_hp"]
        if boss["hp"] <= max_hp * 0.25:
            print(f"{icon} FINAL PHASE — {boss['name']} burns with desperate fury!")
        elif boss["hp"] <= max_hp * 0.5:
            print(f"{icon} PHASE 3 — {boss['name']} unleashes full elemental power!")
        elif boss["hp"] <= max_hp * 0.75:
            print(f"{icon} PHASE 2 — {boss['name']} grows stronger!")

        print(f"\nYou: {player['hp']} HP  |  {boss['name']}: {boss['hp']} HP")
        c = input("1 atk  2 scroll  3 staff > ").strip()

        if c == "1":
            dmg = calculate_damage(player, boss, "weapon")
            boss["hp"] -= dmg
            print(f"You dealt {dmg} damage!")
            _apply_charged_weapon_effect(boss)
            for rune in player.get("runes", []):
                apply_rune_effect(rune, player, boss)
            apply_companion_support(boss)

        elif c == "2":
            use_scroll()

        elif c == "3":
            use_staff(boss)
            for rune in player.get("runes", []):
                apply_rune_effect(rune, player, boss)
            apply_companion_support(boss)

        if boss["hp"] <= 0:
            break

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
                print(
                    f"{icon} {boss['name']} inflicts {eff} on you! ({eff_dmg} dmg/turn)"
                )

        # Regular boss attack
        armour_def = player["armour"].get("def", 0) if player.get("armour") else 0
        boss_dmg = max(
            1, boss["atk"] // 4 - player.get("def", 0) // 4 - armour_def // 5
        )
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
            player["hp"] -= boss_dmg
            print(f"{icon} {boss['name']} strikes you for {boss_dmg}!")

        if player["hp"] <= 0 and player["active_buffs"].get("rebirth"):
            player["hp"] = max(1, player["max_hp"] // 2)
            player["active_buffs"].pop("rebirth", None)
            print("✨ Rebirth activated! You return to half health.")

    if ui:
        ui.clear_enemy()

    if player["hp"] > 0:
        print(f"\n🏆 You defeated {boss['name']}!")
        _give_elemental_core(boss["drop"])
        gain_xp(150)
        player["gold"] += 150
        drop_loot()
        drop_loot()
    else:
        print(f"\n☠ {boss['name']} has destroyed you.")


# =========================
# INFUSE GEAR WITH ELEMENTAL CORE
# =========================


def source_temple():
    """The Source Temple — hidden in the Riftlands. Only place to get Core Stabilisers."""
    if player["region"] != "Riftlands":
        print("The Source Temple can only be accessed from within the Riftlands.")
        return

    print("\n🌌═══════════════════════════════🌌")
    print("     THE SOURCE TEMPLE")
    print("🌌═══════════════════════════════🌌")
    print("A vast rift-stone edifice hums with elemental energy.")
    print("Runes of all four elements spiral up its pillars.")
    print("At its heart, a robed Keeper holds out a hand...\n")

    stabilisers = sum(
        1 for i in player.get("inventory", []) if i.get("name") == "Core Stabiliser"
    )
    print(f"You carry: {stabilisers} Core Stabiliser(s)\n")

    print("1. Purchase a Core Stabiliser  (300 souls)")
    print("2. Infuse your gear here       (core + stabiliser required)")
    print("3. Leave the temple")

    c = input("> ").strip()

    if c == "1":
        if player["gold"] < 300:
            print("The Keeper shakes their head — you lack the souls (300 required).")
            return
        player["gold"] -= 300
        item = {
            "name": "Core Stabiliser",
            "value": 500,
            "desc": "Anchors elemental cores into weapons and staffs.",
        }
        player.setdefault("inventory", []).append(item)
        print("🌌 The Keeper hands you a Core Stabiliser, still warm from the rift.")

    elif c == "2":
        infuse_gear()

    elif c == "3":
        print("You step back through the rift-stone archway.")


def infuse_gear():
    if player["region"] != "Riftlands":
        print(
            "⚠  Elemental infusion can only be performed inside the Riftlands Source Temple."
        )
        print("   Travel to the Riftlands and enter the Source Temple (option 16).")
        return

    cores = player.get("elemental_cores", [])
    has_stabiliser = any(
        i.get("name") == "Core Stabiliser" for i in player.get("inventory", [])
    )

    if not cores:
        print(
            "You have no elemental cores. Find secret elemental villages to obtain them."
        )
        return
    if not has_stabiliser:
        print(
            "You need a Core Stabiliser — purchase one from the Source Temple Keeper."
        )
        return

    print("\n=== ELEMENTAL INFUSION ===")
    print("Cores available:")
    for i, c in enumerate(cores):
        data = ELEMENTAL_CORES[c]
        print(
            f"  {i}. {c}  (+{data['bonus_atk']} ATK, on-hit: {data['on_hit_effect']})"
        )

    try:
        core_idx = int(input("Select core > "))
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
    print(
        f"  +{core_data['bonus_atk']} ATK bonus  |  On-hit: {core_data['on_hit_effect']}"
    )
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
    cores.pop(core_idx)
    for item in player["inventory"]:
        if item.get("name") == "Core Stabiliser":
            player["inventory"].remove(item)
            break

    print(
        f"\n{icon} {target['name']} is now infused with {core_data['element']} energy!"
    )
    print(f"  Every hit will apply {core_data['on_hit_effect']} to the enemy!")


def _apply_charged_weapon_effect(enemy):
    """Called after a weapon attack — apply elemental on-hit if weapon is infused."""
    w = player.get("weapon")
    if not w or not w.get("elemental_charged"):
        return
    eff = w.get("on_hit_effect", "burn")
    icon = _ELEM_ICONS.get(w.get("element", "fire"), "✨")
    enemy.setdefault("status", {})[eff] = enemy["status"].get(eff, 0) + 2
    print(f"{icon} Elemental charge inflicts {eff} on the enemy!")


def _sell_all_loot():
    loot = [item for item in player["inventory"] if "value" in item]
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
    while True:
        loot_count = len([i for i in player["inventory"] if "value" in i])
        loot_value = sum(i["value"] for i in player["inventory"] if "value" in i)
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
        print(
            f"B. Sell ALL unequipped weapons ({len(unequipped_w)} weapons, {weapon_value} souls)"
        )
        print(
            f"C. Sell ALL runes       ({len(player['runes'])} runes, {rune_value} souls)"
        )
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
            loot = [item for item in player["inventory"] if "value" in item]

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
    player["world_event_idx"] = (player.get("world_event_idx", 0) + 1) % len(
        WORLD_EVENTS
    )
    ev = get_current_world_event()
    print(f"\n{'═' * 46}")
    print(f"  🌍 WORLD EVENT CHANGED: {ev['icon']} {ev['name']}")
    print(f"  {ev['desc']}")
    print(f"{'═' * 46}")


def record_kill(enemy_name):
    kc = player.setdefault("kill_counts", {})
    kc[enemy_name] = kc.get(enemy_name, 0) + 1
    count = kc[enemy_name]
    if count == 5:
        print(f"\n📖 BESTIARY: {enemy_name} — weakness discovered! +25% dmg forever.")
    elif count == 20:
        print(
            f"\n📖 BESTIARY MASTERED: {enemy_name} — this creature holds no secrets from you."
        )


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
    if player["region"] != "The Dreamscape":
        return
    pl = player.get("prestige_level", 0)
    if pl >= 3:
        print("\n★★★ MAXIMUM PRESTIGE achieved. Your legend is eternal. ★★★")
        return
    print(f"\n{'═' * 46}")
    print(f"  ✨ PRESTIGE AVAILABLE — Level {pl} → {pl + 1}")
    print(f"  Reset to Lv.1, keep title & achievements.")
    print(f"  Gain: all base stats start {(pl + 1) * 10 + 100}% of normal.")
    print(f"  Type 'prestige' to ascend, anything else to skip.")
    print(f"{'═' * 46}")
    c = input("> ").strip().lower()
    if c != "prestige":
        print("  You choose to remain — for now.")
        return
    new_pl = pl + 1
    saved_title = player.get("title")
    saved_ach = list(player.get("achievements", []))
    saved_cores = list(player.get("forge_cores", []))
    saved_bosses = list(player.get("bosses_defeated", []))
    multiplier = 1.0 + new_pl * 0.10
    player.update(
        {
            "hp": int(100 * multiplier),
            "max_hp": int(100 * multiplier),
            "atk": int(10 * multiplier),
            "def": int(5 * multiplier),
            "speed": 5,
            "level": 1,
            "xp": 0,
            "xp_needed": 100,
            "gold": 50,
            "inventory": [],
            "weapons": [],
            "armours": [],
            "runes": [],
            "staffs": [],
            "quests": [],
            "potions": [],
            "kill_counts": {},
            "corruption": 0,
            "resonance_streak": 0,
            "resonance_ready": False,
            "active_set": None,
            "set_crit_counter": 0,
            "companion_xp": {},
            "companion_levels": {},
            "prestige_level": new_pl,
            "prestige_bonus": new_pl * 10,
            "title": saved_title,
            "achievements": saved_ach,
            "forge_cores": saved_cores,
            "bosses_defeated": saved_bosses,
            "unlocked_regions": {list(REGIONS.keys())[0]},
        }
    )
    print(f"\n🏅 PRESTIGE {new_pl} ASCENSION COMPLETE!")
    print(
        f"  All base stats are now {int(multiplier * 100)}% of normal. The legend grows."
    )


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
        r
        for r in FUSION_RECIPES
        if r["needs"][0] in weapon_names and r["needs"][1] in weapon_names
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
    print(
        f"\n🔥 FUSION COMPLETE! {fused['name']} (ATK {fused['atk']}) — auto-equipped!"
    )
    print(f'  "{recipe["desc"]}"')


def award_companion_xp(amount):
    companions = player.get("companions", [])
    if not companions:
        return
    cxp = player.setdefault("companion_xp", {})
    clvl = player.setdefault("companion_levels", {})
    for c in companions:
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

    print("\n=== RUNES ===")
    for i, r in enumerate(player["runes"]):
        print(f"{i}. {r['name']} ({r['effect']})")

    try:
        r_idx = int(input("Select rune > "))
        rune = player["runes"][r_idx]
    except:
        print("Invalid rune selection.")
        return

    if "rune" in weapon:
        old = weapon["rune"]
        player["runes"].append(old)

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
def game():
    load_game()
    _ui.init_ui(player)

    while True:
        print("\n--- SOULCRYPT ---")
        print("\n⚔️  EXPLORATION & COMBAT")
        print("1. Wander  (explore current region)")
        print("2. Travel  (move to different region)")
        print("9. Boss Fight  (challenge the boss)")
        print("26. Boss Rush Mode  (arcade fights)")

        print("\n🎒 EQUIPMENT & INVENTORY")
        print("4. Equip Weapon")
        print("5. Equip Armour")
        print("10. Inventory")
        print("11. Sell Loot")

        print("\n📚 UPGRADES & PROGRESSION")
        print("3. Upgrades & Runes  (blacksmith, bind runes, merge)")
        print("12. Cast Spell  (use magic abilities)")
        print("34. Enchant Equipment  (add stat bonuses)")
        print("28. Skill Tree  (permanent stat bonuses)")

        print("\n🏗️ REGIONS & STRUCTURES")
        print("13. World Map")
        print(f"17. Structures ({len(player.get('discovered_structures', {}).get(player['region'], []))} here)")
        print("14. Crimson Forge  (if in region)")
        if player["region"] == "Riftlands":
            print("15. Source Temple 🌌  (IN REGION)")
        else:
            print("15. Source Temple 🌌  (travel to Riftlands)")

        print("\n📊 CHARACTER & STATS")
        print("6. Stats & Details")
        sp = player.get("skill_points", 0)
        cls_str = player.get("class", "None")
        print(f"19. Skill Tree  ({sp} pts available) | Class: {cls_str}")
        active_q = len([q for q in player.get("quests", []) if not q.get("completed")])
        print(f"22. Companion Status  ({len(player.get('companions', []))} companions)")

        print("\n🎯 CONTENT & CHALLENGES")
        print("24. Daily Challenges  (quick rewards)")
        print("25. Weekly Challenges  (major rewards)")
        print("31. Seasonal Events  (limited-time)")
        print("32. Challenge Modes  (speedrun, ironman)")
        print("33. Story & Lore  (quest chapters)")

        print("\n🌟 PROGRESSION & ECONOMY")
        print("36. Battle Pass  (seasonal tiers)")
        print("35. New Game+  (prestige run)")
        print("42. Login Streak  (daily bonuses)")
        print("40. Trading Post  (player trading)")
        print("41. Town Building  (passive resources)")

        print("\n💎 CUSTOMIZATION & SOCIAL")
        n_ach = len(player.get("achievements", []))
        print(f"20. Achievements  ({n_ach}/{len(ACHIEVEMENTS)})")
        print("29. Cosmetics Shop  (skins & titles)")
        print("30. Guild  (clan system)")
        print("38. Arena PVP  (ranked battles)")

        print("\n🛠️  OTHER SYSTEMS")
        print("23. Crafting Hub  (armor, staffs)")
        print("21. Bestiary  (creatures catalogued)")
        print("37. Ritual Ceremonies  (bonfire buffs)")
        print("39. Recipe Discovery  (unlock recipes)")
        print("43. Factions  (alignment system)")
        print("44. Treasure Hunting  (find maps)")
        print("45. Mounts  (fast travel)")
        print("46. Status Effects  (active effects)")
        print(f"18. Eat Food  (hunger {player.get('hunger', 100)}/100)")

        print("\n⚙️  SYSTEM")
        print("7. Save Game")
        print("8. Exit  (quit to desktop)")

        ev = get_current_world_event()
        corruption = player.get("corruption", 0)
        corrupt_str = f" | ☠ Corruption {corruption}%" if corruption > 0 else ""

        active_set = player.get("active_set")
        set_str = (
            f" | {GEAR_SETS[active_set]['icon']} Set: {active_set}"
            if active_set
            else ""
        )

        prestige = player.get("prestige_level", 0)
        prestige_str = f" | 🏅 Prestige {prestige}" if prestige > 0 else ""

        print(f"  {ev['icon']} World Event: {ev['name']} — {ev['desc'][:50]}")

        if corruption > 0 or active_set or prestige > 0:
            print(
                f"  {corrupt_str.strip(' |')}{set_str.strip(' |')}{prestige_str.strip(' |')}"
            )

        if player["region"] in ELEMENTAL_VILLAGES:
            v = ELEMENTAL_VILLAGES[player["region"]]
            print(f"  {v['icon']} [{v['name']} territory — wander to find them]")

        c = input("> ")

        if c == "1":
            explore()
        elif c == "2":
            travel()
        elif c == "3":
            x = input(
                "1 blacksmith, 2 scroll, 3 rune, 4 merge runes, 5 cast spell, 6 fusion > "
            )

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
            break
        elif c == "9":
            boss_fight()
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

        check_gear_set()


# =========================================================
# ARMOR CRAFTING SYSTEM
# =========================================================

def craft_armor():
    """Craft armor pieces using the Loom structure"""
    global player

    # Armor only in Elemental Villages
    current_location = player.get("current_location", "Whispering Woods")
    if current_location not in ["Infernal Depths", "Frostbound Tundra", "Crystal Spire", "Whispering Woods"]:
        print("\nArmor can only be crafted in Elemental Villages!")
        print(f"Current location: {current_location}")
        return

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
        print(f"   DEF: +{recipe['def']}, HP: +{recipe['hp']}, SPD: {recipe['spd']}")
        print(f"   Materials: {recipe['materials']}, Cost: {recipe['cost']} gold")

    recipe_choice = input(f"\nSelect recipe (1-{len(recipes)}): ").strip()

    if not recipe_choice.isdigit() or int(recipe_choice) < 1 or int(recipe_choice) > len(recipes):
        print("Invalid choice.")
        return

    recipe = recipes[int(recipe_choice) - 1]

    # Check materials
    for material, amount in recipe["materials"].items():
        material_list = player.get("cloths", []) if material in CLOTHS else player.get("leathers", []) if material in LEATHERS else player.get("metals", [])
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

    player.setdefault("crafted_armor", []).append(armor_piece)

    # Gain structure XP
    player["structures"]["loom"]["xp"] += 5

    print(f"\n✓ Successfully crafted {recipe['name']}!")
    print(f"  DEF: +{recipe['def']}, HP: +{recipe['hp']}, SPD: {recipe['spd']}")


def view_rune_library():
    """Display all available runes and their effects"""
    print("\n=== RUNE LIBRARY ===")
    print("All runes have comprehensive effects:")
    print()

    # RUNES is a list of dicts from data.py with 100+ runes
    for rune in RUNES[:20]:  # Show first 20 runes as sample
        print(f"{rune['name']} [{rune.get('element', 'unknown').upper()}]")
        print(f"   Effect: {rune.get('effect', 'unknown')}")
        print()

    print(f"... and {len(RUNES) - 20} more runes available!")
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
    """Initialize or reset daily challenges"""
    import datetime
    today = datetime.date.today().isoformat()

    if player.get("last_daily_reset") != today:
        player["last_daily_reset"] = today
        player["daily_challenges"] = {}
        for challenge in DAILY_CHALLENGES:
            player["daily_challenges"][challenge["id"]] = {
                "progress": 0,
                "completed": False
            }


def init_weekly_challenges():
    """Initialize or reset weekly challenges"""
    import datetime
    week_start = (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())).isoformat()

    if player.get("last_weekly_reset") != week_start:
        player["last_weekly_reset"] = week_start
        player["weekly_challenges"] = {}
        for challenge in WEEKLY_CHALLENGES:
            player["weekly_challenges"][challenge["id"]] = {
                "progress": 0,
                "completed": False
            }


def update_challenge_progress(challenge_type, amount=1):
    """Update challenge progress when actions occur"""
    init_daily_challenges()
    init_weekly_challenges()

    # Daily challenges
    for challenge_id, data in player["daily_challenges"].items():
        challenge = next((c for c in DAILY_CHALLENGES if c["id"] == challenge_id), None)
        if not challenge or data["completed"]:
            continue

        if challenge["type"] == challenge_type:
            data["progress"] += amount
            if data["progress"] >= challenge["target"]:
                data["completed"] = True
                claim_challenge_reward(challenge, "daily")

    # Weekly challenges
    for challenge_id, data in player["weekly_challenges"].items():
        challenge = next((c for c in WEEKLY_CHALLENGES if c["id"] == challenge_id), None)
        if not challenge or data["completed"]:
            continue

        if challenge["type"] == challenge_type:
            data["progress"] += amount
            if data["progress"] >= challenge["target"]:
                data["completed"] = True
                claim_challenge_reward(challenge, "weekly")


def claim_challenge_reward(challenge, period):
    """Claim reward for completed challenge"""
    player["gold"] += challenge.get("reward_gold", 0)
    for material, amount in challenge.get("reward_materials", {}).items():
        player.setdefault(material, 0)
        player[material] += amount

    print(f"\n✓ Challenge Complete: {challenge['name']}!")
    print(f"  Gold: +{challenge.get('reward_gold', 0)}")
    for material, amount in challenge.get("reward_materials", {}).items():
        print(f"  {material}: +{amount}")


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
    """Start a boss rushing arcade mode"""
    global player

    print("\n=== BOSS RUSHING MODE ===")
    print("Face waves of bosses for epic rewards!\n")

    print("Select difficulty:")
    for i, (key, config) in enumerate(BOSS_RUSH_CONFIGURATIONS.items(), 1):
        print(f"{i}. {config['name']} ({config['bosses_count']} bosses)")
        print(f"   {config['description']}")

    choice = input("\nSelect difficulty (1-3): ").strip()

    difficulties = list(BOSS_RUSH_CONFIGURATIONS.keys())
    if choice not in ["1", "2", "3"]:
        print("Invalid choice.")
        return

    difficulty_key = difficulties[int(choice) - 1]
    config = BOSS_RUSH_CONFIGURATIONS[difficulty_key]

    print(f"\nStarting {config['name']}...")

    bosses_defeated = 0
    gold_earned = 0
    total_damage_taken = 0

    for i in range(config["bosses_count"]):
        print(f"\n--- Boss {i + 1}/{config['bosses_count']} ---")

        # Select random boss from all regions
        all_bosses = []
        for region_bosses in REGION_BOSSES.values():
            all_bosses.extend(region_bosses)

        boss = random.choice(all_bosses).copy()

        # Scale boss difficulty
        boss["hp"] = int(boss["hp"] * config["difficulty_multiplier"])
        boss["atk"] = int(boss["atk"] * config["difficulty_multiplier"])
        boss["def"] = int(boss["def"] * config["difficulty_multiplier"])

        print(f"Facing: {boss['name']}")
        print(f"HP: {boss['hp']} | ATK: {boss['atk']} | DEF: {boss['def']}")

        # Simulate boss fight (simplified)
        initial_hp = player["hp"]
        player_atk = player["atk"]
        damage_per_turn = max(1, player_atk - boss.get("def", 0))
        turns_to_win = max(1, (boss["hp"] + damage_per_turn - 1) // damage_per_turn)

        boss_damage_per_turn = max(1, boss["atk"] - player.get("def", 0))
        damage_taken = boss_damage_per_turn * turns_to_win

        if player["hp"] > damage_taken:
            player["hp"] -= damage_taken
            total_damage_taken += damage_taken
            bosses_defeated += 1
            boss_reward = boss.get("gold_reward", 50) * config["reward_multiplier"]
            gold_earned += int(boss_reward)
            player["gold"] += int(boss_reward)
            print(f"Victory! Took {damage_taken} damage. Earned {int(boss_reward)} gold.")
        else:
            print(f"Defeat! Boss defeated you.")
            break

    print(f"\n=== BOSS RUSH COMPLETE ===")
    print(f"Bosses Defeated: {bosses_defeated}/{config['bosses_count']}")
    print(f"Gold Earned: {gold_earned}")
    print(f"Total Damage Taken: {total_damage_taken}")

    # Update stats
    player["boss_rush_stats"]["total_runs"] += 1
    score = bosses_defeated * 100 + int(gold_earned / 10)
    if difficulty_key == "normal":
        player["boss_rush_stats"]["best_run_normal"] = max(
            player["boss_rush_stats"]["best_run_normal"], bosses_defeated
        )
    elif difficulty_key == "hard":
        player["boss_rush_stats"]["best_run_hard"] = max(
            player["boss_rush_stats"]["best_run_hard"], bosses_defeated
        )
    elif difficulty_key == "nightmare":
        player["boss_rush_stats"]["best_run_nightmare"] = max(
            player["boss_rush_stats"]["best_run_nightmare"], bosses_defeated
        )

    player["boss_rush_stats"]["leaderboard_score"] = max(
        player["boss_rush_stats"]["leaderboard_score"], score
    )


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
    """Browse and upgrade skill trees"""
    global player

    print("\n=== SKILL TREES ===")
    print(f"Skill Points Available: {player.get('skill_points', 0)}\n")

    for tree_key, tree in SKILL_TREES.items():
        print(f"{tree['icon']} {tree['name']}: {tree['description']}")
        learned = len(player.get("skill_tree", {}).get(tree_key, {}))
        print(f"   Skills Learned: {learned}/{len(tree['skills'])}\n")


def learn_skill(tree_name, skill_name):
    """Learn a new skill from the tree"""
    global player

    if player.get("skill_points", 0) < 1:
        print("Not enough skill points!")
        return False

    tree = SKILL_TREES.get(tree_name)
    if not tree or skill_name not in tree["skills"]:
        print("Skill not found!")
        return False

    skill = tree["skills"][skill_name]
    player["skill_tree"][tree_name][skill_name] = True
    player["skill_points"] -= 1

    # Apply stat bonus
    stat = skill["stat"]
    bonus = skill["bonus"]
    if stat == "all":
        player["atk"] += bonus
        player["def"] += bonus
        player["spd"] += bonus
    else:
        player[stat] += bonus

    print(f"Learned {skill_name}! +{bonus} {stat}")
    return True


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
        owned = "OWNED" if key in player.get("cosmetics", {}).get("owned", []) else str(cosmetic["price"])
        print(f"  - {cosmetic['name']}: {owned}")

    print("\nWEAPON SKINS:")
    for key, cosmetic in COSMETICS_SHOP["weapon_skins"].items():
        owned = "OWNED" if key in player.get("cosmetics", {}).get("owned", []) else str(cosmetic["price"])
        print(f"  - {cosmetic['name']}: {owned}")

    print("\nTITLES:")
    for key, cosmetic in COSMETICS_SHOP["titles"].items():
        owned = "OWNED" if key in player.get("cosmetics", {}).get("owned", []) else str(cosmetic["price"])
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
    """Display story and lore"""
    print("\n=== STORY & LORE ===")
    print("Discover the world's secrets through quests!\n")

    for chapter_key, chapter in STORY_QUESTS.items():
        print(f"{chapter['name']}: {chapter['description']}")
        print(f"  NPCs: {', '.join(chapter['npcs'])}")
        print(f"  Rewards: {chapter['rewards']}\n")


# =========================================================
# EQUIPMENT ENCHANTING
# =========================================================

def enchant_equipment():
    """Enchant gear with permanent bonuses"""
    global player

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

    if not weapon_choice.isdigit() or int(weapon_choice) < 1 or int(weapon_choice) > len(player["weapons"]):
        print("Invalid choice.")
        return

    weapon = player["weapons"][int(weapon_choice) - 1]

    print("\nAvailable Enchantments:")
    for i, (key, ench) in enumerate(ENCHANTMENTS.items(), 1):
        print(f"{i}. {ench['name']} - +{ench['bonus']} {ench['stat']} ({int(ench['success_rate']*100)}% success)")

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
        print(f"You need Prestige {NEWGAME_PLUS_CONFIG['prestige_requirements']} to unlock New Game+")
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
        completed = "✓ CLAIMED" if current_tier >= tier_num else f"{tier_data['required_xp']} XP needed"
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
        status = "DISCOVERED" if recipe_key in discovered else f"{int(recipe['discovery_rate']*100)}% chance"
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
        "data": effect
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

    if cure["removes"] == "all":
        target["active_effects"] = {}
        return True

    for effect in cure["removes"]:
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
        print(f"   {effect_info['description']}\n")


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
    """Charge empty staffs with elemental cores at the Source Temple"""
    global player

    # Imbuing ONLY at Source Temple
    current_location = player.get("current_location", "Whispering Woods")
    if current_location != "Source Temple":
        print("\nStaff imbuing can only be performed at the Source Temple!")
        print(f"Current location: {current_location}")
        return

    player_staffs = player.get("staffs", [])
    player_cores = player.get("cores", [])

    if not player_staffs:
        print("\nYou have no staffs to imbue.")
        return

    if not player_cores:
        print("\nYou have no elemental cores to imbue with.")
        return

    print("\n=== SOURCE TEMPLE - STAFF IMBUING ===")
    print("Charge your empty staffs with elemental core energy.\n")

    print("Your staffs:")
    for i, staff in enumerate(player_staffs, 1):
        charged = "✓ CHARGED" if staff.get("charged") else "Empty"
        core_used = staff.get("core_used", "None")
        print(f"{i}. {staff['name']} [{charged}] (Core: {core_used})")

    staff_choice = input(f"\nSelect staff to charge (1-{len(player_staffs)}): ").strip()

    if not staff_choice.isdigit() or int(staff_choice) < 1 or int(staff_choice) > len(player_staffs):
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

    # Charge the staff
    selected_staff["charged"] = True
    selected_staff["core_used"] = selected_core_name
    selected_staff["element"] = selected_core.get("element")
    selected_staff["on_hit_effect"] = selected_core.get("on_hit_effect")
    selected_staff["bonus_atk"] = selected_core.get("bonus_atk", 0)

    # Remove core from inventory
    player["cores"].remove(selected_core_name)

    # Gain Source Temple XP
    player["structures"].setdefault("source_temple", {"level": 1, "xp": 0})
    player["structures"]["source_temple"]["xp"] += 15

    # Track imbuement history
    player.setdefault("imbuement_history", []).append({
        "staff": selected_staff["name"],
        "core": selected_core_name,
        "element": selected_core.get("element"),
        "effect": selected_core.get("on_hit_effect"),
    })

    print(f"\n✨ Successfully charged {selected_staff['name']} with {selected_core_name}!")
    print(f"   Element: {selected_core.get('element').title()}")
    print(f"   Effect: {selected_core.get('on_hit_effect')}")
    print(f"   ATK Bonus: +{selected_core.get('bonus_atk', 0)}")


def craft_staff():
    """Create staffs by combining runes"""
    global player

    # Staffs ONLY in Crimson Depths
    current_location = player.get("current_location", "Whispering Woods")
    if current_location != "Crimson Depths":
        print("\nStaffs can only be crafted in Crimson Depths!")
        print(f"Current location: {current_location}")
        return

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
        "elements": [r.get("element") for r in selected_runes],
    }

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
    """Disenchant equipment to recover materials and runes"""
    global player

    print("\n=== DISENCHANTRY - SALVAGE EQUIPMENT ===")
    print("Break down unwanted equipment to recover materials.")

    equipment = []
    equipment_types = {
        "weapons": (player.get("weapons", []), "weapon"),
        "armor": (player.get("crafted_armor", []), "armor"),
        "staffs": (player.get("staffs", []), "staff"),
    }

    for eq_type, (items, label) in equipment_types.items():
        for item in items:
            equipment.append((item, label))

    if not equipment:
        print("You have no equipment to salvage.")
        return

    print(f"\nAvailable equipment ({len(equipment)} total):")
    for i, (item, label) in enumerate(equipment, 1):
        print(f"  {i}. {item.get('name', 'Unknown')} ({label})")

    choice = input("\nSelect item to salvage: ").strip()

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(equipment):
        print("Invalid choice.")
        return

    item, item_type = equipment[int(choice) - 1]
    print(f"\nSalvaging {item['name']}...")

    # Calculate returns
    materials_recovered = {}

    if item_type == "weapon":
        materials_recovered = {k: max(1, v // 2) for k, v in item.get("materials", {}).items()}
    elif item_type == "armor":
        materials_recovered = {k: max(1, v // 2) for k, v in item.get("materials", {}).items()}
    elif item_type == "staff":
        # Return basic rune materials
        for rune_name in item.get("runes", []):
            materials_recovered[rune_name] = materials_recovered.get(rune_name, 0) + 1

    # Add materials to inventory
    for material, amount in materials_recovered.items():
        if material in CLOTHS:
            player.setdefault("cloths", []).extend([material] * amount)
        elif material in LEATHERS:
            player.setdefault("leathers", []).extend([material] * amount)
        elif material in METALS:
            player.setdefault("metals", []).extend([material] * amount)

    # Remove from equipment lists
    if item_type == "weapon" and item in player.get("weapons", []):
        player["weapons"].remove(item)
    elif item_type == "armor" and item in player.get("crafted_armor", []):
        player["crafted_armor"].remove(item)
    elif item_type == "staff" and item in player.get("staffs", []):
        player["staffs"].remove(item)

    # Gain structure XP
    player["structures"]["disenchantry"]["xp"] += 5

    print(f"✓ Salvaged {item['name']}!")
    print(f"  Materials recovered: {materials_recovered}")


def transmute_materials():
    """Convert materials between types"""
    global player

    print("\n=== MATERIAL TRANSMUTATION ===")
    print("Convert materials to upgrade your gear.")

    transmutations = [
        {"name": "Copper to Iron (3 copper → 1 iron)", "cost": 25, "input": {"Copper": 3}, "output": {"Iron": 1}},
        {"name": "Linen to Silk (3 linen → 1 silk)", "cost": 100, "input": {"Linen": 3}, "output": {"Silk": 1}},
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
        print(merchant['desc'])
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
        collected = sum(1 for piece in pieces if piece in player_weapons or piece in player_armor or piece in player_staffs)

        print(f"{set_name} ({collected}/{len(pieces)} pieces)")
        for piece in pieces:
            status = "✓" if piece in player_weapons or piece in player_armor or piece in player_staffs else "✗"
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
    """View and interact with crafting structures"""
    global player

    while True:
        print("\n=== CRAFTING HUB ===")
        current_loc = player.get("current_location", "Whispering Woods")
        print(f"Current Location: {current_loc}")
        print()

        for key, struct in STRUCTURES.items():
            level = player["structures"].get(key, {"level": 1}).get("level")
            print(f"{struct['icon']} {struct['name']} (Level {level})")
            print(f"   {struct['description']}")
            print(f"   Location: {struct.get('location', 'Unknown')}")

        print("\n--- CRAFTING OPTIONS ---")
        print("1. Travel to Location")
        print("2. Forge (Weapons - Crimson Depths only)")
        print("3. Loom (Armor - Elemental Villages only)")
        print("4. Enchantment Tower (Staffs - Crimson Depths only)")
        print("5. Alchemy Lab (Potions)")
        print("6. Disenchantry (Salvage)")
        print("7. Imbue Staff (Source Temple only)")
        print("8. Rune Library (View All Runes)")
        print("9. Trading Post (Buy/Sell)")
        print("10. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            travel_to_location()
        elif choice == "2":
            forge_weapon()
        elif choice == "3":
            craft_armor()
        elif choice == "4":
            craft_staff()
        elif choice == "5":
            pass  # existing potion crafting
        elif choice == "6":
            salvage_equipment()
        elif choice == "7":
            imbue_staff()
        elif choice == "8":
            view_rune_library()
        elif choice == "9":
            visit_merchants()
        elif choice == "10":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    game()
