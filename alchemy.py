"""Ingredient experiments, original recipes, and consumable potion mixtures."""
from collections import Counter
from copy import deepcopy
import random
import re
import uuid
from data import REGION_INGREDIENTS, INGREDIENT_COMBOS, POTION_RECIPES, REGIONS
from effects import EFFECTS, apply, heal, hurt, cure

INGREDIENTS = {}
BOONS = ['regen','mana_regen','defense_up','speed_up']
for region, names in REGION_INGREDIENTS.items():
    for index,name in enumerate(names):
        INGREDIENTS[name] = dict(name=name, region=region, heal=8+index*3, mana=3+index,
                                 boon=BOONS[index%4])
# Translate the old potion descriptions into explicit mechanics, keeping all recipes.
def legacy_formula(recipe):
    effect=recipe['effect']; name=recipe['name']; desc=recipe.get('desc','')
    result=dict(heal=0,mana=0,full=False,statuses=[],cures=[],wild=False,bad=False)
    match=re.match(r'heal_(\d+)',effect)
    if match:result['heal']=int(match[1])
    if 'atk' in effect:
        match=re.search(r'atk_(?:boost_)?(\d+)',effect)
        result['statuses']=['potion_attack_'+(match[1] if match else '10')]
    if effect.startswith('def_boost'):result['statuses']=['potion_defense_'+effect.rsplit('_',1)[1]]
    if effect=='cure_status':result['cures']=['all']
    if effect=='cure_void':result['cures']=['void','void_burn','curse']
    if effect=='genesis':result['full']=True
    if effect=='mana_full':result['mana']=9999
    if effect=='luck_boost':result['statuses']=['divine_luck']
    if effect=='skip_fight':result['statuses']=['sleep']
    if effect=='random_wild':result['wild']=True
    if effect=='random_bad':result['bad']=True
    if 'cost10' in effect:result['health_cost']=10
    for text,keys in [('cures freeze',['freeze','glacial_chill']),('cures bleed',['bleed']),('cures sleep/fear',['sleep','fear'])]:
        if text in desc:result['cures']+=keys
    return result

NAMED = {tuple(sorted(inputs)):dict(name=r['name'],formula=legacy_formula(r)) for inputs,r in INGREDIENT_COMBOS.items()}
SHOP = {r['name']:dict(name=r['name'],formula=legacy_formula(r),price=max(15,r['cost']//4),stock=3) for r in POTION_RECIPES}
SHOP['Empty Bottle']=dict(name='Empty Bottle',price=5,stock=8)

def describe(f):
    parts=[]
    if f.get('full'):parts.append('Fully restores health and mana')
    else:
        if f.get('heal'):parts.append(f"Restores {f['heal']} health")
        if f.get('mana'):parts.append('Restores all mana' if f['mana']>=999 else f"Restores {f['mana']} mana")
    if f.get('statuses'):
        for key in f['statuses']:
            e=EFFECTS[key]
            parts.append(('Enemy: ' if key=='sleep' else '')+e['name']+f" for {e['duration']} turns: "+e['description'].rstrip('.'))
    if f.get('cures'):parts.append('Cleanses harmful effects' if 'all' in f['cures'] else 'Cures '+', '.join(f['cures']).replace('_',' '))
    if f.get('wild'):parts.append('Unstable: randomly heals or poisons the drinker')
    if f.get('bad'):parts.append('Toxic: poisons the drinker')
    if f.get('health_cost'):parts.append(f"Costs {f['health_cost']} health to drink")
    return '. '.join(parts)+'.'

def potion(name,formula):
    return dict(id=uuid.uuid4().hex,name=name,formula=deepcopy(formula),desc=describe(formula))

def starter():
    return dict(ingredients={'Thorn Petal':2,'Dew Blossom':2},bottles=3,brews=[],recipe_book={},
                shop_stock={k:v['stock'] for k,v in SHOP.items()},forages=0)

def merge_formulas(formulas):
    # Caps prevent repeatedly combining mixtures into unlimited one-hit consumables.
    return dict(heal=min(160,sum(f.get('heal',0) for f in formulas)),
        mana=min(9999,sum(f.get('mana',0) for f in formulas)),full=any(f.get('full') for f in formulas),
        statuses=list(dict.fromkeys(k for f in formulas for k in f.get('statuses',[])))[:4],
        cures=list(dict.fromkeys(k for f in formulas for k in f.get('cures',[]))),
        wild=any(f.get('wild') for f in formulas),bad=any(f.get('bad') for f in formulas),
        health_cost=min(30,sum(f.get('health_cost',0) for f in formulas)))

def experiment(g,ingredients,potion_ids):
    if not isinstance(ingredients,list) or not isinstance(potion_ids,list) or any(not isinstance(n,str) for n in ingredients+potion_ids):
        raise ValueError('Choose ingredients and potions from your satchel.')
    if len(ingredients)+len(potion_ids)!=2:raise ValueError('Mix exactly two things: ingredients, potions, or one of each.')
    ingredients=sorted(ingredients)
    counts=Counter(ingredients)
    if any(n not in INGREDIENTS or g['ingredients'].get(n,0)<qty for n,qty in counts.items()):raise ValueError('You do not have enough of those ingredients.')
    if len(set(potion_ids))!=len(potion_ids):raise ValueError('You need two separate bottles to mix two potions.')
    owned={p['id']:p for p in g['brews']}
    if any(i not in owned for i in potion_ids):raise ValueError('That potion is no longer in your satchel.')
    if not potion_ids and g['bottles']<1:raise ValueError('Buy an empty bottle before brewing.')
    signature=' + '.join(sorted(ingredients+['Potion: '+owned[i]['name'] for i in potion_ids]))
    if len(signature)>1000:raise ValueError('This mixture is too complicated. Try a simpler potion.')
    known=NAMED.get(tuple(sorted(ingredients))) if not potion_ids else None
    if known:
        name=known['name'];formula=deepcopy(known['formula'])
    else:
        formulas=[owned[i]['formula'] for i in potion_ids]
        formulas += [dict(heal=INGREDIENTS[n]['heal'],mana=INGREDIENTS[n]['mana'],statuses=[INGREDIENTS[n]['boon']]) for n in ingredients]
        formula=merge_formulas(formulas)
        if potion_ids:name='Infused '+owned[potion_ids[0]]['name'] if ingredients else 'Blended Elixir'
        else:name=ingredients[0]+' & '+ingredients[1]+' Tonic'
    for n,qty in counts.items():g['ingredients'][n]-=qty
    g['brews']=[p for p in g['brews'] if p['id'] not in potion_ids]
    if not potion_ids:g['bottles']-=1
    elif len(potion_ids)==2:g['bottles']+=1
    result=potion(name,formula);g['brews'].append(result)
    first=signature not in g['recipe_book']
    g['recipe_book'][signature]=dict(name=name,inputs=sorted(ingredients+['Potion: '+owned[i]['name'] for i in potion_ids]),desc=result['desc'])
    g['log'].append(('Recipe discovered! ' if first else 'Brewed again: ')+name+'. '+result['desc'])
    return result

def forage(g,rng=random):
    pool=list(REGION_INGREDIENTS[REGIONS[g['region']]])
    if g['region']==len(REGIONS)-1 and g['victory']:pool+=REGION_INGREDIENTS["Creator's Realm"]
    found=[rng.choice(pool) for _ in range(3)]
    for name in found:g['ingredients'][name]=g['ingredients'].get(name,0)+1
    g['forages']+=1
    # Stock replenishes after time spent gathering, never on page reload.
    if g['forages']%3==0:g['shop_stock']={k:v['stock'] for k,v in SHOP.items()}
    g['log'].append('Gathered: '+', '.join(found)+'.'+(' The apothecary has restocked.' if g['forages']%3==0 else ''))

def buy(g,name):
    if name not in SHOP:raise ValueError('Choose an item from the apothecary.')
    item=SHOP[name]
    if g['shop_stock'][name]<=0:raise ValueError('Sold out. Gather ingredients three times to refresh stock.')
    if g['player']['gold']<item['price']:raise ValueError('You need more gold. Exploring and winning battles earns gold.')
    g['player']['gold']-=item['price'];g['shop_stock'][name]-=1
    if name=='Empty Bottle':g['bottles']+=1
    else:g['brews'].append(potion(name,item['formula']))
    g['log'].append('Bought '+name+'.')

def drink(g,rid,rng=random):
    found=next((p for p in g['brews'] if p['id']==rid),None)
    if not found:raise ValueError('Choose a potion you still own.')
    f=found['formula'];p=g['player'];log=g['log']
    if 'sleep' in f.get('statuses',[]) and not g['enemy']:raise ValueError('Dream Vial needs an enemy. Use it during combat.')
    if p['hp']<=0:raise ValueError('Rest at the sanctuary before drinking a potion.')
    g['brews'].remove(found);g['bottles']+=1
    for key in list(p['status']):
        if ('all' in f.get('cures',[]) and EFFECTS[key]['target']=='enemy') or key in f.get('cures',[]):del p['status'][key]
    if f.get('health_cost'):hurt(p,f['health_cost'],log)
    amount=heal(p,p['max_hp'] if f.get('full') else f.get('heal',0))
    p['mana']=min(p['max_mana'],p['mana']+(p['max_mana'] if f.get('full') else f.get('mana',0)))
    for key in f.get('statuses',[]):apply(g['enemy'] if key=='sleep' else p,key,log,p,rng)
    if f.get('bad') or (f.get('wild') and rng.random()<.5):apply(p,'poison',log,rng=rng)
    elif f.get('wild'):heal(p,60)
    log.append(f"Drank {found['name']}. Restored {round(amount)} health. Empty bottle recovered.")

def catalog():
    return dict(ingredients=list(INGREDIENTS.values()),shop=[dict(**item,desc=describe(item['formula']) if 'formula' in item else 'Holds one experiment. Recovered when drinking a potion.') for item in SHOP.values()],named_count=len(NAMED))

def validate(g):
    import math
    for key in ('bottles','forages'):
        if type(g[key])is not int or not 0<=g[key]<=1000000:raise ValueError('Invalid alchemy supplies.')
    if not isinstance(g['ingredients'],dict) or any(n not in INGREDIENTS or type(v)is not int or not 0<=v<=1000000 for n,v in g['ingredients'].items()):raise ValueError('Invalid ingredient satchel.')
    if not isinstance(g['shop_stock'],dict) or set(g['shop_stock'])!=set(SHOP) or any(type(v)is not int or not 0<=v<=SHOP[n]['stock'] for n,v in g['shop_stock'].items()):raise ValueError('Invalid potion stock.')
    if not isinstance(g['brews'],list) or len(g['brews'])>10000:raise ValueError('Invalid potions.')
    ids=[]
    for p in g['brews']:
        if not isinstance(p,dict) or set(p)!= {'id','name','formula','desc'} or any(not isinstance(p[k],str) or len(p[k])>2000 for k in ('id','name','desc')):raise ValueError('Invalid potion bottle.')
        ids.append(p['id']);f=p['formula']
        allowed={'heal','mana','full','statuses','cures','wild','bad','health_cost'}
        if not isinstance(f,dict) or set(f)-allowed:raise ValueError('Invalid potion formula.')
        for k in ('heal','mana','health_cost'):
            v=f.get(k,0)
            if type(v)not in (int,float) or not math.isfinite(v) or not 0<=v<=10000:raise ValueError('Invalid potion strength.')
        for k in ('full','wild','bad'):
            if type(f.get(k,False))is not bool:raise ValueError('Invalid potion property.')
        for k in ('statuses','cures'):
            if not isinstance(f.get(k,[]),list) or any(not isinstance(e,str) or (e not in EFFECTS and not(k=='cures' and e=='all')) for e in f.get(k,[])):raise ValueError('Invalid potion effects.')
    if len(set(ids))!=len(ids):raise ValueError('Duplicate potion bottles.')
    if not isinstance(g['recipe_book'],dict) or len(g['recipe_book'])>10000:raise ValueError('Invalid recipe book.')
    for signature,r in g['recipe_book'].items():
        if len(signature)>1000 or not isinstance(r,dict) or set(r)!={'name','inputs','desc'} or any(not isinstance(r[k],str) or len(r[k])>2000 for k in ('name','desc')) or not isinstance(r['inputs'],list) or len(r['inputs'])!=2 or any(not isinstance(n,str) or len(n)>1000 for n in r['inputs']):raise ValueError('Invalid discovered recipe.')
