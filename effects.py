"""One registry and turn lifecycle for every rune and legacy status."""
from copy import deepcopy
import random
from data import RUNES, STATUS_EFFECTS
from status_effects import RUNE_EFFECTS, BOSS_EXCLUSIVE_STATUS, STATUS_CURES

EFFECTS = deepcopy(RUNE_EFFECTS)
# Explicit mechanics for the advanced runes missing from the old registry.
EXTRA = {
 'arcane_burn': dict(damage_per_turn=5, pierce_defense=True),
 'plasma_chain': dict(damage_per_turn=5, stun_chance=.3),
 'sonic_echo': dict(damage=8, attack_count=2),
 'ember_crystal': dict(atk_modifier=1.25, crit_chance=.3),
 'glacial_tide': dict(damage=12, spd_modifier=.5),
 'steel_root': dict(def_modifier=1.6, reflect_damage=.3),
 'radiant_aura': dict(hp_restore_per_turn=5, effect_resistance=.3),
 'phase_shift': dict(dodge_chance=.5),
 'blood_decay': dict(damage_per_turn=4, attacker_heal=.5),
 'primal_force': dict(atk_modifier=1.5, def_modifier=1.2),
 'vortex_storm': dict(damage_per_turn=5, spd_modifier=.6),
 'quartz_shine': dict(def_modifier=1.4, hp_restore_per_turn=2),
 'spectral_lash': dict(damage=14, def_bypass=True),
 'inferno_wave': dict(damage=12, damage_per_turn=4),
 'frost_nova': dict(damage=8, frozen=True),
 'thunder_clap': dict(damage=12, stun_chance=.5),
 'tide_blast': dict(damage=15, def_modifier=.8),
 'iron_skin': dict(def_modifier=1.7),
 'aurora_surge': dict(hp_restore_per_turn=4, mana_restore_per_turn=4),
 'lunar_flame': dict(damage_per_turn=4, atk_modifier=.8),
 'shadow_flame': dict(damage_per_turn=4, accuracy_penalty=.3),
 'prism_shard': dict(damage=18, def_bypass=True),
 'magnetic_pull': dict(spd_modifier=.4, def_modifier=.8),
 'tempest_charge': dict(spd_modifier=1.5, atk_modifier=1.25),
 'void_fire': dict(damage_per_turn=6, cannot_heal=True),
 'eternal_light': dict(hp_restore_per_turn=6, effect_resistance=.5),
 'fate_seal': dict(execute_threshold=.3, atk_modifier=.8),
 'harmony_wave': dict(hp_restore_per_turn=4, mana_restore_per_turn=5),
 'ruin_blast': dict(damage=22, def_modifier=.6),
 'glimmer_shield': dict(damage_reduction=.35),
 'ember_wing': dict(atk_modifier=1.2, dodge_chance=.3),
 'seismic_tremor': dict(damage=14, stunned=True),
 'stormheart': dict(atk_modifier=1.3, reflect_damage=.3),
 'soulflare': dict(damage=12, attacker_heal=.7),
 'frostbrand': dict(damage_per_turn=3, spd_modifier=.5),
 'radiant_dawn': dict(hp_restore_per_turn=5, resurrect_once=True),
 'silence_field': dict(silenced=True),
 'enhance_fusion': dict(fusion_multiplier=1.5),
 'barrier': dict(damage_reduction=.3), 'momentum': dict(spd_modifier=1.5, atk_modifier=1.2),
 'shard_burst': dict(damage=18),
 'bleed': dict(damage_per_turn=6), 'void': dict(damage_per_turn=8),
 'slow': dict(spd_modifier=.5), 'silence': dict(silenced=True),
 'weaken': dict(atk_modifier=.7), 'necrosis': dict(damage_per_turn=7),
 'creation': dict(hp_restore_per_turn=6, mana_restore_per_turn=5, all_stats_modifier=1.3),
 'elemental_balance': dict(all_stats_modifier=1.2), 'supercharge': dict(atk_modifier=1.5),
 'fusion_boost': dict(fusion_multiplier=1.5), 'time_loop': dict(resurrect_once=True),
 'bloodlust': dict(atk_modifier=1.4, lifesteal=.3),
 'earthquake': dict(damage=20, stunned=True),
 'frostshade': dict(frozen=True, accuracy_penalty=.3),
 'abyssal_soul': dict(damage_per_turn=6, all_stats_modifier=.8),
 'dragon_flame': dict(damage_per_turn=7, cannot_heal=True),
 'dawn_rebirth': dict(resurrect_once=True, hp_restore_per_turn=5),
 'colossus': dict(atk_modifier=1.8, def_modifier=1.5),
 'phantom': dict(dodge_chance=.4, attack_count=2),
 'entropy': dict(damage_per_turn=6, def_modifier=.6),
 'tide_of_life': dict(hp_restore_per_turn=7, mana_restore_per_turn=3),
}
for key, values in EXTRA.items():
    EFFECTS[key] = dict(name=key.replace('_',' ').title(), icon='✦', duration=3, **values)
for key, value in BOSS_EXCLUSIVE_STATUS.items():
    EFFECTS[key] = deepcopy(value)
# Infinite effects are bounded in this turn-based edition so battles remain escapable.
EFFECTS['ancient_curse'].update(duration=6, all_stats_modifier=.9)
EFFECTS['dimensional_rift'].update(dodge_chance=.3, accuracy_penalty=.2)
EFFECTS['reality_warp'].update(accuracy_penalty=.5)
EFFECTS['infinity_loop'].update(duration=3, trap_in_battle=True)
# Clarify ambiguous legacy fields into mechanics used by this engine.
EFFECTS['wraith_form'].pop('damage', None)
EFFECTS['wraith_form']['damage_reduction'] = .2
EFFECTS['warp']['dodge_chance'] = .8
EFFECTS['vortex_pull']['spd_modifier'] = .5
EFFECTS['necrotic_decay']['cannot_heal'] = True
EFFECTS['moon_guard']['night_bonus'] = 1.4
EFFECTS['ethereal_wisp']['damage_reduction'] = .2
BENEFICIAL = {
 'defense_up','speed_up','regen','heal_tick','crit_up','mana_regen','divine_luck',
 'moon_guard','warp','stability','greater_regen','double_cast','reflect','dragon_fury',
 'rebirth','giant_strength','holy_barrier','fortress','nature_blessing','reality_bend',
 'ember_blade','steel_guard','radiant_glow','ethereal_wisp','primal_roar','quartz_barrier',
 'berserk','sacrifice','thorns','blood_moon','ancient_power','wraith_form','ember_crystal',
 'steel_root','radiant_aura','phase_shift','primal_force','quartz_shine','iron_skin',
 'aurora_surge','tempest_charge','eternal_light','harmony_wave','glimmer_shield',
 'ember_wing','stormheart','radiant_dawn','enhance_fusion','barrier','momentum',
 'creation','elemental_balance','supercharge','fusion_boost','time_loop','bloodlust',
 'dawn_rebirth','colossus','phantom','tide_of_life',
}
# Battles have one opponent. Area and chain effects concentrate their pulses on it.
for info in EFFECTS.values():
    if info.get('chain_targets') or info.get('shock_chain'):
        info['damage_per_turn'] = info.get('damage_per_turn', 0) + 2
    if info.get('aoe'):
        info['damage'] = info.get('damage', 0) + 4
    if info.get('immobilized'):
        info.setdefault('spd_modifier', .1)
# These legacy flags are represented by the concrete mechanics above.
for key in ('ancient_curse',):
    EFFECTS[key].pop('stacking', None)
    EFFECTS[key].pop('stat_reduction_per_stack', None)
for info in EFFECTS.values():
    for field in ('aoe','chain_targets','shock_chain','teleport','pull_effect',
                  'intangible','random_repositioning','pierce_defense'):
        info.pop(field, None)
# Potion buffs share the same lifecycle as rune effects, with flat stat bonuses.
for stat_name,amounts in [('attack',(10,15,20,25)),('defense',(10,12,15))]:
    for amount in amounts:
        key=f'potion_{stat_name}_{amount}'
        EFFECTS[key]=dict(name=f'{stat_name.title()} Tonic +{amount}',icon='✧',duration=3,
                         **{('atk_flat' if stat_name=='attack' else 'def_flat'):amount})
        BENEFICIAL.add(key)

def effect_description(info):
    parts=[]
    modifiers={'atk_modifier':'Attack','def_modifier':'Defense','spd_modifier':'Speed',
               'all_stats_modifier':'All stats','max_hp_reduction':'Maximum health'}
    chances={'crit_chance':'critical-hit chance','dodge_chance':'dodge chance',
             'stun_chance':'chance to lose a turn','freeze_chance':'chance to freeze',
             'flee_chance':'chance to recoil in fear','effect_resistance':'chance to resist afflictions'}
    for key,value in info.items():
        if key in ('atk_flat','def_flat'):
            parts.append(f"{'Attack' if key=='atk_flat' else 'Defense'} +{value}")
        elif key in modifiers:
            change=round((value-1)*100)
            parts.append(f"{modifiers[key]} {'+' if change>=0 else ''}{change}%")
        elif key in chances:parts.append(f"{round(value*100)}% {chances[key]}")
        elif key=='damage_per_turn':parts.append(f"Loses {value} health each turn")
        elif key=='hp_restore_per_turn':parts.append(f"Restores {value} health each turn")
        elif key=='mana_restore_per_turn':parts.append(f"Restores {value} mana each turn")
        elif key=='damage':parts.append(f"Deals {value} immediate damage")
        elif key=='accuracy_penalty':parts.append(f"{round(value*100)}% chance to miss")
        elif key in ('damage_reduction','physical_reduction'):
            parts.append(f"Reduces {'physical ' if key=='physical_reduction' else ''}damage by {round(value*100)}%")
        elif key=='reflect_damage':parts.append(f"Reflects {round(value*100)}% of incoming damage")
        elif key in ('lifesteal','attacker_heal'):parts.append(f"Returns {round(value*100)}% of damage as health")
        elif key in ('frozen','stunned','sleeping') and value:parts.append('Cannot act until this effect ends')
        elif key=='immobilized' and value:parts.append('Movement and speed are restricted')
        elif key=='cannot_heal' and value:parts.append('Cannot recover health')
        elif key=='resurrect_once' and value:parts.append('Revives once at half health; full health with Dragon Fury')
        elif key=='execute_threshold':parts.append(f"Finishes foes below {round(value*100)}% health; guardians take bonus damage instead")
        elif key=='attack_count':parts.append(f"Weapon attack strikes {value} times")
        elif key=='hp_cost':parts.append(f"Costs {value} health when applied")
        elif key=='self_damage':parts.append(f"Caster takes {value} damage")
        elif key=='damage_boost':parts.append(f"Multiplies damage by {value}")
        elif key=='fusion_multiplier':parts.append(f"Multiplies fusion spell damage by {value}")
        elif key in ('light_damage','crystal_damage','undead_damage'):
            target={'light_damage':'light spells','crystal_damage':'crystal spells','undead_damage':'attacks against undead'}[key]
            parts.append(f"Multiplies {target} damage by {value}")
        elif key=='night_bonus':parts.append(f"Multiplies nighttime defense by {value}")
        elif key=='randomized' and value:parts.append('Applies a random harmful effect')
        elif key=='action_inversion' and value:parts.append('Attacks turn back on their caster')
        elif key=='trap_in_battle' and value:parts.append('Cannot flee while active')
        elif key=='silenced' and value:parts.append('Cannot invoke runes')
        elif key=='remove_from_battle' and value:parts.append('Banishes ordinary foes; guardians lose 10% health instead')
        elif key=='def_bypass' and value:parts.append('Ignores defense')
    return '. '.join(parts)+'.'

for key, info in EFFECTS.items():
    info['target'] = 'self' if key in BENEFICIAL else 'enemy'
    info['description'] = effect_description(info)
assert all(r['effect'] in EFFECTS for r in RUNES), 'Every rune must have mechanics'

def active(entity):
    return [EFFECTS[k] for k in entity.get('status', {}) if k in EFFECTS]

def total(entity, key):
    return sum(e.get(key, 0) for e in active(entity))

def stat(entity, key):
    value = entity.get(key, 0)
    field = {'atk':'atk_modifier','def':'def_modifier','speed':'spd_modifier'}[key]
    for effect in active(entity):
        value *= effect.get(field, 1) * effect.get('all_stats_modifier', 1)
        if key == 'def' and entity.get('is_night'):
            value *= effect.get('night_bonus', 1)
    value += total(entity, 'atk_flat' if key=='atk' else 'def_flat') if key in ('atk','def') else 0
    return max(0, value)

def heal(entity, amount):
    if total(entity, 'cannot_heal') or entity['hp'] <= 0:
        return 0
    before = entity['hp']
    cap = entity['max_hp']
    for e in active(entity):
        cap *= e.get('max_hp_reduction', 1)
    entity['hp'] = min(cap, entity['hp'] + max(0, amount))
    return max(0, entity['hp'] - before)

def hurt(entity, amount, log, source=None, reflect=True):
    amount = max(0, round(amount))
    entity['hp'] = max(0, entity['hp'] - amount)
    if entity['hp'] <= 0:
        rebirth = next((k for k in entity['status'] if EFFECTS[k].get('resurrect_once')), None)
        if rebirth:
            del entity['status'][rebirth]
            entity['hp'] = entity['max_hp'] * (1 if 'dragon_fury' in entity['status'] else .5)
            log.append(f"{entity['name']} is reborn from the ashes!")
    if source and reflect:
        returned = min(.8, total(entity, 'reflect_damage'))
        if returned and amount:
            hurt(source, amount * returned, log, reflect=False)
            log.append(f"{entity['name']} reflects {round(amount * returned)} damage.")
    return amount

def hit(source, target, power, log, rng=random, piercing=False, magical=False, element=None):
    if total(source, 'action_inversion') and target is not source:
        target = source
        log.append('Reality Warp turns the strike back on its caster!')
    if element in ('light','radiant'):
        power *= max(1, total(source, 'light_damage'))
    if element in ('crystal','quartz'):
        power *= max(1, total(source, 'crystal_damage'))
    if target.get('undead'):
        power *= max(1, total(source, 'undead_damage'))
    if rng.random() < min(.75, total(target,'dodge_chance')):
        log.append(f"{target['name']} evades the strike.")
        return 0
    if rng.random() < min(.8, total(source,'accuracy_penalty')):
        log.append(f"{source['name']}'s attack misses.")
        return 0
    if rng.random() < min(.8, .05 + total(source,'crit_chance')):
        power *= 1.7
        log.append('Critical strike!')
    power *= max(1, total(source,'damage_boost'))
    if not piercing:
        power = max(1, power - stat(target,'def')*.6)
    reduction = total(target,'damage_reduction') + (0 if magical else total(target,'physical_reduction'))
    amount = hurt(target, power * (1-min(.8,reduction)), log, source)
    heal(source, amount * total(source,'lifesteal'))
    if 'sleep' in target['status']:
        del target['status']['sleep']
    log.append(f"{source['name']} deals {amount} damage to {target['name']}.")
    return amount

def apply(target, key, log, source=None, rng=random):
    info = EFFECTS[key]
    if info['target']=='enemy' and rng.random() < min(.8,total(target,'effect_resistance')):
        log.append(f"{target['name']} resists {info['name']}.")
        return
    if info.get('randomized'):
        target['status']['random_effect'] = info['duration']
        key = rng.choice(['burn','poison','shock','freeze','curse'])
        info = EFFECTS[key]
    target['status'][key] = max(target['status'].get(key, 0), info['duration'])
    log.append(f"{info['icon']} {target['name']}: {info['name']} ({info['duration']} turns).")
    if info.get('max_hp_reduction'):
        target['hp'] = min(target['hp'], target['max_hp']*info['max_hp_reduction'])
    if info.get('hp_cost') and source:
        hurt(source, min(source['hp']-1,info['hp_cost']), log)
    if info.get('damage'):
        amount = hit(source or target, target, info['damage'], log, rng,
                     info.get('def_bypass',False), magical=True, element=info.get('element'))
        if source:
            heal(source, amount*info.get('attacker_heal',0))
    if info.get('remove_from_battle'):
        if target.get('boss'):
            hurt(target, target['max_hp']*.1, log)
            log.append('The guardian resists banishment, but loses 10% vitality.')
        else:
            target['hp'] = 0
            log.append(f"{target['name']} is banished.")
    if info.get('self_damage') and source:
        hurt(source, info['self_damage'], log)

def tick(entity, opponent, log, rng=random):
    """Resolve ticks before expiry; return whether the actor may act this turn."""
    blocked = False
    statuses = entity.setdefault('status', {})
    for key in list(statuses):
        info = EFFECTS[key]
        if info.get('damage_per_turn'):
            mult = 3 if key in ('burn','freeze') and {'burn','freeze'} <= statuses.keys() else 1
            amount = hurt(entity, info['damage_per_turn']*mult, log)
            heal(opponent, amount*info.get('attacker_heal',0))
            log.append(f"{info['name']}: {entity['name']} loses {amount} HP.")
        if info.get('hp_restore_per_turn'):
            amount = heal(entity, info['hp_restore_per_turn'])
            if amount:
                log.append(f"{info['name']}: {entity['name']} restores {round(amount)} HP.")
        entity['mana'] = min(entity.get('max_mana',30), entity.get('mana',0)+info.get('mana_restore_per_turn',0))
        if info.get('execute_threshold') and entity['hp']/entity['max_hp'] <= info['execute_threshold']:
            if entity.get('boss'):
                hurt(entity, entity['max_hp']*.08, log)
            else:
                hurt(entity, entity['hp'], log)
            log.append(f"{entity['name']} suffers the death mark.")
        if any(info.get(k) for k in ('frozen','stunned','sleeping')) or rng.random() < max(info.get('stun_chance',0),info.get('freeze_chance',0)):
            blocked = True
        if rng.random() < info.get('flee_chance',0):
            blocked = True
            log.append(f"{entity['name']} recoils in fear.")
    if blocked:
        log.append(f"{entity['name']} cannot act this turn.")
    return not blocked

def expire(entity, previous):
    # Newly applied statuses get their full duration; existing ones expire after acting.
    for key in previous:
        if key in entity['status']:
            entity['status'][key] -= 1
            if entity['status'][key] <= 0:
                del entity['status'][key]

def cure(entity, kind):
    removes = STATUS_CURES.get(kind, [])
    removed = [k for k in entity['status'] if (k in removes or 'all' in removes) and EFFECTS[k]['target']=='enemy']
    for key in removed:
        del entity['status'][key]
    return removed
