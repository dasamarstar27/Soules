import json
import random
import unittest
from copy import deepcopy
import alchemy
from game import new_game,act,validate_save,encounter
from app import app

class AlchemyTests(unittest.TestCase):
    def setUp(self):self.g=new_game();self.rng=random.Random(13)

    def test_gather_each_region_and_stock(self):
        for region in range(15):
            g=new_game();g['region']=g['unlocked']=region
            before=sum(g['ingredients'].values())
            act(g,'gather',rng=self.rng)
            self.assertEqual(sum(g['ingredients'].values()),before+3)
            self.assertIn('Gathered:',g['log'][-1])
        alchemy.buy(self.g,'Empty Bottle');self.assertEqual(self.g['shop_stock']['Empty Bottle'],7)
        for _ in range(3):alchemy.forage(self.g,self.rng)
        self.assertEqual(self.g['shop_stock']['Empty Bottle'],8)

    def test_every_original_recipe_brews_and_drinks(self):
        for inputs,recipe in alchemy.NAMED.items():
            with self.subTest(recipe=recipe['name']):
                g=new_game();g['ingredients']=dict.fromkeys(inputs,1)
                act(g,'brew',{'ingredients':list(inputs)},self.rng)
                self.assertEqual(g['brews'][0]['name'],recipe['name'])
                self.assertEqual(g['bottles'],2);self.assertEqual(len(g['recipe_book']),1)
                self.assertTrue(all(n==0 for n in g['ingredients'].values()))
                validate_save(g)
                encounter(g,rng=self.rng)
                act(g,'drink',{'potion_id':g['brews'][0]['id']},self.rng)
                self.assertEqual(len(g['brews']),0);self.assertEqual(g['bottles'],3)
                validate_save(g)

    def test_unknown_pair_and_repeat_recipe(self):
        self.g['ingredients']={'Thorn Petal':3,'Forest Mushroom':3}
        for _ in range(2):act(self.g,'brew',{'ingredients':['Thorn Petal','Forest Mushroom']})
        self.assertEqual(len(self.g['recipe_book']),1)
        self.assertEqual(len(self.g['brews']),2)
        self.assertGreater(self.g['brews'][0]['formula']['heal'],0)

    def test_two_same_ingredients_require_two(self):
        self.g['ingredients']={'Thorn Petal':1}
        with self.assertRaises(ValueError):alchemy.experiment(self.g,['Thorn Petal']*2,[])
        self.g['ingredients']['Thorn Petal']=2
        alchemy.experiment(self.g,['Thorn Petal']*2,[])
        self.assertEqual(self.g['ingredients']['Thorn Petal'],0)

    def test_infusion_and_blending_conserve_bottles(self):
        alchemy.experiment(self.g,['Thorn Petal','Dew Blossom'],[])
        first=self.g['brews'][0];self.assertEqual(self.g['bottles'],2)
        infused=alchemy.experiment(self.g,['Thorn Petal'],[first['id']])
        self.assertGreater(infused['formula']['heal'],first['formula']['heal'])
        self.assertEqual(self.g['bottles'],2)
        alchemy.buy(self.g,'Health Potion')
        blended=alchemy.experiment(self.g,[],[p['id'] for p in self.g['brews']])
        self.assertEqual(len(self.g['brews']),1);self.assertEqual(self.g['bottles'],3)
        self.assertGreater(blended['formula']['heal'],infused['formula']['heal'])
        validate_save(self.g)

    def test_potion_cures_and_combat_turn(self):
        alchemy.buy(self.g,'Antidote');self.g['player']['status']={'poison':3,'regen':3}
        act(self.g,'explore',rng=self.rng)
        act(self.g,'drink',{'potion_id':self.g['brews'][0]['id']},self.rng)
        self.assertEqual(self.g['turn'],1)
        self.assertNotIn('poison',self.g['player']['status'])
        self.assertIn('regen',self.g['player']['status'])

    def test_v1_saves_migrate_without_losing_progress(self):
        old=deepcopy(self.g);old['version']=1;old['player']['gold']=999
        for k in list(alchemy.starter())+['tutorial']:del old[k]
        result=validate_save(old)
        self.assertEqual(result['version'],2);self.assertEqual(result['player']['gold'],999)
        self.assertEqual(result['runes'],old['runes'])
        self.assertEqual(result['ingredients'],alchemy.starter()['ingredients'])

    def test_invalid_brew_is_transactional_and_save_is_validated(self):
        client=app.test_client();before=client.get('/api/state').json
        response=client.post('/api/action',json={'action':'brew','ingredients':['wrong','Dew Blossom']})
        self.assertEqual(response.status_code,400);self.assertEqual(before,client.get('/api/state').json)
        bad=deepcopy(before);bad['brews']=[dict(id='x',name='bad',desc='bad',formula={'statuses':['missing']})]
        self.assertEqual(client.post('/api/load',json=bad).status_code,400)
        bad=deepcopy(before);bad['shop_stock']['Health Potion']=-1
        with self.assertRaises(ValueError):validate_save(bad)

    def test_strength_potion_is_temporary_without_hidden_damage(self):
        from effects import stat,expire
        alchemy.buy(self.g,'Strength Draught')
        base=self.g['player']['atk'];hp=self.g['player']['hp']
        act(self.g,'drink',{'potion_id':self.g['brews'][0]['id']})
        self.assertEqual(stat(self.g['player'],'atk'),base+10)
        self.assertEqual(self.g['player']['hp'],hp)
        for _ in range(3):expire(self.g['player'],set(self.g['player']['status']))
        self.assertEqual(stat(self.g['player'],'atk'),base)

    def test_field_draughts_can_join_mixtures(self):
        act(self.g,'bottle_draught')
        self.assertEqual(self.g['potions'],2)
        rid=self.g['brews'][0]['id']
        act(self.g,'brew',{'ingredients':['Thorn Petal'],'potion_ids':[rid]})
        self.assertGreater(self.g['brews'][0]['formula']['heal'],50)
        validate_save(self.g)

    def test_tutorial_progress_survives_save(self):
        act(self.g,'tutorial',{'step':4})
        self.assertEqual(validate_save(json.loads(json.dumps(self.g)))['tutorial'],4)
        with self.assertRaises(ValueError):act(self.g,'tutorial',{'step':99})

if __name__=='__main__':unittest.main()
