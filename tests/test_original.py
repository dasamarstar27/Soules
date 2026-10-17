"""Behavior checks for the original engine and its browser bridge."""

import builtins
from copy import deepcopy
import unittest
from unittest.mock import patch
import data
import original_game as game
import original_worker as worker
from original_menus import GROUPS
from original_sessions import OriginalSession, validate_original_save
from beta_testing import grant_collectibles
from season_two import village_services, use_art, GOODS


class OriginalTests(unittest.TestCase):
    def setUp(self):
        self.before = game.player
        game.player = worker.initial_player({"name": "Tester", "cls": "warrior"})
        self.p = game.player

    def tearDown(self):
        game.player = self.before

    def run_inputs(self, values, fn, *args):
        with patch.object(builtins, "input", side_effect=values), patch.object(builtins, "print"):
            return fn(*args)

    def test_all_original_actions_grouped(self):
        self.assertEqual(sorted(n for g in GROUPS for n, _ in g["options"]), list(range(1, 47)))

    def test_starter_only_rusty_sword(self):
        self.assertEqual([w["name"] for w in self.p["weapons"]], ["Rusty Sword"])
        self.assertIs(self.p["weapon"], self.p["weapons"][0])
        for key in ["runes", "armours", "potions", "staffs", "inventory"]:
            self.assertEqual(self.p[key], [])

    def test_beta_catalogs_and_no_story_skip(self):
        with patch.object(builtins, "print"):
            grant_collectibles(self.p)
        self.assertEqual(len(self.p["runes"]), len({r["name"] for r in data.RUNES}))
        self.assertEqual(set(self.p["metals"]), set(data.METALS))
        self.assertEqual(self.p["chapter"], 1)
        self.assertEqual(self.p["unlocked_regions"], {data.REGIONS[0]})
        self.assertTrue(all(isinstance(x, dict) for x in self.p["inventory"]))
        sizes = {k: len(v) for k, v in self.p.items() if isinstance(v, list)}
        with patch.object(builtins, "print"):
            grant_collectibles(self.p)
        self.assertEqual(sizes, {k: len(v) for k, v in self.p.items() if isinstance(v, list)})

    def test_weapon_binding_permanent(self):
        self.p["runes"] = deepcopy(data.RUNES[:2])
        self.run_inputs(["0", "0"], game.bind_rune_weapon)
        bound = self.p["weapon"]["rune"]
        self.run_inputs(["0"], game.bind_rune_weapon)
        self.assertIs(self.p["weapon"]["rune"], bound)
        self.assertEqual(len(self.p["runes"]), 1)

    def test_bound_rune_survives_repeated_attacks(self):
        self.p["weapon"]["rune"] = deepcopy(data.RUNES[0])
        rune = deepcopy(self.p["weapon"]["rune"])
        enemy = dict(
            name="Test Dummy",
            hp=10000,
            max_hp=10000,
            atk=1,
            **{"def": 0},
            xp=0,
            gold=0,
            status={},
            active_buffs={},
            speed=1
        )
        with patch.object(game, "apply_rune_effect") as apply:
            self.run_inputs(["1", "1", "4"], game.fight, enemy)
            self.assertEqual(apply.call_count, 2)
        self.assertEqual(self.p["weapon"]["rune"], rune)

    def test_loose_rune_consumed(self):
        self.p["runes"] = deepcopy(data.RUNES[:1])
        with patch.object(game, "apply_rune_effect") as apply:
            self.assertTrue(self.run_inputs(["0"], game.use_combat_rune, {"hp": 100}))
            apply.assert_called_once()
        self.assertEqual(self.p["runes"], [])

    def test_village_shop_library_quest(self):
        self.p["chapter"] = 2
        self.p["gold"] = 1000
        village = data.ELEMENTAL_VILLAGES[self.p["region"]]
        self.run_inputs(["1", "1", "3", "1", "4", "y", "6"], village_services, game, village)
        self.assertEqual(self.p["elemental_shop_stock"]["nature"][0], 0)
        self.assertIn("Vine Touch", self.p["elemental_arts"])
        self.assertEqual(self.p["elemental_quests"]["nature"], "accepted")
        ingredient = data.REGION_INGREDIENTS[self.p["region"]][0]
        self.p["ingredients"] = [ingredient] * 3
        self.run_inputs(["4", "y", "6"], village_services, game, village)
        gold = self.p["gold"]
        self.run_inputs(["4", "6"], village_services, game, village)
        self.assertEqual(self.p["gold"], gold)
        self.assertEqual(self.p["ingredients"], [])

    def test_art_costs_finite_mana(self):
        self.p["elemental_arts"] = ["Vine Touch"]
        self.p["mana"] = 8
        enemy = {"hp": 100}
        self.assertTrue(self.run_inputs(["1"], use_art, self.p, enemy))
        self.assertEqual(enemy["hp"], 88)
        self.assertEqual(self.p["mana"], 0)
        self.assertFalse(self.run_inputs(["1"], use_art, self.p, enemy))
        self.assertEqual(enemy["hp"], 88)

    def test_session_cheat_save_and_stale_input(self):
        session = OriginalSession({"name": "Bridge", "cls": "warrior"})
        try:
            state = session.poll(0)
            session.send("DAMAR", state["prompt_id"], None)
            state = session.poll(0)
            self.assertTrue(state["snapshot"]["player"]["beta_mode"])
            restored = validate_original_save(state["snapshot"])
            self.assertEqual(restored["player"]["name"], "Bridge")
            with self.assertRaises(ValueError):
                session.send("1", 0, None)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
