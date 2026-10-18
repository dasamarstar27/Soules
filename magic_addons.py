"""Rune research, provenance, counterspells and environmental elemental uses."""

import data
from expansion_state import state, mark, pay, choose


def record_cast(player, rune, components):
    magic = state(player)["magic"]
    used = magic.setdefault("effects_used", [])
    for effect in components:
        if effect not in used:
            used.append(effect)
    if rune.get("effect") == "fusion":
        pair = sorted(rune.get("inputs", []))
        key = " + ".join(pair)
        if key and key not in magic.setdefault("tested_fusions", []):
            magic["tested_fusions"].append(key)
        rune.setdefault("first_used_region", player["region"])
    magic["casts"] = magic.get("casts", 0) + 1


def record_fusion(player, rune):
    rune["creator"] = player["name"]
    rune["created_region"] = player["region"]
    rune["created_wander"] = player.get("wander_count", 0)
    state(player)["magic"].setdefault("made_fusions", []).append(
        dict(name=rune["name"], inputs=rune.get("inputs", []), region=player["region"])
    )


def activity(game, feature):
    p = game.player
    m = state(p)["magic"]
    if feature == 61:
        for pair in m.get("tested_fusions", []):
            print(pair)
        if not m.get("tested_fusions"):
            print("Cast a fusion in a real battle to record its tested ingredients.")
        mark(p, 61)
    elif feature == 62:
        arts = p.get("elemental_arts", [])
        if not arts:
            print("Learn an elemental art from a clan keeper first.")
            return
        from expansion_combat import practice

        if practice(game, "arcane"):
            m["practice_trials"] = m.get("practice_trials", 0) + 1
            mark(p, 62)
    elif feature == 63:
        print(
            "Dictionary rune cards now display a distinct generated rune seal for every normal type. Seals are visual identifiers; their mechanics remain in the effect descriptions."
        )
        mark(p, 63)
    elif feature == 64:
        used = m.get("effects_used", [])
        researched = m.setdefault("researched", [])
        new = [x for x in used if x not in researched]
        print(
            "Research requires three newly demonstrated effects. Recorded: "
            + ", ".join(new)
        )
        if len(new) < 3:
            return
        researched.extend(new[:3])
        p["gold"] += 70
        item = (
            next(r.copy() for r in data.RUNES if r["effect"] == new[0])
            if any(r["effect"] == new[0] for r in data.RUNES)
            else data.RUNES[0].copy()
        )
        p["runes"].append(item)
        mark(p, 64)
        print(
            "Research accepted. +70 souls and one replacement rune; those demonstrations cannot be claimed twice."
        )
    elif feature == 65:
        for rune in p.get("runes", []):
            if rune.get("effect") == "fusion":
                print(
                    rune["name"]
                    + " · "
                    + str(
                        {
                            k: rune.get(k)
                            for k in (
                                "creator",
                                "inputs",
                                "created_region",
                                "created_wander",
                                "first_used_region",
                            )
                        }
                    )
                )
        mark(p, 65)
    elif feature == 66:
        if m.get("counterspell"):
            print(
                "Counterspell learned: 5 mana to stop a telegraphed charged spell in tactical combat."
            )
            return
        if not pay(p, 50):
            print("Counterspell training costs 50 souls.")
            return
        m.update(counterspell=True, intent_training=True)
        mark(p, 66)
    elif feature == 67:
        from season_two import ARTS

        arts = [x for x in p.get("elemental_arts", []) if x in ARTS]
        index = choose("ELEMENTAL FIELD USE · 8 MANA", arts)
        if index is None:
            return
        if p.get("mana", 0) < 8:
            print("Need eight mana.")
            return
        p["mana"] -= 8
        from expedition import field

        element = ARTS[arts[index]]["element"]
        field(p).setdefault("crossings", {})[p["region"]] = True
        m["terrain_ward"] = True
        mark(p, 67)
        print(
            element.title()
            + " manipulation secured a crossing and wards tactical terrain hazards."
        )
    elif feature == 68:
        print(
            "Customise → Rune sounds controls optional effect tones and volume. It starts muted."
        )
        mark(p, 68)
    elif feature == 69:
        from expansion_combat import practice

        if practice(game, "arcane"):
            mark(p, 69)
    elif feature == 70:
        if m.get("philosophy"):
            print("Your elemental philosophy: " + m["philosophy"])
            return
        index = choose(
            "ELEMENTAL PHILOSOPHY",
            [
                "Harmony: lower terrain risk",
                "Precision: +1 damage in tactical spells",
                "Restoration: regional cooking heals 2 extra HP",
            ],
        )
        if index is None:
            return
        m["philosophy"] = ["harmony", "precision", "restoration"][index]
        if index == 0:
            m["terrain_ward"] = True
        mark(p, 70)
        print("Philosophy chosen. Clan cores remain protected.")
