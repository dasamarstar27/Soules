from unittest import TestCase
from unittest.mock import patch
from copy import deepcopy
import data
import original_game as game
import original_ui as ui
from original_worker import initial_player
import village_jobs as jobs
import village_life as villages
from player_qol import loot, drink, sanctuary


class PlayerQualityTests(TestCase):
    def setUp(self):
        self.old = game.player
        self.old_v = ui.village
        self.old_ui = ui.get_ui()
        game.player = initial_player({"name": "Quality", "cls": "warrior"})
        self.p = game.player
        self.p["gold"] = 10000
        self.p["building_materials"] = {"Timber": 10, "Stone": 10, "Iron fittings": 10}
        ui.init_ui(self.p)
        self.v = villages.profile("Whispering Woods", "Old Village")
        ui.village = self.v

    def tearDown(self):
        game.player = self.old
        ui.village = self.old_v
        ui._ui = self.old_ui

    def call(self, answers, fn, *args, **kw):
        with patch("builtins.input", side_effect=answers), patch("builtins.print"):
            return fn(*args, **kw)

    def test_monster_roll_precedes_structure_roll(self):
        with patch.object(game.random, "random", return_value=0), patch.object(
            game, "fight"
        ) as fight, patch.object(game, "visit_elemental_village") as clan, patch(
            "builtins.print"
        ):
            game.explore()
        fight.assert_called_once()
        clan.assert_not_called()
        self.assertFalse(
            self.p.get("discovered_structures", {}).get("Whispering Woods")
        )

    def test_beta_returns_clean_character_and_survives_save(self):
        from beta_testing import grant_collectibles, disable_beta
        from original_sessions import validate_original_save

        original = deepcopy(self.p)
        self.call([], grant_collectibles, self.p)
        validate_original_save(ui.snapshot())
        self.p["gold"] = 999999
        self.p["weapons"].append(dict(name="Test-crafted", atk=100))
        self.call([], disable_beta, self.p)
        self.assertEqual(self.p["weapons"], original["weapons"])
        self.assertEqual(self.p["gold"], original["gold"])
        self.assertEqual(self.p["unlocked_regions"], original["unlocked_regions"])
        self.call([],disable_beta,self.p)
        self.assertEqual(self.p["weapons"],original["weapons"])
        validate_original_save(ui.snapshot())

    def test_older_beta_cleanup_preserves_an_exportable_recovery_copy(self):
        from beta_testing import grant_collectibles, disable_beta
        from original_sessions import validate_original_save

        self.p["beta_mode"] = True
        self.call([], grant_collectibles, self.p)
        self.assertNotIn("beta_backup", self.p)
        before = deepcopy(self.p["weapons"])
        self.p["beta_mode"] = False  # old release already switched off but kept all grants
        self.call([], disable_beta, self.p)
        self.assertEqual(self.p["beta_legacy_recovery"]["weapons"], before)
        self.assertEqual([w["name"] for w in self.p["weapons"]], ["Rusty Sword"])
        self.assertEqual(self.p["runes"], [])
        saved = ui.snapshot()
        validate_original_save(saved)
        validate_original_save(
            dict(
                format="soules-original-v1",
                player=saved["player"]["beta_legacy_recovery"],
            )
        )

    def test_loot_sales_preserve_food_and_scrolls(self):
        food = deepcopy(data.FOOD_ITEMS[0])
        scroll = deepcopy(data.SCROLLS[0])
        trinket = deepcopy(data.LOOT_ITEMS[0])
        self.p["inventory"] = [food, scroll, trinket]
        self.assertFalse(loot(food))
        self.assertFalse(loot(scroll))
        self.assertTrue(loot(trinket))
        self.call([], game._sell_all_loot)
        self.assertEqual(self.p["inventory"], [food, scroll])

    def test_potions_keep_full_health_bottles_and_consume_one(self):
        self.p["potions"] = ["Health Potion", "Health Potion"]
        self.assertFalse(drink(game, 0)[0])
        self.assertEqual(len(self.p["potions"]), 2)
        self.p["hp"] = 1
        self.call([], drink, game, 0)
        self.assertEqual(self.p["hp"], 51)
        self.assertEqual(len(self.p["potions"]), 1)

    def test_food_bulk_is_priced_and_stock_is_finite(self):
        food = villages.food_catalog(self.v)[0]
        gold = self.p["gold"]
        price = villages.food_price(self.p, self.v, food)
        self.call(["1", "3"], villages.restaurant, game, self.v)
        self.assertEqual(self.p["gold"], gold - price * 3)
        self.assertEqual(len(self.p["inventory"]), 3)
        self.call(["1", "999"], villages.restaurant, game, self.v)
        self.assertEqual(len(self.p["inventory"]), 3)

    def test_commission_needs_core_wood_and_metal_and_can_buy_finite_stock(self):
        v = villages.profile("Crimson Depths", "Smiths' Quarter")
        self.p["metals"] = ["Iron"]
        self.assertFalse(jobs.commission(self.p, v, "weapon", ["Iron"])[0])
        self.p["cores"] = ["Molten Core"]
        self.p["woods"] = ["Oak"]
        self.assertTrue(
            jobs.commission(self.p, v, "weapon", ["Iron", "Molten Core", "Oak"])[0]
        )
        self.assertEqual(self.p["metals"], [])
        self.assertEqual(self.p["cores"], [])
        self.assertEqual(self.p["woods"], [])
        jobs.advance(self.p, v, 10)
        jobs.collect(self.p, v, 0)
        gold = self.p["gold"]
        stock = jobs.commission_stock(self.p, v)
        before = stock["cores"]["Molten Core"]
        self.assertTrue(
            jobs.commission(
                self.p, v, "weapon", ["Iron", "Molten Core", "Oak"], village_stock=True
            )[0]
        )
        self.assertLess(self.p["gold"], gold - 35)
        self.assertEqual(stock["cores"]["Molten Core"], before - 1)
        self.assertEqual(self.p["metals"], [])

    def test_each_wander_advances_orders_even_away(self):
        v = villages.profile("Crimson Depths", "Smiths' Quarter")
        local = jobs.record(self.p, v)
        local["work_orders"] = [dict(remaining=3)]
        with patch.object(game.random, "random", return_value=0.99), patch.object(
            game.random, "randint", return_value=99
        ), patch("builtins.print"):
            game.explore()
        self.assertEqual(local["work_orders"][0]["remaining"], 2)

    def test_more_companions_wait_at_home_and_party_can_swap(self):
        pets = [pet for pool in data.COMPANIONS.values() for pet in pool][:5]
        for pet in pets:
            self.call([], game.recruit_companion, pet)
        self.assertEqual(len(self.p["companions"]), 3)
        self.assertEqual(len(self.p["home_companions"]), 2)
        self.call(["1", "1", "2", "1", "0"], sanctuary, game)
        self.assertEqual(len(self.p["companions"]), 3)
        self.assertEqual(len(self.p["home_companions"]), 2)
        self.assertEqual(self.p["companions"][-1]["name"], pets[3]["name"])

    def test_raid_group_and_live_assignment_metadata_clear_on_return(self):
        from community_addons import defence

        observed = []

        def choose_role(prompt):
            observed.append(deepcopy(ui.snapshot()["assignment"]))
            return "1"

        with patch("builtins.input", side_effect=choose_role), patch(
            "builtins.print"
        ), patch("expansion_combat.encounter", return_value=True) as battle:
            defence(game, self.v)
        self.assertEqual(len(battle.call_args.args[1]), 3)
        self.assertTrue(observed[0]["roles"])
        self.assertIsNone(ui.assignment)
