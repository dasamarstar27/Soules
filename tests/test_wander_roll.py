"""Exact one-roll weights, boundary coverage, and exclusive reward dispatch."""

from collections import Counter
from copy import deepcopy
from unittest import TestCase
from unittest.mock import Mock, patch
import data
import original_game as game
from original_worker import initial_player
from wander_roll import CHANCES, TOTAL, pick, resolve, ticket_table
from wander_reference import probabilities


class OneRollWanderTests(TestCase):
    def test_exact_primary_weights_and_all_boundary_tickets(self):
        for mode in CHANCES:
            p = initial_player({"difficulty": mode})
            table = ticket_table(p["region"], difficulty=mode)
            primary = Counter()
            cursor = 0
            for key, count in table:
                group = (
                    "special_event"
                    if key.startswith("event:")
                    else (
                        "monster"
                        if key == "bounty"
                        else (
                            "gather"
                            if key in ("ingredient", "building_supply")
                            else "structure" if key == "elemental_village" else key
                        )
                    )
                )
                primary[group] += count
                for ticket in (cursor, cursor + count - 1):
                    rng = Mock()
                    rng.randrange.return_value = ticket
                    self.assertEqual(pick(p, rng), key, (mode, ticket))
                    rng.randrange.assert_called_once_with(TOTAL)
                    rng.random.assert_not_called()
                    rng.randint.assert_not_called()
                cursor += count
            self.assertEqual(cursor, TOTAL)
            self.assertEqual(
                dict(primary),
                {key: chance * TOTAL // 100 for key, chance in CHANCES[mode].items()},
            )

    def test_all_regions_progress_states_and_difficulties_keep_exact_total(self):
        for mode in CHANCES:
            for region in data.REGIONS + [data.SECRET_REGION]:
                for undiscovered in (True, False):
                    for bounty in (True, False):
                        table = ticket_table(region, undiscovered, bounty, mode)
                        self.assertEqual(sum(n for _, n in table), TOTAL)
                        self.assertTrue(all(n > 0 for _, n in table))
                        odds = probabilities(region, undiscovered, bounty, mode)
                        self.assertAlmostEqual(sum(odds.values()), 1)
                        if not undiscovered:
                            self.assertEqual(odds["structure"], 0)
                        if not bounty:
                            self.assertEqual(odds["bounty"], 0)
                        self.assertAlmostEqual(
                            odds["monster"] + odds["bounty"],
                            CHANCES[mode]["monster"] / 100,
                        )

    def test_event_weights_and_rare_subtypes_are_in_the_main_table(self):
        for mode in CHANCES:
            table = dict(ticket_table("Whispering Woods", difficulty=mode))
            event_total = sum(e["weight"] for e in data.WANDER_EVENTS)
            for event in data.WANDER_EVENTS:
                self.assertEqual(
                    table["event:" + event["id"]],
                    CHANCES[mode]["special_event"]
                    * TOTAL
                    // 100
                    * event["weight"]
                    // event_total,
                )
            odds = probabilities("Whispering Woods", difficulty=mode)
            self.assertAlmostEqual(
                odds["elemental_village"], CHANCES[mode]["structure"] / 10000
            )
            self.assertAlmostEqual(odds["bounty"], CHANCES[mode]["monster"] * 0.0002)

    def test_gathering_and_quiet_do_not_stack_rewards_or_encounters(self):
        previous = game.player
        try:
            for outcome in ("ingredient", "building_supply", "peaceful"):
                game.player = initial_player({})
                with patch("wander_roll.pick", return_value=outcome), patch.object(
                    game.random, "choice", side_effect=lambda pool: pool[0]
                ), patch("builtins.print"), patch.object(
                    game, "fight"
                ) as fight, patch.object(
                    game, "merchant"
                ) as merchant, patch.object(
                    game, "visit_elemental_village"
                ) as clan:
                    resolve(game)
                self.assertEqual(
                    len(game.player["ingredients"]), int(outcome == "ingredient")
                )
                self.assertEqual(
                    sum(game.player.get("building_materials", {}).values()),
                    int(outcome == "building_supply"),
                )
                self.assertEqual(game.player["weapons"][0]["name"], "Rusty Sword")
                fight.assert_not_called()
                merchant.assert_not_called()
                clan.assert_not_called()
        finally:
            game.player = previous

    def test_each_event_dispatches_once_without_a_second_event_selection(self):
        previous = game.player
        try:
            game.player = initial_player({})
            for event in data.WANDER_EVENTS:
                with patch(
                    "wander_roll.pick", return_value="event:" + event["id"]
                ), patch.object(game, "_handle_wander_event") as handler, patch.object(
                    game, "_check_achievements"
                ), patch.object(
                    game.random, "random"
                ) as extra, patch(
                    "builtins.print"
                ):
                    resolve(game)
                handler.assert_called_once_with(event["id"], game.player["region"])
                extra.assert_not_called()
        finally:
            game.player = previous
