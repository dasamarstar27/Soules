"""Finite work sites award both regional craft and construction resources."""

from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import data
import resource_sites as sites
import world_sites
import regional_forges


class ResourceSiteTests(TestCase):
    def test_every_region_yields_native_craft_and_building_supplies(self):
        for region in data.REGIONS + [data.SECRET_REGION]:
            for kind, bag, building, catalog in (
                ("quarry", "metals", "Stone", sites.REGIONAL_METALS),
                ("lumberyard", "woods", "Timber", sites.REGIONAL_WOODS),
            ):
                with self.subTest(region=region, kind=kind), redirect_stdout(
                    StringIO()
                ):
                    p = {}
                    site = dict(name=region + kind, type=kind)
                    self.assertTrue(sites.gather(p, site, region))
                    self.assertEqual(p["building_materials"], {building: 2})
                    self.assertEqual(p[bag], [catalog[region]])
                    self.assertIn(
                        catalog[region], data.METALS if kind == "quarry" else data.WOODS
                    )
                    self.assertFalse(sites.gather(p, site, region))
                    self.assertEqual(len(p[bag]), 1)
                    p["wander_count"] = 20
                    self.assertTrue(sites.gather(p, site, region))
                    self.assertEqual(len(p[bag]), 2)
                    self.assertEqual(p["building_materials"][building], 4)

    def test_site_menu_leave_and_gather(self):
        game = SimpleNamespace(player={})
        site = dict(name="Timber yard", type="lumberyard")
        with patch("builtins.input", return_value="0"), redirect_stdout(StringIO()):
            world_sites.visit(game, site, "Whispering Woods")
        self.assertEqual(game.player, {})
        with patch("builtins.input", return_value="1"), redirect_stdout(
            StringIO()
        ) as out:
            world_sites.visit(game, site, "Whispering Woods")
        self.assertEqual(game.player["woods"], ["Oak"])
        self.assertIn("2 Timber + 1 Oak", out.getvalue())

    def test_dwarven_menu_uses_same_finite_quarry_yield(self):
        game = SimpleNamespace(player={})
        site = dict(name="Ironpeak Mountains Quarry", type="quarry")
        with patch("regional_forges.choose", side_effect=[0, 0, None]), redirect_stdout(
            StringIO()
        ):
            regional_forges.dwarven_quarry(game, site)
        self.assertEqual(game.player["metals"], ["Titanium"])
        self.assertEqual(game.player["building_materials"], {"Stone": 2})

    def test_sites_have_independent_quotas(self):
        p = {}
        with redirect_stdout(StringIO()):
            for name in ("North quarry", "South quarry"):
                self.assertTrue(
                    sites.gather(p, dict(name=name, type="quarry"), "Whispering Woods")
                )
        self.assertEqual(p["metals"], ["Iron", "Iron"])
