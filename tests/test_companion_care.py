from copy import deepcopy
import io
import json
import random
from unittest import TestCase
from unittest.mock import patch

import companion_care as care
import data
import original_game as game
import original_ui as ui
import original_worker as worker
from original_sessions import OriginalSession, validate_original_save
from season_two import available, village_services
from game_guide import GUIDE, ACTION_HELP
from original_menus import GROUPS
from app import app


class CompanionCareTests(TestCase):
    def setUp(self):
        self.old = game.player
        self.old_village = ui.village
        game.player = worker.initial_player({'name': 'Companion tester', 'cls': 'warrior'})
        self.p = game.player
        self.c = deepcopy(data.COMPANIONS['Ashen Wastes'][0])
        self.c.update(stage=0, xp=0)
        care.normalise(self.c)
        self.p['companions'] = [self.c]
        ui.init_ui(self.p)
        ui.village = None

    def tearDown(self):
        game.player = self.old
        ui.village = self.old_village

    def quiet(self, fn, *args):
        with patch('builtins.print'):
            return fn(*args)

    def test_recruitment_sets_hunger_and_correct_home_without_giving_food(self):
        self.p['companions'] = []
        self.quiet(game.recruit_companion, data.COMPANIONS['Ashen Wastes'][0])
        pet = self.p['companions'][0]
        self.assertEqual(pet['hunger'], 100)
        self.assertEqual(pet['home_region'], 'Ashen Wastes')
        self.assertEqual(pet['stage'], 0)
        self.assertEqual(self.p['inventory'], [])

    def test_all_catalogued_companions_have_food_and_distinct_final_forms(self):
        finals = set()
        for region, group in data.COMPANIONS.items():
            for source in group:
                c = deepcopy(source)
                care.normalise(c)
                self.assertEqual(c['home_region'], region)
                self.assertTrue(care.foods(c), c['name'])
                c.update(stage=2)
                name = care.form_name(c)
                self.assertNotIn(name, finals)
                finals.add(name)

    def test_hunger_only_falls_on_wanders_and_is_clamped(self):
        self.quiet(care.wander, self.p)
        self.assertEqual(self.c['hunger'], 95)
        self.c['hunger'] = 2
        self.quiet(care.wander, self.p)
        self.assertEqual(self.c['hunger'], 0)
        self.assertIn(self.c, self.p['companions'])
        self.c['hunger'] = 60
        with patch('builtins.input', return_value='0'), patch('builtins.print'):
            care.menu(game)
        self.assertEqual(self.c['hunger'], 60)

    def test_actual_explore_drains_companion_once(self):
        with patch.object(game.random, 'random', return_value=.99), patch.object(game.random, 'randint', return_value=15), patch('builtins.print'):
            game.explore()
        self.assertEqual(self.c['hunger'], 95)

    def test_home_food_consumes_one_and_restores_canonical_hunger(self):
        self.p['region'] = 'Whispering Woods'
        food = care.foods(self.c)[0]
        self.c['hunger'] = 10
        self.p['inventory'] = [deepcopy(food), deepcopy(food)]
        okay, message = care.feed(self.p, self.c, 0)
        self.assertTrue(okay, message)
        self.assertEqual(self.c['hunger'], min(100, 10+food['hunger']))
        self.assertEqual(len(self.p['inventory']), 1)
        self.assertEqual(self.c['xp'], 1)
        self.assertEqual(self.c['meals_eaten'], 1)
        self.assertEqual(self.p['hunger'], 100)

    def test_wrong_food_full_and_negative_index_preserve_supplies(self):
        wrong = next(f for f in data.FOOD_ITEMS if f['name'] not in {x['name'] for x in care.foods(self.c)})
        self.p['inventory'] = [deepcopy(wrong)]
        self.c['hunger'] = 20
        self.assertFalse(care.feed(self.p, self.c, 0)[0])
        self.assertEqual(self.p['inventory'], [wrong])
        food = care.foods(self.c)[0]
        self.p['inventory'] = [deepcopy(food)]
        self.c['hunger'] = 100
        self.assertFalse(care.feed(self.p, self.c, 0)[0])
        self.assertFalse(care.feed(self.p, self.c, -1)[0])
        self.assertEqual(self.p['inventory'], [food])
        self.assertEqual(self.c['xp'], 0)

    def test_three_and_six_meals_evolve_with_named_final_form(self):
        food = care.foods(self.c)[0]
        self.p['inventory'] = [deepcopy(food) for _ in range(6)]
        for meal in range(1, 7):
            self.c['hunger'] = 20
            self.assertTrue(care.feed(self.p, self.c, 0)[0])
            self.assertEqual(self.c['stage'], 0 if meal < 3 else 1 if meal < 6 else 2)
        self.assertEqual(self.c['form_name'], 'Sunfire Ember Fox')
        self.assertEqual(self.c['xp'], 6)
        self.assertEqual(self.p['inventory'], [])

    def test_peaceful_species_evolve_and_stay_peaceful(self):
        c = deepcopy(data.COMPANIONS['Whispering Woods'][0])
        c.update(stage=1, xp=6)
        self.assertTrue(care.evolve(c))
        self.assertIn('Elderwood', c['form_name'])
        self.assertFalse(care.ready(c))

    def test_hungry_companions_do_not_support_or_earn_battle_xp(self):
        self.c.update(stage=2, hunger=29)
        enemy = dict(hp=100, max_hp=100, atk=5, **{'def': 3})
        before = deepcopy(enemy)
        self.quiet(game.apply_companion_support, enemy)
        self.quiet(game.award_companion_xp, 10)
        self.assertEqual(enemy, before)
        self.assertEqual(self.p['companion_xp'], {})
        self.c['hunger'] = 30
        self.quiet(game.award_companion_xp, 10)
        self.assertEqual(self.p['companion_xp'][self.c['name']], 10)

    def test_final_form_has_stronger_support(self):
        self.c.update(stage=1, hunger=100)
        enemy = dict(hp=100, **{'def': 3})
        self.quiet(game.apply_companion_support, enemy)
        self.assertEqual(enemy['hp'], 97)
        self.c['stage'] = 2
        self.quiet(game.apply_companion_support, enemy)
        self.assertEqual(enemy['hp'], 91)

    def test_earth_support_is_temporary_not_permanent_base_defence(self):
        self.c = deepcopy(data.COMPANIONS['Ironpeak Mountains'][0])
        self.c.update(stage=2, hunger=100)
        self.p['companions'] = [self.c]
        before = self.p['def']
        self.quiet(game.apply_companion_support, {'hp': 100})
        self.assertEqual(self.p['def'], before)
        self.assertEqual(self.p['active_buffs']['fortress'], 2)

    def test_unready_move_cancel_and_crystal_move(self):
        enemy = dict(hp=100, **{'def': 10})
        self.c.update(stage=1, hunger=10)
        with patch('builtins.input', side_effect=AssertionError('Asked hungry pet for move')), patch('builtins.print'):
            self.assertFalse(game._use_companion_move([self.c], enemy))
        c = deepcopy(data.COMPANIONS['Shattered Wastes'][0]); c.update(stage=1, hunger=50)
        with patch('builtins.input', return_value='0'), patch('builtins.print'):
            self.assertTrue(game._use_companion_move([c], enemy))
        self.assertEqual(enemy['hp'], 76)
        self.assertEqual(enemy['def'], 7)

    def test_old_save_migrates_and_care_progress_round_trips(self):
        self.c.pop('hunger'); self.c.pop('home_region')
        migrated = worker.initial_player({'save': validate_original_save(ui.snapshot())})
        self.assertEqual(migrated['companions'][0]['hunger'], 100)
        self.assertEqual(migrated['companions'][0]['home_region'], 'Ashen Wastes')
        self.c.update(hunger=45, home_region='Ashen Wastes', stage=2, xp=6, meals_eaten=6)
        restored = worker.initial_player({'save': validate_original_save(ui.snapshot())})
        self.assertEqual(restored['companions'][0]['form_name'], 'Sunfire Ember Fox')
        self.assertEqual(restored['companions'][0]['hunger'], 45)

    def test_invalid_care_or_mode_save_rejected(self):
        for key, value in [('hunger', -1), ('hunger', 101), ('hunger', True), ('home_region', 'Unknown'), ('stage', 3), ('meals_eaten', -1)]:
            saved = ui.snapshot()
            saved['player']['companions'][0][key] = value
            with self.assertRaises(ValueError, msg=key):
                validate_original_save(saved)
        saved = ui.snapshot(); saved['player']['beta_mode'] = 'false'
        with self.assertRaises(ValueError):
            validate_original_save(saved)

    def test_mode_off_reprompts_without_answering_pending_question(self):
        self.p['beta_mode'] = True
        source = io.StringIO(json.dumps({'text': ' sAmAr '})+'\n'+json.dumps({'text': 'y'})+'\n')
        with patch.object(worker.sys, 'stdin', source), patch.object(worker, 'emit') as emit, patch('builtins.print'):
            self.assertEqual(worker.input_line('Buy this? > '), 'y')
        self.assertFalse(self.p['beta_mode'])
        self.assertEqual([call.kwargs['prompt'] for call in emit.call_args_list], ['Buy this? > ', 'Buy this? > '])

    def test_mode_off_works_in_category_and_persists(self):
        session = OriginalSession({'name': 'Modes', 'cls': 'warrior'})
        try:
            session.send('7', session.poll()['prompt_id'])
            session.send('DAMAR', session.poll()['prompt_id'])
            session.send('2', session.poll()['prompt_id'])
            before = session.poll()['snapshot']['player']
            session.send(' samar ', session.poll()['prompt_id'])
            packet = session.poll()
            self.assertEqual(packet['snapshot']['group'], 'inventory')
            self.assertFalse(packet['snapshot']['player']['beta_mode'])
            self.assertEqual(packet['snapshot']['player']['weapons'], before['weapons'])
            self.assertFalse(available(packet['snapshot']['player']))
            saved = validate_original_save(packet['snapshot'])
            self.assertFalse(worker.initial_player({'save': saved})['beta_mode'])
        finally:
            session.close()

    def test_open_postgame_purchase_rechecks_mode_after_prompt(self):
        self.p.update(beta_mode=True, chapter=1, gold=1000)
        self.p['region'] = 'Infernal Depths'
        answers = iter(['1', '1'])
        def answer(prompt):
            value = next(answers)
            if 'Buy number' in prompt:
                self.p['beta_mode'] = False
            return value
        before = len(self.p['weapons'])
        with patch('builtins.input', side_effect=answer), patch('builtins.print'):
            village_services(game, data.ELEMENTAL_VILLAGES['Infernal Depths'])
        self.assertEqual(self.p['gold'], 1000)
        self.assertEqual(len(self.p['weapons']), before)

    def test_guide_explains_every_action_without_revealing_hidden_commands(self):
        ids = {action for group in GROUPS for action, _ in group['options']}
        self.assertEqual(ids, set(ACTION_HELP))
        text = json.dumps(GUIDE)
        for hidden in ('DAMAR', 'SAMAR'):
            self.assertNotIn(hidden, text)
        response = app.test_client().get('/api/original/catalog')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['guide']['actions']), 47)
        self.assertIn('preview', text.lower())
