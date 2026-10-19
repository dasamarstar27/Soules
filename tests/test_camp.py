"""Camp options preserve rewards, level up normally and report their results."""

import ast
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import original_game as game
from original_worker import initial_player


class CampTests(TestCase):
    def setUp(self):
        self.previous = game.player
        game.player = initial_player({"name": "Camp tester"})
        self.p = game.player
        self.camp = {"name": "Bandit Camp", "type": "camp"}

    def tearDown(self):
        game.player = self.previous

    def call(self, *answers):
        with patch("builtins.input", side_effect=answers), patch(
            "builtins.print"
        ) as output:
            game.visit_camp(self.camp, self.p["region"])
        return "\n".join(str(call) for call in output.call_args_list)

    def test_trade_stories_awards_xp_once_and_records_challenge_progress(self):
        with patch.object(game.random, "randint", return_value=20), patch.object(
            game, "update_challenge_progress", wraps=game.update_challenge_progress
        ) as challenge:
            text = self.call("2")
        self.assertEqual(self.p["xp"], 20)
        self.assertEqual(self.p["level"], 1)
        challenge.assert_any_call("xp_gain", 20)
        self.assertIn("+20 XP", text)
        self.assertIn("grizzled wanderer", text)

    def test_story_xp_crossing_threshold_levels_up_without_crashing(self):
        self.p["xp"] = 45
        old_hp = self.p["max_hp"]
        with patch.object(game.random, "randint", return_value=20):
            self.call("2")
        self.assertEqual(self.p["level"], 2)
        self.assertEqual(self.p["max_hp"], old_hp + 5)
        self.assertEqual(self.p["hp"], self.p["max_hp"])
        self.assertEqual(self.p["skill_points"], 1)

    def test_rest_caps_stats_and_reports_actual_recovery(self):
        self.p.update(hp=self.p["max_hp"] - 3, hunger=95)
        text = self.call("1")
        self.assertEqual(self.p["hp"], self.p["max_hp"])
        self.assertEqual(self.p["hunger"], 100)
        self.assertIn("+3 HP, +5 hunger", text)

    def test_ingredient_trade_consumes_one_pays_once_and_shows_result(self):
        self.p["ingredients"] = ["Thorn Petal", "Vine Root"]
        gold = self.p["gold"]
        with patch.object(game.random, "randint", return_value=25), patch.object(
            game.random, "choice", side_effect=lambda values: values[0]
        ):
            text = self.call("3")
        self.assertEqual(self.p["ingredients"], ["Vine Root"])
        self.assertEqual(self.p["gold"], gold + 25)
        self.assertIn("Thorn Petal", text)
        self.assertIn("25 souls", text)

    def test_empty_trade_costs_nothing_and_invalid_answer_reprompts(self):
        gold = self.p["gold"]
        text = self.call("wrong", "3")
        self.assertIn("Choose 1 Rest", text)
        self.assertIn("no ingredients", text)
        self.assertEqual(self.p["gold"], gold)

    def test_leaving_preserves_existing_fallen_tree_reward(self):
        before = len(self.p["woods"])
        text = self.call("4")
        self.assertEqual(len(self.p["woods"]), before + 1)
        self.assertIn("leave the camp", text)

    def test_only_one_live_camp_definition(self):
        tree = ast.parse(Path(game.__file__).read_text())
        self.assertEqual(
            sum(
                isinstance(node, ast.FunctionDef) and node.name == "visit_camp"
                for node in tree.body
            ),
            1,
        )
