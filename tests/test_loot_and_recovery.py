"""Native loot pools and full-hunger recovery across actual wander outcomes."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

import data
import original_game as game
import original_ui as ui
from original_worker import initial_player


class LootAndRecoveryTests(TestCase):
    def setUp(self):
        self.old = game.player
        self.old_village = ui.village
        game.player = initial_player({'name': 'Explorer', 'cls': 'warrior'})
        self.p = game.player
        ui.init_ui(self.p)
        ui.village = None

    def tearDown(self):
        game.player = self.old
        ui.village = self.old_village

    def wander(self, roll=99):
        with patch('wander_roll.pick', return_value='monster' if roll==80 else 'peaceful'), patch.object(game.random, 'random', return_value=0 if roll==80 else .99), patch.object(game.random, 'randint', return_value=roll), patch.object(game, 'fight') as fight, patch('builtins.print'):
            game.explore()
            return fight

    def test_sea_pearls_only_in_sunken_coast(self):
        for region in data.REGIONS+[data.SECRET_REGION]:
            names = {item['name'] for item in game.regional_loot(region)}
            self.assertEqual('Sea Pearl' in names, region == 'Sunken Coast', region)

    def test_forest_has_native_and_common_trinkets_without_endgame_treasures(self):
        names = {item['name'] for item in game.regional_loot('Whispering Woods')}
        self.assertTrue({'Wolf Pelt', 'Thorn Branch', 'Ancient Coin'} <= names)
        self.assertFalse({'Frozen Core', 'Sea Pearl', 'Divine Artifact', 'Primordial Shard', 'Infernal Ember', 'Abyssal Soul'} & names)

    def test_every_region_has_nonempty_pool_and_all_restrictions_are_valid(self):
        regions = set(data.REGIONS+[data.SECRET_REGION])
        reachable = set()
        for region in regions:
            pool = game.regional_loot(region)
            self.assertTrue(pool, region)
            self.assertIn('Ancient Coin', {item['name'] for item in pool})
            for item in pool:
                self.assertTrue(not item.get('regions') or region in item['regions'])
                reachable.add(item['name'])
        self.assertEqual(reachable, {item['name'] for item in data.LOOT_ITEMS})
        for item in data.LOOT_ITEMS:
            self.assertTrue(set(item.get('regions', [])) <= regions)

    def test_actual_monster_loot_is_native_and_independently_copied(self):
        for region in data.REGIONS+[data.SECRET_REGION]:
            self.p['region'] = region
            with patch.object(game.random, 'randint', return_value=1), patch.object(game.random, 'choice', side_effect=lambda pool: pool[-1]), patch('builtins.print'):
                game.drop_loot()
            item = self.p['inventory'][-1]
            self.assertTrue(not item.get('regions') or region in item['regions'])
            source = next(x for x in data.LOOT_ITEMS if x['name'] == item['name'])
            self.assertIsNot(item, source)
            item['value'] = 99999
            self.assertNotEqual(source['value'], 99999)

    def test_arena_cave_and_dungeon_rewards_all_use_the_region_pool(self):
        native = [dict(name='Forest-only test reward', value=1)]
        for function in (game.visit_arena, game.visit_cave, game.visit_dungeon):
            self.p['inventory'] = []
            with patch('builtins.input', return_value='1'), patch('builtins.print'), patch.object(game, 'fight'), patch.object(game.random, 'random', return_value=0), patch.object(game, 'regional_loot', return_value=native) as pool:
                function({'name': 'Testing site'}, 'Whispering Woods')
            self.assertTrue(pool.called, function.__name__)
            self.assertTrue(all(call.args == ('Whispering Woods',) for call in pool.call_args_list))
            self.assertTrue(self.p['inventory'])
            self.assertTrue(all(item['name'] == native[0]['name'] for item in self.p['inventory']))

    def test_full_hunger_heals_before_normal_hunger_drain(self):
        self.p.update(hp=30, hunger=100)
        self.wander()
        self.assertEqual(self.p['hp'], 33)
        self.assertEqual(self.p['hunger'], 95)
        self.assertEqual(self.p['wander_count'], 1)

    def test_no_healing_if_not_at_full_hunger(self):
        for hunger in (99, 95, 50, 30):
            self.p.update(hp=30, hunger=hunger)
            self.wander()
            self.assertEqual(self.p['hp'], 30, hunger)

    def test_recovery_does_not_repeat_next_wander_without_refilling(self):
        self.p.update(hp=30, hunger=100)
        self.wander(); self.wander()
        self.assertEqual(self.p['hp'], 33)
        self.assertEqual(self.p['hunger'], 90)

    def test_recovery_caps_at_maximum_and_full_health_stays_full(self):
        self.p.update(hp=self.p['max_hp']-1, hunger=100)
        self.wander()
        self.assertEqual(self.p['hp'], self.p['max_hp'])
        self.p['hunger'] = 100
        self.wander()
        self.assertEqual(self.p['hp'], self.p['max_hp'])

    def test_starvation_still_hurts_without_recovery(self):
        self.p.update(hp=30, hunger=0)
        self.wander()
        self.assertEqual(self.p['hp'], 20)
        self.assertEqual(self.p['hunger'], 0)

    def test_food_based_recovery_cannot_revive(self):
        self.p.update(hp=0, hunger=100)
        with patch('builtins.print'):
            self.assertEqual(game.regenerate_from_full_hunger(), 0)
        self.assertEqual(self.p['hp'], 0)

    def test_recovery_applies_once_before_an_encounter(self):
        self.p.update(hp=30, hunger=100)
        fight = self.wander(80)
        fight.assert_called_once()
        self.assertEqual(self.p['hp'], 33)

    def test_discovery_early_return_also_gets_one_recovery(self):
        self.p.update(hp=30, hunger=100)
        # The structure outcome must still receive exactly one recovery.
        with patch('wander_roll.pick', return_value='structure'), patch.object(game.random, 'random', return_value=.99), patch('builtins.print'):
            game.explore()
        self.assertEqual(self.p['hp'], 33)
        self.assertEqual(self.p['hunger'], 95)
        self.assertTrue(self.p['discovered_structures']['Whispering Woods'])

    def test_hunger_resistance_still_checks_full_hunger_before_spending(self):
        self.p.update(hp=30, hunger=100, skills=['hunger_resist'])
        self.wander()
        self.assertEqual(self.p['hp'], 33)
        self.assertEqual(self.p['hunger'], 99)

    def test_opening_menus_never_triggers_recovery(self):
        self.p.update(hp=30, hunger=100)
        with patch('builtins.print'):
            game.show_map()
        with patch('builtins.print'), patch('builtins.input', return_value='7'):
            game.sell()
        self.assertEqual(self.p['hp'], 30)
        self.assertEqual(self.p['hunger'], 100)

    def test_tower_material_bonus_uses_catalog_keys_without_crashing(self):
        for bag, catalog in [('cores', game.CORES), ('woods', game.WOODS), ('metals', game.METALS)]:
            before = len(self.p.get(bag, []))
            def choose(pool):
                if len(pool) == 3 and pool[0] is game.CORES:
                    return catalog
                return pool[0]
            with patch('builtins.input', return_value='1'), patch('builtins.print'), patch.object(game, 'fight'), patch.object(game.random, 'choice', side_effect=choose):
                game.visit_tower({'name': 'Test Tower'}, 'Whispering Woods')
            self.assertEqual(len(self.p[bag]), before+1)
            self.assertIn(self.p[bag][-1], catalog)
