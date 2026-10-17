import json
import random
import unittest
from copy import deepcopy
from itertools import combinations_with_replacement
from app import app, games
from game import CATALOG, RECIPES, new_game, act, fuse, rune, validate_save, encounter, finish
from effects import EFFECTS, apply, tick, expire, stat, hurt, heal, cure

class Rules(unittest.TestCase):
    def setUp(self):
        self.g=new_game();self.rng=random.Random(42)

    def test_every_rune_casts(self):
        for name in CATALOG:
            with self.subTest(rune=name):
                g=new_game(); encounter(g,rng=self.rng)
                g['runes']=[rune(name)];g['player'].update(hp=1000,max_hp=1000,mana=100,max_mana=100)
                act(g,'cast',{'rune_id':g['runes'][0]['id']},self.rng)
                self.assertGreater(len(g['log']),2)
                self.assertGreaterEqual(g['player']['hp'],0)
                validate_save(g)

    def test_all_base_pairings_preserve_components(self):
        count=0
        for a,b in combinations_with_replacement(CATALOG,2):
            ra,rb=rune(a),rune(b)
            result=fuse([ra,rb]);count+=1
            self.assertTrue(set([ra['effect'],rb['effect']])<=set(result['components']))
            self.assertTrue(all(k in EFFECTS for k in result['components']))
        self.assertEqual(count,8778)

    def test_every_named_recipe_reachable(self):
        known=set(CATALOG)
        pending=list(RECIPES.items())
        while pending:
            remaining=[]
            for inputs,recipe in pending:
                if inputs<=known:
                    known.add(recipe['name'])
                else:remaining.append((inputs,recipe))
            self.assertLess(len(remaining),len(pending),'Unreachable named recipe')
            pending=remaining

    def test_named_fusions_cast_all_components(self):
        available={name:rune(name) for name in CATALOG}
        pending=list(RECIPES.items())
        while pending:
            rest=[]
            for inputs,recipe in pending:
                if not inputs<=available.keys():
                    rest.append((inputs,recipe));continue
                result=fuse([available[n] for n in inputs])
                available[result['name']]=result
                g=new_game();g['runes']=[result]
                g['player'].update(hp=1000,max_hp=1000,mana=100,max_mana=100)
                encounter(g,rng=self.rng)
                act(g,'cast',{'rune_id':result['id']},self.rng)
                validate_save(g)
            self.assertLess(len(rest),len(pending))
            pending=rest

    def test_recursion_and_three_rune_recipe(self):
        result=fuse([rune('Flame Rune'),rune('Water Rune')])
        self.assertEqual(result['name'],'Steam Cataclysm Rune')
        result=fuse([result,rune('Ice Rune')])
        self.assertTrue({'burn','soak','blind','freeze'}<=set(result['components']))
        result=fuse([rune('Flame Rune'),rune('Earth Rune'),rune('Storm Rune')])
        self.assertEqual(result['name'],'Rune of Elements')
        with self.assertRaises(ValueError):fuse([rune('Water Rune'),rune('Ice Rune'),rune('Wind Rune')])

    def test_final_tick_and_temporary_stats(self):
        p=self.g['player'];p['hp']=50
        apply(p,'burn',[],rng=self.rng);p['status']['burn']=1
        tick(p,self.g['player'],[],self.rng);expire(p,{'burn'})
        self.assertEqual(p['hp'],48);self.assertNotIn('burn',p['status'])
        original=p['def'];apply(p,'defense_up',[],rng=self.rng)
        self.assertGreater(stat(p,'def'),original)
        for _ in range(4):expire(p,{'defense_up'})
        self.assertEqual(stat(p,'def'),original)

    def test_cures_preserve_buffs_and_blocked_healing(self):
        p=self.g['player'];p['status']={'poison':3,'regen':3,'hellfire':3};p['hp']=50
        self.assertEqual(heal(p,10),0)
        self.assertEqual(set(cure(p,'cleanse')),{'poison','hellfire'})
        self.assertEqual(p['status'],{'regen':3})
        heal(p,1000);self.assertEqual(p['hp'],p['max_hp'])

    def test_every_effect_ticks_without_corrupting_base_stats(self):
        for key in EFFECTS:
            with self.subTest(effect=key):
                p=deepcopy(self.g['player']);e=deepcopy(p);e['name']='Enemy'
                apply(p,key,[],source=e,rng=self.rng)
                before=(p['atk'],p['def'],p['speed'])
                for _ in range(8):
                    prior=set(p['status']);tick(p,e,[],self.rng);expire(p,prior)
                self.assertEqual(before,(p['atk'],p['def'],p['speed']))
                self.assertFalse(p['status'])

    def test_rebirth_only_once(self):
        p=self.g['player'];p['status']['rebirth']=4
        hurt(p,1000,[]);self.assertEqual(p['hp'],50)
        hurt(p,1000,[]);self.assertEqual(p['hp'],0)

    def test_campaign_ending_and_unlocks(self):
        for i in range(15):
            act(self.g,'travel',{'region':i});act(self.g,'boss')
            self.g['enemy']['hp']=0;finish(self.g,self.rng)
        self.assertTrue(self.g['victory']);self.assertEqual(len(self.g['bosses']),15)
        self.assertEqual(self.g['unlocked'],14)

    def test_fusion_consumption_and_duplicate_rejection(self):
        g=self.g;g['shards']=1;ids=[r['id'] for r in g['runes'][:2]]
        act(g,'fuse',{'ids':ids});self.assertEqual(len(g['runes']),5);self.assertEqual(g['shards'],0)
        self.assertEqual(g['runes'][-1]['name'],'Steam Cataclysm Rune')
        with self.assertRaises(ValueError):fuse([g['runes'][0]]*2)

    def test_full_campaign_through_real_combat(self):
        rng=random.Random(54);g=new_game(cls='Warden');fights=0
        for region in range(15):
            act(g,'travel',{'region':region},rng)
            target=region*2+3
            while g['player']['level']<target:
                act(g,'rest',rng=rng);act(g,'explore',rng=rng)
                for _ in range(200):
                    if not g['enemy']:break
                    act(g,'attack',rng=rng)
                assert not g['enemy']
                assert g['player']['hp']>0,('grinding death',region,g['player'])
                fights+=1
            act(g,'rest',rng=rng)
            while g['potions']<5:act(g,'buy',{'item':'potion'},rng)
            act(g,'boss',rng=rng)
            for _ in range(200):
                if not g['enemy']:break
                action='potion' if g['player']['hp']<g['player']['max_hp']*.5 and g['potions'] else 'attack'
                if 'reality_warp' in g['player']['status']:
                    action='cleanse' if g['cleanses'] else 'guard'
                act(g,action,rng=rng)
            assert g['player']['hp']>0,('boss death',region,g['player'])
            assert region in g['bosses']
            fights+=1
        self.assertTrue(g['victory'])

    def test_saves_validate_and_reject_bad_data(self):
        self.assertEqual(validate_save(json.loads(json.dumps(self.g))),self.g)
        for modify in (lambda g:g['player'].update(hp=float('nan')),lambda g:g.update(region=99),lambda g:g['runes'][0].update(effect='nope'),lambda g:g.update(log=[{}])):
            bad=deepcopy(self.g);modify(bad)
            with self.assertRaises(ValueError):validate_save(bad)

class API(unittest.TestCase):
    def setUp(self):app.config['TESTING']=True;self.client=app.test_client()
    def test_full_session_and_transactional_failures(self):
        self.assertEqual(self.client.get('/').status_code,200)
        original=self.client.get('/api/state').json
        self.assertEqual(self.client.post('/api/action',json={'action':'cast','rune_id':'fake'}).status_code,400)
        self.assertEqual(original,self.client.get('/api/state').json)
        self.assertEqual(self.client.post('/api/action',json={'action':'explore'}).status_code,200)
        save=self.client.get('/api/save').json
        self.client.post('/api/new',json={'name':'Another'})
        self.assertEqual(self.client.post('/api/load',json=save).json,save)
        self.assertEqual(self.client.post('/api/load',json={}).status_code,400)
    def test_session_isolation(self):
        other=app.test_client()
        self.client.post('/api/new',json={'name':'One'})
        other.post('/api/new',json={'name':'Two'})
        self.assertEqual(self.client.get('/api/state').json['player']['name'],'One')
        self.assertEqual(other.get('/api/state').json['player']['name'],'Two')

if __name__=='__main__':unittest.main()
