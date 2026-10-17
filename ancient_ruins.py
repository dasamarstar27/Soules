"""Non-tradeable archaeological finds reserved for Season Three."""

import random
import data

REGION_ELEMENTS = {
    region: data.REGION_ITEM_ELEMENTS[region][0]
    for region in data.REGIONS
}


def search(player, structure, region, rng=random):
    site = region + '::' + structure['name']
    cycle = player.get('wander_count', 0) // 20
    records = player.setdefault('ruin_searches', {})
    if records.get(site) == cycle:
        print('This part of the ruins has been searched. Return after the next 20-wander milestone.')
        return None
    records[site] = cycle
    roll = rng.random()
    if roll >= .6:
        print('You find weathered stone and faded writing, but nothing you can safely recover.')
        return None
    kind = 'fragment' if roll < .35 else 'tome'
    origin = 'Riftlands' if region == data.SECRET_REGION else region
    element = REGION_ELEMENTS.get(origin, 'void')
    relic = dict(
        id=site + '::' + kind,
        name=(f'{origin} Broken-Core Fragment' if kind == 'fragment'
              else f'Tome of {origin} — Before the Fall'),
        kind=kind, region=origin, element=element,
        protected=True, reserved_for='Season Three',
    )
    relic['text'] = (
        'A surviving splinter of one of the eleven destroyed elemental cores. '
        'Its use is unknown; keep it for Season Three.'
        if kind == 'fragment' else
        'The pages record the old civilisation and the war in which eleven cores '
        'were destroyed and only four civilisations survived. Much of the writing '
        'cannot yet be understood.'
    )
    bag = player.setdefault('protected_relics', [])
    if any(old['id'] == relic['id'] for old in bag):
        print('You recognise the same record already preserved in your collection. Nothing is duplicated.')
        return None
    bag.append(relic)
    print(f"Recovered: {relic['name']}. Protected for Season Three: cannot be sold, salvaged or used for imbuing.")
    return relic


def visit(game, structure, region):
    p = game.player
    game.advance_quest('explore_structure', region)
    print('\n--- ' + structure['name'].upper() + ' ---')
    if region == data.SECRET_REGION:
        print('These displaced ruins were carried here from the mortal regions by the rift.')
    else:
        print('The ruins of an old elemental civilisation stand here. Its broken walls remember the war and the destruction of the cores.')
    print('1. Search for ancient finds\n2. Read recovered tomes / inspect fragments\n0. Leave')
    print('Search chances: 35% core fragment, 25% tome, 40% nothing. One search per site each 20-wander cycle; each type can be recovered here only once.')
    choice = input('Ruins > ').strip()
    if choice == '1':
        search(p, structure, region, game.random)
    elif choice == '2':
        origin = 'Riftlands' if region == data.SECRET_REGION else region
        finds = [relic for relic in p.get('protected_relics', []) if relic['region'] == origin]
        for relic in finds:
            print(relic['name'] + '\n' + relic['text'])
        if not finds:
            print('No finds from this civilisation yet.')
