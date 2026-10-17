"""Regional companion food, finite feeding and exploration-driven hunger."""

import data

HUNGER_DRAIN = 5
READY_HUNGER = 30
EVOLUTION_TITLES = {
    'fire': 'Sunfire', 'ice': 'Everfrost', 'water': 'Tidebound',
    'earth': 'Mountainheart', 'nature': 'Elderwood', 'shadow': 'Nightveil',
    'poison': 'Venomcrest', 'void': 'Riftborn', 'light': 'Starcrowned',
    'crystal': 'Prismatic', 'arcane': 'Dreamwoven', 'soul': 'Soulbound',
    'storm': 'Tempest',
}


def form_name(companion):
    stage = companion.get('stage', 0)
    if stage >= 2:
        return EVOLUTION_TITLES.get(companion.get('element'), 'Ascendant') + ' ' + companion['name']
    if stage == 1:
        return 'Awakened ' + companion['name']
    return companion['name']


def evolve(companion):
    before = companion.get('stage', 0)
    xp = companion.get('xp', 0)
    if before == 0 and xp >= 3:
        companion['stage'] = 1
    elif before == 1 and xp >= 6:
        companion['stage'] = 2
    companion['form_name'] = form_name(companion)
    return companion.get('stage', 0) > before


def normalise(companion, fallback_region='Whispering Woods'):
    home = next((region for region, group in data.COMPANIONS.items()
                 if any(c['name'] == companion['name'] for c in group)), fallback_region)
    companion.setdefault('home_region', home)
    companion.setdefault('hunger', 100)
    companion.setdefault('meals_eaten', 0)
    companion['form_name'] = form_name(companion)
    return companion


def foods(companion):
    home = normalise(companion)['home_region']
    names = data.VILLAGE_STOCK.get(home, {}).get('food', [])
    return [food for food in data.FOOD_ITEMS if food['name'] in names]


def ready(companion):
    return (companion.get('can_battle', False) and companion.get('stage', 0) > 0
            and companion.get('hunger', 100) >= READY_HUNGER)


def wander(player):
    for companion in player.get('companions', []):
        normalise(companion, player['region'])
        before = companion['hunger']
        companion['hunger'] = max(0, before - HUNGER_DRAIN)
        if before >= READY_HUNGER > companion['hunger']:
            print(f"🐾 {companion['name']} is hungry ({companion['hunger']}/100) and will rest instead of assisting. Feed food from {companion['home_region']} through Character → Companions.")
        elif before > 0 and companion['hunger'] == 0:
            print(f"🐾 {companion['name']} is very hungry. They stay with you but need their regional food.")


def feed(player, companion, inventory_index):
    normalise(companion, player['region'])
    inventory = player.get('inventory', [])
    if type(inventory_index) is not int or not 0 <= inventory_index < len(inventory):
        return False, 'Choose a carried food.'
    item = inventory[inventory_index]
    food = next((f for f in foods(companion) if f['name'] == item.get('name')), None)
    if not food:
        return False, f"{companion['name']} eats food from {companion['home_region']}. That food is unsuitable."
    if companion['hunger'] >= 100:
        return False, 'Already full. Your food is kept.'
    inventory.pop(inventory_index)
    companion['hunger'] = min(100, companion['hunger'] + food['hunger'])
    companion['meals_eaten'] += 1
    companion['xp'] = companion.get('xp', 0) + 1
    evolved = evolve(companion)
    message = (f"{companion['form_name']} ate {food['name']}: hunger {companion['hunger']}/100, "
               f"stage {companion.get('stage', 0)}, evolution XP {companion['xp']}. One food consumed.")
    if evolved:
        message += ' EVOLVED into ' + companion['form_name'] + '!'
        if companion['stage'] == 2:
            message += ' Final forms have stronger passive battle support.'
    return True, message



def menu(game):
    player = game.player
    companions = player.get('companions', [])
    if not companions:
        print('You have no companions. You may meet them while wandering; up to three can join.')
        return
    while True:
        print('\n--- COMPANIONS · CARE & STATUS ---')
        for i, companion in enumerate(companions, 1):
            normalise(companion, player['region'])
            status = ('Ready to assist' if ready(companion) else
                      'Hungry: resting' if companion['hunger'] < READY_HUNGER else
                      'Needs stage 1' if companion.get('can_battle') else 'Peaceful companion')
            print(f"{i}. {companion['form_name']} · {companion.get('element', 'unknown')} · stage {companion.get('stage', 0)} · evolution XP {companion.get('xp', 0)}")
            print(f"   Hunger {companion['hunger']}/100 · {status} · home: {companion['home_region']}")
            print('   Eats: ' + ', '.join(f['name'] for f in foods(companion)))
        print('Hunger falls 5 per wander. Below 30, companions rest from combat and earn no battle XP. Feeding one suitable carried food restores its listed hunger and adds 1 evolution XP (stage 1 at 3; stage 2 at 6). Stage 1 awakens their combat support if they are a battle species; stage 2 gives a named final form and stronger passive support. Peaceful species also evolve but stay peaceful. They never leave or die from hunger.')
        print('1. Feed a companion\n2. Regional food guide\n0. Back')
        choice = input('Companions > ').strip()
        if choice == '0':
            return
        if choice == '2':
            for companion in companions:
                print(companion['name'] + ' — buy takeaway food at a restaurant in ' + companion['home_region'] + ': ' + ', '.join(f"{f['name']} (+{f['hunger']})" for f in foods(companion)))
            continue
        if choice != '1':
            continue
        try:
            index = int(input('Companion number (0 cancel) > ')) - 1
        except ValueError:
            continue
        if not 0 <= index < len(companions):
            continue
        companion = companions[index]
        allowed = {f['name']: f for f in foods(companion)}
        carried = [(i, item) for i, item in enumerate(player.get('inventory', [])) if item.get('name') in allowed]
        if not carried:
            print('You have no suitable carried food. Buy takeaway food in ' + companion['home_region'] + '.')
            continue
        for n, (_, item) in enumerate(carried, 1):
            print(f"{n}. {item['name']} — +{allowed[item['name']]['hunger']} hunger (uses one)")
        try:
            food_index = int(input('Food number (0 cancel) > ')) - 1
        except ValueError:
            continue
        if 0 <= food_index < len(carried):
            print(feed(player, companion, carried[food_index][0])[1])
