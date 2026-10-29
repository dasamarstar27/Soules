from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch
import monster_behaviour as ai
import original_game as game
import original_ui as ui
from original_worker import initial_player


class MonsterBehaviourTests(TestCase):
    def enemy(self):
        return dict(name="Road Brute", hp=40, max_hp=100, atk=20, active_buffs={})

    def test_all_intents_available_and_do_not_reroll_on_reprompt(self):
        keys = set()
        for ticket in range(100):
            enemy = self.enemy()
            rng = Mock()
            rng.randrange.return_value = ticket
            intent = ai.prepare(enemy, rng)
            keys.add(intent["key"])
            self.assertIs(ai.prepare(enemy, rng), intent)
            rng.randrange.assert_called_once_with(100)
        self.assertEqual(keys, set(ai.INTENTS) - {"drain"})

    def test_stun_overrides_an_existing_plan_without_drawing_again(self):
        enemy = self.enemy()
        enemy.update(intent={"key": "guard"}, _behaviour_enabled=True)
        enemy["active_buffs"]["stun"] = 1
        rng = Mock()
        self.assertEqual(ai.prepare(enemy, rng)["key"], "stunned")
        rng.randrange.assert_not_called()
        self.assertEqual(ai.guard_damage(enemy, 20), 20)

    def test_creature_families_change_actions(self):
        for name, key in [("Forest Wraith", "drain"), ("Thorn Wolf", "pounce")]:
            found = set()
            for ticket in range(100):
                e = self.enemy()
                e["name"] = name
                rng = Mock()
                rng.randrange.return_value = ticket
                found.add(ai.prepare(e, rng)["key"])
            self.assertIn(key, found)

    def test_recovery_limited_and_never_overheals(self):
        e = self.enemy()
        for n in range(2):
            e["intent"] = {"key": "recover"}
            with redirect_stdout(StringIO()):
                self.assertEqual(ai.enemy_action(e, 10), 0)
        self.assertEqual(e["hp"], 56)
        e.pop("intent")
        rng = Mock()
        rng.randrange.return_value = 90
        self.assertEqual(ai.prepare(e, rng)["key"], "attack")
        e = self.enemy()
        e["hp"] = 100
        self.assertEqual(ai.prepare(e, rng)["key"], "attack")

    def test_guard_and_interruption_cost_and_damage(self):
        e = self.enemy()
        e.update(_behaviour_enabled=True, intent={"key": "guard"})
        with redirect_stdout(StringIO()):
            self.assertEqual(ai.guard_damage(e, 19), 10)
        p = {"mana": 8}
        self.assertFalse(ai.interrupt(p, e)[0])
        self.assertEqual(p["mana"], 8)
        e["intent"] = {"key": "heavy"}
        self.assertTrue(ai.interrupt(p, e)[0])
        self.assertEqual(p["mana"], 5)
        self.assertEqual(ai.enemy_action(e, 20), 0)
        e["intent"] = {"key": "pounce"}
        p["mana"] = 2
        self.assertFalse(ai.interrupt(p, e)[0])
        self.assertEqual(p["mana"], 2)

    def test_actions_and_drain(self):
        e = self.enemy()
        for key, damage in [
            ("attack", 20),
            ("heavy", 33),
            ("pounce", 24),
            ("drain", 17),
            ("guard", 0),
            ("fumble", 0),
        ]:
            e["intent"] = {"key": key}
            with redirect_stdout(StringIO()):
                self.assertEqual(ai.enemy_action(e, 20), damage)
        e["intent"] = {"key": "drain"}
        with redirect_stdout(StringIO()):
            ai.after_hit(e, 20)
        self.assertEqual(e["hp"], 45)
        ai.after_hit(e, 0)
        self.assertEqual(e["hp"], 45)

    def test_live_interrupt_and_guard_react_to_heavy_intent(self):
        previous = game.player, ui._ui
        try:
            losses = {}
            for choice in ("10", "11"):
                game.player = initial_player({})
                game.player.update(hp=200, max_hp=200, mana=20, speed=0, **{"def": 0})
                ui.init_ui(game.player)
                with patch("builtins.input", side_effect=[choice, "4"]), patch(
                    "builtins.print"
                ), patch.object(
                    game.random, "randrange", return_value=65
                ), patch.object(
                    game.random, "random", return_value=0.99
                ), patch.object(
                    game.random, "randint", side_effect=lambda a, b: b
                ), patch.object(
                    game,
                    "get_current_world_event",
                    return_value={"enemy_hp_mod": 1, "enemy_atk_mod": 1},
                ):
                    game.fight(
                        dict(
                            name="Road Brute", hp=100, max_hp=100, atk=20, **{"def": 0}
                        )
                    )
                losses[choice] = 200 - game.player["hp"]
                self.assertEqual(game.player["mana"], 20 - (3 if choice == "11" else 0))
            self.assertGreater(losses["10"], 0)
            self.assertLess(losses["10"], 25)
            self.assertEqual(losses["11"], 0)
        finally:
            game.player, ui._ui = previous
