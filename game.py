"""Soules browser edition: deterministic, serializable adventure rules."""

from copy import deepcopy
import random
import uuid
import alchemy
import village
from data import RUNES, REGIONS, NORMAL_MONSTERS, REGION_BOSSES, STORY_QUESTS, REGION_STRUCTURES
from recipes import SPECIAL_FUSION_RECIPES
from effects import EFFECTS, apply, tick, expire, hit, heal, stat, total, cure

CATALOG = {r["name"]: deepcopy(r) for r in RUNES}
ALIASES = {"Fire Rune": "Flame Rune", "Reality Rune": "Cosmic Rune"}
RECIPES = {
    frozenset(ALIASES.get(n, n) for n in names): deepcopy(r)
    for names, r in SPECIAL_FUSION_RECIPES.items()
}
for recipe in RECIPES.values():
    for component in recipe["components"]:
        assert component in EFFECTS, component


# ============================================================================
# CHARACTER & SHARED JOURNAL
# ============================================================================


def new_game(name="Wanderer", cls="Runekeeper"):
    name = str(name).strip()[:24] or "Wanderer"
    p = dict(
        name=name,
        cls=cls if cls in ("Runekeeper", "Warden", "Reaver") else "Runekeeper",
        hp=100,
        max_hp=100,
        mana=40,
        max_mana=40,
        atk=14,
        **{"def": 4},
        speed=10,
        is_night=False,
        level=1,
        xp=0,
        gold=65,
        status={},
    )
    if p["cls"] == "Warden":
        p.update(hp=120, max_hp=120)
        p["def"] = 7
    elif p["cls"] == "Reaver":
        p.update(atk=18, max_mana=30, mana=30)
    else:
        p.update(max_mana=50, mana=50)
    return dict(
        version=2,
        **alchemy.starter(),
        tutorial=0,
        player=p,
        region=0,
        unlocked=0,
        enemy=None,
        kills=0,
        bosses=[],
        turn=0,
        runes=[
            rune(n)
            for n in (
                "Flame Rune",
                "Water Rune",
                "Earth Rune",
                "Nature Rune",
                "Ice Rune",
                "Lightning Rune",
            )
        ],
        equipped=[],
        discoveries=[],
        log=["You awaken beneath the roots of the World Tree. The first seal is calling."],
        victory=False,
        shards=0,
        potions=3,
        cleanses=2,
    )


def log(g, text):
    g["log"].append(text)
    g["log"] = g["log"][-100:]


# ============================================================================
# STORY & CHAPTER PROGRESSION
# ============================================================================


def chapter_one_complete(g):
    """The original game's ending: all main regions open, Dreamscape guardian beaten."""
    dreamscape = REGIONS.index("The Dreamscape")
    return g["unlocked"] >= len(REGIONS) - 1 and dreamscape in g["bosses"]


def story_progress(g):
    chapter = 2 if chapter_one_complete(g) else 1
    return dict(
        chapter=chapter,
        quest=STORY_QUESTS[f"chapter_{chapter}"],
        unlocked_regions=g["unlocked"] + 1,
        total_regions=len(REGIONS),
        original_game_complete=chapter_one_complete(g),
    )


# ============================================================================
# EXPLORATION, TRAVEL & SANCTUARY
# ============================================================================


def encounter(g, boss=False, rng=random):
    if g["enemy"]:
        raise ValueError("Finish the current encounter first.")
    if g["player"]["hp"] <= 0:
        raise ValueError("Rest at the sanctuary first.")
    region = REGIONS[g["region"]]
    original = (
        REGION_BOSSES.get(region)
        if boss
        else rng.choice(NORMAL_MONSTERS.get(region, NORMAL_MONSTERS[REGIONS[0]]))
    )
    original = original or dict(name="The Dream Eater", hp=200, atk=25, **{"def": 8})
    # Rebalance old late-game boss statistics into a complete region-by-region curve.
    i = g["region"]
    hp = (100 + 38 * i) if boss else (32 + 17 * i)
    e = dict(
        name=original["name"],
        hp=hp,
        max_hp=hp,
        atk=(13 + 4 * i) if boss else (8 + 3 * i),
        **{"def": 3 + 2 * i},
        speed=8 + i,
        mana=30,
        max_mana=30,
        status={},
        boss=boss,
        undead=any(
            word in original["name"].lower()
            for word in ("soul", "wraith", "skeleton", "undead", "ghost")
        ),
        effect=original.get("effect", ["poison", "burn", "freeze", "shock", "curse"][i % 5]),
        phase=1,
    )
    e["effect"] = {"light": "blind"}.get(e["effect"], e["effect"])
    g["enemy"] = e
    log(g, f"{'Guardian awakened' if boss else 'Encounter'}: {e['name']}.")


def _exploration_action(g, action, body, rng):
    if action in ("explore", "boss"):
        encounter(g, action == "boss", rng)
        return True
    elif action == "travel":
        if g["enemy"]:
            raise ValueError("You cannot travel during a battle.")
        i = body.get("region")
        if type(i) is not int or not 0 <= i <= g["unlocked"]:
            raise ValueError("Defeat the previous guardian to unlock this region.")
        g["region"] = i
        log(g, f"You travel to {REGIONS[i]}.")
        return True
    elif action == "rest":
        if g["enemy"]:
            raise ValueError("You cannot rest during a battle.")
        p = g["player"]
        p["hp"] = p["max_hp"]
        p["mana"] = p["max_mana"]
        p["status"] = {}
        log(g, "The sanctuary restores your soul, mana, and health.")
        return True
    return False


# ============================================================================
# COMBAT, SYNERGIES & REWARDS
# ============================================================================


def synergies(g):
    p, e = g["player"], g["enemy"]
    if "stability" in p["status"] and (
        "random_effect" in p["status"] or "random_effect" in e["status"]
    ):
        p["mana"] = p["max_mana"]
        log(g, "Equilibrium restores your mana.")
    if {"holy_barrier", "sun_blast"} <= p["status"].keys() or (
        "holy_barrier" in p["status"] and "sun_blast" in e["status"]
    ):
        cure(p, "cleanse")
        log(g, "Divine Judgment purifies your afflictions.")
    if {"void_burn", "reality_bend"} <= e["status"].keys() or (
        "void_burn" in e["status"] and "reality_bend" in p["status"]
    ):
        from effects import hurt

        hurt(e, 10, g["log"])
        log(g, "Void Singularity tears through defense for 10 damage.")
    if {"shock", "chain_shock"} <= e["status"].keys():
        from effects import hurt

        hurt(e, 6, g["log"])
        log(g, "Perfect Storm strikes for 6 extra damage.")


def combat(g, action, rune_id=None, rng=random, potion_id=None):
    p, e = g["player"], g["enemy"]
    if not e:
        raise ValueError("Explore or challenge a guardian first.")
    if action == "drink" and not any(p["id"] == potion_id for p in g["brews"]):
        raise ValueError("Choose a potion from your satchel.")
    if action == "cast":
        r = next((r for r in g["runes"] if r["id"] == rune_id), None)
        if not r:
            raise ValueError("Choose a rune you own.")
        if total(p, "silenced"):
            raise ValueError("Silenced: attack, guard, or cleanse instead.")
        if p["mana"] < cost(r):
            raise ValueError("Not enough mana. Guard to recover mana.")
    if action == "potion" and g["potions"] <= 0:
        raise ValueError("No potions left. Buy one at the sanctuary.")
    if action == "cleanse" and g["cleanses"] <= 0:
        raise ValueError("No cleansing salts left.")
    if action == "flee" and (e["boss"] or total(p, "trap_in_battle")):
        raise ValueError("You cannot flee this encounter.")
    g["turn"] += 1
    p["is_night"] = g["turn"] % 12 >= 6
    ps, es = set(p["status"]), set(e["status"])
    can_act = tick(p, e, g["log"], rng)
    enemy_can_act = tick(e, p, g["log"], rng)
    if p["hp"] <= 0 or e["hp"] <= 0:
        expire(p, ps)
        expire(e, es)
        finish(g, rng)
        return
    guarding = False
    if can_act:
        if action == "attack":
            for _ in range(min(2, max(1, int(total(p, "attack_count"))))):
                hit(p, e, stat(p, "atk"), g["log"], rng)
                if e["hp"] <= 0 or p["hp"] <= 0:
                    break
            for r in g["runes"]:
                if r["id"] in g["equipped"] and rng.random() < 0.35:
                    for key in r.get("components", [r["effect"]]):
                        apply(p if EFFECTS[key]["target"] == "self" else e, key, g["log"], p, rng)
        elif action == "cast":
            p["mana"] -= cost(r)
            log(g, f"You invoke {r['name']}.")
            multiplier = max(1, total(p, "fusion_multiplier")) if r["effect"] == "fusion" else 1
            hit(
                p,
                e,
                (6 + p["level"] * 2) * multiplier,
                g["log"],
                rng,
                magical=True,
                element=r.get("element"),
            )
            for key in r.get("components", [r["effect"]]):
                apply(p if EFFECTS[key]["target"] == "self" else e, key, g["log"], p, rng)
            synergies(g)
        elif action == "guard":
            guarding = True
            p["mana"] = min(p["max_mana"], p["mana"] + 10)
            log(g, "You brace for impact. +10 mana; incoming damage halved.")
        elif action == "potion":
            g["potions"] -= 1
            log(g, f"Restored {round(heal(p,p['max_hp']*.5))} HP.")
        elif action == "drink":
            alchemy.drink(g, potion_id, rng)
        elif action == "cleanse":
            g["cleanses"] -= 1
            removed = cure(p, "cleanse")
            log(g, f"Cleansed {len(removed)} afflictions.")
        elif action == "flee":
            log(g, "You escape into the mist.")
            g["enemy"] = None
            expire(p, ps)
            return
    # Newly applied control effects must affect this response, without ticking twice.
    controlled = any(
        EFFECTS[k].get("stunned") or EFFECTS[k].get("frozen") or EFFECTS[k].get("sleeping")
        for k in set(e["status"]) - es
    )
    if e["hp"] > 0 and p["hp"] > 0 and enemy_can_act and not controlled:
        if e["boss"]:
            phase = min(3, 1 + int((1 - e["hp"] / e["max_hp"]) * 3))
            if phase > e["phase"]:
                e["phase"] = phase
                log(g, f"{e['name']} enters phase {phase}!")
                signature = ("ancient_curse", "dimensional_rift", "reality_warp", "infinity_loop")[
                    g["region"] % 4
                ]
                apply(p, signature, g["log"], e, rng)
        power = stat(e, "atk") * (1 + 0.15 * (e.get("phase", 1) - 1))
        if stat(p, "speed") > stat(e, "speed") * 1.5:
            power *= 0.8
        hit(e, p, power * (0.5 if guarding else 1), g["log"], rng)
        if rng.random() < 0.25:
            apply(p, e["effect"], g["log"], e, rng)
    p["mana"] = min(p["max_mana"], p["mana"] + 2)
    expire(p, ps)
    expire(e, es)
    finish(g, rng)


def finish(g, rng=random):
    p, e = g["player"], g["enemy"]
    if p["hp"] <= 0:
        log(g, "Your soul fractures. Return to the sanctuary to recover; your runes remain yours.")
        g["enemy"] = None
        return
    if e and e["hp"] <= 0:
        boss = e.get("boss", False)
        g["kills"] += 1
        reward = (30 if boss else 12) + g["region"] * 4
        xp_reward = (65 + 20 * g["region"]) if boss else (25 + 12 * g["region"])
        p["gold"] += reward
        p["xp"] += xp_reward
        g["shards"] += 3 if boss else 1
        ingredient = rng.choice(alchemy.REGION_INGREDIENTS[REGIONS[g["region"]]])
        g["ingredients"][ingredient] = g["ingredients"].get(ingredient, 0) + 1
        log(g, f"Found ingredient: {ingredient}.")
        log(
            g,
            f"{e['name']} falls. +{reward} gold, +{xp_reward} XP, +{'3' if boss else '1'} soul shards.",
        )
        drop = rune(rng.choice(list(CATALOG)))
        g["runes"].append(drop)
        log(g, f"Discovered: {drop['name']}.")
        if (
            boss
            and e["name"] == REGION_BOSSES[REGIONS[g["region"]]]["name"]
            and g["region"] not in g["bosses"]
        ):
            g["bosses"].append(g["region"])
            g["unlocked"] = min(len(REGIONS) - 1, max(g["unlocked"], g["region"] + 1))
            g["cleanses"] += 1
            g["potions"] += 1
            if chapter_one_complete(g):
                g["victory"] = True
                log(
                    g,
                    "CHAPTER 1 COMPLETE — The Dreaming God has fallen. You unlocked every main region and beat the original game. CHAPTER 2: After the Dream begins. Your postgame journey continues; the Creator is not required for this victory.",
                )
            else:
                log(g, "A seal breaks. A new region opens on the world map.")
        while p["xp"] >= p["level"] * 60:
            p["xp"] -= p["level"] * 60
            p["level"] += 1
            p["max_hp"] += 12
            p["max_mana"] += 3
            p["atk"] += 3
            p["def"] += 1
            p["hp"] = p["max_hp"]
            p["mana"] = p["max_mana"]
            log(g, f"Soul awakened: level {p['level']}. Vitality and mana restored.")
        g["enemy"] = None


def _combat_action(g, action, body, rng):
    if action == "drink" and (not g["enemy"]):
        alchemy.drink(g, body.get("potion_id"), rng)
        return True
    elif action in ("attack", "cast", "guard", "potion", "cleanse", "flee", "drink"):
        combat(g, action, body.get("rune_id"), rng, body.get("potion_id"))
        return True
    return False


# ============================================================================
# RUNES, FUSIONS & BINDINGS
# ============================================================================


def rune(name):
    result = deepcopy(CATALOG[name])
    result["id"] = uuid.uuid4().hex
    return result


def fuse(runes):
    if len(runes) < 2 or len(runes) > 3:
        raise ValueError("Choose two runes, or three for a named recipe.")
    if len({r["id"] for r in runes}) != len(runes):
        raise ValueError("Select distinct inventory copies. Duplicate rune types need two copies.")
    recipe = RECIPES.get(frozenset(r["name"] for r in runes))
    if len(runes) == 3 and recipe is None:
        raise ValueError("Three-rune fusions require a named recipe.")
    if sum(len(r["name"]) for r in runes) > 4500:
        raise ValueError("This fusion name is too long. Choose simpler runes.")
    components = list(dict.fromkeys(c for r in runes for c in r.get("components", [r["effect"]])))
    return dict(
        id=uuid.uuid4().hex,
        name=(
            recipe["name"]
            if recipe
            else " + ".join(r["name"].removesuffix(" Rune") for r in runes) + " Rune"
        ),
        effect="fusion",
        components=list(dict.fromkeys(components + (recipe["components"] if recipe else []))),
        element="fusion",
        special_effect=recipe["effect"] if recipe else None,
    )


def cost(r):
    return min(25, 5 + 2 * len(r.get("components", [r["effect"]])))


def _runes_action(g, action, body, rng):
    if action == "fuse":
        if g["enemy"]:
            raise ValueError("The fusion altar is unavailable during battle.")
        ids = body.get("ids", [])
        if not isinstance(ids, list) or len(ids) != len(set(ids)):
            raise ValueError("Select distinct runes.")
        selected = [r for r in g["runes"] if r["id"] in ids]
        if len(selected) != len(ids):
            raise ValueError("A selected rune is missing.")
        result = fuse(selected)
        if g["shards"] < 1:
            raise ValueError("Fusion requires one soul shard. Win an encounter to earn one.")
        g["shards"] -= 1
        g["runes"] = [r for r in g["runes"] if r["id"] not in ids] + [result]
        g["equipped"] = [i for i in g["equipped"] if i not in ids]
        if result["name"] not in g["discoveries"]:
            g["discoveries"].append(result["name"])
        log(g, f"Fusion complete: {result['name']}. The original runes were consumed.")
        return True
    elif action == "equip":
        if g["enemy"]:
            raise ValueError("Change bindings outside battle.")
        rid = body.get("rune_id")
        if not any((r["id"] == rid for r in g["runes"])):
            raise ValueError("Rune not owned.")
        if rid in g["equipped"]:
            g["equipped"].remove(rid)
        elif len(g["equipped"]) < 2:
            g["equipped"].append(rid)
        else:
            raise ValueError("Two bindings maximum. Unbind a rune first.")
        return True
    return False


# ============================================================================
# INGREDIENTS & ALCHEMY
# ============================================================================


def _alchemy_action(g, action, body, rng):
    if action in ("gather", "brew", "buy_alchemy", "bottle_draught"):
        if g["enemy"]:
            raise ValueError("Finish the battle before gathering, brewing, or shopping.")
        if g["player"]["hp"] <= 0:
            raise ValueError("Rest at the sanctuary first.")
        if action == "bottle_draught":
            if g["potions"] < 1:
                raise ValueError("No field draughts left to move to the shelf.")
            g["potions"] -= 1
            g["brews"].append(
                alchemy.potion("Healing Draught", dict(heal=round(g["player"]["max_hp"] * 0.5)))
            )
            log(g, "Moved a healing draught to your mixing shelf. You can drink or blend it there.")
        elif action == "gather":
            alchemy.forage(g, rng)
        elif action == "brew":
            alchemy.experiment(g, body.get("ingredients", []), body.get("potion_ids", []))
        else:
            alchemy.buy(g, body.get("item"))
        return True
    return False


# ============================================================================
# VILLAGE, SHOPS & CRAFTING
# ============================================================================


def _village_action(g, action, body, rng):
    if action == "craft":
        village.craft(g, body, fuse)
        return True
    elif action == "buy":
        if g["enemy"]:
            raise ValueError("Visit the sanctuary outside battle.")
        what = body.get("item")
        prices = {"potion": 15, "cleanse": 20, "rune": 35}
        if what not in prices:
            raise ValueError("Unknown item.")
        if g["player"]["gold"] < prices[what]:
            raise ValueError("Not enough gold.")
        g["player"]["gold"] -= prices[what]
        if what == "rune":
            r = rune(rng.choice(list(CATALOG)))
            g["runes"].append(r)
            log(g, f"The runesmith reveals {r['name']}.")
        else:
            g["potions" if what == "potion" else "cleanses"] += 1
            log(g, f"Purchased {('healing draught' if what == 'potion' else 'cleansing salts')}.")
        return True
    return False


# ============================================================================
# TUTORIAL & ACTION DISPATCH
# ============================================================================


def _interface_action(g, action, body, rng):
    if action == "tutorial":
        step = body.get("step")
        if type(step) is not int or not 0 <= step <= 7:
            raise ValueError("Choose a tutorial step.")
        g["tutorial"] = step
        return True
    return False


def act(g, action, body=None, rng=random):
    """Dispatch actions to the system that owns their rules."""
    body = body or {}
    handlers = (
        _exploration_action,
        _combat_action,
        _runes_action,
        _alchemy_action,
        _village_action,
        _interface_action,
    )
    if not any(handler(g, action, body, rng) for handler in handlers):
        raise ValueError("Unknown action.")
    g["log"] = g["log"][-100:]
    return g


# ============================================================================
# CATALOG & SAVE VALIDATION
# ============================================================================


def catalog():
    return dict(
        story=STORY_QUESTS,
        structures=village.catalog(),
        villages={
            region: next(
                (s["name"] for s in buildings if s["type"] == "village"), region + " Village"
            )
            for region, buildings in REGION_STRUCTURES.items()
        },
        alchemy=alchemy.catalog(),
        runes=list(CATALOG.values()),
        effects=EFFECTS,
        regions=REGIONS,
        recipes=[dict(inputs=sorted(inputs), **recipe) for inputs, recipe in RECIPES.items()],
        pair_count=len(CATALOG) * (len(CATALOG) + 1) // 2,
    )


def validate_save(value):
    """Only restore the exact browser-save schema; never execute uploaded code."""
    if not isinstance(value, dict) or value.get("version") not in (1, 2):
        raise ValueError(
            "Use a Soules browser-edition save (version 1 or 2). The malformed legacy save is preserved under legacy/."
        )
    value = deepcopy(value)
    if value["version"] == 1:
        value.update(version=2, **alchemy.starter(), tutorial=0)
    reference = new_game()
    if set(value) != set(reference):
        raise ValueError("Incomplete save file.")
    alchemy.validate(value)
    if type(value["tutorial"]) is not int or not 0 <= value["tutorial"] <= 7:
        raise ValueError("Invalid tutorial progress.")
    p = value.get("player")
    if not isinstance(p, dict) or set(p) != set(reference["player"]):
        raise ValueError("Invalid character.")
    import math

    for key in ("hp", "max_hp", "mana", "max_mana", "atk", "def", "speed", "level", "xp", "gold"):
        n = p.get(key)
        if type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n <= 1e7:
            raise ValueError("Invalid character statistics.")
    if type(p.get("is_night")) is not bool:
        raise ValueError("Invalid day cycle.")
    if (
        p["max_hp"] < 1
        or p["max_mana"] < 1
        or p["level"] < 1
        or p["hp"] > p["max_hp"]
        or p["mana"] > p["max_mana"]
    ):
        raise ValueError("Invalid character limits.")
    if (
        not isinstance(p["name"], str)
        or len(p["name"]) > 24
        or p["cls"] not in ("Runekeeper", "Warden", "Reaver")
    ):
        raise ValueError("Invalid character identity.")
    for key in ("region", "unlocked", "kills", "turn", "shards", "potions", "cleanses"):
        if type(value[key]) is not int or not 0 <= value[key] <= 1000000:
            raise ValueError("Invalid progression.")
    if not 0 <= value["region"] <= value["unlocked"] < len(REGIONS):
        raise ValueError("Invalid region.")
    if type(value["victory"]) is not bool:
        raise ValueError("Invalid ending state.")
    if not isinstance(value["bosses"], list) or any(
        type(i) is not int or not 0 <= i < len(REGIONS) for i in value["bosses"]
    ):
        raise ValueError("Invalid seals.")
    if not isinstance(value["runes"], list) or not 1 <= len(value["runes"]) <= 10000:
        raise ValueError("Invalid rune inventory.")
    ids = []
    for r in value["runes"]:
        if (
            not isinstance(r, dict)
            or not isinstance(r.get("id"), str)
            or not isinstance(r.get("name"), str)
            or len(r["name"]) > 5000
        ):
            raise ValueError("Invalid rune.")
        ids.append(r["id"])
        if r.get("kind") is not None and (
            r["kind"] != "staff"
            or r.get("effect") != "fusion"
            or not isinstance(r.get("components"), list)
        ):
            raise ValueError("Invalid crafted staff.")
        components = r.get("components", [r.get("effect")])
        if (
            not isinstance(components, list)
            or not components
            or any(k not in EFFECTS for k in components)
        ):
            raise ValueError("Unknown rune effect.")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate rune identities.")
    if (
        not isinstance(value["equipped"], list)
        or len(value["equipped"]) > 2
        or any(i not in ids for i in value["equipped"])
    ):
        raise ValueError("Invalid bindings.")
    for key in ("log", "discoveries"):
        if (
            not isinstance(value[key], list)
            or len(value[key]) > 10000
            or any(not isinstance(x, str) or len(x) > 10000 for x in value[key])
        ):
            raise ValueError("Invalid journal.")

    def statuses(entity):
        s = entity.get("status")
        if not isinstance(s, dict) or any(
            k not in EFFECTS
            or type(v) not in (int, float)
            or not math.isfinite(v)
            or not 0 < v <= 100
            for k, v in s.items()
        ):
            raise ValueError("Invalid status effects.")

    statuses(p)
    e = value["enemy"]
    if e is not None:
        if not isinstance(e, dict):
            raise ValueError("Invalid encounter.")
        for key in ("hp", "max_hp", "atk", "def", "speed", "mana", "max_mana", "phase"):
            n = e.get(key)
            if type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n <= 1e7:
                raise ValueError("Invalid enemy statistics.")
        if (
            e["max_hp"] < 1
            or e.get("effect") not in EFFECTS
            or type(e.get("boss")) is not bool
            or not isinstance(e.get("name"), str)
        ):
            raise ValueError("Invalid enemy.")
        statuses(e)
    value["victory"] = chapter_one_complete(value)
    return deepcopy(value)
