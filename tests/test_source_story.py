import unittest
from copy import deepcopy
from unittest.mock import patch
import data
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import validate_original_save
import source_story as story
import village_life as villages


class StoryTests(unittest.TestCase):
    def setUp(self):
        self.before = game.player
        self.previous_village = ui.village
        game.player = initial_player({"name": "Story tester", "cls": "warrior"})
        self.p = game.player
        ui.init_ui(self.p)
        ui.village = None

    def tearDown(self):
        game.player = self.before
        ui.village = self.previous_village

    def inputs(self, values, fn, *args):
        with patch("builtins.input", side_effect=values), patch("builtins.print"):
            return fn(*args)

    def test_opening_is_invasion_without_source_plot(self):
        with patch("builtins.print") as output:
            story.opening(self.p)
        text = " ".join(str(arg) for call in output.call_args_list for arg in call.args)
        self.assertIn("rare", text)
        self.assertIn("peacefully", text)
        self.assertIn("Dreaming God", text)
        self.assertNotIn("Core Stabiliser", text)
        self.assertNotIn("Vael", text)
        self.assertNotIn("Source", text)
        with patch("builtins.print") as output:
            story.opening(self.p)
        output.assert_not_called()

    def test_canon_history_and_clan_memories(self):
        with patch("builtins.print") as output:
            story.opening(self.p)
        text = " ".join(str(arg) for call in output.call_args_list for arg in call.args)
        for phrase in [
            "Riftlands",
            "Sacred Temple",
            "gave their lives",
            "only Ignar",
            "rift has opened again",
        ]:
            self.assertIn(phrase, text)
        with patch("builtins.print"):
            for region, clan in data.ELEMENTAL_VILLAGES.items():
                story.remember_warriors(self.p, villages.profile(region, clan["name"], True))
        self.assertEqual(
            len([c for c in story.state(self.p)["clues"] if c["id"].startswith("ancestor_")]), 4
        )
        self.assertNotIn("overarching antagonist", text)

    def test_first_victory_and_early_clue_are_invasion(self):
        with patch("builtins.print"):
            story.first_victory(self.p)
            story.first_victory(self.p)
        self.assertEqual(len(story.state(self.p)["clues"]), 1)
        self.p["wander_count"] = 3
        with patch(
            "builtins.input",
            side_effect=AssertionError("Chapter One cannot have Source anomaly prompts"),
        ), patch("builtins.print"):
            story.anomaly(game)
        self.assertTrue(all("Source" not in clue["text"] for clue in story.state(self.p)["clues"]))

    def test_starting_balance_needs_multiple_attacks(self):
        enemy = data.NORMAL_MONSTERS["Whispering Woods"][0]
        damage = game.calculate_damage(self.p, enemy)
        self.assertEqual(self.p["max_hp"], 70)
        self.assertEqual(self.p["atk"], 7)
        self.assertEqual(self.p["def"], 2)
        self.assertLess(damage, enemy["hp"] / 2)

    def test_early_ranger_and_necromancer_skills_do_not_one_shot(self):
        for key in ("ranger", "necromancer"):
            game.player = initial_player({"name": "Skill tester", "cls": key})
            enemy = deepcopy(data.NORMAL_MONSTERS["Whispering Woods"][0])
            with patch("builtins.print"):
                game._use_class_skill(data.CLASSES[key], enemy)
            self.assertGreater(enemy["hp"], 0)

    def test_existing_save_stats_are_preserved(self):
        self.p["atk"] = 42
        self.p["max_hp"] = 333
        self.p["hp"] = 222
        loaded = initial_player(
            {"save": dict(format="soules-original-v1", player=ui.clean(self.p))}
        )
        self.assertEqual((loaded["atk"], loaded["max_hp"], loaded["hp"]), (42, 333, 222))

    def test_chapter_one_keeper_does_not_unlock_postgame_witness(self):
        v = villages.profile("Whispering Woods", "Sylvar Circle", True)
        self.inputs(["1", "0"], story.talk, game, v)
        self.assertEqual(story.state(self.p)["witnesses"], [])
        self.assertIn("rare and peaceful", story.state(self.p)["clues"][0]["text"])

    def test_journal_does_not_offer_source_quest_in_chapter_one(self):
        with patch("builtins.input", return_value="0"), patch("builtins.print") as output:
            story.journal(game)
        text = " ".join(str(arg) for call in output.call_args_list for arg in call.args)
        self.assertNotIn("Source Temple", text)
        self.assertNotIn("Repair the bridge", text)

    def test_source_investigation_is_gated(self):
        self.p["chapter"] = 2
        with patch.object(game, "fight") as fight:
            self.inputs(["4", "0"], story.journal, game)
            fight.assert_not_called()

    def test_all_four_witnesses_vael_and_repairs(self):
        self.p["chapter"] = 2
        self.p["unlocked_regions"] = set(data.REGIONS)
        for region, v in data.ELEMENTAL_VILLAGES.items():
            self.inputs(
                ["1", "1", "0"], story.talk, game, villages.profile(region, v["name"], True)
            )
        self.assertEqual(len(story.state(self.p)["witnesses"]), 4)
        self.p["elemental_cores"] = [v["core"] for v in data.ELEMENTAL_VILLAGES.values()]
        self.p["atk"] = 10000
        self.p["hp"] = self.p["max_hp"] = 10000
        before_bosses = deepcopy(self.p["bosses_defeated"])
        self.inputs(["4", "y", "1", "5", "y", "0"], story.journal, game)
        self.assertTrue(story.state(self.p)["vael_defeated"])
        self.assertTrue(story.state(self.p)["complete"])
        self.assertTrue(self.p["chapter_2_complete"])
        self.assertEqual(self.p["elemental_cores"], [])
        self.assertEqual(self.p["bosses_defeated"], before_bosses)
        self.assertEqual(self.p["chapter"], 2)
        self.inputs(["5", "0"], story.journal, game)
        self.assertEqual(self.p["elemental_cores"], [])

    def test_anomaly_fragments_are_finite_per_wander_and_consumable(self):
        self.p["chapter"] = 2
        self.p["wander_count"] = 10
        self.inputs(["y"], story.anomaly, game)
        self.inputs([], story.anomaly, game)
        self.assertEqual(story.state(self.p)["fragments"], 1)
        self.p["hp"] = 1
        mana = self.p["mana"]
        self.inputs(["6", "0"], story.journal, game)
        self.assertEqual(story.state(self.p)["fragments"], 0)
        self.assertEqual(self.p["hp"], 16)
        self.assertEqual(self.p["mana"], mana + 5)

    def test_professions_cap_and_progress_persist(self):
        with patch("builtins.print"):
            for _ in range(40):
                story.craft_xp(self.p, "smithing")
        self.assertEqual(story.rank(self.p, "smithing"), 5)
        saved = validate_original_save(ui.snapshot())
        self.assertEqual(story.rank(saved["player"], "smithing"), 5)
        saved["player"]["source_story"]["fragments"] = "infinite"
        with self.assertRaises(ValueError):
            validate_original_save(saved)

    def test_rumours_do_not_discover_structures(self):
        village = villages.profile("Whispering Woods", "Old Village")
        before = deepcopy(self.p.get("discovered_structures", {}))
        with patch("builtins.print"):
            story.rumour(self.p, village)
            story.rumour(self.p, village)
        self.assertEqual(self.p.get("discovered_structures", {}), before)
        self.assertEqual(len(story.state(self.p)["rumours"]), 1)
