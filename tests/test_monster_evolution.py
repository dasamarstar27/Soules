"""Evolution boundaries, level scaling, live damage/rewards and difficulty modifiers."""

from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import data
import original_game as game
import original_ui as ui
from original_worker import initial_player
from monster_evolution import (
    LEVELS,
    stage,
    form,
    pool,
    tracked,
    attack_range,
    reference_entries,
)
from expansion_hooks import scale_enemy

NEUTRAL = dict(
    name="Calm", icon="", enemy_hp_mod=1, enemy_atk_mod=1, xp_mod=1, gold_mod=1
)


class MonsterEvolutionTests(TestCase):
    def test_stage_boundaries_and_all_species_have_four_distinct_forms(self):
        for level, wanted in [
            (1, 0),
            (4, 0),
            (5, 1),
            (9, 1),
            (10, 2),
            (14, 2),
            (15, 3),
            (50, 3),
        ]:
            self.assertEqual(stage(level), wanted)
        count = 0
        for region, bases in data.NORMAL_MONSTERS.items():
            for index, base in enumerate(bases):
                forms = [form(region, index, level) for level in LEVELS]
                self.assertEqual(forms[0]["name"], base["name"])
                self.assertEqual(len({monster["name"] for monster in forms}), 4)
                for key in ("hp", "atk", "def"):
                    self.assertEqual(
                        sorted(monster[key] for monster in forms),
                        [monster[key] for monster in forms],
                    )
                count += 4
        self.assertEqual(len(reference_entries()), count)
        self.assertEqual(count, 120)

    def test_growth_inside_stages_and_after_fifteen_does_not_read_player_gear(self):
        for region, bases in data.NORMAL_MONSTERS.items():
            for index in range(len(bases)):
                previous = None
                for level in range(1, 31):
                    monster = form(region, index, level)
                    self.assertEqual(monster["hp"], monster["max_hp"])
                    if previous:
                        self.assertGreater(monster["hp"], previous["hp"])
                        self.assertGreaterEqual(monster["atk"], previous["atk"])
                        self.assertGreaterEqual(monster["def"], previous["def"])
                    previous = monster
        self.assertGreater(
            form("Whispering Woods", 0, 20)["hp"], form("Whispering Woods", 0, 15)["hp"]
        )

    def test_catalogues_stay_unchanged_and_encounters_are_independent(self):
        before = deepcopy(
            (data.NORMAL_MONSTERS, data.EVOLVED_MONSTERS, data.MINI_BOSSES)
        )
        enemy = form("Whispering Woods", 0, 10)
        enemy.setdefault("effects", []).append("test")
        self.assertNotIn("test", form("Whispering Woods", 0, 10).get("effects", []))
        for level in (1, 5, 10, 15, 20):
            pool("Whispering Woods", level)
        self.assertEqual(
            before, (data.NORMAL_MONSTERS, data.EVOLVED_MONSTERS, data.MINI_BOSSES)
        )

    def test_mini_boss_share_and_tracking_cannot_bypass_evolution(self):
        for level in (1, 5, 10, 15):
            monsters = pool("Whispering Woods", level)
            champion_count = sum(
                bool(enemy["evolution"].get("champion")) for enemy in monsters
            )
            self.assertEqual(champion_count / len(monsters), 0.25 if level >= 10 else 0)
        base = data.NORMAL_MONSTERS["Whispering Woods"][0]
        self.assertEqual(
            tracked(base, "Whispering Woods", 15), form("Whispering Woods", 0, 15)
        )
        custom = dict(name="Quest Guardian", hp=500, atk=30)
        self.assertEqual(tracked(custom, "Whispering Woods", 15), custom)

    def test_easy_and_night_modifiers_apply_once_and_maximum_health_matches(self):
        old = game.player
        try:
            for level in LEVELS:
                game.player = initial_player({"difficulty": "easy"})
                game.player["level"] = level
                original = form("Whispering Woods", 0, level)
                with patch.object(
                    game.random, "choice", side_effect=lambda rows: rows[0]
                ), patch.object(game.random, "random", return_value=0.99), patch.object(
                    game, "fight"
                ) as fight, patch(
                    "builtins.print"
                ):
                    game._wander_monster("Whispering Woods", True)
                night = fight.call_args.args[0]
                self.assertEqual(night["hp"], int(original["hp"] * 1.15))
                easy = scale_enemy(game.player, night)
                self.assertEqual(easy["hp"], round(night["hp"] * 0.75))
                self.assertEqual(easy["max_hp"], easy["hp"])
                self.assertEqual(night["hp"], night["max_hp"])
                self.assertEqual(easy["atk"], night["atk"])
        finally:
            game.player = old

    def test_live_evolved_attack_uses_attack_stat_instead_of_flat_old_damage(self):
        previous = (game.player, ui._ui)
        try:
            game.player = initial_player({})
            game.player.update(level=5, hp=200, max_hp=200)
            ui.init_ui(game.player)
            monster = form("Whispering Woods", 0, 5)
            self.assertEqual(attack_range(monster), (13, 20))
            with patch("builtins.input", side_effect=["1", StopIteration]), patch(
                "builtins.print"
            ), patch.object(
                game, "get_current_world_event", return_value=NEUTRAL
            ), patch.object(
                game.random, "random", return_value=0.99
            ), patch.object(
                game.random, "randint", side_effect=lambda low, high: high
            ):
                with self.assertRaises(StopIteration):
                    game.fight(monster)
            self.assertEqual(game.player["hp"], 180)
            self.assertEqual(attack_range(dict(atk=900)), (5, 15))
        finally:
            game.player, ui._ui = previous

    def test_live_victory_awards_stage_rewards_once(self):
        previous = (game.player, ui._ui)
        try:
            game.player = initial_player({})
            game.player["level"] = 5
            game.player["weapon"]["atk"] = 1000
            ui.init_ui(game.player)
            monster = form("Whispering Woods", 0, 5)
            gold = game.player["gold"]
            with patch("builtins.input", return_value="1"), patch(
                "builtins.print"
            ), patch.object(game, "drop_loot"), patch.object(
                game, "get_current_world_event", return_value=NEUTRAL
            ), patch.object(
                game.random, "random", return_value=0.99
            ):
                game.fight(monster)
            self.assertEqual(game.player["xp"], 30)
            self.assertEqual(game.player["gold"], gold + 28)
        finally:
            game.player, ui._ui = previous

    def test_carried_weapon_power_does_not_change_spawned_enemy(self):
        old = game.player
        try:
            game.player = initial_player({})
            game.player["level"] = 5
            captures = []
            for power in (1, 999999):
                game.player["weapon"]["atk"] = power
                with patch.object(
                    game.random, "choice", side_effect=lambda rows: rows[0]
                ), patch.object(game, "fight") as fight, patch("builtins.print"):
                    game._wander_monster("Whispering Woods", False)
                captures.append(fight.call_args.args[0])
            self.assertEqual(captures[0], captures[1])
        finally:
            game.player = old
