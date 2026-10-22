"""Exact primary weights and finite, reward-preserving gathering follow-ups."""

from collections import Counter
from unittest import TestCase
from unittest.mock import Mock, patch
import data
import original_game as game
from original_worker import initial_player
from wander_roll import CHANCES, TOTAL, pick, resolve, ticket_table, gathering_encounter
from wander_reference import probabilities, encounter_probabilities


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
                            (
                                CHANCES[mode]["monster"]
                                + (
                                    0
                                    if undiscovered
                                    else CHANCES[mode]["structure"]
                                    * (0.99 if region in data.ELEMENTAL_VILLAGES else 1)
                                )
                            )
                            / 100,
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

    def test_gathering_keeps_reward_then_dispatches_one_encounter(self):
        previous = game.player
        try:
            for outcome in ("ingredient", "building_supply"):
                for followup in ("monster", "structure"):
                    game.player = initial_player({})
                    with patch(
                        "wander_roll.pick", return_value=outcome
                    ) as primary, patch(
                        "wander_roll.gathering_encounter", return_value=followup
                    ) as follow, patch.object(
                        game.random, "choice", side_effect=lambda pool: pool[0]
                    ), patch(
                        "builtins.print"
                    ), patch.object(
                        game, "_wander_monster"
                    ) as monster, patch.object(
                        game, "_check_achievements"
                    ), patch.object(
                        game, "merchant"
                    ) as merchant, patch.object(
                        game, "visit_elemental_village"
                    ) as clan:
                        resolve(game)
                    primary.assert_called_once()
                    follow.assert_called_once()
                    self.assertEqual(
                        len(game.player["ingredients"]), int(outcome == "ingredient")
                    )
                    self.assertEqual(
                        sum(game.player.get("building_materials", {}).values()),
                        int(outcome == "building_supply"),
                    )
                    self.assertEqual(monster.call_count, int(followup == "monster"))
                    self.assertEqual(
                        sum(map(len, game.player["discovered_structures"].values())),
                        int(followup == "structure"),
                    )
                    self.assertEqual(game.player.get("wander_count", 0), 0)
                    merchant.assert_not_called()
                    clan.assert_not_called()
        finally:
            game.player = previous

    def test_real_wander_advances_survival_and_work_only_once(self):
        previous = game.player
        try:
            game.player = initial_player({})
            with patch("wander_roll.pick", return_value="ingredient"), patch(
                "wander_roll.gathering_encounter", return_value="monster"
            ), patch.object(game, "_wander_monster") as monster, patch.object(
                game.random, "random", return_value=0.99
            ), patch(
                "village_jobs.advance_all"
            ) as jobs, patch(
                "builtins.print"
            ):
                game.explore()
            self.assertEqual(game.player["wander_count"], 1)
            self.assertEqual(game.player["hunger"], 95)
            self.assertEqual(len(game.player["ingredients"]), 1)
            jobs.assert_called_once()
            monster.assert_called_once()
        finally:
            game.player = previous

    def test_followup_exact_70_30_split_and_exhausted_structures(self):
        p = initial_player({})
        rng = Mock()
        counts = Counter()
        for ticket in range(100):
            rng.randrange.return_value = ticket
            counts[gathering_encounter(p, rng)] += 1
        self.assertEqual(counts, {"monster": 70, "structure": 30})
        p["discovered_structures"][p["region"]] = [
            s["name"] for s in data.REGION_STRUCTURES[p["region"]]
        ]
        for ticket in range(100):
            rng.randrange.return_value = ticket
            self.assertEqual(gathering_encounter(p, rng), "monster")

    def test_final_encounters_account_for_item_followups(self):
        for mode, combat, structures in (("normal", 0.65, 0.16), ("easy", 0.57, 0.21)):
            for region in data.REGIONS + [data.SECRET_REGION]:
                for unknown in (False, True):
                    odds = encounter_probabilities(region, unknown, True, mode)
                    self.assertAlmostEqual(sum(odds.values()), 1)
                    self.assertAlmostEqual(odds["peaceful"], 0.03)
                    if unknown:
                        self.assertAlmostEqual(odds["monster"] + odds["bounty"], combat)
                        self.assertAlmostEqual(
                            odds["structure"] + odds["elemental_village"], structures
                        )
                    else:
                        self.assertEqual(odds["structure"], 0)

    def test_quiet_does_not_gather_or_reroll(self):
        previous = game.player
        try:
            game.player = initial_player({})
            with patch("wander_roll.pick", return_value="peaceful"), patch(
                "wander_roll.gathering_encounter"
            ) as follow, patch.object(game, "_wander_monster") as monster, patch(
                "builtins.print"
            ):
                resolve(game)
            self.assertEqual(game.player["ingredients"], [])
            self.assertFalse(game.player.get("building_materials"))
            follow.assert_not_called()
            monster.assert_not_called()
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
