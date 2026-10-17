"""Arrivals, independent economies, construction and protected archaeology."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
import random
import data
import original_game as game
import original_ui as ui
from original_worker import initial_player
from original_sessions import OriginalSession, validate_original_save
import village_life as v
import village_projects as projects
import ancient_ruins
import world_sites


class VillageExpansionTests(TestCase):
    def setUp(self):
        self.previous = game.player
        self.previous_village = ui.village
        game.player = initial_player({'name': 'New traveller', 'cls': 'warrior'})
        self.p = game.player
        self.v = v.profile(data.REGIONS[0], 'Old Village')
        ui.init_ui(self.p)
        ui.village = self.v

    def tearDown(self):
        game.player = self.previous
        ui.village = self.previous_village

    def call(self, answers, fn, *args):
        with patch('builtins.input', side_effect=answers), patch('builtins.print'):
            return fn(*args)

    def test_start_is_actual_village_with_mentor_and_no_free_gear(self):
        session = OriginalSession({'name': 'Arrival', 'cls': 'warrior'})
        try:
            packet = session.poll()
            self.assertEqual(packet['prompt'], 'Village > ')
            self.assertEqual(packet['snapshot']['village']['name'], 'Old Village')
            p = packet['snapshot']['player']
            self.assertEqual(p['source_story']['mentor_village']['name'], 'Old Village')
            self.assertEqual(p['runes'], [])
            self.assertEqual([x['name'] for x in p['weapons']], ['Rusty Sword'])
            self.assertIn('Old Village', p['discovered_structures'][data.REGIONS[0]])
            session.send('18', packet['prompt_id'])
            self.assertEqual(session.poll()['prompt'], 'Mentor > ')
        finally:
            session.close()

    def test_every_region_has_varied_villages_and_work_sites(self):
        for region in data.REGIONS + [data.SECRET_REGION]:
            entries = data.REGION_STRUCTURES[region]
            villages = [v.profile(region, x['name']) for x in entries if x['type'] == 'village']
            self.assertGreaterEqual(len(villages), 2)
            self.assertGreater(len({x['kind'] for x in villages}), 1)
            self.assertTrue({'quarry', 'lumberyard', 'watchpost', 'ruins'} <= {x['type'] for x in entries})
            self.assertTrue(all('temple' not in x['services'] for x in villages))

    def test_growth_occurs_only_at_threshold_and_persists(self):
        rng = random.Random(42)
        with patch('builtins.print'):
            v.register_visit(self.p, self.v, rng)
            record = v.state(self.p, self.v)
            target = record['next_development']
            self.assertTrue(10 <= target <= 15)
            initial = deepcopy(record['levels'])
            for _ in range(target-2):
                v.register_visit(self.p, self.v, rng)
            self.assertEqual(record['levels'], initial)
            v.snapshot(self.p, self.v)
            self.assertEqual(record['visits'], target-1)
            v.register_visit(self.p, self.v, rng)
            self.assertEqual(sum(record['levels'].values()), sum(initial.values())+1)
            self.assertTrue(10 <= record['next_development']-record['visits'] <= 15)
            restored = validate_original_save(ui.snapshot())['player']
            self.assertEqual(restored['village_records'][self.v['id']], record)

    def test_growth_is_local_and_capped(self):
        other = v.profile('Whispering Woods', 'Briarwick')
        original = deepcopy(v.state(self.p, other)['levels'])
        record = v.state(self.p, self.v)
        record.update(visits=9, next_development=10)
        record['levels'] = {x: 5 for x in self.v['services']}
        with patch('builtins.print'):
            v.register_visit(self.p, self.v, random.Random(1))
        self.assertEqual(record['reputation'], 1)
        self.assertTrue(all(x == 5 for x in record['levels'].values()))
        self.assertEqual(v.state(self.p, other)['levels'], original)

    def test_material_stock_not_reset_by_revisit_or_reload(self):
        self.p['gold'] = 1000
        row = v.material_rows(self.p, self.v)[0]
        self.call(['1'], v.material_shop, game, self.v)
        self.assertEqual(v.material_rows(self.p, self.v)[0]['left'], row['left']-1)
        self.assertEqual(self.p[row['bag']][-1], row['name'])
        restored = validate_original_save(ui.snapshot())['player']
        self.assertEqual(v.material_rows(restored, self.v)[0]['left'], row['left']-1)
        restored['wander_count'] = 20
        self.assertEqual(v.material_rows(restored, self.v)[0]['left'], row['left'])
        poor = deepcopy(self.p); poor['gold'] = 0
        before = deepcopy(v.material_rows(poor, self.v))
        game.player = poor
        self.call(['1'], v.material_shop, game, self.v)
        self.assertEqual(v.material_rows(poor, self.v), before)

    def test_project_catalog_and_real_effects_no_double_spend(self):
        self.assertEqual(len(projects.PROJECTS), 100)
        self.assertEqual(len(projects.BY_ID), 100)
        self.p.update(gold=10000, building_materials={'Timber': 1000, 'Stone': 1000, 'Iron fittings': 1000})
        rows = [x for x in projects.offers(self.v) if x['service'] == 'farm'][:3]
        before = v.service_quality(self.p, self.v, 'farm')
        for row in rows:
            self.assertTrue(projects.build(self.p, self.v, row['id'])[0])
        self.assertEqual(v.service_quality(self.p, self.v, 'farm'), before+1)
        self.assertEqual(v.state(self.p, self.v)['reputation'], 3)
        saved = deepcopy(self.p)
        self.assertFalse(projects.build(self.p, self.v, rows[0]['id'])[0])
        self.assertEqual(saved, self.p)
        self.assertFalse(projects.build(self.p, self.v, 'temple:0')[0])
        self.assertNotIn('temple', self.v['services'])
        restored = validate_original_save(ui.snapshot())['player']
        self.assertEqual(projects.completed(restored, self.v), [x['id'] for x in rows])

    def test_every_project_can_be_found_in_some_village(self):
        available = set()
        for region, entries in data.REGION_STRUCTURES.items():
            for struct in entries:
                if struct['type'] == 'village':
                    available.update(x['id'] for x in projects.offers(v.profile(region, struct['name'])))
        for region, elem in data.ELEMENTAL_VILLAGES.items():
            available.update(x['id'] for x in projects.offers(v.profile(region, elem['name'], True)))
        self.assertEqual(available, set(projects.BY_ID))

    def test_work_sites_are_finite_local_and_reload_safe(self):
        site = dict(name='Test Quarry', type='quarry')
        self.call(['1'], world_sites.visit, game, site, data.REGIONS[0])
        self.call(['1'], world_sites.visit, game, site, data.REGIONS[0])
        self.assertEqual(self.p['building_materials']['Stone'], 2)
        saved = validate_original_save(ui.snapshot())['player']
        self.assertEqual(saved['work_sites'], self.p['work_sites'])
        self.p['wander_count'] = 20
        self.call(['1'], world_sites.visit, game, site, data.REGIONS[0])
        self.assertEqual(self.p['building_materials']['Stone'], 4)

    def test_watchpost_only_reveals_ordinary_village(self):
        self.call(['1'], world_sites.visit, game, dict(name='Watch', type='watchpost'), data.REGIONS[0])
        names = self.p['discovered_structures'][data.REGIONS[0]]
        self.assertEqual(len(names), 1)
        self.assertIn(names[0], [s['name'] for s in data.REGION_STRUCTURES[data.REGIONS[0]] if s['type'] == 'village'])
        self.assertNotIn(data.ELEMENTAL_VILLAGES[data.REGIONS[0]]['name'], names)

    def test_ruins_find_protected_unique_fragments_and_tomes(self):
        rng = random.Random()
        site = dict(name='Ancient site', type='ruins')
        with patch.object(rng, 'random', return_value=.1), patch('builtins.print'):
            item = ancient_ruins.search(self.p, site, data.REGIONS[0], rng)
            self.assertEqual(item['kind'], 'fragment')
            self.assertNotIn('value', item)
            self.assertIsNone(ancient_ruins.search(self.p, site, data.REGIONS[0], rng))
            self.p['wander_count'] = 20
            self.assertIsNone(ancient_ruins.search(self.p, site, data.REGIONS[0], rng))
        self.p['wander_count'] = 40
        with patch.object(rng, 'random', return_value=.5), patch('builtins.print'):
            tome = ancient_ruins.search(self.p, site, data.REGIONS[0], rng)
        self.assertEqual(tome['kind'], 'tome')
        self.assertEqual(len(self.p['protected_relics']), 2)
        self.assertNotIn(item, self.p['inventory'])
        self.assertNotIn(item, self.p.get('elemental_cores', []))
        self.assertEqual(validate_original_save(ui.snapshot())['player']['protected_relics'], self.p['protected_relics'])

    def test_invalid_development_project_or_stock_rejected(self):
        v.state(self.p, self.v)
        for key, value in [('visits', -1), ('next_development', 'tomorrow'), ('projects', ['unknown']), ('material_stock', {'Iron': -1}), ('development_log', [{}])]:
            saved = ui.snapshot()
            saved['player']['village_records'][self.v['id']][key] = value
            with self.assertRaises(ValueError, msg=key):
                validate_original_save(saved)

    def test_temple_sells_stabiliser_and_consumes_physical_core(self):
        self.p.update(region='Riftlands', gold=500)
        self.call(['1'], game.source_temple)
        self.assertEqual(self.p['gold'], 200)
        self.assertEqual(self.p['inventory'][0]['name'], 'Core Stabiliser')
        core = next(iter(game.ELEMENTAL_CORES))
        self.p['elemental_cores'] = [core]
        rune = {'name': 'Permanent test rune', 'effect': 'burn'}
        self.p['weapon']['rune'] = deepcopy(rune)
        before = self.p['weapon']['atk']
        self.call(['0', '1', 'y'], game.infuse_gear)
        self.assertEqual(self.p['elemental_cores'], [])
        self.assertEqual(self.p['inventory'], [])
        self.assertEqual(self.p['weapon']['rune'], rune)
        self.assertEqual(self.p['weapon']['atk'], before+game.ELEMENTAL_CORES[core]['bonus_atk'])
        self.assertTrue(self.p['weapon']['elemental_charged'])

    def test_clan_attunement_remains_and_fragments_cannot_be_used(self):
        self.p['region'] = 'Riftlands'
        core = next(iter(game.ELEMENTAL_CORES))
        self.p['core_attunements'] = [core]
        self.p['elemental_cores'] = []
        self.p['inventory'] = [dict(name='Core Stabiliser', value=150)]
        self.call(['0', '1', 'y'], game.infuse_gear)
        self.assertEqual(self.p['core_attunements'], [core])
        self.p['core_attunements'] = []
        self.p['inventory'] = [dict(name='Core Stabiliser', value=150)]
        self.p['protected_relics'] = [dict(name='Broken-Core Fragment', kind='fragment')]
        before = deepcopy(self.p)
        self.call([], game.infuse_gear)
        self.assertEqual(self.p, before)
        self.call([], game._sell_all_loot)
        self.assertEqual(len(self.p['protected_relics']), 1)
        self.assertEqual(self.p['gold'], before['gold']+150)

    def test_brewing_rejects_negative_same_ingredient_index(self):
        ui.village = self.v
        self.p['ingredients'] = ['Moonleaf', 'Moonleaf']
        before = deepcopy(self.p['ingredients'])
        self.call(['-1', '-1'], game._ingredient_brew_menu)
        self.assertEqual(self.p['ingredients'], before)
