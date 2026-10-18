from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import data
from item_reference import reference, item_odds
from core_charging import compatible, charge, FUSION_ENERGIES
from rune_pairs import fusion, BASE
from original_worker import initial_player
import original_game as game
import original_ui as ui


class ExtensiveDictionaryTests(TestCase):
    def test_all_catalogues_and_each_named_item_are_indexed(self):
        ref = reference()
        tables = {
            key
            for key, value in vars(data).items()
            if key.isupper() and isinstance(value, (list, dict)) and value
        }
        self.assertFalse(tables - {entry["source"] for entry in ref["entries"]})
        self.assertGreater(ref["count"], 1900)
        for table in (
            "WEAPONS",
            "ARMOURS",
            "STAFFS",
            "RUNES",
            "FOOD_ITEMS",
            "LOOT_ITEMS",
            "SCROLLS",
            "COMPANIONS",
        ):
            names = {
                entry["name"] for entry in ref["entries"] if entry["source"] == table
            }
            self.assertFalse(
                {
                    item["name"]
                    for item in (
                        [
                            item
                            for pool in getattr(data, table).values()
                            for item in pool
                        ]
                        if isinstance(getattr(data, table), dict)
                        else getattr(data, table)
                    )
                }
                - names,
                table,
            )
        self.assertEqual(sum(e["source"] == "ADDONS" for e in ref["entries"]), 100)
        self.assertEqual(
            sum(e["source"] == "VILLAGE_PROJECTS" for e in ref["entries"]), 100
        )

    def test_item_odds_follow_actual_level_and_regional_pools(self):
        pearl = next(x for x in data.LOOT_ITEMS if x["name"] == "Sea Pearl")
        line = item_odds("LOOT_ITEMS", pearl, ())
        pool = [
            x
            for x in data.LOOT_ITEMS
            if not x.get("regions") or "Sunken Coast" in x["regions"]
        ]
        self.assertIn(f"{60/len(pool):.4g}%", line)
        self.assertNotIn("Whispering Woods:", line)
        blade = data.WEAPONS[0]
        line = item_odds("WEAPONS", blade, ())
        eligible = sum(x["tier"] == "basic" for x in data.WEAPONS)
        self.assertIn(f"levels 1–4: {10/eligible:.4g}%", line)
        self.assertIn("levels 15+: unavailable", line)
        self.assertIn(
            "No independent item rarity", item_odds("METALS", data.METALS["Iron"], ())
        )

    def test_catalog_api_serializes_extensive_reference_and_core_limits(self):
        from app import app

        response = app.test_client().get("/api/original/catalog")
        self.assertEqual(response.status_code, 200)
        entries = response.json["content"]["encyclopedia"]["entries"]
        phoenix = next(
            e for e in entries if e["name"] == "Phoenix Core" and e["source"] == "CORES"
        )
        self.assertIn("Fusion requires BOTH", phoenix["description"])
        self.assertIn(
            "Starting services:",
            next(e for e in entries if e["name"] == "Old Village")["description"],
        )
        self.assertEqual(len(response.json["content"]["runes"]), 132)
        preview = (
            app.test_client()
            .get("/api/original/fusion?first=Flame%20Rune&second=Magma%20Rune")
            .json
        )
        self.assertIn("Phoenix Core", preview["compatible_cores"])
        mixed = (
            app.test_client()
            .get("/api/original/fusion?first=Flame%20Rune&second=Water%20Rune")
            .json
        )
        self.assertNotIn("Phoenix Core", mixed["compatible_cores"])


class FusionCoreTests(TestCase):
    def test_only_matching_canonical_fusions_charge_and_rejections_keep_supplies(self):
        valid = fusion(BASE["Flame Rune"], BASE["Magma Rune"])
        mixed = fusion(BASE["Flame Rune"], BASE["Water Rune"])
        self.assertTrue(compatible("Phoenix Core", valid))
        self.assertFalse(compatible("Phoenix Core", mixed))
        self.assertFalse(compatible("Ocean Core", valid))
        self.assertEqual(set(FUSION_ENERGIES), set(data.CORES))
        p = initial_player({"name": "Fusion test", "cls": "warrior"})
        p["cores"] = ["Phoenix Core"]
        p["runes"] = [mixed]
        before = deepcopy(p)
        self.assertFalse(charge(p, "Phoenix Core", 0)[0])
        self.assertEqual(p, before)
        forged = deepcopy(valid)
        forged["inputs"] = ["Flame Rune", "Flame Rune"]
        self.assertFalse(compatible("Phoenix Core", forged))
        self.assertFalse(
            compatible(
                "Phoenix Core", dict(effect="fusion", inputs=["unknown", "unknown"])
            )
        )
        p["runes"] = [valid]
        self.assertTrue(charge(p, "Phoenix Core", 0)[0])
        self.assertEqual(p["cores"], [])
        self.assertEqual(p["runes"], [])
        self.assertEqual(p["charged_cores"][0]["rune"], valid)

    def test_fused_core_weapon_keeps_all_real_abilities_after_save(self):
        from regional_forges import craft, forge_state
        from original_sessions import validate_original_save

        old = game.player
        old_ui = ui.get_ui()
        try:
            p = initial_player({"name": "Fused weapon", "cls": "warrior"})
            game.player = p
            p["unlocked_regions"].add("Crimson Depths")
            ui.init_ui(p)
            p.update(
                region="Crimson Depths",
                metals=["Iron"],
                woods=["Oak"],
                cores=["Phoenix Core"],
                runes=[fusion(BASE["Flame Rune"], BASE["Magma Rune"])],
            )
            forge_state(p).update(waves=3, cleared=True)
            self.assertTrue(charge(p, "Phoenix Core", 0)[0])
            self.assertTrue(
                craft(p, p["charged_cores"][0], "Iron", "Oak", "Phoenix fusion")[0]
            )
            p["weapon"] = p["weapons"][-1]
            foe = dict(name="Target", hp=1000, max_hp=1000, atk=1, **{"def": 0})
            with patch("builtins.print"):
                game._apply_charged_weapon_effect(foe)
            self.assertIn("burn", foe["rune_status"])
            self.assertIn("magma", foe["rune_status"])
            key = p["weapon"]["forge_core_rune"]["pair_ability"]
            self.assertTrue(
                key in foe.get("rune_status", {}) or key in p.get("rune_status", {})
            )
            restored = validate_original_save(ui.snapshot())["player"]
            self.assertEqual(
                restored["weapons"][-1]["forge_core_rune"],
                p["weapon"]["forge_core_rune"],
            )
            self.assertEqual(p["runes"], [])
        finally:
            game.player = old
            ui._ui = old_ui

    def test_shared_prompt_and_community_rows_explain_input_and_costs(self):
        from expansion_state import choose
        from community_addons import INSTRUCTIONS

        with patch("builtins.input", return_value="1") as prompt, patch(
            "builtins.print"
        ) as output:
            self.assertEqual(choose("STOREHOUSE", ["Deposit", "Withdraw"]), 0)
            self.assertIn("Option number", prompt.call_args.args[0])
            self.assertIn("LEFT", str(output.call_args_list))
        self.assertEqual(set(INSTRUCTIONS), set(range(21, 31)))
        self.assertIn("30 souls", INSTRUCTIONS[22])
        self.assertIn("permanently consumed", INSTRUCTIONS[24])
