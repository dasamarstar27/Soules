import unittest
from copy import deepcopy
from unittest.mock import patch
from inventory_tools import sell_duplicates, sort_items, inventory_menu
from original_worker import initial_player
import original_game as game


class InventoryTests(unittest.TestCase):
    def test_duplicate_sales_keep_equipped_and_variants(self):
        p = initial_player({"name": "Test", "cls": "warrior"})
        equipped = p["weapon"]
        spare = deepcopy(equipped)
        upgraded = dict(equipped, atk=10)
        bound = dict(equipped, rune={"name": "Flame Rune"})
        p["weapons"] = [spare, equipped, upgraded, bound, deepcopy(bound)]
        p["runes"] = [{"name": "Flame Rune"}] * 2
        p["inventory"] = [{"name": "Scroll", "turns": 3, "value": 5}] * 2
        gold = p["gold"]
        with patch("builtins.print"):
            sold, earned = sell_duplicates(p)
        self.assertEqual(sold, 1)
        self.assertEqual(earned, 25)
        self.assertEqual(p["gold"], gold + 25)
        self.assertTrue(any(x is equipped for x in p["weapons"]))
        self.assertEqual(len(p["weapons"]), 4)
        self.assertEqual(len(p["runes"]), 2)
        self.assertEqual(len(p["inventory"]), 2)
        with patch("builtins.print"):
            self.assertEqual(sell_duplicates(p), (0, 0))

    def test_older_repeated_object_references(self):
        p = initial_player({"name": "Test", "cls": "warrior"})
        weapon = {"name": "Spare", "atk": 4}
        p["weapons"] += [weapon, weapon, weapon]
        with patch("builtins.print"):
            self.assertEqual(sell_duplicates(p), (2, 40))
        self.assertEqual(len(p["weapons"]), 2)

    def test_sorting_and_secondary_sort_preserve_bags(self):
        items = [
            {"name": "C", "element": "fire", "atk": 3},
            {"name": "B", "element": "ice", "atk": 9},
            {"name": "A", "element": "fire", "atk": 7},
        ]
        self.assertEqual([x["name"] for x in sort_items(items, "element", "atk")], ["A", "C", "B"])
        self.assertEqual(
            [x["name"] for x in sort_items(items, "value", kind="weapons")], ["B", "A", "C"]
        )
        self.assertEqual([x["name"] for x in items], ["C", "B", "A"])

    def test_scroll_attack_defence_sort(self):
        items = [
            {"name": "Guard", "effect": "def_up", "value": 12, "turns": 3},
            {"name": "Might", "effect": "atk_up", "value": 5, "turns": 3},
        ]
        self.assertEqual(sort_items(items, "atk")[0]["name"], "Might")
        self.assertEqual(sort_items(items, "def")[0]["name"], "Guard")

    def test_elemental_and_massive_buff_scroll_sorting(self):
        from inventory_tools import item_element, item_stat

        scroll = {"name": "Flame", "effect": "fire_weapon", "value": 8, "turns": 4}
        self.assertEqual(item_element(scroll), "fire")
        self.assertEqual(item_stat(scroll, "atk"), 8)
        self.assertEqual(
            item_stat({"effect": "massive_def_up", "value": 15, "turns": 5}, "def"), 15
        )

    def test_favourites_survive_autosell(self):
        p = initial_player({"name": "Test", "cls": "warrior"})
        p["weapons"] += [{"name": "Favourite Blade", "atk": 12} for _ in range(2)]
        p["inventory_favourites"] = ["Favourite Blade"]
        with patch("builtins.print"):
            self.assertEqual(sell_duplicates(p), (0, 0))
        self.assertEqual(len(p["weapons"]), 3)

    def test_search_quantities_and_favourite_menu(self):
        p = initial_player({"name": "Test", "cls": "warrior"})
        p["runes"] = [{"name": "Flame Rune", "element": "fire", "effect": "burn"}] * 2
        original = game.player
        game.player = p
        try:
            with patch("builtins.input", side_effect=["8", "flame rune", "9", "fire", "0"]), patch(
                "builtins.print"
            ) as output:
                inventory_menu(game)
            lines = "\n".join(" ".join(map(str, call.args)) for call in output.call_args_list)
            self.assertIn("Flame Rune ×2", lines)
            self.assertIn("Flame Rune", p["inventory_favourites"])
            self.assertEqual(p["inventory_search"], "fire")
        finally:
            game.player = original

    def test_crafting_choices_are_printed_in_journal(self):
        with patch("builtins.input", return_value="0"), patch("builtins.print") as output:
            game.perform_original_action("3")
        text = " ".join(str(arg) for call in output.call_args_list for arg in call.args)
        self.assertIn("1. Blacksmith", text)
        self.assertIn("4. Fuse runes", text)

    def test_inventory_preferences_and_toggle(self):
        p = initial_player({"name": "Test", "cls": "warrior"})
        self.assertFalse(p.get("auto_sell_duplicates", False))
        original = game.player
        game.player = p
        try:
            with patch("builtins.input", side_effect=["4", "2", "6", "0"]), patch("builtins.print"):
                inventory_menu(game)
            self.assertEqual(p["inventory_sort"], "element")
            self.assertEqual(p["inventory_sort_secondary"], "atk")
            self.assertTrue(p["auto_sell_duplicates"])
        finally:
            game.player = original
