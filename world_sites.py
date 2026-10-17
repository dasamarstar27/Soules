"""Finite construction resource sites and peaceful regional watch posts."""
import original_ui as ui


def visit(game, struct, region):
    previous = ui.location
    ui.location = dict(name=struct['name'], kind=struct['type'], region=region)
    try:
        print('\n--- ' + struct['name'].upper() + ' ---')
        if struct['type'] == 'watchpost':
            print('A watchkeeper marks safe settlements on a worn map. The monsters were once peaceful; now the roads need guarding.')
            print('1. Ask for a village direction\n2. Read local side quests\n0. Leave')
            choice = input('Watch post > ').strip()
            if choice == '1':
                candidates = [x for x in game.REGION_STRUCTURES.get(region, []) if x['type'] == 'village']
                found = game.player.setdefault('discovered_structures', {}).setdefault(region, [])
                unknown = [x for x in candidates if x['name'] not in found]
                if unknown:
                    village = game.random.choice(unknown)
                    found.append(village['name'])
                    print('The keeper shows you the route to ' + village['name'] + '. It is now in your Village Directory.')
                else:
                    print('You already know every ordinary village here. Hidden elemental settlements are not marked on this map.')
            elif choice == '2':
                game.quest_board(region)
            return
        material = 'Stone' if struct['type'] == 'quarry' else 'Timber'
        print(f'1. Work for 2 {material}\n0. Leave\nOne gathering trip per site each 20-wander cycle. No charge; supplies are finite.')
        if input('Work site > ').strip() != '1':
            return
        record = game.player.setdefault('work_sites', {})
        key = region + '::' + struct['name']
        cycle = game.player.get('wander_count', 0) // 20
        if record.get(key) == cycle:
            print('This site needs time to replenish.'); return
        record[key] = cycle
        bag = game.player.setdefault('building_materials', {})
        bag[material] = bag.get(material, 0) + 2
        print(f'Gathered 2 {material} for village construction.')
    finally:
        ui.location = previous
