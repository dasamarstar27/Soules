"""Batch costs, finite supplies, duplicate ingredients and alchemy progression."""

from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import validate_original_save
from village_life import profile
import bulk_brewing as bulk


class BulkBrewingTests(TestCase):
    def setUp(self):
        self.previous = game.player, ui._ui, ui.village
        self.p = game.player = initial_player({})
        ui.init_ui(self.p)
        ui.village = profile("Whispering Woods", "Old Village")
        self.p["ingredients"] = ["Dew Blossom"] * 4 + ["Thorn Petal"] * 4

    def tearDown(self):
        game.player, ui._ui, ui.village = self.previous

    def test_batch_consumes_pairs_bottles_and_awards_each_craft(self):
        with patch.object(game.random, "random", return_value=0.99), patch.object(
            game, "update_challenge_progress"
        ) as progress, patch("source_story.craft_xp") as xp, patch("builtins.print"):
            ok, text = bulk.brew(game, "Dew Blossom", "Thorn Petal", 3)
        self.assertTrue(ok)
        self.assertIn("3 Forest Salve", text)
        self.assertEqual(self.p["potions"], ["Forest Salve"] * 3)
        self.assertEqual(sorted(self.p["ingredients"]), ["Dew Blossom", "Thorn Petal"])
        self.assertEqual(progress.call_count, 3)
        self.assertEqual(xp.call_count, 3)
        self.assertIn("Forest Salve", self.p["expansion"]["food"]["discovered"])
        self.assertEqual(
            validate_original_save(ui.snapshot())["player"]["potions"],
            self.p["potions"],
        )

    def test_quality_preserves_only_second_ingredient_per_potion(self):
        with patch.object(game.random, "random", return_value=0), patch(
            "builtins.print"
        ):
            self.assertTrue(bulk.brew(game, "Dew Blossom", "Thorn Petal", 4)[0])
        self.assertEqual(self.p["ingredients"], ["Thorn Petal"] * 4)
        self.assertEqual(len(self.p["potions"]), 4)

    def test_same_ingredient_needs_two_copies(self):
        self.p["ingredients"] = ["Dew Blossom"] * 5
        self.assertEqual(bulk.capacity(self.p, "Dew Blossom", "Dew Blossom"), 2)
        recipe = {"name": "Test Salve", "effect": "heal", "desc": "test"}
        with patch("bulk_brewing.brew_recipe", return_value=recipe), patch.object(
            game.random, "random", return_value=0.99
        ), patch("builtins.print"):
            self.assertTrue(bulk.brew(game, "Dew Blossom", "Dew Blossom", 2)[0])
        self.assertEqual(self.p["ingredients"], ["Dew Blossom"])

    def test_invalid_or_excess_quantity_never_spends_ingredients(self):
        for qty in (0, -1, 5, True, 1.5, "2"):
            with self.subTest(qty=qty):
                before = deepcopy(self.p["ingredients"])
                self.assertFalse(bulk.brew(game, "Dew Blossom", "Thorn Petal", qty)[0])
                self.assertEqual(self.p["ingredients"], before)
                self.assertEqual(self.p["potions"], [])

    def test_unknown_or_missing_lab_does_not_spend(self):
        self.p["ingredients"] += ["Vine Root"] * 4
        before = deepcopy(self.p["ingredients"])
        self.assertFalse(bulk.brew(game, "Vine Root", "Thorn Petal", 2)[0])
        self.assertEqual(self.p["ingredients"], before)
        ui.village = profile("Crimson Depths", "Smiths' Quarter")
        with patch("builtins.print"):
            self.assertFalse(bulk.brew(game, "Dew Blossom", "Thorn Petal", 2)[0])
        self.assertEqual(self.p["ingredients"], before)

    def test_cancel_confirmation_does_not_spend(self):
        before = deepcopy(self.p["ingredients"])
        with patch("builtins.input", side_effect=["0", "1", "3", "n"]), patch(
            "builtins.print"
        ):
            bulk.menu(game)
        self.assertEqual(self.p["ingredients"], before)
        self.assertEqual(self.p["potions"], [])

    def test_batch_limit_and_remaining_supplies(self):
        self.p["ingredients"] = ["Dew Blossom"] * 1500 + ["Thorn Petal"] * 1200
        self.assertEqual(
            bulk.capacity(self.p, "Dew Blossom", "Thorn Petal"), bulk.MAX_BATCH
        )
        self.p["ingredients"] = ["Dew Blossom"] * 3 + ["Thorn Petal"]
        self.assertEqual(bulk.capacity(self.p, "Dew Blossom", "Thorn Petal"), 1)
