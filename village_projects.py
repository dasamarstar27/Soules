"""One hundred named, paid community projects with persistent local benefits.

These are construction projects, not a claim that the separate 100-addon design
backlog has been implemented. Each service has ten projects; settlements offer
only projects compatible with the services they actually possess.
"""
import hashlib

NAMES = {
    'forge': ['Covered bellows','Quenching trough','Charcoal store','Anvil foundation','Ore sorting table','Tempering furnace','Tool racks','Apprentice shelter','Balanced hammers','Master smith annex'],
    'loom': ['Drying lines','Spindle rack','Dye vats','Pattern desk','Weatherproof yarn store','Cutting table','Reinforced loom','Needle workshop','Weavers guildhall','Master pattern room'],
    'tower': ['Focus stand','Insulated floor','Crystal shelves','Staff balancing rig','Conduit braces','Ward engraving desk','Power test chamber','Arcane ventilation','Enchanter study','Resonance chamber'],
    'alchemy': ['Herb washbasin','Reagent cabinets','Glass cooling rack','Ventilated still','Stone mixing benches','Sealed jars','Apothecary sink','Recipe archive','Purification coils','Master distillery'],
    'disenchantry': ['Sorting bins','Safety screens','Salvage tongs','Runic clamps','Material separator','Recovery press','Dust collectors','Protected dismantling bench','Recycler workshop','Reclamation hall'],
    'temple': ['Pilgrim steps','Quiet alcove','Channel markers','Core safety rails','Prayer benches','Harmonic instruments','Attunement chamber','Warden archive','Channel insulation','Guardian observatory'],
    'restaurant': ['Public kitchen','Clean water well','Bread oven','Root cellar','Spice shelves','Smokehouse','Refugee dining room','Market serving stalls','Cook training room','Village feast hall'],
    'inn': ['Clean bedding','Rainproof roof','Hearth repairs','Quiet guest rooms','Medic corner','Warm bath','Night watch lanterns','Travellers lounge','Infirmary wing','Restoration suite'],
    'farm': ['Irrigation ditch','Seed bank','Compost beds','Field fencing','Community greenhouse','Medicinal garden','Pollinator beds','Mushroom cellar','Terraced plots','Rare herb nursery'],
    'trade': ['Village storehouse','Road repairs','Market awnings','Weighing scales','Caravan hitching posts','Merchant noticeboard','Secure cargo shed','Public exchange','Artisan stalls','Regional trading hall'],
}
PROJECTS = tuple(dict(id=f'{key}:{i}', name=name, service=key, stage=i,
                     cost={'Timber': 2+i, 'Stone': 2+i, 'Iron fittings': 1+i//3}, gold=30+i*15)
                 for key, names in NAMES.items() for i, name in enumerate(names))
BY_ID = {p['id']: p for p in PROJECTS}


def completed(player, village):
    return player.setdefault('village_records', {}).setdefault(village['id'], {}).setdefault('projects', [])


def service_bonus(player, village, service):
    # +1 effective service quality per three completed local projects, max +3.
    return min(3, sum(BY_ID[x]['service'] == service for x in completed(player, village) if x in BY_ID)//3)


def offers(village):
    seed = int(hashlib.sha256(village['id'].encode()).hexdigest()[:8], 16)
    # Starter projects plus a different selection in every village. The final
    # project is unlocked locally by completing two earlier projects.
    return [p for p in PROJECTS if p['service'] in village['services'] and
            (p['stage'] < 2 or (p['stage'] + seed) % 3 != 0)]


def build(player, village, project_id):
    import village_life as v
    project = BY_ID.get(project_id)
    if not project or project not in offers(village):
        return False, 'This project is not available in this settlement.'
    done = completed(player, village)
    if project_id in done:
        return False, 'Already built here.'
    local_count = sum(BY_ID[x]['service'] == project['service'] for x in done if x in BY_ID)
    if project['stage'] >= 8 and local_count < 2:
        return False, 'Finish two earlier projects for this service first.'
    materials = player.setdefault('building_materials', {})
    if player['gold'] < project['gold'] or any(materials.get(k, 0) < n for k, n in project['cost'].items()):
        return False, 'Not enough materials or souls.'
    for key, amount in project['cost'].items():
        materials[key] -= amount
    player['gold'] -= project['gold']
    done.append(project_id)
    record = v.state(player, village)
    record['reputation'] = min(100, record.get('reputation', 0) + 1)
    return True, f"Built {project['name']}! +1 local reputation. {local_count+1} {project['service']} projects complete; every third gives +1 service quality (maximum +3)."


def menu(game, village):
    while True:
        done = completed(game.player, village)
        rows = offers(village)
        print('\n--- COMMUNITY PROJECTS · '+village['name']+' ---')
        print('100 projects across the world; only locally compatible projects are offered here. Each costs supplies, grants +1 reputation, and every third for one service grants +1 effective quality. Buildings and projects stay in this village.')
        for i, p in enumerate(rows, 1):
            cost = ', '.join(f'{n} {k}' for k, n in p['cost'].items())
            print(f"{i}. {p['name']} [{p['service']}] — {'BUILT' if p['id'] in done else cost+', '+str(p['gold'])+' souls'}")
        print('0. Back')
        try:
            index = int(input('Project > '))-1
        except ValueError:
            continue
        if index == -1:
            return
        if not 0 <= index < len(rows):
            continue
        p = rows[index]
        if input('Fund this local project? (y/n) > ').strip().lower() != 'y':
            continue
        print(build(game.player, village, p['id'])[1])
