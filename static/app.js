'use strict';
let state, catalog, page='menu', selected=[], search='', filter='all', busy=false, preview=null;
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const symbols={fire:'♨',water:'≋',earth:'⬡',nature:'♧',ice:'❄',lightning:'ϟ',fusion:'⟡',shadow:'☽',light:'✧',void:'◈',blood:'♢',storm:'ϟ',wind:'彡'};
const sigil=r=>symbols[r.element]||'◇';
const keys=r=>r.components||[r.effect];
const manaCost=r=>Math.min(25,5+2*keys(r).length);
const descriptions=[
 'The roots remember what the world has forgotten. Follow their whispers into the green.',
 'Embers drift over a kingdom buried beneath its own fire.',
 'Deep below the earth, the ancient furnaces still hunger.',
 'Beneath the ice, the fourth seal beats like a frozen heart.',
 'A thousand fractured reflections. Only one path forward.',
 'The tide brings back the names of those it took.',
 'Climb beyond the clouds, where stone remembers the stars.',
 'Nothing truly dies here. Not even the things that should.',
 'The earth is broken. The soul beneath it is still alive.',
 'Keep your light close. The shadows have learned your name.',
 'At the bottom of the world, a fire burns without warmth.',
 'Walk among the echoes of fallen constellations.',
 'The veil between worlds wears thin with every step.',
 'All lost souls eventually find their way here.',
 'One final dream. One last seal. Bring them home.'
];
async function api(path,body){
 const response=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
 const data=await response.json();if(!response.ok)throw new Error(data.error||'Something went wrong.');return data;
}
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').classList.remove('show'),4500);}
function meter(label,value,max,type=''){return `<div class="meter-label"><span>${esc(label)}</span><span>${Math.ceil(value)} / ${max}</span></div><div class="meter ${type}"><i style="width:${Math.max(0,Math.min(100,value/max*100))}%"></i></div>`;}
function statuses(entity){return `<div class="status-list">${Object.entries(entity.status||{}).map(([k,v])=>`<span class="status-chip ${catalog.effects[k].target==='self'?'buff':''}" title="${esc(catalog.effects[k].description)}">${esc(catalog.effects[k].name)} · ${v}</span>`).join('')}</div>`;}
function character(){const p=state.player;return `<div class="panel"><div class="panel-head"><h3>Your character</h3><small>LV. ${p.level}</small></div><div class="character"><div class="character-id"><div class="avatar">♙</div><div><h3>${esc(p.name)}</h3><small>${esc(p.cls)} · Soulbound</small></div></div>${meter('VITALITY',p.hp,p.max_hp)}${meter('MANA',p.mana,p.max_mana,'mana')}${meter('AWAKENING',p.xp,p.level*60,'xp')}<div class="stats"><div><b>${p.atk}</b><small>ATTACK</small></div><div><b>${p.def}</b><small>DEFENSE</small></div><div><b>${p.speed}</b><small>SPEED</small></div></div>${statuses(p)}</div></div>`;}
function actionButton(action,label,cls='',disabled=false,extra=''){return `<button class="${cls}" data-action="${action}" ${disabled?'disabled':''} ${extra}>${label}</button>`;}
function adventure(){const e=state.enemy,p=state.player;return `${state.victory?'<div class="victory"><span class="eyebrow">THE ORIGINAL GAME IS COMPLETE</span><h2>Chapter 2 · After the Dream</h2><p>Chapter 1 complete: you unlocked all main regions and defeated The Dreaming God. Chapter 2 is your postgame journey.</p></div>':''}<div class="adventure-grid"><div><div class="hero"><div class="hero-art" style="filter:hue-rotate(${state.region*13}deg)"></div><div class="hero-top"><span class="tag">${e?(e.boss?'GUARDIAN ENCOUNTER':'IN COMBAT'):'REGION '+String(state.region+1).padStart(2,'0')}</span><span class="tag">${e?'TURN '+state.turn:(p.is_night?'☽ THE DREAMING WORLD':'☼ THE WAKING WORLD')}</span></div>${e?`<div class="hero-encounter">${e.boss?'♜':'♞'}</div>`:''}<div class="hero-content"><div class="eyebrow">${e?(e.boss?'SEAL GUARDIAN · PHASE '+e.phase:'A SOUL LOST TO THE WILDS'):'THE JOURNEY CONTINUES'}</div><h2>${esc(e?e.name:catalog.regions[state.region])}</h2>${e?`<div class="enemy-meter">${meter('VITALITY',e.hp,e.max_hp)}</div>${statuses(e)}`:`<p>${descriptions[state.region]}</p>`}</div></div>${e?combatControls():`<div class="actions"><button class="action-card" data-action="explore" ${p.hp<=0?'disabled':''}><span class="action-icon">♜</span><strong>Explore the wilds ↗</strong><small>Find runes. Face the unknown.</small></button><button class="action-card" data-action="boss" ${p.hp<=0?'disabled':''}><span class="action-icon">♛</span><strong>Challenge guardian ↗</strong><small>Break the seal of this region.</small></button><button class="action-card" data-action="rest"><span class="action-icon">♧</span><strong>Rest at sanctuary</strong><small>Restore health and mana. Free.</small></button></div>`}</div>${character()}</div><div class="lower-grid"><div class="panel"><div class="panel-head"><h3>Chronicle of your journey</h3><small>${state.kills} SOULS FREED</small></div><div class="journal" aria-live="polite">${state.log.slice(-8).reverse().map(t=>`<p>${esc(t)}</p>`).join('')}</div></div><div class="panel"><div class="panel-head"><h3>Bound runes</h3><button class="text-button" data-goto="runes">Manage ↗</button></div><div class="binding-list">${[0,1].map(i=>{const r=state.runes.find(r=>r.id===state.equipped[i]);return `<div class="binding"><span>${r?sigil(r):'◇'}</span><div>${r?esc(r.name):'Empty binding'}<small>${r?'35% chance to invoke on attack':'Bind a rune to awaken its power'}</small></div></div>`;}).join('')}</div></div></div>${!e?`<div class="panel sanctuary"><div class="eyebrow">THE SANCTUARY RUNESMITH</div><div class="button-row">${actionButton('buy','Healing draught · 15 gold','',false,'data-item="potion"')}${actionButton('buy','Cleansing salts · 20 gold','',false,'data-item="cleanse"')}${actionButton('buy','Mystery rune · 35 gold','',false,'data-item="rune"')}<small class="muted">${state.potions} draughts · ${state.cleanses} salts in your satchel</small></div></div>`:''}`;}
function combatControls(){return `<div class="panel battle-controls"><div class="button-row">${actionButton('attack','⚔ Attack','primary')}${actionButton('guard','◇ Guard · +10 mana')}${actionButton('potion','♡ Heal ('+state.potions+')','',!state.potions)}${actionButton('cleanse','✧ Cleanse ('+state.cleanses+')','',!state.cleanses)}${actionButton('flee','↶ Flee','',state.enemy.boss)}</div><div class="button-row"><select id="cast-rune" aria-label="Rune to cast">${state.runes.map(r=>`<option value="${esc(r.id)}">${esc(r.name)} · ${manaCost(r)} mana</option>`).join('')}</select>${actionButton('cast','Invoke rune ↗')}</div>${combatPotions()}<p class="muted" style="margin:12px 0 0">Actions advance one turn. Guard halves incoming damage. Hover an effect to inspect it.</p></div>`;}
function runeCard(r,mode='equip'){
 const chosen=selected.includes(r.id),bound=state.equipped.includes(r.id);
 return `<article class="rune-card ${chosen?'selected':''}"><div class="card-top"><div class="rune-sigil">${sigil(r)}</div><small>${r.effect==='fusion'?'FUSED':bound?'BOUND':'RUNE'}</small></div><span class="element">${esc(r.element||'arcane')}</span><h3>${esc(r.name)}</h3><p>${keys(r).map(k=>esc(catalog.effects[k]?.name||k)).join(' · ')}<br>${manaCost(r)} mana to invoke</p>${mode==='fusion'?`<button data-select="${esc(r.id)}" aria-pressed="${chosen}">${chosen?'✓ Selected':'＋ Add to altar'}</button>`:`<button data-action="equip" data-rune="${esc(r.id)}" ${state.enemy?'disabled':''}>${bound?'Unbind rune':'Bind to weapon'}</button>`}</article>`;
}
function toolbar(placeholder,withFilter=false){return `<div class="toolbar"><input id="search" aria-label="Search" type="search" placeholder="${placeholder}" value="${esc(search)}">${withFilter?`<select id="filter" aria-label="Filter runes"><option value="all">All runes</option><option value="bound" ${filter==='bound'?'selected':''}>Bound runes</option><option value="fusion" ${filter==='fusion'?'selected':''}>Fused runes</option></select>`:''}<small class="muted">${page==='codex'?Object.keys(catalog.effects).length+' working effects':state.runes.length+' runes collected'}</small></div>`;}
function filteredRunes(){return state.runes.filter(r=>(r.name+' '+keys(r).join(' ')).toLowerCase().includes(search.toLowerCase())&&(filter==='all'||(filter==='bound'?state.equipped.includes(r.id):r.effect==='fusion')));}
function runes(){const rs=filteredRunes();return `<div class="help-box">Bind up to two runes for a 35% chance to trigger their effects on each attack. Every owned rune can also be invoked directly during combat.</div>${toolbar('Search your collection…',true)}<div class="rune-grid">${rs.map(r=>runeCard(r)).join('')}</div>${!rs.length?'<div class="empty">No runes match your search.</div>':''}`;}
function fusion(){return `<div class="fusion-layout"><div class="panel altar"><span class="eyebrow">THE ART OF SOULWEAVING</span><div class="altar-orb">⟡</div><h3>${preview?esc(preview.name):'Two memories. One new power.'}</h3><p>${preview?keys(preview).map(k=>esc(catalog.effects[k].name)).join(' · '):'Select two runes below to preview their fusion.<br>Named recipes can also use three runes.'}</p><div class="status-list" style="justify-content:center">${selected.map(id=>`<span class="status-chip buff">${esc(state.runes.find(r=>r.id===id)?.name)}</span>`).join('')}</div><button class="primary" data-action="fuse" ${!preview||!state.shards||state.enemy?'disabled':''}>Fuse memories · 1 shard</button><p class="muted" style="margin-top:12px">Fusion consumes selected runes. Their powers are preserved.<br>${state.shards?state.shards+' shards available':'Win an encounter to earn soul shards.'}</p></div><div class="panel"><div class="panel-head"><h3>Named fusion recipes</h3><small>${catalog.recipes.length} RECIPES</small></div><div class="recipe-list">${catalog.recipes.map(r=>`<div class="recipe"><strong>⟡ ${esc(r.name)}</strong><p>${r.inputs.map(esc).join(' + ')}</p><small class="muted">${r.components.map(k=>esc(catalog.effects[k].name)).join(' · ')}</small></div>`).join('')}</div></div></div><div class="help-box">Any two rune types can fuse: ${catalog.pair_count.toLocaleString()} base pairings, plus recursive combinations. Two copies of the same rune are valid. Named recipes add their special components without losing the original effects.</div>${toolbar('Find a rune for the altar…')}<div class="rune-grid">${filteredRunes().map(r=>runeCard(r,'fusion')).join('')}</div>`;}
function world(){return `<div class="help-box">Chapter 1 ends after you unlock all main regions and defeat The Dreaming God in The Dreamscape. Chapter 2 is the postgame. The Creator is not required to beat the original game. Defeat each region’s guardian to open the next path. Explore for runes, gold, and levels before challenging a seal. Sanctuary rest is always free outside combat.</div><div class="world-grid">${catalog.regions.map((r,i)=>`<article class="region-card ${i>state.unlocked?'locked':''}"><small>${String(i+1).padStart(2,'0')} / ${state.bosses.includes(i)?'SEAL RESTORED':i<=state.unlocked?'PATH OPEN':'SEALED'}</small><h3>${esc(r)}</h3><p class="muted">${descriptions[i]}</p><button data-action="travel" data-region="${i}" ${i>state.unlocked||!!state.enemy||i===state.region?'disabled':''}>${i===state.region?'You are here':i>state.unlocked?'⌑ Defeat the previous guardian':'Travel here ↗'}</button></article>`).join('')}</div>`;}
function codex(){const effects=Object.entries(catalog.effects).filter(([k,e])=>(k+' '+e.name+' '+e.description).toLowerCase().includes(search.toLowerCase()));return `${toolbar('Search effects and mechanics…')}<div class="help-box">Effects last a fixed number of combat turns. Reapplying refreshes duration; buffs modify effective stats without permanently changing your character. Cleansing salts remove harmful effects. Burn + Freeze creates Crystallized Flame; Shock + Chain Lightning creates Perfect Storm.</div><div class="codex-list">${effects.map(([k,e])=>`<article class="effect-card"><h3>${esc(e.icon)} ${esc(e.name)}</h3><small>${e.target==='self'?'SELF · BLESSING':'ENEMY · AFFLICTION'} · ${e.duration} TURN${e.duration===1?'':'S'}</small><p>${esc(e.description)}</p></article>`).join('')}</div>${!effects.length?'<div class="empty">No matching effects.</div>':''}`;}
const pageInfo={adventure:['Adventure','Into the whispering wilds.','Beyond the sanctuary, something ancient stirs.'],runes:['Rune collection','Memories made tangible.','Gather their power. Discover what they can become.'],fusion:['Fusion altar','Something greater, together.','Weave your runes into a power the world has never seen.'],world:['World map','Fifteen seals. One world.','Follow the roots. Restore what was lost.'],codex:['The codex','Know the unseen.','A field guide to every blessing, affliction, and arcane possibility.']};
Object.assign(pageInfo,{
 menu:['Main menu','Every soul has a story.','Continue yours, or discover something new.'],
 alchemy:['Alchemy & potions','A little curiosity. A little magic.','Gather, experiment, and write your own recipe book.'],
 saves:['Save slots','Keep every journey.','Six independent saves in this browser, plus your automatic save.'],
 village:['Village & crafting','A place to build and begin again.','Every crafting structure, together in your village.'],
 dictionary:['Rune dictionary','A language of lost souls.','Every rune in the world, whether you own it yet or not.']
});
function render(){
 try{localStorage.setItem('soules-autosave',JSON.stringify(state));}catch(_){toast('Browser storage is full or unavailable. Export your save to keep your progress.');}
 const info=pageInfo[page];$('#page-title').textContent=info[0];$('#heading').textContent=info[1];$('#subheading').textContent=info[2];
 $('#gold').textContent=state.player.gold;$('#shards').textContent=state.shards;$('#rune-count').textContent=String(state.runes.length).padStart(2,'0');$('#seal-count').textContent=state.bosses.length+' / 15 seals restored';$('#quest-progress').style.width=(state.bosses.length/15*100)+'%';
 document.querySelectorAll('.nav').forEach(b=>{b.classList.toggle('active',b.dataset.page===page);b.setAttribute('aria-current',b.dataset.page===page?'page':'false');});
 $('#view').innerHTML=({menu,adventure,runes,fusion,world,codex,alchemy,saves,dictionary,village})[page]();
 renderTutorial();
}
function go(next){page=next;search='';filter='all';render();window.scrollTo({top:0,behavior:'instant'});}
async function doAction(button){
 if(busy)return;busy=true;button.disabled=true;
 const action=button.dataset.action;
 const body={action};
 if(button.dataset.rune)body.rune_id=button.dataset.rune;
 if(button.dataset.region)body.region=Number(button.dataset.region);
 if(button.dataset.item)body.item=button.dataset.item;
 if(action==='cast')body.rune_id=$('#cast-rune').value;
 if(action==='drink')body.potion_id=button.dataset.potion;
 if(action==='craft'){
  const card=button.closest('.workshop');body.structure=button.dataset.station;
  body.rune_ids=Array.from(card.querySelectorAll('select[data-craft-rune]')).map(s=>s.value).filter(Boolean);
  body.staff_id=card.querySelector('select[data-craft-staff]')?.value;
 }
 if(action==='buy_alchemy')body.item=button.dataset.item;
 if(action==='brew'){
  const choices=[$('#mix-one').value,$('#mix-two').value];
  body.ingredients=choices.filter(v=>v.startsWith('ingredient:')).map(v=>v.slice(11));
  body.potion_ids=choices.filter(v=>v.startsWith('potion:')).map(v=>v.slice(7));
 }
 if(action==='fuse')body.ids=selected;
 try{state=await api('action',body);if(action==='fuse'){selected=[];preview=null;toast('Fusion complete. A new memory awakens.');}if(action==='travel')go('adventure');else render();}
 catch(e){toast(e.message);button.disabled=false;}finally{busy=false;}
}
document.addEventListener('click',async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(b.dataset.slotAction){handleSlot(b);return;}
 if(b.dataset.tutorial!==undefined){await tutorialStep(Number(b.dataset.tutorial));return;}
 if(b.dataset.page)go(b.dataset.page);
 else if(b.dataset.goto)go(b.dataset.goto);
 else if(b.dataset.action)await doAction(b);
 else if(b.dataset.select){
  const id=b.dataset.select;
  if(selected.includes(id))selected=selected.filter(i=>i!==id);
  else if(selected.length<3)selected.push(id);else return toast('Select at most three runes.');
  preview=null;
  if(selected.length>=2){try{preview=await api('fusion-preview',{ids:selected});}catch(e){toast(e.message);}}
  render();
 }
});
document.addEventListener('input',event=>{if(event.target.id==='search'){const pos=event.target.selectionStart;search=event.target.value;render();$('#search').focus();$('#search').setSelectionRange(pos,pos);}});
document.addEventListener('change',event=>{if(event.target.id==='filter'){filter=event.target.value;render();}});
$('#save-button').onclick=async()=>{try{const save=await api('save');const url=URL.createObjectURL(new Blob([JSON.stringify(save,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='soules-save.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Journey exported. Keep this file to restore your progress.');}catch(e){toast(e.message);}};
$('#load-button').onclick=()=>$('#load-file').click();
$('#load-file').onchange=async event=>{const file=event.target.files[0];if(!file)return;try{if(file.size>2*1024*1024)throw new Error('Save must be smaller than 2 MB.');state=await api('load',JSON.parse(await file.text()));selected=[];preview=null;render();toast('Your journey has been restored.');}catch(e){toast(e.message);}event.target.value='';};
$('#character-button').onclick=()=>$('#character-dialog').showModal();$('#cancel-character').onclick=()=>$('#character-dialog').close();
$('#character-form').onsubmit=async event=>{event.preventDefault();try{state=await api('new',Object.fromEntries(new FormData(event.target)));selected=[];preview=null;$('#character-dialog').close();go('adventure');toast('A new soul awakens.');}catch(e){toast(e.message);}};
// Save/import actions remain available on narrow screens via the character dialog.
const mobileSave=document.createElement('div');mobileSave.className='button-row';mobileSave.innerHTML='<button type="button" id="dialog-export">Export current save</button><button type="button" id="dialog-import">Import a save</button>';
$('#character-form').append(mobileSave);$('#dialog-export').onclick=()=>$('#save-button').click();$('#dialog-import').onclick=()=>$('#load-button').click();
Promise.all([api('state'),api('catalog')]).then(async ([s,c])=>{state=s;catalog=c;try{const cached=localStorage.getItem('soules-autosave');if(cached)state=await api('load',JSON.parse(cached));}catch(_){toast('Previous local save could not be restored. Import an exported save to recover it.');}render();}).catch(e=>{$('#view').textContent='Unable to open your journey. '+e.message;});

function menu(){return `<div class="menu-hero"><div class="hero-art"></div><div class="menu-copy"><span class="eyebrow">${state.victory?'CHAPTER 2 · AFTER THE DREAM':'CHAPTER 1 · THE ORIGINAL JOURNEY'}</span><h2>Welcome back, ${esc(state.player.name)}.</h2><p>Your story is waiting in ${esc(catalog.regions[state.region])}.</p><div class="button-row"><button class="primary" data-goto="adventure">▶ Play / Continue</button><button data-tutorial="1">Start guided tutorial</button><button id="menu-new">New journey</button></div></div></div><div class="menu-grid">${[['village','⌂','Village & crafting','Forge, loom, tower, alchemy, salvage, and the Source Temple.'],['saves','▣','Your save slots','Keep different characters and adventures.'],['alchemy','⚗','Alchemy & potions','Gather ingredients. Discover something unexpected.'],['dictionary','◇','Rune dictionary','Learn what every rune can do.'],['fusion','⟡','Rune fusions','Combine memories into new powers.'],['codex','▤','Effects dictionary','Look up blessings, afflictions, and cures.'],['world','⌘','World map','Find your next destination.']].map(([target,icon,title,desc])=>`<button class="menu-card" data-goto="${target}"><span>${icon}</span><h3>${title}</h3><p>${desc}</p><small>Open ↗</small></button>`).join('')}</div><div class="help-box">Your journey saves automatically in this browser. Use a save slot before starting another character. Export a save file to take it to another device. No commands or coding needed to play.</div>`;}
function dictionary(){const rs=catalog.runes.filter(r=>(r.name+' '+keys(r).join(' ')).toLowerCase().includes(search.toLowerCase()));return `<div class="help-box">This is the whole rune dictionary. Find runes by winning encounters or visiting the runesmith. Use Rune collection to bind the ones you own.</div>${toolbar('Look up any rune…')}<div class="rune-grid">${rs.map(r=>`<article class="rune-card"><div class="rune-sigil">${sigil(r)}</div><span class="element">${esc(r.element)}</span><h3>${esc(r.name)}</h3><p>${keys(r).map(k=>`${esc(catalog.effects[k].name)}: ${esc(catalog.effects[k].description)}`).join('<br>')}</p><small class="muted">${state.runes.some(owned=>owned.name===r.name)?'✓ In your collection':'Not yet collected'}</small></article>`).join('')}</div>`;}
function combatPotions(){return state.brews.length?`<div class="combat-potions"><small class="muted">Your brewed potions · drinking takes one turn</small><div class="button-row">${state.brews.map(p=>`<button data-action="drink" data-potion="${esc(p.id)}" title="${esc(p.desc)}">⚗ ${esc(p.name)}</button>`).join('')}</div></div>`:'';}
function alchemy(){
 const ingredients=Object.entries(state.ingredients).filter(([n,qty])=>qty>0);
 const options='<option value="">Choose something to mix…</option>'+ingredients.map(([n,q])=>`<option value="ingredient:${esc(n)}">${esc(n)} × ${q}</option>`).join('')+state.brews.map(p=>`<option value="potion:${esc(p.id)}">Potion: ${esc(p.name)}</option>`).join('');
 return `<div class="help-box">Mix any two ingredients, two potions, or one of each. New mixtures go into your recipe book. Ingredients and potions are consumed by brewing. Using a potion in a mixture reuses its bottle; blending two returns one spare bottle. You have ${state.bottles} empty bottles.</div><div class="fusion-layout"><div class="panel alchemy-workbench"><span class="eyebrow">THE EXPERIMENT TABLE</span><div class="altar-orb">⚗</div><h3>What happens if…?</h3><label>First ingredient or potion<select id="mix-one" aria-label="First mixing ingredient">${options}</select></label><label>Second ingredient or potion<select id="mix-two" aria-label="Second mixing ingredient">${options}</select></label><button class="primary" data-action="brew" ${state.enemy?'disabled':''}>Mix & discover</button><p class="muted">Try Thorn Petal + Dew Blossom for your first recipe. Extra effects last combat turns, rather than permanently changing your stats.</p></div><div class="panel"><div class="panel-head"><h3>Your ingredient satchel</h3><small>${ingredients.reduce((n,[k,q])=>n+q,0)} INGREDIENTS</small></div><div class="satchel"><p class="muted">Gathering finds three random ingredients native to ${esc(catalog.regions[state.region])}. Battles can also drop ingredients.</p><button data-action="gather" ${state.enemy||state.player.hp<=0?'disabled':''}>♧ Gather nearby ingredients</button><div class="ingredient-list">${ingredients.map(([n,q])=>`<div><span>❧ ${esc(n)}</span><strong>× ${q}</strong></div>`).join('')||'<p class="muted">Your satchel is empty. Gather to refill it.</p>'}</div><small class="muted">${state.bottles} empty bottles · ${3-state.forages%3} gatherings until the next shop restock</small></div></div></div><div class="section-title"><h2>Your potion shelf</h2><small>${state.brews.length} BOTTLES READY</small></div><div class="button-row" style="margin-bottom:15px"><button data-action="bottle_draught" ${!state.potions||state.enemy?'disabled':''}>Move a field draught to the mixing shelf (${state.potions} available)</button></div><div class="rune-grid">${state.brews.map(p=>`<article class="rune-card"><div class="rune-sigil">⚗</div><h3>${esc(p.name)}</h3><p>${esc(p.desc)}</p><button data-action="drink" data-potion="${esc(p.id)}" ${state.player.hp<=0||(!state.enemy&&p.formula.statuses?.includes('sleep'))?'disabled':''}>Drink potion${state.enemy?' · 1 turn':''}</button></article>`).join('')||'<div class="empty">No potions yet. Brew one above, or visit the apothecary below.</div>'}</div><div class="section-title"><h2>The apothecary</h2><small>STOCK REPLENISHES EVERY THREE GATHERINGS</small></div><div class="rune-grid">${catalog.alchemy.shop.map(p=>`<article class="rune-card"><div class="card-top"><h3>${esc(p.name)}</h3><small>× ${state.shop_stock[p.name]}</small></div><p>${esc(p.desc)}</p><button data-action="buy_alchemy" data-item="${esc(p.name)}" ${state.enemy||state.player.gold<p.price||!state.shop_stock[p.name]?'disabled':''}>Buy · ${p.price} gold</button></article>`).join('')}</div><div class="section-title"><h2>Your discovered recipes</h2><small>${Object.keys(state.recipe_book).length} DISCOVERIES</small></div><div class="codex-list">${Object.values(state.recipe_book).map(r=>`<article class="effect-card"><h3>${esc(r.name)}</h3><small>${r.inputs.map(esc).join(' + ')}</small><p>${esc(r.desc)}</p></article>`).join('')||'<div class="empty">Your recipe book is blank. Every new experiment adds an entry—even an unexpected one.</div>'}</div>`;
}
function getSlots(){try{const value=JSON.parse(localStorage.getItem('soules-save-slots')||'[]');return Array.isArray(value)?value.slice(0,6):[];}catch(_){return [];}}
function saves(){const slots=getSlots();return `<div class="help-box">Save slots keep separate snapshots in this browser. Loading a slot replaces your current autosave. Slots change only when you save over or delete them. Export a file for a backup that survives clearing browser data.</div><div class="world-grid">${Array.from({length:6},(_,i)=>{const slot=slots[i];return `<article class="region-card save-card"><small>SLOT ${i+1} · ${slot?'SAVED JOURNEY':'EMPTY'}</small><h3>${esc(slot?.label||'An unwritten story')}</h3>${slot?`<p class="muted">${esc(slot.game?.player?.name)} · Level ${esc(slot.game?.player?.level)}<br>${esc(catalog.regions[slot.game?.region]||'Unknown region')}<br>${esc(new Date(slot.savedAt).toLocaleString())}</p>`:'<p class="muted">Save your current adventure here.</p>'}<div class="button-row"><button data-slot-action="save" data-slot="${i}">Save here</button>${slot?`<button class="primary" data-slot-action="load" data-slot="${i}">Load</button><button data-slot-action="delete" data-slot="${i}">Delete</button>`:''}</div></article>`;}).join('')}</div><div class="sanctuary panel"><h3>Portable backups</h3><p class="muted">These files let you move your current journey to another browser or device.</p><div class="button-row"><button id="slots-export">Export current journey</button><button id="slots-import">Import a save file</button></div></div>`;}
async function handleSlot(button){
 const index=Number(button.dataset.slot);const action=button.dataset.slotAction;const slots=getSlots();
 try{
  if(action==='save'){
   if(slots[index]&&!confirm('Overwrite this saved journey? Your other slots will stay safe.'))return;
   const label=prompt('Name this save:',slots[index]?.label||state.player.name+' — '+catalog.regions[state.region]);
   if(label===null)return;
   slots[index]={label:label.trim().slice(0,60)||'My journey',savedAt:new Date().toISOString(),game:structuredClone(state)};
   localStorage.setItem('soules-save-slots',JSON.stringify(slots));toast('Journey saved in slot '+(index+1)+'.');render();
  }else if(action==='load'){
   if(!confirm('Load this slot? Your current autosave will be replaced. Save it in another slot first if you want to keep it.'))return;
   state=await api('load',slots[index].game);selected=[];preview=null;go('adventure');toast('Saved journey restored.');
  }else if(action==='delete'){
   if(!confirm('Delete this slot? This cannot be undone. Your current journey will stay safe.'))return;
   slots[index]=null;localStorage.setItem('soules-save-slots',JSON.stringify(slots));render();toast('Slot cleared.');
  }
 }catch(e){toast('Could not update the save slot. '+e.message+' You can still export a save file.');}
}
const tutorialSteps=[
 ['menu','Welcome to Soules','You are restoring fifteen lost seals. Nothing here needs code or typed commands. Use Play to continue your adventure. This guide never erases your progress.'],
 ['adventure','Your first steps','Explore starts a battle. Attack uses no mana. Guard halves incoming damage and restores mana. Rest is free after a battle—even if you lose. Try an encounter whenever you feel ready.'],
 ['runes','Meet your runes','Bind up to two runes to your weapon. They can trigger when you attack. In combat, choose any rune you own and press Invoke rune to cast it using mana.'],
 ['fusion','Make something new','Winning encounters earns soul shards. At the altar, select two runes and preview their fusion. Fusing uses a shard and consumes both runes, preserving their powers.'],
 ['alchemy','Your first brew','Choose Thorn Petal and Dew Blossom, then Mix & discover. You start with enough for this recipe. Gather more ingredients, infuse a potion with an ingredient, or blend two potions. Discoveries stay in your recipe book.'],
 ['saves','Keep more than one adventure','Save here stores your current journey in one of six slots. Name it anything you like. You can start another character and return to this one with Load. Export a file for an extra backup.'],
 ['world','The world is yours','Chapter 1 is the original game: unlock all main regions, then defeat The Dreaming God in The Dreamscape. Chapter 2 begins afterward. All crafting stations are in the village menu. Defeat the guardian to unlock the next region. The main menu has the full rune dictionary, fusion recipes, and effects dictionary whenever you need help. You can replay this guide from the main menu.']
];
function renderTutorial(){const step=state.tutorial;const guide=$('#tutorial-guide');if(step<1||step>7){guide.innerHTML='';return;}const [target,title,text]=tutorialSteps[step-1];guide.innerHTML=`<div class="tutorial-banner"><div><span class="eyebrow">GUIDED TUTORIAL · ${step} / 7</span><h3>${title}</h3><p>${text}</p></div><div class="button-row">${step>1?`<button data-tutorial="${step-1}">Back</button>`:''}<button data-goto="${target}">Show me</button><button class="primary" data-tutorial="${step===7?0:step+1}">${step===7?'Ready to play':'Next →'}</button><button data-tutorial="0">Close guide</button></div></div>`;}
async function tutorialStep(step){try{state=await api('action',{action:'tutorial',step});go(step?tutorialSteps[step-1][0]:'menu');}catch(e){toast(e.message);}}
document.addEventListener('click',event=>{const id=event.target.closest('button')?.id;if(id==='menu-new')$('#character-dialog').showModal();if(id==='slots-export')$('#save-button').click();if(id==='slots-import')$('#load-button').click();});

function village(){
 const name=catalog.villages[catalog.regions[state.region]]||'Village';
 const runeOptions='<option value="">Choose a rune or staff…</option>'+state.runes.map(r=>`<option value="${esc(r.id)}">${esc(r.name)}</option>`).join('');
 const staffOptions='<option value="">Choose a crafted staff…</option>'+state.runes.filter(r=>r.kind==='staff').map(r=>`<option value="${esc(r.id)}">${esc(r.name)}</option>`).join('');
 return `<div class="help-box"><strong>${esc(name)}</strong> · All six crafting structures are available here. You do not need to travel to a special region to use a workstation. Crafting is available outside battle.</div><div class="button-row" style="margin-bottom:22px">${actionButton('rest','Rest at the village sanctuary','primary',!!state.enemy)}<button data-goto="fusion">Visit the rune fusion altar</button><button data-goto="runes">Manage weapon bindings</button></div><div class="world-grid">${catalog.structures.map(s=>{
 let controls='';
 if(s.key==='alchemy_lab')controls='<button class="primary" data-goto="alchemy">Open alchemy lab</button>';
 else {
  if(s.key==='enchantment_tower')controls=`<label>First rune<select data-craft-rune aria-label="First staff rune">${runeOptions}</select></label><label>Second rune<select data-craft-rune aria-label="Second staff rune">${runeOptions}</select></label>`;
  if(s.key==='disenchantry')controls=`<label>Recover materials from<select data-craft-rune aria-label="Rune to salvage">${runeOptions}</select></label>`;
  if(s.key==='source_temple')controls=`<label>Staff to imbue<select data-craft-staff aria-label="Staff to imbue">${staffOptions}</select></label><label>Rune to consume<select data-craft-rune aria-label="Infusion rune">${runeOptions}</select></label>`;
  controls+=`<button class="primary" data-action="craft" data-station="${s.key}" ${state.enemy||state.player.hp<=0?'disabled':''}>${s.key==='forge'?'Temper weapon':s.key==='loom'?'Weave reinforcement':s.key==='enchantment_tower'?'Craft staff':s.key==='source_temple'?'Imbue staff':'Salvage selected rune'}</button>`;
 }
 return `<article class="region-card workshop" data-workshop="${s.key}"><small>VILLAGE WORKSTATION</small><h3>${esc(s.icon)} ${esc(s.name)}</h3><p class="muted">${s.work?esc(s.work.action):'Gather ingredients, mix potions, and discover recipes at the village alchemy lab.'}</p>${s.work?`<p class="muted">${s.work.gold} gold · ${s.work.shards} soul shards${s.key==='enchantment_tower'?' · consumes both chosen runes':s.key==='source_temple'?' · consumes the infusion rune':''}</p>`:''}${controls}</article>`;
 }).join('')}</div><div class="help-box" style="margin-top:22px">Crafted staffs appear in your rune collection and combat spell list. Their component effects work just like rune spells. Forge and loom improvements are permanent; salvage consumes the selected rune. Your last rune is protected.</div>`;
}
