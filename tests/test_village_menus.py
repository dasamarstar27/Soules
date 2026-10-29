from unittest import TestCase
from unittest.mock import patch
from village_life import profile
from village_menus import choose, groups


class VillageMenuTests(TestCase):
    def test_short_categories_keep_all_available_actions(self):
        from village_life import village_options

        for region, name in [
            ("Whispering Woods", "Old Village"),
            ("Crimson Depths", "Smiths' Quarter"),
        ]:
            v = profile(region, name)
            self.assertLessEqual(len(groups(v)), 6)
            flattened = {key for _, rows in groups(v) for key, _ in rows}
            self.assertEqual(flattened, {k for k, _ in village_options(v)} - {7})

    def test_root_category_secondary_choice_and_back(self):
        v = profile("Whispering Woods", "Old Village")
        with patch("builtins.input", side_effect=["1", "4"]), patch("builtins.print"):
            self.assertEqual(choose(v), ("4", 0))
        with patch("builtins.input", side_effect=["0", "7"]), patch("builtins.print"):
            self.assertEqual(choose(v, 0), ("7", None))

    def test_sidebar_shortcuts_do_not_change_categories(self):
        v = profile("Whispering Woods", "Old Village")
        with patch("builtins.input", return_value="v:17"), patch("builtins.print"):
            self.assertEqual(choose(v, 1), ("17", 1))
        with patch("builtins.input", side_effect=["v:9", "7"]), patch("builtins.print"):
            self.assertEqual(choose(v), ("7", None))
