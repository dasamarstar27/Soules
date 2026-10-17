# =========================================================
# COMPREHENSIVE RUNE STATUS EFFECTS - EACH RUNE'S EFFECTS
# =========================================================

# Maps each rune to its unique status effect
RUNE_EFFECTS = {
    "burn": {"name": "Burn", "icon": "🔥", "duration": 3, "damage_per_turn": 2, "element": "fire"},
    "soak": {"name": "Soaked", "icon": "💧", "duration": 2, "def_modifier": 0.8, "element": "water"},
    "defense_up": {"name": "Defense Up", "icon": "🛡", "duration": 4, "def_modifier": 1.3, "element": "earth"},
    "speed_up": {"name": "Speed Boost", "icon": "⚡", "duration": 3, "spd_modifier": 1.4, "element": "wind"},
    "shock": {"name": "Shocked", "icon": "⚡", "duration": 2, "stun_chance": 0.3, "element": "lightning"},
    "freeze": {"name": "Frozen", "icon": "❄", "duration": 2, "frozen": True, "spd_modifier": 0.3, "element": "ice"},
    "regen": {"name": "Regeneration", "icon": "🌿", "duration": 5, "hp_restore_per_turn": 3, "element": "nature"},
    "poison": {"name": "Poisoned", "icon": "☠", "duration": 4, "damage_per_turn": 1, "element": "poison"},
    "blind": {"name": "Blinded", "icon": "👁", "duration": 3, "accuracy_penalty": 0.5, "element": "shadow"},
    "heal_tick": {"name": "Healing", "icon": "✨", "duration": 4, "hp_restore_per_turn": 2, "element": "light"},
    "armor_break": {"name": "Armor Broken", "icon": "🔨", "duration": 3, "def_modifier": 0.5, "element": "metal"},
    "crit_up": {"name": "Critical Chance", "icon": "⭐", "duration": 4, "crit_chance": 0.4, "element": "crystal"},
    "life_drain": {"name": "Life Drain", "icon": "🩸", "duration": 2, "damage_per_turn": 2, "attacker_heal": 0.5, "element": "blood"},
    "mana_regen": {"name": "Mana Regen", "icon": "🔮", "duration": 5, "mana_restore_per_turn": 5, "element": "spirit"},
    "chain_shock": {"name": "Chain Lightning", "icon": "⚡", "duration": 2, "damage_per_turn": 3, "chain_targets": 2, "element": "storm"},
    "magma": {"name": "Magma", "icon": "🌋", "duration": 3, "damage_per_turn": 4, "element": "magma"},
    "burn_freeze": {"name": "Frozen Flames", "icon": "🔥❄", "duration": 3, "damage_per_turn": 2, "freeze_chance": 0.4, "element": "frostfire"},
    "deadly_poison": {"name": "Deadly Poison", "icon": "☠☠", "duration": 5, "damage_per_turn": 3, "element": "venom"},
    "root": {"name": "Rooted", "icon": "🌳", "duration": 3, "immobilized": True, "spd_modifier": 0.0, "element": "nature"},
    "stun": {"name": "Stunned", "icon": "😵", "duration": 1, "stunned": True, "element": "earth"},
    "void_burn": {"name": "Void Burn", "icon": "🌑🔥", "duration": 4, "damage_per_turn": 3, "pierce_defense": True, "element": "void"},
    "curse": {"name": "Cursed", "icon": "💀", "duration": 5, "atk_modifier": 0.7, "def_modifier": 0.7, "element": "abyss"},
    "divine_luck": {"name": "Divine Fortune", "icon": "✨🌟", "duration": 4, "crit_chance": 0.3, "dodge_chance": 0.2, "element": "celestial"},
    "starfall": {"name": "Starfall", "icon": "⭐", "duration": 2, "damage_per_turn": 4, "aoe": True, "element": "astral"},
    "sun_blast": {"name": "Solar Blast", "icon": "☀", "duration": 2, "damage_per_turn": 5, "element": "solar"},
    "moon_guard": {"name": "Lunar Shield", "icon": "🌙", "duration": 4, "def_modifier": 1.2, "night_bonus": 1.4, "element": "lunar"},
    "slow_time": {"name": "Time Slow", "icon": "⏱", "duration": 3, "spd_modifier": 0.4, "element": "time"},
    "warp": {"name": "Warp", "icon": "🌌", "duration": 1, "teleport": True, "element": "space"},
    "crush": {"name": "Crushed", "icon": "💥", "duration": 2, "damage": 10, "def_bypass": True, "element": "gravity"},
    "random_effect": {"name": "Chaos", "icon": "🌀", "duration": 2, "randomized": True, "element": "chaos"},
    "stability": {"name": "Stabilized", "icon": "⚖", "duration": 4, "effect_resistance": 0.5, "element": "order"},
    "sleep": {"name": "Sleep", "icon": "😴", "duration": 2, "sleeping": True, "element": "dream"},
    "fear": {"name": "Feared", "icon": "😱", "duration": 3, "atk_modifier": 0.6, "flee_chance": 0.3, "element": "nightmare"},
    "soul_drain": {"name": "Soul Drained", "icon": "👻", "duration": 3, "all_stats_modifier": 0.8, "element": "soul"},
    "greater_regen": {"name": "Greater Regen", "icon": "🌿🌿", "duration": 5, "hp_restore_per_turn": 5, "element": "life"},
    "execute": {"name": "Marked for Death", "icon": "💀", "duration": 2, "execute_threshold": 0.25, "element": "death"},
    "double_cast": {"name": "Echo", "icon": "✖✖", "duration": 2, "attack_count": 2, "element": "echo"},
    "reflect": {"name": "Reflection", "icon": "🪞", "duration": 3, "reflect_damage": 0.5, "element": "mirror"},
    "dragon_fury": {"name": "Dragon Fury", "icon": "🐉", "duration": 2, "atk_modifier": 1.6, "damage_per_turn": 2, "element": "dragon"},
    "rebirth": {"name": "Rebirth", "icon": "🔄", "duration": 4, "resurrect_once": True, "element": "phoenix"},
    "giant_strength": {"name": "Giant Form", "icon": "💪", "duration": 3, "atk_modifier": 1.8, "def_modifier": 1.3, "element": "titan"},
    "hellfire": {"name": "Hellfire", "icon": "🔥💀", "duration": 3, "damage_per_turn": 4, "cannot_heal": True, "element": "demon"},
    "holy_barrier": {"name": "Holy Shield", "icon": "⛪", "duration": 4, "damage_reduction": 0.4, "undead_damage": 1.5, "element": "angel"},
    "tidal_wave": {"name": "Tidal Wave", "icon": "🌊", "duration": 2, "damage": 15, "aoe": True, "element": "water"},
    "fortress": {"name": "Fortress", "icon": "🏰", "duration": 4, "def_modifier": 2.0, "damage_reduction": 0.5, "element": "earth"},
    "nature_blessing": {"name": "Nature's Blessing", "icon": "🌲", "duration": 5, "hp_restore_per_turn": 4, "atk_modifier": 1.1, "element": "forest"},
    "dimension_break": {"name": "Dimension Break", "icon": "🌌💥", "duration": 2, "damage": 20, "def_bypass": True, "element": "rift"},
    "reality_bend": {"name": "Reality Bend", "icon": "🌀", "duration": 3, "all_stats_modifier": 1.3, "element": "cosmic"},
    "time_lock": {"name": "Time Lock", "icon": "⏰", "duration": 2, "immobilized": True, "stunned": True, "element": "eternity"},
    "arcane_burst": {"name": "Arcane Burst", "icon": "✨", "duration": 1, "damage": 12, "element": "arcane"},
    "plasma_surge": {"name": "Plasma Surge", "icon": "⚡💥", "duration": 2, "damage_per_turn": 4, "shock_chain": True, "element": "plasma"},
    "sonic_shock": {"name": "Sonic Blast", "icon": "🔊", "duration": 2, "damage": 8, "stun_chance": 0.4, "element": "sonic"},
    "ember_blade": {"name": "Ember Blade", "icon": "🔪🔥", "duration": 2, "damage_per_turn": 2, "atk_modifier": 1.2, "element": "ember"},
    "glacial_chill": {"name": "Glacial Chill", "icon": "❄💎", "duration": 3, "spd_modifier": 0.5, "freeze_chance": 0.3, "element": "glacial"},
    "steel_guard": {"name": "Steel Guard", "icon": "⚔🛡", "duration": 4, "def_modifier": 1.5, "physical_reduction": 0.3, "element": "steel"},
    "radiant_glow": {"name": "Radiant Glow", "icon": "✨🌟", "duration": 4, "hp_restore_per_turn": 3, "light_damage": 1.3, "element": "radiant"},
    "ethereal_wisp": {"name": "Ethereal Form", "icon": "👻", "duration": 3, "dodge_chance": 0.4, "intangible": True, "element": "ethereal"},
    "necrotic_decay": {"name": "Necrotic Decay", "icon": "☠🖤", "duration": 4, "damage_per_turn": 2, "max_hp_reduction": 0.8, "element": "necrotic"},
    "primal_roar": {"name": "Primal Roar", "icon": "🦁", "duration": 2, "atk_modifier": 1.5, "def_modifier": 0.8, "element": "primal"},
    "vortex_pull": {"name": "Vortex", "icon": "🌀", "duration": 2, "damage": 10, "pull_effect": True, "element": "vortex"},
    "quartz_barrier": {"name": "Quartz Barrier", "icon": "💎", "duration": 3, "def_modifier": 1.4, "crystal_damage": 1.2, "element": "quartz"},
    "berserk": {"name": "Berserk", "icon": "⚔", "duration": 3, "atk_modifier": 1.5, "def_modifier": 0.7, "element": "rage"},
    "sacrifice": {"name": "Sacrifice", "icon": "💔", "duration": 2, "hp_cost": 10, "damage_boost": 2.0, "element": "blood"},
    "shatter": {"name": "Shatter", "icon": "💔", "duration": 1, "damage": 25, "element": "break"},
    "overload": {"name": "Overload", "icon": "⚡", "duration": 2, "damage": 15, "self_damage": 3, "element": "arcane"},
    "thorns": {"name": "Thorns", "icon": "🌵", "duration": 3, "reflect_damage": 0.7, "element": "earth"},
    "banish": {"name": "Banish", "icon": "🌑", "duration": 1, "remove_from_battle": True, "element": "void"},
    "lightning_storm": {"name": "Lightning Storm", "icon": "⛈", "duration": 3, "damage_per_turn": 4, "chain_targets": 3, "element": "storm"},
    "blood_moon": {"name": "Blood Moon", "icon": "🌙🔴", "duration": 4, "atk_modifier": 1.4, "def_modifier": 0.9, "element": "blood"},
    "ancient_power": {"name": "Ancient Power", "icon": "👑", "duration": 5, "all_stats_modifier": 1.2, "element": "ancient"},
    "wraith_form": {"name": "Wraith Form", "icon": "👻", "duration": 3, "dodge_chance": 0.5, "damage": 0.8, "element": "shadow"},
}

# Categorize effects by type
OFFENSIVE_STATUS = {k: v for k, v in RUNE_EFFECTS.items()
                    if any(x in v for x in ["damage_per_turn", "damage", "stun_chance", "atk_modifier"])}

DEFENSIVE_STATUS = {k: v for k, v in RUNE_EFFECTS.items()
                    if any(x in v for x in ["def_modifier", "damage_reduction", "hp_restore", "dodge_chance"])}

UTILITY_STATUS = {k: v for k, v in RUNE_EFFECTS.items()
                  if any(x in v for x in ["teleport", "randomized", "effect_resistance", "sleeping"])}

# Status effect synergies - combining effects
STATUS_SYNERGIES = {
    "frozen_inferno": {
        "trigger": ["burn", "freeze"],
        "result": "Crystallized Flame",
        "effect": "Triple damage from both effects combined"
    },
    "electric_storm": {
        "trigger": ["shock", "chain_shock"],
        "result": "Perfect Storm",
        "effect": "All nearby enemies take damage"
    },
    "dragon_reborn": {
        "trigger": ["dragon_fury", "rebirth"],
        "result": "Eternal Dragon",
        "effect": "Resurrect with full power"
    },
    "chaos_order": {
        "trigger": ["random_effect", "stability"],
        "result": "Equilibrium",
        "effect": "All stats balanced perfectly"
    },
    "void_reality": {
        "trigger": ["void_burn", "reality_bend"],
        "result": "Void Singularity",
        "effect": "Devastating damage ignoring all defense"
    },
    "holy_fire": {
        "trigger": ["holy_barrier", "sun_blast"],
        "result": "Divine Judgment",
        "effect": "Purify all negative effects and damage enemies"
    },
}

# Cures for negative status effects
STATUS_CURES = {
    "water": ["burn", "hellfire", "magma"],
    "fire": ["freeze", "glacial_chill", "root"],
    "antidote": ["poison", "deadly_poison"],
    "purify": ["curse", "necrotic_decay"],
    "cleanse": ["all"],
    "light": ["blind"],
    "adrenaline": ["stun", "sleep"],
}

# Boss-exclusive status effects (unique, powerful)
BOSS_EXCLUSIVE_STATUS = {
    "ancient_curse": {
        "name": "Ancient Curse",
        "icon": "⚱",
        "duration": float('inf'),
        "stacking": True,
        "stat_reduction_per_stack": 0.05,
        "description": "Permanent curse that stacks"
    },
    "dimensional_rift": {
        "name": "Dimensional Rift",
        "icon": "🌀",
        "duration": 5,
        "random_repositioning": True,
        "description": "Cannot control battle position"
    },
    "reality_warp": {
        "name": "Reality Warp",
        "icon": "✨",
        "duration": 2,
        "action_inversion": True,
        "description": "All actions reversed"
    },
    "infinity_loop": {
        "name": "Infinity Loop",
        "icon": "∞",
        "duration": float('inf'),
        "trap_in_battle": True,
        "description": "Permanently trapped in battle"
    },
}
