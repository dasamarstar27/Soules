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
        self.assertEqual(sorted(n for g in GROUPS for n, _ in g["options"]), list(range(1, 49)))

    def test_wander_encounters_day_night_and_level_ten(self):
        from copy import deepcopy

        for count, level in [(0, 1), (7, 1), (0, 10), (7, 11)]:
            self.p["wander_count"] = count
            self.p["level"] = level
            with patch.object(game.random, "random", return_value=0.99), patch.object(
                game.random, "randint", return_value=80
            ), patch.object(game, "fight") as fight, patch("builtins.print"):
                game.explore()
                fight.assert_called_once()
                enemy = fight.call_args.args[0]
                self.assertGreater(enemy["hp"], 0)

    def test_merchant_and_quiet_roll_do_not_start_fights(self):
        for roll in [5, 15]:
            with patch.object(game.random, "random", return_value=0.99), patch.object(
                game.random, "randint", return_value=roll
            ), patch.object(game, "fight") as fight, patch.object(
                game, "merchant"
            ) as merchant, patch(
                "builtins.print"
            ):
                game.explore()
                fight.assert_not_called()
                self.assertEqual(merchant.call_count, int(roll == 5))

    def test_death_ends_run_without_restoring_character(self):
        import original_ui as ui

        def lethal_action(choice):
            self.p["hp"] = 0
            return True

        with patch.object(game, "load_game"), patch.object(
            game, "perform_original_action", side_effect=lethal_action
        ), patch("builtins.input", return_value="1"), patch("builtins.print"):
            with self.assertRaises(ui.RunEnded):
                game.game()
        self.assertEqual(self.p["hp"], 0)

    def test_dead_worker_exits_without_another_prompt(self):
        import original_ui as ui

        ui.init_ui(self.p)
        self.p["hp"] = 0
        saved = ui.snapshot()
        session = OriginalSession({"save": saved})
        try:
            state = session.poll(0)
            self.assertEqual(state["snapshot"]["phase"], "dead")
            self.assertFalse(state["waiting"])
            self.assertEqual(state["snapshot"]["player"]["hp"], 0)
        finally:
            session.close()

    def test_numbered_category_then_secondary_action(self):
        session = OriginalSession({"name": "Menus", "cls": "warrior"})
        try:
            self.assertEqual(session.poll(0)["prompt"], "Village > ")
            session.send("7", session.poll(0)["prompt_id"])
            state = session.poll(0)
            self.assertEqual(state["snapshot"]["phase"], "main")
            self.assertEqual(state["snapshot"]["group"], "")
            session.send("1", state["prompt_id"])
            state = session.poll(0)
            self.assertEqual(state["snapshot"]["phase"], "category")
            self.assertEqual(state["snapshot"]["group"], "explore")
            session.send("0", state["prompt_id"])
            state = session.poll(0)
            self.assertEqual(state["snapshot"]["phase"], "main")
            session.send("2", state["prompt_id"])
            state = session.poll(0)
            self.assertEqual(state["snapshot"]["group"], "inventory")
            session.send("1", state["prompt_id"])
            state = session.poll(0)
            self.assertEqual(state["snapshot"]["phase"], "action")
            self.assertIn("Rusty Sword", "".join(x["text"] for x in state["output"]))
        finally:
            session.close()

    def test_merchant_lists_price_before_selection_and_charges_it(self):
        region = self.p["region"]
        weapon = data.WEAPONS[0]
        price = weapon["atk"] * 10
        self.p["gold"] = price + 10
        with patch.dict(game.MERCHANT_ITEMS, {region: [weapon["name"]]}), patch(
            "builtins.input", side_effect=["1", "y", "0"]
        ), patch("builtins.print") as output:
            game.merchant()
        lines = [" ".join(str(arg) for arg in call.args) for call in output.call_args_list]
        self.assertTrue(any(f"1. {weapon['name']} — {price} souls" in line for line in lines))
        self.assertEqual(self.p["gold"], 10)
        self.assertEqual(self.p["weapons"][-1]["name"], weapon["name"])

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
        self.assertEqual(self.p["unlocked_regions"], set(data.REGIONS + [data.SECRET_REGION]))
        self.assertTrue(all(isinstance(x, dict) for x in self.p["inventory"]))
        sizes = {k: len(v) for k, v in self.p.items() if isinstance(v, list)}
        with patch.object(builtins, "print"):
            grant_collectibles(self.p)
        self.assertEqual(sizes, {k: len(v) for k, v in self.p.items() if isinstance(v, list)})

    def test_beta_unlocks_all_structures_and_can_be_disabled(self):
        from beta_testing import disable_beta
        from season_two import available

        with patch("builtins.print"):
            grant_collectibles(self.p)
        for region, structures in data.REGION_STRUCTURES.items():
            self.assertTrue(
                {x["name"] for x in structures}.issubset(self.p["discovered_structures"][region])
            )
        for region, village in data.ELEMENTAL_VILLAGES.items():
            self.assertIn(village["name"], self.p["discovered_structures"][region])
        self.assertTrue(available(self.p))
        gold = self.p["gold"]
        weapons = deepcopy(self.p["weapons"])
        with patch("builtins.print"):
            disable_beta(self.p)
        self.assertFalse(available(self.p))
        self.assertEqual(self.p["gold"], gold)
        self.assertEqual(self.p["weapons"], weapons)
        self.assertEqual(self.p["chapter"], 1)

    def test_hidden_off_code_in_main_menu(self):
        session = OriginalSession({"name": "Codes", "cls": "warrior"})
        try:
            session.send("7", session.poll(0)["prompt_id"])
            session.send("DAMAR", session.poll(0)["prompt_id"])
            state = session.poll(0)
            self.assertTrue(state["snapshot"]["player"]["beta_mode"])
            session.send("SAMAR", state["prompt_id"])
            state = session.poll(0)
            self.assertFalse(state["snapshot"]["player"]["beta_mode"])
            self.assertEqual(
                len(state["snapshot"]["player"]["unlocked_regions"]), len(data.REGIONS) + 1
            )
        finally:
            session.close()

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
            speed=1,
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
            session.send("7", session.poll(0)["prompt_id"])
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
