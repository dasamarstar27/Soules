"""Difficulty preserves standard balance and saves while easing all encounter types."""

from copy import deepcopy
import unittest
from unittest.mock import patch
from difficulty import easy_enemy, incoming_strike, validate
from original_worker import initial_player
from original_sessions import validate_original_save


class DifficultyTests(unittest.TestCase):
    def test_normal_and_old_characters_keep_starting_stats_and_items(self):
        standard = initial_player({"name": "Test", "cls": "warrior"})
        explicit = initial_player(
            {"name": "Test", "cls": "warrior", "difficulty": "normal"}
        )
        easy = initial_player({"name": "Test", "cls": "warrior", "difficulty": "easy"})
        for player in (standard, explicit, easy):
            player["expansion"].pop("character_id", None)
        self.assertEqual(standard, explicit)
        self.assertEqual(standard["difficulty"], "normal")
        easy["difficulty"] = "normal"
        self.assertEqual(standard, easy)
        self.assertEqual(len(easy["weapons"]), 1)
        self.assertEqual(easy["runes"], [])

    def test_enemy_scaling_leaves_templates_rewards_and_normal_untouched(self):
        from expansion_hooks import scale_enemy

        enemy = dict(
            name="Boss", hp=80, max_hp=100, atk=20, xp=30, gold=12, status={"burn": 2}
        )
        before = deepcopy(enemy)
        self.assertIs(easy_enemy({}, enemy), enemy)
        easy = scale_enemy(initial_player({"difficulty": "easy"}), enemy)
        self.assertEqual((easy["hp"], easy["max_hp"]), (60, 75))
        for key in ("atk", "xp", "gold", "status"):
            self.assertEqual(easy[key], enemy[key])
        easy["status"]["burn"] = 0
        self.assertEqual(enemy, before)
        self.assertEqual(easy_enemy({"difficulty": "easy"}, dict(hp=1))["hp"], 1)

    def test_direct_strikes_are_reduced_once_without_boosting_player_damage(self):
        from original_magic import strike

        base = dict(
            name="Hero", hp=100, max_hp=100, atk=10, def_=0, region="Whispering Woods"
        )
        enemy = dict(name="Monster", hp=100, max_hp=100, atk=10)
        with patch("builtins.print"):
            standard = deepcopy(base)
            self.assertEqual(strike(deepcopy(enemy), standard, 20), 20)
            easy = dict(base, difficulty="easy")
            self.assertEqual(strike(deepcopy(enemy), easy, 20), 12)
            self.assertEqual(easy["hp"], 88)
            target = deepcopy(enemy)
            self.assertEqual(strike(easy, target, 20), 20)
        self.assertEqual(incoming_strike({"difficulty": "easy"}, 1), 1)
        self.assertEqual(incoming_strike({"difficulty": "easy"}, 0), 0)
        self.assertEqual(incoming_strike({}, 20), 20)

    def test_tactical_enemies_use_easy_health_and_keep_original_templates(self):
        import expansion_combat

        class Game:
            pass

        game = Game()
        game.player = initial_player({"difficulty": "easy"})
        enemies = [dict(name="Raider", hp=80, atk=10)]
        with patch("builtins.input", return_value="0"), patch("builtins.print") as out:
            self.assertFalse(expansion_combat.encounter(game, enemies))
        self.assertTrue(any("HP 60/60" in str(call) for call in out.call_args_list))
        self.assertEqual(enemies[0]["hp"], 80)

    def test_save_roundtrip_and_legacy_default(self):
        p = initial_player({"difficulty": "easy"})
        p["unlocked_regions"] = list(p["unlocked_regions"])
        save = dict(format="soules-original-v1", player=p)
        valid = validate_original_save(save)
        self.assertEqual(
            initial_player({"save": valid, "difficulty": "normal"})["difficulty"],
            "easy",
        )
        p.pop("difficulty")
        self.assertEqual(
            initial_player({"save": validate_original_save(save)})["difficulty"],
            "normal",
        )
        for value in ("hard", "EZ", None, [], {}):
            p["difficulty"] = value
            with self.assertRaises(ValueError):
                validate_original_save(save)
            with self.assertRaises(ValueError):
                validate(value)

    def test_api_rejects_unknown_difficulty_before_creating_session(self):
        from app import app

        with app.test_client() as client:
            for value in ("hard", [], None):
                response = client.post(
                    "/api/original/start", json={"difficulty": value}
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("Easy or Normal", response.json["error"])

    def test_fresh_prestige_and_ngplus_keep_easy_choice(self):
        import original_game as game
        import original_ui as ui
        from legacy_workshops import ascend
        from legacy_systems import menu

        previous = game.player, ui._ui, ui.village, ui.location
        try:
            for kind in ("prestige", "ngplus"):
                with self.subTest(kind=kind):
                    game.player = initial_player({"difficulty": "easy"})
                    game.player["source_story"] = {"season_one_complete": True}
                    ui.village = None
                    ui.init_ui(game.player)
                    with patch.object(game, "visit_village"), patch(
                        "builtins.input", return_value="yes"
                    ), patch("builtins.print"):
                        if kind == "prestige":
                            self.assertTrue(ascend(game))
                        else:
                            menu(game, "ngplus")
                    self.assertEqual(game.player["difficulty"], "easy")
        finally:
            game.player, ui._ui, ui.village, ui.location = previous
