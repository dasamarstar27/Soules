"""Paid local facilities, farm growth and old-save compatibility."""

from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest.mock import patch
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import validate_original_save
import village_life as v
import village_projects


class FacilityConstructionTests(TestCase):
    def setUp(self):
        self.old_player, self.old_village = game.player, ui.village
        self.p = game.player = initial_player({})
        self.p.update(
            gold=10000,
            building_materials={"Timber": 200, "Stone": 200, "Iron fittings": 200},
        )
        self.place = v.profile("Whispering Woods", "Old Village")
        ui.init_ui(self.p)
        ui.village = self.place

    def tearDown(self):
        game.player, ui.village = self.old_player, self.old_village

    def test_build_missing_forge_costs_and_immediate_service(self):
        before = deepcopy(self.p["building_materials"])
        self.assertNotIn("forge", self.place["services"])
        ok, _ = v.improve_facility(self.p, self.place, "forge")
        self.assertTrue(ok)
        self.assertIn("forge", self.place["services"])
        self.assertEqual(v.building_level(self.p, self.place, "forge"), 1)
        self.assertIn(9, dict(v.village_options(self.place)))
        self.assertEqual(self.p["gold"], 9900)
        self.assertEqual(
            {k: before[k] - self.p["building_materials"][k] for k in before},
            v.FACILITY_BUILD_COST,
        )
        self.assertIn("forge", v.snapshot(self.p, self.place)["service_details"])
        self.assertEqual(self.place["smith_label"], "Apprentice")
        self.assertTrue(
            any(p["service"] == "forge" for p in village_projects.offers(self.place))
        )

    def test_upgrade_to_five_cap_and_no_second_build_charge(self):
        v.improve_facility(self.p, self.place, "forge")
        for level in range(2, 6):
            self.assertTrue(v.improve_facility(self.p, self.place, "forge")[0])
            self.assertEqual(v.building_level(self.p, self.place, "forge"), level)
        before = deepcopy(self.p)
        self.assertFalse(v.improve_facility(self.p, self.place, "forge")[0])
        self.assertEqual(self.p, before)
        self.assertEqual(v.state(self.p, self.place)["built_services"], ["forge"])

    def test_farm_build_upgrade_harvest_and_regrowth(self):
        place = v.profile("Crimson Depths", "Ember Village")
        ui.village = place
        self.assertNotIn("farm", place["services"])
        self.assertTrue(v.improve_facility(self.p, place, "farm")[0])
        self.assertIn(10, dict(v.village_options(place)))
        with redirect_stdout(StringIO()):
            v.harvest(game, place)
        count = len(self.p["ingredients"])
        self.assertEqual(count, 2)
        self.assertTrue(v.improve_facility(self.p, place, "farm")[0])
        with redirect_stdout(StringIO()):
            v.harvest(game, place)
        self.assertEqual(len(self.p["ingredients"]), count)
        self.p["wander_count"] = 20
        with redirect_stdout(StringIO()):
            v.harvest(game, place)
        self.assertEqual(len(self.p["ingredients"]) - count, 3)

    def test_all_ordinary_services_can_be_built_but_not_temple(self):
        for key in v.SERVICE_NAMES:
            if key == "temple":
                self.assertFalse(v.improve_facility(self.p, self.place, key)[0])
            elif key not in self.place["services"]:
                self.assertTrue(v.improve_facility(self.p, self.place, key)[0])
        self.assertEqual(set(self.place["services"]), set(v.SERVICE_NAMES) - {"temple"})

    def test_revisit_directory_save_restore_and_rollback(self):
        v.improve_facility(self.p, self.place, "forge")
        self.p["discovered_structures"]["Whispering Woods"] = ["Old Village"]
        fresh = v.profile("Whispering Woods", "Old Village")
        v.state(self.p, fresh)
        self.assertIn("forge", fresh["services"])
        self.assertIn("forge", v.known_villages(self.p)[0]["services"])
        restored = validate_original_save(ui.snapshot())["player"]
        loaded = v.profile("Whispering Woods", "Old Village")
        v.state(restored, loaded)
        self.assertIn("forge", loaded["services"])
        self.p["village_records"].pop(self.place["id"])
        v.state(self.p, self.place)
        self.assertNotIn("forge", self.place["services"])
        elsewhere = v.profile("Whispering Woods", "Briarwick")
        self.assertNotIn("forge", v.state(self.p, elsewhere).get("built_services", []))

    def test_insufficient_funds_cancel_budget_and_invalid_save(self):
        self.p["gold"] = 0
        before = deepcopy(self.p["building_materials"])
        self.assertFalse(v.improve_facility(self.p, self.place, "forge")[0])
        self.assertEqual(self.p["building_materials"], before)
        self.p["gold"] = 1000
        choice = str(v.facility_rows(self.p, self.place).index("forge") + 1)
        with patch("builtins.input", side_effect=[choice, "n", "0"]), redirect_stdout(
            StringIO()
        ):
            v.upgrade_buildings(game, self.place)
        self.assertNotIn("forge", self.place["services"])
        from expansion_state import state

        state(self.p).setdefault("systems", {})["mode"] = {"id": "budget_run"}
        self.assertFalse(v.improve_facility(self.p, self.place, "forge")[0])
        v.state(self.p, self.place)["built_services"] = ["not-a-building"]
        with self.assertRaises(ValueError):
            validate_original_save(ui.snapshot())
