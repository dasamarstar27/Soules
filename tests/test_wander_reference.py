from unittest import TestCase
from unittest.mock import patch
from copy import deepcopy
import data
import wander_reference as reference
import original_game as game
from original_worker import initial_player
from app import app


class WanderReferenceTests(TestCase):
    def test_sequential_probabilities_sum_to_one_for_every_region_and_progress_state(
        self,
    ):
        for region in data.REGIONS + [data.SECRET_REGION]:
            for undiscovered in (False, True):
                for bounty in (False, True):
                    odds = reference.probabilities(region, undiscovered, bounty)
                    self.assertAlmostEqual(sum(odds.values()), 1)
                    self.assertTrue(all(0 <= value <= 1 for value in odds.values()))
                    if not undiscovered:
                        self.assertEqual(odds["structure"], 0)
                    if not bounty:
                        self.assertEqual(odds["bounty"], 0)
                    if region not in data.ELEMENTAL_VILLAGES:
                        self.assertEqual(odds["elemental_village"], 0)
        woods = reference.probabilities("Whispering Woods")
        self.assertAlmostEqual(woods["structure"], 0.2 * 0.12)
        self.assertAlmostEqual(woods["elemental_village"], 0.2 * 0.88 * 0.01)
        self.assertAlmostEqual(woods["monster"], 0.80)

    def test_reference_covers_every_weather_world_event_and_special_event(self):
        ref = reference.reference()
        self.assertEqual({x["name"] for x in ref["weather"]}, set(data.WEATHER_EFFECTS))
        self.assertEqual(
            {x["name"] for x in ref["world"]}, {x["name"] for x in data.WORLD_EVENTS}
        )
        names = {x["name"] for x in ref["wandering"]}
        self.assertTrue(all(x["title"] in names for x in data.WANDER_EVENTS))
        self.assertTrue(
            all(region in names for region in data.REGIONS + [data.SECRET_REGION])
        )
        self.assertAlmostEqual(reference.WEATHER_RESELECT * 5 / 6, 1 / 6)
        text = str(ref)
        self.assertNotIn("DAMAR", text)
        self.assertNotIn("SAMAR", text)

    def test_catalog_exposes_searchable_reference(self):
        response = app.test_client().get("/api/original/catalog")
        self.assertEqual(response.status_code, 200)
        ref = response.get_json()["content"]["exploration"]
        self.assertEqual(len(ref["weather"]), 6)
        self.assertIn("1:1", ref["regions"]["Whispering Woods"]["scenarios"])

    def test_engine_uses_shared_thresholds_without_adding_new_rolls(self):
        old = game.player
        game.player = initial_player({"name": "Wander reference", "cls": "warrior"})
        try:
            with patch.multiple(
                reference,
                WEATHER_RESELECT=0,
                BUILDING_SUPPLY=0,
                STRUCTURE=0,
                INGREDIENT=0,
                ELEMENTAL_VILLAGE=0,
                BOUNTY=0,
                SPECIAL_EVENT=0,
            ), patch.object(game.random, "random", return_value=0.99), patch.object(
                game.random, "randint", return_value=99
            ), patch(
                "builtins.print"
            ) as output, patch.object(
                game, "fight"
            ) as fight, patch.object(
                game, "visit_elemental_village"
            ) as clan:
                game.explore()
                self.assertTrue(
                    any(
                        "Peaceful wandering" in str(call)
                        for call in output.call_args_list
                    )
                )
                fight.assert_not_called()
                clan.assert_not_called()
                self.assertEqual(game.player["ingredients"], [])
        finally:
            game.player = old
