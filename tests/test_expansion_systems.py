"""Playable expansion contracts, resource safety and campaign persistence."""

from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import data
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import validate_original_save
from expansion_state import state
import daily_rewards
import village_jobs as jobs
import village_life as villages
import addon_quests
import season_three
import food_addons
import artisan_addons
import expansion_combat
import community_store
from addon_catalog import ADDONS
from addons import run


class ExpansionSystems(unittest.TestCase):
    def setUp(self):
        self.old = game.player
        self.old_village = ui.village
        self.p = initial_player({"name": "Expansion tester", "cls": "warrior"})
        game.player = self.p
        self.p.update(hp=1000, max_hp=1000, atk=50, level=10, mana=200, gold=100000)
        self.p["def"] = 20
        self.p["unlocked_regions"] = set(data.REGIONS + [data.SECRET_REGION])
        self.p["bosses_defeated"] = list(data.REGIONS)
        self.p["inventory"] = [
            deepcopy(x) for _ in range(4) for x in data.FOOD_ITEMS
        ] + [{"name": "Stormfruit", "hunger": 25, "value": 25}]
        for bag, catalog in [
            ("metals", data.METALS),
            ("woods", data.WOODS),
            ("cores", data.CORES),
            ("cloths", data.CLOTHS),
            ("leathers", data.LEATHERS),
        ]:
            self.p[bag] = list(catalog) * 10
        self.p["ingredients"] = [
            x for pool in data.REGION_INGREDIENTS.values() for x in pool
        ] * 10
        self.p["runes"] = [deepcopy(r) for _ in range(3) for r in data.RUNES]
        self.p["weapons"].extend(deepcopy(data.WEAPONS))
        self.p["armours"] = deepcopy(data.ARMOURS)
        self.p["potions"] = [x["name"] for x in data.POTION_RECIPES] * 3
        self.p["building_materials"] = {
            "Timber": 1000,
            "Stone": 1000,
            "Iron fittings": 1000,
        }
        self.p["source_story"] = {
            "opened": True,
            "profession_xp": {"smithing": 100, "weaving": 100, "enchanting": 100},
            "dialogue": {"one": [1], "two": [1]},
            "witnesses": ["one", "two", "three", "four"],
            "season_one_complete": True,
            "complete": True,
            "fragments": 10,
        }
        self.p["discovered_structures"] = {
            r: [x["name"] for x in entries]
            for r, entries in data.REGION_STRUCTURES.items()
        }
        for r, ev in data.ELEMENTAL_VILLAGES.items():
            self.p["discovered_structures"][r].append(ev["name"])
        self.p["protected_relics"] = [
            dict(
                id=r + "::" + kind,
                name=r + " " + kind,
                kind=kind,
                region=r,
                element="nature",
                text="A preserved record.",
                protected=True,
            )
            for r in data.REGIONS
            for kind in ("tome", "fragment")
        ]
        self.p["ruin_searches"] = {r + "::site": 0 for r in data.REGIONS}
        self.p["companions"] = [
            dict(
                name="Ember Fox",
                element="fire",
                can_battle=True,
                stage=1,
                xp=20,
                bond_xp=20,
                hunger=100,
                home_region="Ashen Wastes",
                meals_eaten=0,
            )
        ]
        self.v = villages.profile("Whispering Woods", "Old Village")
        self.forge = villages.profile("Crimson Depths", "Smiths' Quarter")
        ui.init_ui(self.p)
        ui.village = self.v
        s = state(self.p)
        s["field"]["observations"] = ["one", "two", "three"]
        s["statistics"]["commissions_collected"] = 1
        self.p["source_story"]["mentor_village"] = {
            "id": self.v["id"],
            "name": self.v["name"],
            "region": self.v["region"],
        }

    def tearDown(self):
        game.player = self.old
        ui.village = self.old_village

    def call(self, answers, fn, *args, **kwargs):
        with patch("builtins.input", side_effect=answers), patch("builtins.print"):
            return fn(*args, **kwargs)

    def test_daily_claim_is_calendar_based_unique_and_resets_after_gap(self):
        today = date(2026, 10, 18)
        before = self.p["gold"]
        self.assertTrue(daily_rewards.claim(self.p, today)[0])
        self.assertEqual(self.p["gold"], before + 50)
        self.assertFalse(daily_rewards.claim(self.p, today)[0])
        self.assertFalse(daily_rewards.claim(self.p, today - timedelta(days=1))[0])
        self.assertTrue(daily_rewards.claim(self.p, today + timedelta(days=1))[0])
        self.assertEqual(self.p["login_streak"], 2)
        self.assertTrue(daily_rewards.claim(self.p, today + timedelta(days=3))[0])
        self.assertEqual(self.p["login_streak"], 1)
        restored = validate_original_save(ui.snapshot())["player"]
        self.assertEqual(state(restored)["daily"], state(self.p)["daily"])

    def test_work_order_escrows_cost_waits_and_delivers_exactly_once(self):
        before = self.p["metals"].count("Iron")
        gold = self.p["gold"]
        ok, _ = jobs.commission(self.p, self.forge, "weapon", ["Iron"])
        self.assertTrue(ok)
        self.assertEqual(self.p["metals"].count("Iron"), before - 1)
        self.assertEqual(self.p["gold"], gold - 35)
        self.assertFalse(jobs.collect(self.p, self.forge, 0)[0])
        self.assertFalse(jobs.commission(self.p, self.forge, "weapon", ["Iron"])[0])
        restored = validate_original_save(ui.snapshot())["player"]
        self.assertEqual(
            jobs.record(restored, self.forge)["work_orders"],
            jobs.record(self.p, self.forge)["work_orders"],
        )
        jobs.advance(self.p, self.forge, 10)
        n = len(self.p["weapons"])
        self.assertTrue(jobs.collect(self.p, self.forge, 0)[0])
        self.assertEqual(len(self.p["weapons"]), n + 1)
        self.assertFalse(jobs.collect(self.p, self.forge, 0)[0])
        self.assertEqual(self.p["weapons"][-1]["provenance"], "Crimson Depths")

    def test_no_order_is_created_when_materials_or_service_missing(self):
        before = deepcopy(self.p)
        self.assertFalse(jobs.commission(self.p, self.v, "weapon", ["Iron"])[0])
        self.assertEqual(self.p["gold"], before["gold"])
        self.assertFalse(
            jobs.commission(self.p, self.forge, "weapon", ["Not a metal"])[0]
        )
        self.assertEqual(self.p["gold"], before["gold"])

    def test_alchemist_commissions_real_recipe_and_rejects_unknown_pair(self):
        self.assertFalse(
            jobs.commission(self.p, self.v, "potion", ["Thorn Petal", "Vine Root"])[0]
        )
        before = self.p["ingredients"].count("Thorn Petal")
        self.assertTrue(
            jobs.commission(self.p, self.v, "potion", ["Thorn Petal", "Dew Blossom"])[0]
        )
        self.assertEqual(self.p["ingredients"].count("Thorn Petal"), before - 1)
        jobs.advance(self.p, self.v, 10)
        self.assertTrue(jobs.collect(self.p, self.v, 0)[0])
        self.assertIn("Forest Salve", self.p["potions"])

    def test_gathering_is_finite_and_reopening_never_advances_it(self):
        for _ in range(2):
            self.assertTrue(
                jobs.commission(self.p, self.v, "gather", resource="ingredients")[0]
            )
            remaining = jobs.record(self.p, self.v)["work_orders"][-1]["remaining"]
            self.call(["0"], jobs.menu, game, self.v)
            self.assertEqual(
                jobs.record(self.p, self.v)["work_orders"][-1]["remaining"], remaining
            )
            jobs.advance(self.p, self.v, 10)
            self.assertTrue(jobs.collect(self.p, self.v, 0)[0])
        self.assertFalse(
            jobs.commission(self.p, self.v, "gather", resource="ingredients")[0]
        )
        self.p["wander_count"] = 20
        self.assertTrue(
            jobs.commission(self.p, self.v, "gather", resource="ingredients")[0]
        )

    def test_apprentice_batch_requires_all_materials_and_collects_separate_orders(self):
        state(self.p)["professions"]["apprentice"] = 2
        self.assertTrue(jobs.batch(self.p, self.forge, "weapon", ["Iron"], 3)[0])
        self.assertEqual(len(jobs.record(self.p, self.forge)["work_orders"]), 3)
        jobs.advance(self.p, self.forge, 10)
        for _ in range(3):
            self.assertTrue(jobs.collect(self.p, self.forge, 0)[0])
        self.assertFalse(jobs.batch(self.p, self.forge, "weapon", ["Iron"], 4)[0])

    def test_every_story_has_travel_gates_unique_reward_and_preserved_relics(self):
        base = deepcopy(self.p)
        for quest_id in range(1, 21):
            with self.subTest(quest=quest_id):
                self.p.clear()
                self.p.update(deepcopy(base))
                ui.init_ui(self.p)
                self.assertTrue(addon_quests.accept(self.p, quest_id)[0])
                self.assertFalse(addon_quests.progress(game, quest_id)[0])
                region, destination, _, _ = addon_quests.QUESTS[quest_id]
                self.p["region"] = region
                self.p["wander_count"] = 2
                self.assertTrue(addon_quests.progress(game, quest_id)[0])
                q = state(self.p)["quests"][str(quest_id)]
                q["trial_won"] = True
                if quest_id == 19:
                    state(self.p)["quests"]["11"] = {"stage": 3, "complete": True}
                if quest_id == 5:
                    for place in (
                        "Sunken Coast",
                        "Whispering Woods",
                        "Ironpeak Mountains",
                    ):
                        self.p["region"] = place
                        self.assertTrue(addon_quests.progress(game, quest_id)[0])
                else:
                    self.p["region"] = destination
                    self.assertTrue(addon_quests.progress(game, quest_id)[0])
                relics = deepcopy(self.p["protected_relics"])
                with patch("builtins.print"):
                    self.assertTrue(addon_quests.progress(game, quest_id, "share")[0])
                gold = self.p["gold"]
                self.assertFalse(addon_quests.progress(game, quest_id)[0])
                self.assertEqual(self.p["gold"], gold)
                self.assertEqual(self.p["protected_relics"], relics)
                self.assertEqual(
                    validate_original_save(ui.snapshot())["player"]["expansion"][
                        "quests"
                    ][str(quest_id)]["complete"],
                    True,
                )

    def test_named_evolution_comes_from_actual_help_not_meals(self):
        import companion_care as care

        pet = self.p["companions"][0]
        pet.update(stage=0, bond_xp=0, xp=0, hunger=10)
        food = care.foods(pet)[0]
        self.p["inventory"].append(deepcopy(food))
        self.assertTrue(care.feed(self.p, pet, len(self.p["inventory"]) - 1)[0])
        self.assertEqual(pet["bond_xp"], 0)
        for _ in range(4):
            pet["helped_this_battle"] = True
            care.battle_credit(self.p, 5)
        self.assertEqual(pet["stage"], 1)
        for _ in range(8):
            pet["helped_this_battle"] = True
            care.battle_credit(self.p, 5)
        self.assertEqual(pet["stage"], 2)
        self.assertEqual(pet["form_name"], "Sunfire Ember Fox")
        before = pet["bond_xp"]
        care.battle_credit(self.p, 5)
        self.assertEqual(pet["bond_xp"], before)

    def test_practice_restores_health_mana_effects_and_never_awards_combat_progress(
        self,
    ):
        self.p["hp"] = 80
        self.p["mana"] = 70
        before = deepcopy(self.p)
        won = self.call(
            ["1"] * 10,
            expansion_combat.encounter,
            game,
            [{"name": "Practice", "hp": 10, "atk": 2, "def": 0}],
            True,
        )
        self.assertTrue(won)
        self.assertEqual(self.p["hp"], 80)
        self.assertEqual(self.p["mana"], 70)
        self.assertEqual(self.p["gold"], before["gold"])
        self.assertEqual(self.p["xp"], before["xp"])
        self.assertEqual(self.p["kill_counts"], before["kill_counts"])

    def test_pair_encounter_has_explicit_target_and_records_replay(self):
        enemies = [
            {"name": "One", "hp": 10, "atk": 1, "def": 0},
            {"name": "Two", "hp": 10, "atk": 1, "def": 0},
        ]
        won = self.call(["2", "2", "1", "1"], expansion_combat.encounter, game, enemies)
        self.assertTrue(won)
        self.assertEqual(state(self.p)["statistics"]["tactical_victories"], 1)
        replay = state(self.p)["activities"]["battle_replays"][-1]
        self.assertTrue(replay["won"])
        self.assertGreaterEqual(len(replay["turns"]), 2)

    def test_season_three_gates_reveal_and_completes_without_taking_the_four_cores(
        self,
    ):
        self.p["source_story"]["complete"] = False
        self.assertFalse(season_three.advance(game)[0])
        self.assertFalse(state(self.p)["season_three"].get("reveal_seen"))
        self.p["source_story"]["complete"] = True
        cores = deepcopy(self.p.get("elemental_cores", []))
        relics = deepcopy(self.p["protected_relics"])
        with patch("builtins.print"), patch(
            "expansion_combat.encounter", return_value=True
        ):
            for _ in range(5):
                self.assertTrue(season_three.advance(game)[0])
            self.assertTrue(state(self.p)["season_three"]["reveal_seen"])
            self.assertFalse(season_three.advance(game)[0])
            self.assertTrue(season_three.craft_pair(self.p, 0)[0])
            for _ in range(3):
                self.assertTrue(season_three.advance(game, 1)[0])
        self.assertTrue(state(self.p)["season_three"]["complete"])
        self.assertEqual(self.p.get("elemental_cores", []), cores)
        self.assertEqual(self.p["protected_relics"], relics)
        self.assertIn("council", state(self.p)["season_three"]["ending"])
        self.assertEqual(validate_original_save(ui.snapshot())["player"]["chapter"], 3)

    def test_shared_trade_escrow_purchase_cancel_and_proceeds_are_one_time(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "community.sqlite3"
            seller = self.p
            buyer = initial_player({"name": "Buyer", "cls": "warrior"})
            buyer["gold"] = 1000
            count = len(seller["weapons"])
            self.assertTrue(community_store.publish(seller, "weapons", 1, 70, path)[0])
            self.assertEqual(len(seller["weapons"]), count - 1)
            offer = community_store.offers(path)[0]
            self.assertTrue(community_store.buy(buyer, offer["id"], path)[0])
            self.assertFalse(community_store.buy(buyer, offer["id"], path)[0])
            self.assertEqual(buyer["gold"], 930)
            self.assertEqual(community_store.settle(seller, path=path)[0], 70)
            self.assertEqual(community_store.settle(seller, path=path)[0], 0)
            self.assertFalse(community_store.publish(seller, "weapons", 0, 70, path)[0])
            self.assertTrue(community_store.publish(seller, "weapons", 1, 50, path)[0])
            offer = community_store.offers(path)[0]
            self.assertTrue(
                community_store.settle(seller, cancel=offer["id"], path=path)[1]
            )
            self.assertFalse(
                community_store.settle(seller, cancel=offer["id"], path=path)[1]
            )

    def test_fishing_and_cooking_create_edible_items_without_infinite_sites(self):
        self.call([], run, game, 41)
        self.call([], run, game, 41)
        before = len(self.p["inventory"])
        self.call([], run, game, 41)
        self.assertEqual(len(self.p["inventory"]), before)
        self.call(["1"], run, game, 71)
        item = self.p["inventory"][-1]
        self.assertTrue(food_addons.is_food(item))
        self.assertGreater(item["hunger"], 0)

    def test_research_substitution_only_applies_after_paid_discovery(self):
        self.assertIsNone(
            food_addons.brew_recipe(self.p, "Thorn Petal", "Forest Mushroom")
        )
        self.call([], run, game, 79)
        self.assertEqual(
            food_addons.brew_recipe(self.p, "Thorn Petal", "Forest Mushroom")["name"],
            "Forest Salve",
        )

    def test_repair_tools_and_specialties_apply_once_to_new_crafts(self):
        self.call(["1"], run, game, 31)
        self.call([], run, game, 35)
        item = {"name": "Test", "atk": 10}
        artisan_addons.apply_traits(self.p, item, "smithing")
        self.assertEqual(item["atk"], 14)
        artisan_addons.apply_traits(self.p, item, "smithing")
        self.assertEqual(item["atk"], 14)
        self.assertEqual(state(self.p)["professions"]["tool"]["durability"], 9)

    def test_bad_expansion_and_work_order_saves_are_rejected(self):
        saved = ui.snapshot()
        saved["player"]["expansion"]["quests"] = []
        with self.assertRaises(ValueError):
            validate_original_save(saved)
        jobs.record(self.p, self.v)
        saved = ui.snapshot()
        saved["player"]["village_records"][self.v["id"]]["work_orders"] = [
            {"remaining": -1, "worker": "x", "destination": "weapons", "result": {}}
        ]
        with self.assertRaises(ValueError):
            validate_original_save(saved)

    def test_all_hundred_addons_have_a_dispatch_path(self):
        self.assertEqual(set(ADDONS), set(range(1, 101)))
        for feature in range(1, 101):
            module = (
                "addon_quests"
                if feature <= 20
                else (
                    "community_addons"
                    if feature <= 30
                    else (
                        "artisan_addons"
                        if feature <= 40
                        else (
                            "expedition"
                            if feature <= 50
                            else (
                                "expansion_combat"
                                if feature <= 60
                                else (
                                    "magic_addons"
                                    if feature <= 70
                                    else (
                                        "food_addons"
                                        if feature <= 80
                                        else (
                                            "relationship_addons"
                                            if feature <= 90
                                            else "journal_addons"
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
            method = "menu" if feature <= 20 else "activity"
            with patch(module + "." + method) as handler:
                run(game, feature)
                handler.assert_called_once_with(game, feature)

    def test_addons_21_to_100_execute_their_positive_player_paths(self):
        base = deepcopy(self.p)
        answers = {
            21: ["1", "1", "2"],
            23: ["1"],
            24: ["1", "1"],
            26: ["1"],
            27: ["1"],
            28: ["1"],
            31: ["1"],
            32: ["1"],
            33: ["1"],
            37: ["1"],
            38: ["1"],
            39: ["1"],
            40: ["1", "Signed by Tester"],
            44: ["1"],
            46: ["2"],
            47: ["Field observation"],
            48: ["1"],
            49: ["1"],
            50: ["y"],
            54: ["1"],
            60: ["1"],
            67: ["1"],
            70: ["1"],
            71: ["1"],
            74: ["1"],
            75: ["1"],
            76: ["1", "Tastes herbal"],
            78: ["1"],
            81: ["1"],
            82: ["1", "1"],
            83: ["1"],
            84: ["1"],
            85: ["1", "1"],
            87: ["1", "1"],
            91: ["1"],
            95: ["1", "Good shelter"],
            97: ["1", "1"],
            99: ["y"],
        }
        for feature in range(21, 101):
            with self.subTest(feature=feature):
                self.p.clear()
                self.p.update(deepcopy(base))
                ui.init_ui(self.p)
                ui.village = self.v
                self.p["elemental_arts"] = ["Ember Touch"]
                state(self.p)["magic"]["effects_used"] = ["burn", "freeze", "poison"]
                self.p["weapons"][1]["masterwork"] = True
                state(self.p)["activities"]["battle_replays"] = [
                    dict(practice=True, won=True, turns=[dict(hp=90, action="attack")])
                ]
                if feature == 81:
                    self.p["region"] = "Ashen Wastes"
                    self.p["companions"][0]["helped_victories"] = 3
                    state(self.p)["relationships"]["companion_quests"] = {
                        "Ember Fox": dict(accepted=0, complete=False)
                    }
                if feature == 88:
                    state(self.p)["field"]["escort"] = {"destination": "Ashen Wastes"}
                if feature == 89:
                    state(self.p)["quests"]["5"] = {"stage": 3, "complete": True}
                if feature == 90:
                    state(self.p)["quests"]["1"] = {"stage": 3, "complete": True}
                with patch("expansion_combat.practice", return_value=True), patch(
                    "expansion_combat.encounter", return_value=True
                ), patch.object(game.random, "random", return_value=0):
                    self.call(answers.get(feature, []), run, game, feature)
                    if feature == 48:
                        self.p["region"] = state(self.p)["field"]["escort"][
                            "destination"
                        ]
                        self.p["wander_count"] = 1
                        self.call([], run, game, 48)
                if feature != 58:
                    self.assertIn(str(feature), state(self.p)["features"])
                self.assertTrue(validate_original_save(ui.snapshot()))

    def test_mercy_records_a_spared_enemy_instead_of_a_kill(self):
        before = deepcopy(self.p["kill_counts"])
        enemy = dict(
            name="Surrendering Raider",
            hp=10,
            max_hp=100,
            atk=2,
            **{"def": 0},
            intelligent=True
        )
        self.assertTrue(self.call(["9"], expansion_combat.encounter, game, [enemy]))
        self.assertIn(
            "Surrendering Raider", state(self.p)["relationships"]["spared_enemies"]
        )
        self.assertEqual(self.p["kill_counts"], before)
        self.assertIn("58", state(self.p)["features"])

    def test_potion_blends_are_consumed_once_and_cannot_be_blended_recursively(self):
        self.p["potions"] = ["Health Potion", "Health Potion"]
        self.p["hp"] = 20
        self.call(["1", "1", "1"], food_addons.mix_potions, game)
        self.assertEqual(len(self.p["potions"]), 1)
        name = self.p["potions"][0]
        self.assertEqual(food_addons.potion_effect(self.p, name), "blend")
        self.assertTrue(self.call(["1"], food_addons.use_potion, game))
        self.assertEqual(self.p["hp"], 120)
        self.assertEqual(self.p["potions"], [])

    def test_ngplus_is_a_fresh_character_with_a_chronicle_and_harder_enemies(self):
        from legacy_systems import menu

        with patch.object(game, "visit_village"), patch(
            "builtins.input", return_value="yes"
        ), patch("builtins.print"):
            menu(game, "ngplus")
        self.assertEqual([w["name"] for w in self.p["weapons"]], ["Rusty Sword"])
        self.assertEqual(self.p["runes"], [])
        self.assertEqual(self.p["unlocked_regions"], {"Whispering Woods"})
        self.assertEqual(self.p["bosses_defeated"], [])
        self.assertTrue(state(self.p)["chronicles"])
        self.assertEqual(state(self.p)["systems"]["ngplus"], 1)
        from expansion_hooks import scale_enemy

        enemy = scale_enemy(self.p, dict(name="Test", hp=20, atk=10))
        self.assertEqual(enemy["hp"], 30)
        self.assertEqual(enemy["atk"], 15)

    def test_legacy_rewards_cosmetics_faction_contracts_rituals_and_stocks(self):
        from legacy_systems import menu, systems, ritual_bonus

        self.p["cosmetics"] = {"currency": 1000}
        self.call(["2"], menu, game, "cosmetics")
        self.assertEqual(
            systems(self.p)["equipped_cosmetics"]["character_skins"], "dark_knight"
        )
        self.assertEqual(self.p["cosmetics"]["currency"], 900)
        systems(self.p)["battle_xp"] = 100
        gold = self.p["gold"]
        self.call(["1"], menu, game, "battle_pass")
        self.assertEqual(self.p["gold"], gold + 50)
        self.call(["1"], menu, game, "battle_pass")
        self.assertEqual(self.p["gold"], gold + 50)
        self.call(["1"], menu, game, "factions")
        self.assertEqual(self.p["faction"], "crimson_order")
        self.call(["1"], menu, game, "factions")
        self.p["wander_count"] = 3
        self.call(["1"], menu, game, "factions")
        self.assertEqual(systems(self.p)["faction_progress"]["reputation"], 1)
        self.call(["2"], menu, game, "factions")
        potions = len(self.p["potions"])
        self.call(["2"], menu, game, "factions")
        self.assertEqual(len(self.p["potions"]), potions)
        self.call(["1"], menu, game, "rituals")
        self.assertEqual(ritual_bonus(self.p, "atk"), 3)
        from expansion_hooks import finish_battle

        self.call([], finish_battle, self.p, True)
        self.assertEqual(systems(self.p)["ritual"]["remaining"], 4)
        self.call(["1"], menu, game, "town")
        self.assertEqual(systems(self.p)["town"]["tavern"], 1)
        gold = self.p["gold"]
        self.call(["5"], menu, game, "town")
        self.assertEqual(self.p["gold"], gold + 40)
        self.call(["5"], menu, game, "town")
        self.assertEqual(self.p["gold"], gold + 40)
        self.call(["1"], menu, game, "mounts")
        self.assertIn(systems(self.p)["mount"], self.p["mounts"])
        self.call(["1"], menu, game, "treasure")
        item = systems(self.p)["treasure_maps"][0]
        self.p["region"] = item["region"]
        self.p["wander_count"] += 1
        gold = self.p["gold"]
        self.call(["2", "1"], menu, game, "treasure")
        self.assertEqual(self.p["gold"], gold + 90)
        self.call(["1"], menu, game, "treasure")
        item = systems(self.p)["treasure_maps"][0]
        item["region"] = self.p["region"]
        self.p["wander_count"] += 1
        gold = self.p["gold"]
        self.call(["2", "1"], menu, game, "treasure")
        self.assertEqual(self.p["gold"], gold)
        self.assertTrue(validate_original_save(ui.snapshot()))

    def test_shared_guild_join_upgrade_and_ghost_registration(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "community.sqlite3"
            visitor = initial_player({"name": "Guild member", "cls": "warrior"})
            visitor["gold"] = 200
            self.assertTrue(community_store.create_guild(self.p, "Wayfinders", path)[0])
            row = community_store.guilds(path)[0]
            self.assertTrue(community_store.join_guild(visitor, row["id"], path)[0])
            self.assertEqual(community_store.guild_level(visitor, path=path), 1)
            self.assertEqual(community_store.guild_level(visitor, True, path), 2)
            self.assertEqual(community_store.guild_level(self.p, path=path), 2)
            self.assertEqual(visitor["gold"], 100)
            community_store.register(self.p, path)
            rows = community_store.ghosts(visitor, path)
            self.assertEqual(rows[0]["name"], self.p["name"])
            self.assertNotIn("password_hash", rows[0])
            self.assertEqual(community_store.ghosts(self.p, path), [])

    def test_budget_batch_failure_is_atomic_and_discount_quote_is_exact(self):
        from legacy_systems import systems

        systems(self.p)["town"] = {"market": 3}
        state(self.p)["projects"][self.forge["id"]] = {"roads": True}
        state(self.p)["professions"]["apprentice"] = 2
        fee = jobs.order_fee(self.p, self.forge, "weapon")
        self.p["gold"] = fee * 2
        before = len(self.p["metals"])
        self.assertTrue(jobs.batch(self.p, self.forge, "weapon", ["Iron"], 2)[0])
        self.assertEqual(self.p["gold"], 0)
        self.assertEqual(len(self.p["metals"]), before - 2)
        jobs.advance(self.p, self.forge, 10)
        self.p["gold"] = 1000
        systems(self.p)["mode"] = {"id": "budget_run"}
        before = deepcopy(self.p)
        self.assertFalse(jobs.batch(self.p, self.forge, "weapon", ["Iron"], 2)[0])
        self.assertEqual(self.p, before)

    def test_wards_rituals_and_permanent_paired_staff_have_real_combat_effects(self):
        from original_magic import strike

        enemy = dict(name="Caster", hp=100, atk=10, **{"def": 0})
        self.p["armour"] = {
            "name": "Ward",
            "element_resistance": 0.2,
            "damage_reduction": 0.1,
        }
        hp = self.p["hp"]
        with patch("effects.random.random", return_value=1):
            self.call([], strike, enemy, self.p, 20, True)
        self.assertEqual(hp - self.p["hp"], 14)
        from legacy_systems import systems

        systems(self.p)["ritual"] = {"bonus": {"def": 3}, "remaining": 3}
        hp = self.p["hp"]
        with patch("effects.random.random", return_value=1):
            self.call([], strike, enemy, self.p, 20, True)
        self.assertEqual(hp - self.p["hp"], 11)
        state(self.p)["season_three"]["stage"] = 5
        self.assertTrue(season_three.craft_pair(self.p, 1)[0])
        staff = self.p["staffs"][-1]
        enemy["hp"] = 100
        with patch.object(game, "choose_staff", return_value=staff), patch.object(
            game, "apply_rune_effect"
        ) as cast, patch("builtins.print"):
            game.use_staff(enemy)
            game.use_staff(enemy)
        self.assertEqual(cast.call_count, 4)
        self.assertIn("rune", staff)

    def test_interrupt_counterspell_and_village_defence_assignments(self):
        self.p["atk"] = 1
        self.p["weapon"] = {"name": "Training stick", "atk": 0}
        self.p["companions"] = []
        state(self.p)["magic"]["counterspell"] = True
        enemy = dict(name="Charger", hp=300, atk=10, **{"def": 0})
        self.p["def"] = 0
        hp = self.p["hp"]
        mana = self.p["mana"]
        with patch("effects.random.random", return_value=1):
            self.call(["1", "1", "8", "0"], expansion_combat.encounter, game, [enemy])
        self.assertEqual(self.p["hp"], hp - 20)
        self.assertEqual(self.p["mana"], mana - 5)
        self.assertIn("66", state(self.p)["features"])
        from community_addons import defence, project

        with patch("expansion_combat.encounter", return_value=True) as battle:
            self.call(["1", "2", "3"], defence, game, self.v)
        self.assertTrue(battle.called)
        self.assertEqual(project(self.p, self.v)["defences_won"], 1)
        gold = self.p["gold"]
        self.call([], defence, game, self.v)
        self.assertEqual(self.p["gold"], gold)

    def test_material_records_track_new_gathering_without_inventing_old_origins(self):
        artisan_addons.record_materials(self.p)
        self.p["region"] = "Sunken Coast"
        self.p["metals"].append("Iron")
        artisan_addons.record_materials(self.p)
        item = dict(
            name="Coastal blade",
            atk=10,
            materials={"metal": "Iron", "wood": "Oak Wood"},
        )
        artisan_addons.apply_traits(self.p, item, "smithing")
        self.assertEqual(item["material_origins"]["Iron"], ["Sunken Coast"])
        self.assertIn("unknown", item["material_origins"]["Oak Wood"][0])
        self.assertEqual(
            validate_original_save(ui.snapshot())["player"]["weapons"][0]["name"],
            "Rusty Sword",
        )

    def test_daily_and_pass_materials_convert_once_into_usable_supplies(self):
        from legacy_systems import menu, systems

        daily_rewards.claim(self.p, date(2026, 10, 18))
        before = self.p["building_materials"]["Iron fittings"]
        self.call(["1"], menu, game, "recipes")
        self.assertEqual(self.p["building_materials"]["Iron fittings"], before + 1)
        self.call(["1"], menu, game, "recipes")
        self.assertEqual(self.p["building_materials"]["Iron fittings"], before + 1)
        systems(self.p)["pass_materials"] = {"essence_dust": 1}
        before = self.p["ingredients"].count("Dew Blossom")
        self.call(["2"], menu, game, "recipes")
        self.assertEqual(self.p["ingredients"].count("Dew Blossom"), before + 1)

    def test_mercy_visitor_returns_after_scouting_and_can_join_the_watch(self):
        enemy = dict(
            name="Returning Raider",
            hp=10,
            max_hp=100,
            atk=2,
            **{"def": 0},
            intelligent=True
        )
        self.assertTrue(self.call(["9"], expansion_combat.encounter, game, [enemy]))
        self.call([], run, game, 58)
        self.p["wander_count"] += 2
        self.call(["1"], run, game, 58)
        visitor = state(self.p)["relationships"]["mercy_visitors"]["Returning Raider"]
        self.assertTrue(visitor["returned"])
        from community_addons import project

        self.assertEqual(project(self.p, self.v)["watch_training"], 1)
        self.call([], run, game, 58)
        self.assertEqual(project(self.p, self.v)["watch_training"], 1)

    def test_tactical_armour_and_native_stun_apply_before_enemy_damage(self):
        self.p["atk"] = 1
        self.p["weapon"] = {"name": "Stick", "atk": 0}
        self.p["companions"] = []
        self.p["def"] = 0
        self.p["armour"] = {"name": "Shielded coat", "def": 7}
        hp = self.p["hp"]
        self.p["active_buffs"]["stun"] = 1
        enemy = dict(name="Raider", hp=100, atk=10, **{"def": 0})
        with patch("effects.random.random", return_value=1):
            self.call(["1", "0"], expansion_combat.encounter, game, [enemy])
        self.assertEqual(self.p["hp"], hp - 3)
        replay = state(self.p)["activities"]["battle_replays"][-1]
        self.assertEqual(replay["turns"][0]["action"], "disabled")
        self.assertEqual(replay["turns"][0]["enemies"][0]["hp"], 100)

    def test_advanced_skills_charge_exact_cost_once_and_apply_real_hp_speed_fields(
        self,
    ):
        from legacy_workshops import learn

        self.p["skill_points"] = 10
        entry = data.SKILL_TREES["warrior"]["skills"]["final_stand"]
        hp = self.p["max_hp"]
        self.assertTrue(learn(self.p, "warrior", "final_stand")[0])
        self.assertEqual(self.p["skill_points"], 10 - entry["cost"])
        self.assertEqual(self.p["max_hp"], hp + entry["bonus"])
        before = deepcopy(self.p)
        self.assertFalse(learn(self.p, "warrior", "final_stand")[0])
        self.assertEqual(self.p, before)
        speed_skill = next(
            (tree, name, info)
            for tree, t in data.SKILL_TREES.items()
            for name, info in t["skills"].items()
            if info["stat"] == "spd"
        )
        speed = self.p["speed"]
        self.assertTrue(learn(self.p, *speed_skill[:2])[0])
        self.assertEqual(self.p["speed"], speed + speed_skill[2]["bonus"])
        self.assertNotIn("spd", self.p)

    def test_collection_sets_and_legacy_crafting_rewards_are_finite(self):
        from legacy_workshops import sync_sets, collections

        self.p["weapons"] = [
            dict(name=name, atk=10)
            for name in data.EQUIPMENT_SETS["Crimson Knight"]["pieces"]
        ]
        base = self.p["atk"]
        sync_sets(self.p)
        self.assertEqual(self.p["atk"], base + 10)
        sync_sets(self.p)
        self.assertEqual(self.p["atk"], base + 10)
        self.p["weapons"].clear()
        sync_sets(self.p)
        self.assertEqual(self.p["atk"], base)
        ui.village = self.forge
        self.call(["4", "yes", "0"], collections, game)
        self.assertEqual(self.p["weapons"][-1]["name"], "Blade of the Abyss")
        count = len(self.p["weapons"])
        self.call(["4", "0"], collections, game)
        self.assertEqual(len(self.p["weapons"]), count)
        self.call(["6", "1", "0"], collections, game)
        self.assertIn("crown_of_kings", self.p["artifacts"])
        atk = self.p["atk"]
        self.call(["6", "1", "0"], collections, game)
        self.assertEqual(self.p["atk"], atk)
        self.p["prestige_level"] = 1
        self.call(["5", "1", "0"], collections, game)
        stock = self.p["metals"].count("Titanium")
        self.call(["5", "1", "0"], collections, game)
        self.assertEqual(self.p["metals"].count("Titanium"), stock)
        self.assertTrue(validate_original_save(ui.snapshot()))

    def test_prestige_resets_supplies_and_regions_without_the_original_list_keys_crash(
        self,
    ):
        from legacy_workshops import ascend

        ui.village = None
        with patch.object(game, "visit_village") as visit:
            self.assertTrue(self.call([], ascend, game))
        visit.assert_called_once()
        self.assertEqual(self.p["prestige_level"], 1)
        self.assertEqual(self.p["region"], "Whispering Woods")
        self.assertEqual(self.p["unlocked_regions"], {"Whispering Woods"})
        self.assertEqual(self.p["runes"], [])
        self.assertEqual([x["name"] for x in self.p["weapons"]], ["Rusty Sword"])
        self.assertTrue(state(self.p)["chronicles"])
        self.assertTrue(validate_original_save(ui.snapshot()))

    def test_daily_weekly_progress_is_event_driven_unique_and_calendar_reset(self):
        from challenge_progress import update, initialise

        with patch("challenge_progress.today", return_value=date(2026, 10, 18)):
            initialise(self.p)
            gold = self.p["gold"]
            self.call([], update, self.p, "kill_count", 10)
            self.assertEqual(self.p["gold"], gold + 100)
            self.call([], update, self.p, "kill_count", 0)
            self.assertEqual(self.p["gold"], gold + 100)
            self.call([], update, self.p, "region_boss_clear", "Whispering Woods")
            self.call([], update, self.p, "region_boss_clear", "Whispering Woods")
            self.assertEqual(self.p["weekly_challenges"]["weekly_1"]["progress"], 1)
            self.call([], update, self.p, "region_boss_clear", "Sunken Coast")
            self.call([], update, self.p, "region_boss_clear", "Ashen Wastes")
            self.assertTrue(self.p["weekly_challenges"]["weekly_1"]["completed"])
            self.assertEqual(self.p["gold"], gold + 600)
        with patch("challenge_progress.today", return_value=date(2026, 10, 19)):
            initialise(self.p)
            self.assertFalse(self.p["daily_challenges"]["daily_1"]["completed"])
            self.assertFalse(self.p["weekly_challenges"]["weekly_1"]["completed"])
        self.assertTrue(validate_original_save(ui.snapshot()))

    def test_boss_rush_runs_real_encounters_updates_records_and_limits_attempts(self):
        from legacy_workshops import boss_rush

        with patch("expansion_combat.encounter", return_value=True) as fight:
            self.call(["1", "y", "y", "y", "y"], boss_rush, game)
        self.assertEqual(fight.call_count, 5)
        self.assertEqual(self.p["boss_rush_stats"]["best_run_normal"], 5)
        self.assertTrue(
            all(isinstance(call.args[1][0], dict) for call in fight.call_args_list)
        )
        with patch("expansion_combat.encounter") as fight:
            self.call(["1"], boss_rush, game)
        fight.assert_not_called()
