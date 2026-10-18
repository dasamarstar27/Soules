from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import data
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import validate_original_save
import regional_forges as forges
import regional_sellers as sellers
from core_charging import charge, make_charged
import village_life as villages


class RegionalForgeTests(TestCase):
    def setUp(self):
        self.old = game.player
        self.old_ui = ui.get_ui()
        self.old_v = ui.village
        game.player = initial_player({"name": "Regional forge test", "cls": "warrior"})
        self.p = game.player
        self.p.update(
            region="Crimson Depths",
            gold=100000,
            hp=1000,
            max_hp=1000,
            atk=100,
            level=12,
        )
        self.p["unlocked_regions"] = set(data.REGIONS)
        self.p["cores"] = ["Molten Core"]
        self.p["metals"] = ["Iron"]
        self.p["woods"] = ["Oak"]
        self.p["runes"] = [
            deepcopy(next(r for r in data.RUNES if r["name"] == "Lightning Rune"))
        ]
        ui.init_ui(self.p)
        ui.village = None

    def tearDown(self):
        game.player = self.old
        ui._ui = self.old_ui
        ui.village = self.old_v

    def call(self, answers, method, *args):
        with patch("builtins.input", side_effect=answers), patch("builtins.print"):
            return method(*args)

    def test_sacrificing_a_loose_rune_consumes_exactly_one_of_each_and_saves(self):
        self.assertTrue(charge(self.p, "Molten Core", 0)[0])
        self.assertEqual(self.p["cores"], [])
        self.assertEqual(self.p["runes"], [])
        charged = self.p["charged_cores"][0]
        self.assertEqual(charged["rune"]["name"], "Lightning Rune")
        self.assertFalse(charge(self.p, "Molten Core", 0)[0])
        restored = validate_original_save(ui.snapshot())["player"]
        self.assertEqual(restored["charged_cores"], self.p["charged_cores"])

    def test_opposing_elements_cannot_be_sacrificed_or_imported(self):
        from core_charging import compatible

        self.p["cores"] = ["Phoenix Core"]
        self.p["runes"] = [
            deepcopy(next(r for r in data.RUNES if r["name"] == "Water Rune"))
        ]
        before = deepcopy(self.p)
        self.assertFalse(charge(self.p, "Phoenix Core", 0)[0])
        self.assertEqual(self.p, before)
        for core in data.CORES:
            self.assertTrue(any(compatible(core, rune) for rune in data.RUNES))
        self.p["charged_cores"] = [
            dict(
                name="Invalid",
                core_name="Phoenix Core",
                charged=True,
                rune=self.p["runes"][0],
            )
        ]
        with self.assertRaises(ValueError):
            validate_original_save(ui.snapshot())

    def test_uncharged_core_wrong_region_and_uncleared_hearth_cannot_spend_materials(
        self,
    ):
        forges.forge_state(self.p)["cleared"] = True
        before = deepcopy(self.p)
        self.assertFalse(
            forges.craft(self.p, "Molten Core", "Iron", "Oak", "Invalid")[0]
        )
        self.assertEqual(self.p, before)
        charge(self.p, "Molten Core", 0)
        core = self.p["charged_cores"][0]
        forges.forge_state(self.p)["cleared"] = False
        self.assertFalse(forges.craft(self.p, core, "Iron", "Oak", "Blocked")[0])
        self.assertEqual(len(self.p["charged_cores"]), 1)
        forges.forge_state(self.p)["cleared"] = True
        self.p["region"] = "Whispering Woods"
        self.assertFalse(forges.craft(self.p, core, "Iron", "Oak", "Wrong place")[0])
        self.assertEqual(len(self.p["charged_cores"]), 1)

    def test_three_chambers_unlock_crafting_and_permanent_real_core_and_rune_effects(
        self,
    ):
        with patch("expansion_combat.encounter", return_value=True) as fight:
            for _ in range(3):
                self.assertTrue(self.call([], forges.clear_wave, game)[0])
            self.assertFalse(self.call([], forges.clear_wave, game)[0])
            self.assertEqual(fight.call_count, 3)
        self.assertTrue(charge(self.p, "Molten Core", 0)[0])
        core = self.p["charged_cores"][0]
        self.assertTrue(
            self.call([], forges.craft, self.p, core, "Iron", "Oak", "Frostfire")[0]
        )
        self.assertEqual(self.p["charged_cores"], [])
        self.assertEqual(self.p["metals"], [])
        self.assertEqual(self.p["woods"], [])
        weapon = self.p["weapons"][-1]
        self.p["weapon"] = weapon
        enemy = dict(name="Test target", hp=100, max_hp=100, atk=1, **{"def": 0})
        self.call([], game._apply_charged_weapon_effect, enemy)
        self.assertIn("burn", enemy["rune_status"])
        self.assertIn("shock", enemy["rune_status"])
        self.call([], game._apply_charged_weapon_effect, enemy)
        self.assertEqual(weapon["forge_core_rune"]["name"], "Lightning Rune")
        self.assertTrue(validate_original_save(ui.snapshot()))

    def test_ordinary_forging_stays_physical_and_cannot_spend_a_charged_core(self):
        ui.village = villages.profile("Crimson Depths", "Smiths' Quarter")
        with patch.dict(game.FORGE_DATABASE, {}, clear=True):
            self.call(["1", "1", "1", "Ordinary blade"], game.forge_weapon)
        plain = self.p["weapons"][-1]
        self.assertNotIn("forge_core_effect", plain)
        self.assertNotIn("elemental_charged", plain)
        self.p["cores"] = ["Molten Core"]
        self.assertTrue(charge(self.p, "Molten Core", 0)[0])
        before = len(self.p["charged_cores"])
        self.call([], game.forge_weapon)
        self.assertEqual(len(self.p["charged_cores"]), before)

    def test_dwarven_bulk_prices_quantities_depletion_and_restocks(self):
        self.p["region"] = "Ironpeak Mountains"
        self.p["level"] = 1
        self.assertEqual(len(forges.dwarven_goods(self.p)), 8)
        gold = self.p["gold"]
        owned = self.p["metals"].count("Iron")
        self.call(["1", "20", "0"], forges.dwarven_market, game)
        self.assertEqual(self.p["gold"], gold - 100)
        self.assertEqual(self.p["metals"].count("Iron"), owned + 20)
        self.call(["1", "-3", "1", "11", "0"], forges.dwarven_market, game)
        self.assertEqual(self.p["gold"], gold - 100)
        self.call(["1", "10", "0"], forges.dwarven_market, game)
        self.call(["1", "0"], forges.dwarven_market, game)
        self.assertEqual(self.p["gold"], gold - 150)
        self.p["wander_count"] = 20
        self.call(["0"], forges.dwarven_market, game)
        self.assertEqual(
            self.p["expansion"]["activities"]["dwarven_market"]["stock"]["Iron"], 30
        )
        self.assertTrue(validate_original_save(ui.snapshot()))

    def test_riftlands_abundant_normal_cores_and_rare_charged_stock_are_persistent(
        self,
    ):
        self.p["region"] = "Riftlands"
        with patch("regional_sellers.random.Random") as rng:
            rng.return_value.random.return_value = 0
            rng.return_value.choice.side_effect = lambda pool: pool[0]
            shipment = sellers.shipment(self.p)
        ordinary = [x for x in shipment["offers"] if x["bag"] == "cores"]
        rare = [x for x in shipment["offers"] if x["bag"] == "charged_cores"]
        self.assertEqual(len(ordinary), len(data.CORES))
        self.assertTrue(all(x["left"] == 8 for x in ordinary))
        self.assertEqual(len(rare), 1)
        self.assertEqual(rare[0]["left"], 1)
        index = shipment["offers"].index(rare[0])
        self.assertTrue(sellers.buy(self.p, index, 1)[0])
        self.assertFalse(sellers.buy(self.p, index, 1)[0])
        with patch("regional_sellers.random.Random") as rng:
            self.assertEqual(sellers.shipment(self.p)["offers"][index]["left"], 0)
            rng.assert_not_called()
        self.assertTrue(validate_original_save(ui.snapshot()))
        self.p["wander_count"] = 20
        with patch("regional_sellers.random.Random") as rng:
            rng.return_value.random.return_value = 1
            self.assertFalse(
                any(
                    x["bag"] == "charged_cores"
                    for x in sellers.shipment(self.p)["offers"]
                )
            )
        self.assertTrue(
            all(
                "dwar" not in str(profile).lower()
                for profile in sellers.PROFILES.values()
            )
        )

    def test_each_regional_specialist_has_working_distinct_stock(self):
        for region in sellers.PROFILES:
            with self.subTest(region=region):
                self.p["region"] = region
                stock = sellers.shipment(self.p)
                self.assertTrue(stock["offers"])
                first = stock["offers"][0]
                before = len(self.p.get(first["bag"], []))
                self.assertTrue(sellers.buy(self.p, 0, 1)[0])
                self.assertEqual(len(self.p[first["bag"]]), before + 1)
        self.assertTrue(validate_original_save(ui.snapshot()))

    def test_clan_shop_rows_show_stats_price_and_stock(self):
        from season_two import GOODS, goods_line

        for element, goods in GOODS.items():
            for bag, item, price in goods:
                row = goods_line(bag, item, price, 2)
                self.assertIn("Price: " + str(price), row)
                self.assertIn("Stock: 2", row)
                if bag == "weapons":
                    self.assertIn("ATK +28", row)
                if bag == "armours":
                    self.assertIn("DEF +16", row)
                if bag == "staffs":
                    self.assertIn("Power +18", row)
                if bag in ("weapons", "armours", "staffs"):
                    self.assertIn("Element: " + element.title(), row)

    def test_invalid_forge_progress_and_weapon_cannot_import(self):
        progress = forges.forge_state(self.p)
        progress.update(waves=4, cleared=True)
        with self.assertRaises(ValueError):
            validate_original_save(ui.snapshot())
        progress.update(waves=3, cleared=True)
        self.p["weapons"].append(
            dict(
                name="Bad forge",
                elemental_core="Phoenix Core",
                elemental_charged=True,
                forge_core_effect="rebirth",
                forge_core_rune=deepcopy(
                    next(r for r in data.RUNES if r["name"] == "Water Rune")
                ),
            )
        )
        with self.assertRaises(ValueError):
            validate_original_save(ui.snapshot())
