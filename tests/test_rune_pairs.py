import unittest
from unittest.mock import patch
from copy import deepcopy
from rune_pairs import BASE, PAIR_COUNT, all_pairs, fusion
from effects import EFFECTS
import original_magic as magic
import original_game as game


def actor(name):
    return dict(
        name=name,
        hp=1000000,
        max_hp=1000000,
        atk=20,
        **{"def": 10},
        speed=10,
        mana=10,
        status={},
        active_buffs={},
        staffs=[],
        weapon={"atk": 5}
    )


class RunePairTests(unittest.TestCase):
    def test_every_pair_has_valid_component_and_distinct_synergy(self):
        ids = set()
        count = 0
        with patch("builtins.print"):
            for rune in all_pairs():
                ids.add(rune["pair_ability"])
                count += 1
                user = actor("Tester")
                enemy = actor("Target")
                magic.apply(rune, user, enemy)
                self.assertIn(
                    rune["pair_ability"], user.get("rune_status", {}) | enemy.get("rune_status", {})
                )
                magic.turn(user, enemy)
                magic.turn(enemy, user)
        self.assertEqual(count, 8778)
        self.assertEqual(count, PAIR_COUNT)
        self.assertEqual(len(ids), count)

    def test_every_normal_rune_has_executable_abilities(self):
        with patch("builtins.print"):
            for rune in BASE.values():
                user = actor("Tester")
                enemy = actor("Target")
                magic.apply(rune, user, enemy)
                self.assertTrue(user.get("rune_status") or enemy.get("rune_status"))
                magic.turn(user, enemy)
                magic.turn(enemy, user)

    def test_rage_modifies_attack_and_defence_and_expires(self):
        user = actor("Tester")
        enemy = actor("Target")
        before = magic.damage(user, enemy, 20)
        with patch("builtins.print"):
            magic.apply({"effect": "berserk"}, user, enemy)
        self.assertGreater(magic.damage(user, enemy, 20), before)
        self.assertGreater(magic.damage(enemy, user, 20), 20)
        with patch("builtins.print"):
            for _ in range(4):
                magic.turn(user, enemy)
        self.assertNotIn("berserk", user["rune_status"])

    def test_same_type_supported_and_fusions_not_ingredients(self):
        a = next(iter(BASE.values()))
        result = fusion(a, a)
        self.assertEqual(result["inputs"], [a["name"], a["name"]])
        with self.assertRaises(ValueError):
            fusion(result, a)

    def test_saved_pair_effect_rebuilds_its_registry(self):
        a, b = list(BASE.values())[:2]
        rune = fusion(a, b)
        user = actor("Tester")
        enemy = actor("Target")
        with patch("builtins.print"):
            magic.apply(rune, user, enemy)
        owner = user if rune["ability"]["target"] == "self" else enemy
        EFFECTS.pop(rune["pair_ability"])
        restored = deepcopy(owner)
        magic.proxy(restored)
        self.assertIn(rune["pair_ability"], EFFECTS)
        self.assertIn(rune["pair_ability"], restored["rune_status"])

    def test_rejected_fusion_does_not_consume_inventory(self):
        old = game.player
        user = actor("Tester")
        a = next(iter(BASE.values()))
        user["runes"] = [fusion(a, a), deepcopy(a)]
        game.player = user
        try:
            before = deepcopy(user["runes"])
            with patch("builtins.input", side_effect=["0", "1"]), patch("builtins.print"):
                game.merge_runes()
            self.assertEqual(user["runes"], before)
        finally:
            game.player = old
