from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import data
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import validate_original_save
import clan_defence as defence
import village_life as villages
from expansion_state import state


class ClanDefenceTests(TestCase):
    def setUp(self):
        self.old = game.player
        self.old_ui = ui.get_ui()
        self.old_village = ui.village
        game.player = initial_player({"name": "Clan defender", "cls": "warrior"})
        self.p = game.player
        self.p["gold"] = 1000
        self.p["building_materials"] = {"Timber": 10, "Stone": 10, "Iron fittings": 0}
        self.clan = data.ELEMENTAL_VILLAGES["Whispering Woods"]
        self.profile = villages.profile("Whispering Woods", self.clan["name"], True)
        ui.init_ui(self.p)
        ui.village = None

    def tearDown(self):
        game.player = self.old
        ui.village = self.old_village
        ui._ui = self.old_ui

    def call(self, answers, method, *args):
        with patch("builtins.input", side_effect=answers) as prompt, patch(
            "builtins.print"
        ):
            result = method(*args)
        return result, prompt

    def test_history_and_season_one_purchase_both_return_to_clan_menu(self):
        gold = self.p["gold"]
        _, prompts = self.call(["5", "3", "1", "0", "4"], game.visit_elemental_village)
        self.assertEqual(
            sum(
                call.args[0] == "Elemental village > "
                for call in prompts.call_args_list
            ),
            3,
        )
        self.assertEqual(self.p["gold"], gold - 25)
        self.assertEqual(len(self.p["inventory"]), 1)
        self.assertIn(
            self.clan["name"], self.p["discovered_structures"]["Whispering Woods"]
        )
        self.assertIn(
            "ancestor_nature", {clue["id"] for clue in self.p["source_story"]["clues"]}
        )
        self.assertEqual(villages.state(self.p, self.profile)["visits"], 1)

    def test_local_services_do_not_count_a_second_arrival_or_leave_the_clan(self):
        _, prompts = self.call(["6", "7", "4"], game.visit_elemental_village)
        self.assertEqual(
            sum(
                call.args[0] == "Elemental village > "
                for call in prompts.call_args_list
            ),
            2,
        )
        self.assertEqual(villages.state(self.p, self.profile)["visits"], 1)

    def test_structures_revisits_discovered_clan_and_raid_is_available_in_season_one(
        self,
    ):
        self.p["discovered_structures"] = {"Whispering Woods": [self.clan["name"]]}
        with patch.object(game, "visit_elemental_village") as visit:
            self.call(["0"], game.visit_structures)
            visit.assert_called_once()
        with patch("community_addons.defence") as defend:
            self.call(["7", "4"], game.visit_elemental_village)
            self.assertEqual(defend.call_args.args[1]["id"], self.profile["id"])

    def test_main_quest_clan_assignments_three_waves_and_unique_report_survive_save(
        self,
    ):
        self.assertFalse(
            defence.assign(self.p, "Whispering Woods", defence.ROLES[0])[0]
        )
        self.p["discovered_structures"] = {"Whispering Woods": [self.clan["name"]]}
        self.assertTrue(defence.assign(self.p, "Whispering Woods", defence.ROLES[0])[0])
        self.call(["2", "0"], defence.menu, game)
        self.assertEqual(self.p["building_materials"]["Timber"], 8)
        self.assertEqual(self.p["building_materials"]["Stone"], 9)
        with patch("expansion_combat.encounter", return_value=True) as battle:
            for _ in range(3):
                self.assertTrue(self.call([], defence.defend_woods, game)[0])
            self.assertFalse(self.call([], defence.defend_woods, game)[0])
        self.assertEqual(battle.call_count, 3)
        self.assertEqual(len(battle.call_args_list[0].args[1]), 2)
        self.assertEqual(len(battle.call_args_list[2].args[1]), 4)
        self.assertEqual(self.p["bosses_defeated"], [])
        self.assertFalse(self.call([], defence.report, game)[0][0])
        ui.village = villages.profile("Whispering Woods", "Old Village")
        gold = self.p["gold"]
        self.assertTrue(self.call([], defence.report, game)[0][0])
        self.assertEqual(self.p["gold"], gold + 100)
        self.assertFalse(self.call([], defence.report, game)[0][0])
        self.assertEqual(self.p["gold"], gold + 100)
        self.assertTrue(
            validate_original_save(ui.snapshot())["player"]["expansion"]["activities"][
                "woods_defence"
            ]["complete"]
        )
        self.assertEqual(self.p["elemental_cores"], [])

    def test_clans_are_optional_and_wrong_region_or_postgame_does_not_spend_supplies(
        self,
    ):
        self.call(["2", "0"], defence.menu, game)
        with patch("expansion_combat.encounter", return_value=True):
            self.assertTrue(self.call([], defence.defend_woods, game)[0])
        self.assertEqual(defence.quest(self.p)["assignments"], {})
        self.p["region"] = "Sunken Coast"
        with patch("expansion_combat.encounter") as fight:
            self.assertFalse(self.call([], defence.defend_woods, game)[0])
            fight.assert_not_called()
        self.p["chapter"] = 2
        before = deepcopy(self.p["building_materials"])
        self.call([], defence.menu, game)
        self.assertEqual(before, self.p["building_materials"])

    def test_bad_volunteer_save_is_rejected(self):
        defence.quest(self.p)["assignments"] = {"unfound clan": "invalid role"}
        with self.assertRaises(ValueError):
            validate_original_save(ui.snapshot())
