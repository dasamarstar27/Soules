import ast
from copy import deepcopy
from pathlib import Path
import unittest
import data
from game import new_game,act,encounter,finish,chapter_one_complete,story_progress,validate_save
from app import app

class OrganizationTests(unittest.TestCase):
    def test_one_definition_per_data_catalog_and_no_extensions(self):
        tree=ast.parse(Path(data.__file__).read_text());names=[]
        for node in tree.body:
            self.assertIsInstance(node,(ast.Assign,ast.Expr))
            if isinstance(node,ast.Assign):names.extend(t.id for t in node.targets)
        self.assertEqual(len(names),len(set(names)))
        self.assertFalse(any(isinstance(n,ast.Attribute) and n.attr in ('extend','insert','update','append') for n in ast.walk(tree)))
        self.assertNotIn('EXTRA_STRUCTURES',names)

    def test_late_content_and_overwritten_achievements_preserved(self):
        self.assertTrue({'Voidfang Scimitar','Plague Scythe','Stormcaller Spear','Nightmare Glaive','Frostbite Axe','Soulrender Blade',"Titan's Fist",'Celestial Archblade'} <= {r['name'] for r in data.WEAPONS})
        self.assertTrue({'Plague Sceptre','Stormrider Staff','Soulweaver Rod'} <= {r['name'] for r in data.STAFFS})
        self.assertIn('Voidfang Scimitar',data.MERCHANT_ITEMS['Whispering Woods'])
        self.assertIn('Whispering Skull',{r['name'] for r in data.LOOT_ITEMS})
        self.assertEqual(data.DUNGEON_MONSTERS['Whispering Woods'][1]['name'],'Thornmaw Beast')
        for region,structures in data.REGION_STRUCTURES.items():
            self.assertIn(region.split()[0]+' Shrine',{s['name'] for s in structures})
        self.assertEqual(len(data.ACHIEVEMENTS),17)
        self.assertIn('first_blood',data.ACHIEVEMENTS);self.assertIn('first_victory',data.ACHIEVEMENTS)

    def test_dreamscape_is_original_game_ending(self):
        g=new_game();g['region']=g['unlocked']=data.REGIONS.index('The Dreamscape')
        encounter(g,boss=True);self.assertEqual(g['enemy']['name'],'The Dreaming God')
        g['enemy']['hp']=0;finish(g)
        self.assertTrue(g['victory']);self.assertTrue(chapter_one_complete(g))
        self.assertEqual(story_progress(g)['chapter'],2)
        self.assertIn('CHAPTER 1 COMPLETE',' '.join(g['log']))
        self.assertEqual(g['bosses'],[14]) # Victory uses the final boss and region unlocks, not a Creator kill.
        self.assertNotIn("Creator's Realm",data.REGIONS)

    def test_creator_cannot_trigger_original_game_ending(self):
        g=new_game();g['region']=g['unlocked']=14
        encounter(g,boss=True);g['enemy']['name']='The Creator';g['enemy']['hp']=0
        finish(g);self.assertFalse(g['victory']);self.assertFalse(chapter_one_complete(g))
        self.assertEqual(story_progress(g)['chapter'],1)
        bad=deepcopy(g);bad['victory']=True
        self.assertFalse(validate_save(bad)['victory'])

    def test_crafting_structures_are_all_village_services(self):
        self.assertEqual(set(data.STRUCTURES),{'forge','loom','enchantment_tower','alchemy_lab','disenchantry','source_temple'})
        self.assertTrue(all(s['location']=='Village' for s in data.STRUCTURES.values()))

    def test_craft_upgrade_staff_infuse_and_salvage(self):
        g=new_game();g['player']['gold']=1000;g['shards']=20
        attack=g['player']['atk'];defense=g['player']['def']
        act(g,'craft',{'structure':'forge'});act(g,'craft',{'structure':'loom'})
        self.assertEqual(g['player']['atk'],attack+2);self.assertEqual(g['player']['def'],defense+1)
        inputs=[r['id'] for r in g['runes'][:2]]
        act(g,'craft',{'structure':'enchantment_tower','rune_ids':inputs})
        staff=g['runes'][-1];self.assertEqual(staff['kind'],'staff')
        ice=next(r for r in g['runes'] if r['name']=='Ice Rune')
        act(g,'craft',{'structure':'source_temple','staff_id':staff['id'],'rune_ids':[ice['id']]})
        self.assertIn('freeze',g['runes'][-1]['components'])
        self.assertFalse(any(r['id']==ice['id'] for r in g['runes']))
        restored=validate_save(g);self.assertEqual(restored,g)
        encounter(g);act(g,'cast',{'rune_id':staff['id']})
        g['enemy']=None
        old=g['shards'];act(g,'craft',{'structure':'disenchantry','rune_ids':[staff['id']]})
        self.assertEqual(g['shards'],old+1)
        self.assertFalse(any(r['id']==staff['id'] for r in g['runes']))

    def test_crafting_failures_do_not_spend_resources(self):
        client=app.test_client();before=client.get('/api/state').json
        response=client.post('/api/action',json={'action':'craft','structure':'enchantment_tower','rune_ids':[]})
        self.assertEqual(response.status_code,400);self.assertEqual(before,client.get('/api/state').json)
        g=new_game();encounter(g)
        with self.assertRaises(ValueError):act(g,'craft',{'structure':'forge'})
        g=new_game();g['runes']=g['runes'][:1]
        with self.assertRaises(ValueError):act(g,'craft',{'structure':'disenchantry','rune_ids':[g['runes'][0]['id']]})

if __name__=='__main__':unittest.main()
