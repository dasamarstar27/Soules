import unittest
from copy import deepcopy
from unittest.mock import patch
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import validate_original_save
import village_life as v
import data


class VillageLifeTests(unittest.TestCase):
    def setUp(self):
        self.old = game.player
        self.previous = ui.village
        game.player = initial_player({"name": "Village tester", "cls": "warrior"})
        self.p = game.player
        self.farm = v.profile("Whispering Woods", "Old Village")
        self.forge = v.profile("Crimson Depths", "Smiths' Quarter")
        ui.village = self.farm
        ui.init_ui(self.p)

    def tearDown(self):
        game.player = self.old
        ui.village = self.previous

    def inputs(self, values, fn, *args):
        with patch("builtins.input", side_effect=values), patch("builtins.print"):
            return fn(*args)

    def test_services_and_qualities_differ(self):
        self.assertNotIn("forge", self.farm["services"])
        self.assertIn("forge", self.forge["services"])
        self.assertNotIn("restaurant", self.forge["services"])
        self.assertEqual(self.farm["quality"]["farm"], 3)
        self.assertEqual(self.farm["quality"]["loom"], 1)
        mountain = v.profile("Ironpeak Mountains", "Mountain Village")
        self.assertEqual(mountain["quality"]["loom"], 3)
        self.assertEqual(mountain["quality"]["restaurant"], 1)
        poor_farm = v.profile("Blight Swamp", "Rotwood Village")
        self.assertEqual(poor_farm["quality"]["farm"], 1)
        self.assertEqual(v.profile("Sunken Coast", "Dockside Village")["quality"]["restaurant"], 3)

    def test_missing_workstation_cannot_be_used(self):
        before = deepcopy(self.p)
        with patch(
            "builtins.input", side_effect=AssertionError("Unavailable bench asked for input")
        ), patch("builtins.print"):
            game.forge_weapon()
            game.craft_staff()
            game.imbue_staff()
        self.assertEqual(self.p, before)

    def test_blacksmith_quality_changes_upgrade(self):
        ui.village = self.forge
        self.p["gold"] = 500
        before = self.p["weapon"]["atk"]
        self.inputs(["1", "1", "y"], v.smith, game, self.forge)
        self.assertEqual(self.p["weapon"]["atk"], before + 5)
        self.assertEqual(self.p["gold"], 380)

    def test_restaurant_stock_is_finite_and_reload_safe(self):
        self.p["gold"] = 1000
        f = v.food_catalog(self.farm)[0]
        price = v.food_price(self.p, self.farm, f)
        for _ in range(4):
            self.inputs(["1"], v.restaurant, game, self.farm)
        self.assertEqual(self.p["gold"], 1000 - price * 3)
        self.assertEqual(len(self.p["inventory"]), 3)
        restored = validate_original_save(ui.snapshot())
        self.assertEqual(
            restored["player"]["village_records"][self.farm["id"]]["food_stock"][f["name"]], 0
        )
        self.p["wander_count"] = 20
        self.assertEqual(v.stock(self.p, self.farm)[f["name"]], 3)

    def test_meal_quality_restores_hp_and_hunger(self):
        self.p["gold"] = 1000
        self.p["hp"] = 1
        self.p["hunger"] = 0
        food = v.food_catalog(self.farm)[0]
        self.inputs(["1"], v.restaurant, game, self.farm, True)
        self.assertEqual(self.p["hp"], 11)
        self.assertEqual(self.p["hunger"], food["hunger"] + 5)
        self.assertEqual(self.p["inventory"], [])

    def test_farm_quality_and_regrowth(self):
        with patch("builtins.print"):
            v.harvest(game, self.farm)
            v.harvest(game, self.farm)
        self.assertEqual(len(self.p["ingredients"]), 4)
        self.p["wander_count"] = 20
        with patch("builtins.print"):
            v.harvest(game, self.farm)
        self.assertEqual(len(self.p["ingredients"]), 8)

    def test_errand_reward_only_once_per_cycle_and_discount(self):
        name = data.REGION_INGREDIENTS[self.p["region"]][0]
        self.p["ingredients"] = [name] * 6
        food = v.food_catalog(self.farm)[0]
        price = v.food_price(self.p, self.farm, food)
        self.inputs(["y"], v.errand, game, self.farm)
        self.inputs([], v.errand, game, self.farm)
        self.assertEqual(self.p["gold"], 130)
        self.assertEqual(self.p["ingredients"], [name] * 3)
        self.assertEqual(v.state(self.p, self.farm)["reputation"], 1)
        self.assertLessEqual(v.food_price(self.p, self.farm, food), price)

    def test_notes_tags_and_snapshot_round_trip(self):
        v.bookmark(self.p, self.farm, "cheap food / farming", "cheap food,farming")
        snapshot = ui.snapshot()
        self.assertEqual(snapshot["village"]["note"], "cheap food / farming")
        self.assertIn("Restaurant", v.SERVICE_NAMES.values())
        saved = validate_original_save(snapshot)
        self.assertEqual(
            saved["player"]["saved_villages"][self.farm["id"]]["tags"], ["cheap food", "farming"]
        )
        saved["player"]["saved_villages"][self.farm["id"]]["tags"] = "bad"
        with self.assertRaises(ValueError):
            validate_original_save(saved)

    def test_directory_revisit_only_discovered_and_unlocked(self):
        self.p["discovered_structures"] = {"Whispering Woods": ["Old Village"]}
        self.assertEqual(len(v.known_villages(self.p)), 1)
        v.bookmark(self.p, self.farm, "cheap food", "farming")
        with patch.object(game, "visit_village") as visit:
            self.inputs(["f", "farming", "1", "0"], v.directory, game)
            visit.assert_called_once()
            self.assertEqual(visit.call_args.args[0]["name"], "Old Village")
        self.p["unlocked_regions"] = set()
        with patch.object(game, "visit_village") as visit:
            self.inputs(["1", "0"], v.directory, game)
            visit.assert_not_called()

    def test_master_loom_bonus_and_equippable_crafted_armour(self):
        ui.village = v.profile("Ironpeak Mountains", "Mountain Village")
        recipe = data.ARMOR_RECIPES["helmet"][0]
        self.p["gold"] = 10000
        for name, count in recipe["materials"].items():
            key = (
                "cloths"
                if name in data.CLOTHS
                else "leathers" if name in data.LEATHERS else "metals"
            )
            self.p[key].extend([name] * count)
        self.inputs(["1", "1"], game.craft_armor)
        self.assertEqual(self.p["armours"][-1]["def"], recipe["def"] + 4)
        self.assertIs(self.p["armours"][-1], self.p["crafted_armor"][-1])

    def test_tower_quality_changes_staff_power(self):
        ui.village = self.forge
        self.p["runes"] = deepcopy(data.RUNES[:2])
        self.inputs(["1", "2"], game.craft_staff)
        self.assertEqual(self.p["staffs"][-1]["power"], 14)
        self.assertEqual(self.p["runes"], [])

    def test_temple_consumes_elemental_core_and_adds_quality_power(self):
        ui.village = v.profile("Frostbound Tundra", "Ice Hamlet")
        self.p["staffs"] = [deepcopy(data.STAFFS[0])]
        core = next(iter(data.ELEMENTAL_CORES))
        self.p["elemental_cores"] = [core]
        base = self.p["staffs"][0]["power"]
        self.inputs(["1", "1"], game.imbue_staff)
        self.assertEqual(self.p["elemental_cores"], [])
        self.assertEqual(
            self.p["staffs"][0]["power"], base + data.ELEMENTAL_CORES[core]["bonus_atk"] + 4
        )
        self.assertTrue(self.p["staffs"][0]["charged"])

    def test_market_quality_reduces_actual_merchant_price(self):
        ui.village = v.profile("Crystal Spire", "Crystal Village")
        self.p["gold"] = 1000
        weapon = data.WEAPONS[0]
        with patch.dict(game.MERCHANT_ITEMS, {self.p["region"]: [weapon["name"]]}):
            self.inputs(["1", "y", "0"], game.merchant)
        self.assertEqual(self.p["gold"], 1000 - round(weapon["atk"] * 10 * 0.9))

    def test_inn_quality_changes_actual_rest(self):
        self.p["gold"] = 100
        self.p["hp"] = 1
        self.inputs(
            ["4", "y", "7"], game.visit_village, {"name": "Ice Hamlet"}, "Frostbound Tundra"
        )
        self.assertEqual(self.p["gold"], 30)
        self.assertEqual(self.p["hp"], 51)

    def test_salvage_quality_and_materials(self):
        ui.village = self.forge
        self.p["weapons"].append({"name": "Spare", "atk": 20, "materials": {"Iron": 4}})
        self.inputs(["1", "y"], game.salvage_equipment)
        self.assertEqual(self.p["gold"], 95)
        self.assertEqual(self.p["metals"], ["Iron"] * 3)
        self.assertEqual(len(self.p["weapons"]), 1)

    def test_successful_alchemy_can_preserve_one_ingredient(self):
        combo, result = next(iter(data.INGREDIENT_COMBOS.items()))
        self.p["ingredients"] = sorted(combo)
        with patch.object(game.random, "random", return_value=0):
            self.inputs(["0", "1", "n"], game._ingredient_brew_menu)
        self.assertEqual(len(self.p["ingredients"]), 1)
        self.assertEqual(self.p["potions"], [result["name"]])
