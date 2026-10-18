'use strict';
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let commandHistory=[], historyPosition=0, historyDraft='';
let catalog, packet=null, view='home', cursor=0, busy=false, pollBusy=false, epoch=0, dictionaryTab='all', dictionarySearch='', dictionaryCategory='', dictionaryLimit=60;
const STORE='soules-original-autosave',SLOTS='soules-original-slots',PREFS='soules-appearance';
function stored(key,fallback){try{return JSON.parse(localStorage.getItem(key))??fallback;}catch(_){return fallback;}}
let checkpoint=stored(STORE,null),preferences=stored(PREFS,{mode:'auto',preset:'crypt',bg:'#100d1c',accent:'#b998f0',font:15});
const presets={crypt:['Dark crypt','#100d1c','#b998f0'],forest:['Forest','#101b16','#a9cf88'],ember:['Ember','#221411','#efad7c'],frost:['Frost','#111b2a','#99cfe9'],ocean:['Ocean','#0b1d25','#78d7cf'],rose:['Rose dusk','#211320','#eba5c8']};
const regions={
 'Whispering Woods':['#101b16','#a9cf88'], 'Ashen Wastes':['#211912','#d9b17a'],
 'Crimson Depths':['#241211','#ed9c79'],'Frostbound Tundra':['#121e2c','#a3d3ed'],
 'Crystal Spire':['#20172a','#c7abed'],'Sunken Coast':['#0d202a','#87cadf'],
 'Ironpeak Mountains':['#191d22','#b3c2d4'],'Blight Swamp':['#1a2011','#bdca79'],
 'Shattered Wastes':['#211923','#d4b0d3'],'Shadow Vale':['#171127','#bb9ee9'],
 'Infernal Depths':['#261211','#f19a78'],'Celestial Expanse':['#11182c','#b1c8f5'],
 'Riftlands':['#211129','#d9a4ef'],'Abyss of Souls':['#120e20','#b99bd4'],
 'The Dreamscape':['#19142a','#dbb1ef'],"Creator's Realm":['#241e10','#e9ce84']};
const structures={quarry:['#1c1e22','#c5b7a3'],lumberyard:['#172218','#b6cd96'],watchpost:['#1c2028','#a8b9df'],village:['#201b13','#d5be8c'],library:['#1d1726','#c1a9e0'],forge:['#251512','#ecaf7a'],loom:['#231a24','#e0b4d1'],alchemy:['#12231e','#99d6b5'],temple:['#191d2a','#b5cbee'],shrine:['#242010','#e4d08c'],ruins:['#1c211a','#b7c6a1'],cave:['#191b23','#aab6d4'],graveyard:['#181626','#baa7d3'],dungeon:['#201518','#dca3ae'],tower:['#1d192c','#bda9ed'],camp:['#231a12','#dfb58b'],arena:['#241719','#e7b2a8'],elemental:['#241625','#ddb1ed']};
const elementalPalettes={fire:['#2a120d','#f7a366'],ice:['#101f30','#a3dffc'],storm:['#241d0d','#f4d575'],nature:['#0e2619','#9dda91']};
const validHex=x=>typeof x==='string'&&/^#[0-9a-f]{6}$/i.test(x);
function mix(a,b,amount){return '#'+[1,3,5].map(i=>Math.round(parseInt(a.slice(i,i+2),16)*(1-amount)+parseInt(b.slice(i,i+2),16)*amount).toString(16).padStart(2,'0')).join('');}
function light(hex){const c=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return c[0]*.2126+c[1]*.7152+c[2]*.0722;}
function contrast(a,b){const x=light(a),y=light(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
function theme(){
 let bg,accent;const p=packet?.snapshot?.player||checkpoint?.player,location=packet?.snapshot?.location;
 if(preferences.mode==='custom'&&validHex(preferences.bg)&&validHex(preferences.accent)){bg=preferences.bg;accent=preferences.accent;}
 else if(preferences.mode==='fixed'){[,bg,accent]=presets[preferences.preset]||presets.crypt;}
 else [bg,accent]=(location?.element&&elementalPalettes[location.element])||(location&&structures[location.kind])||regions[p?.region]||presets.crypt.slice(1);
 const text=contrast(bg,'#eeeaf5')>contrast(bg,'#18201c')?'#eeeaf5':'#18201c';
 if(contrast(accent,bg)<3)accent=mix(accent,text,.65);
 const props={'--bg':bg,'--accent':accent,'--text':text,'--muted':mix(bg,text,.68),'--panel':mix(bg,text,.035),'--raised':mix(bg,text,.08),'--line':mix(bg,accent,.27),'--button-text':contrast(accent,'#101018')>contrast(accent,'#fffdf6')?'#101018':'#fffdf6','--font-size':Math.max(12,Math.min(22,Number(preferences.font)||15))+'px'};
 for(const [k,v]of Object.entries(props))document.documentElement.style.setProperty(k,v);
 document.body.classList.toggle('scene-structure',Boolean(location));
 document.body.classList.toggle('tablet-mode',preferences.tablet??(navigator.maxTouchPoints>0&&innerWidth>=600&&innerWidth<=1400));
 $('#tablet-mode')?.setAttribute('aria-pressed',String(document.body.classList.contains('tablet-mode')));
 document.body.classList.toggle('compact-sidebar',Boolean(preferences.compact));
 $('#compact-status').setAttribute('aria-pressed',String(Boolean(preferences.compact)));
 document.documentElement.dataset.themeMode=preferences.mode||'auto';
 document.documentElement.dataset.scene=location?.kind||p?.region||'title';
 window.updateComfortAppearance?.();
}
function notice(text){$('#notice').textContent=text;$('#notice').classList.add('show');clearTimeout(notice.timer);notice.timer=setTimeout(()=>$('#notice').classList.remove('show'),5500);}
async function api(path,body){const response=await fetch('/api/original/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw new Error(result.error||'The game could not complete that request.');return result;}
function writeStore(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true;}catch(_){notice('Browser storage is unavailable or full. Export a save to keep your progress.');return false;}}
function quickReady(){return Boolean(packet?.waiting&&!packet?.snapshot?.enemy&&(['main','category'].includes(packet?.snapshot?.phase)||['Village > ','Elemental village > '].includes(packet?.prompt)));}
function canSave(){return Boolean(packet?.snapshot?.player&&packet.waiting&&['main','category'].includes(packet.snapshot.phase));}
function safeSave(){return canSave()?{format:'soules-original-v1',player:structuredClone(packet.snapshot.player)}:checkpoint;}
function append(text,cls=''){const line=document.createElement('p');line.textContent=text;line.className=cls;$('#terminal').append(line);while($('#terminal').children.length>650)$('#terminal').firstChild.remove();return line;}
function journalNearBottom(terminal){return terminal.scrollHeight-terminal.scrollTop-terminal.clientHeight<=32;}
let journalScrollRevision=0;
function followShortJournalUpdate(terminal,lines,follow){
 if(!lines.length)return;
 const revision=++journalScrollRevision;
 const potionUpdate=lines.some(line=>/POTION|BREW COMPLETE/.test(line.textContent));
 if((!follow&&!potionUpdate)||terminal.clientHeight<=0)return;
 const lineHeight=parseFloat(getComputedStyle(terminal).lineHeight)||26;
 const limit=Math.max(60*(lineHeight+4),terminal.clientHeight*3);
 const height=lines.reduce((total,line)=>{const style=getComputedStyle(line);return total+line.getBoundingClientRect().height+parseFloat(style.marginTop)+parseFloat(style.marginBottom);},0);
 if(height<=limit){
  terminal.scrollTop=terminal.scrollHeight;
  const followedTop=terminal.scrollTop;
  requestAnimationFrame(()=>{if(revision===journalScrollRevision&&Math.abs(terminal.scrollTop-followedTop)<2)terminal.scrollTop=terminal.scrollHeight;});
 }
}
function apply(result,followShortUpdates){
 if(packet&&result.prompt_id&&result.prompt_id<packet.prompt_id)return;
 const terminal=$('#terminal'),follow=followShortUpdates??journalNearBottom(terminal),added=[];
 for(const line of result.output||[]){if(line.id<cursor)continue;added.push(append(line.text,line.text.includes('could not finish')?'error-line':line.text.trim().startsWith('---')?'menu-heading':''));cursor=line.id+1;}
 const newlyDead=result.snapshot?.phase==='dead'&&packet?.snapshot?.phase!=='dead';
 const effectKeys=s=>['player','enemy'].flatMap(k=>Object.keys(s?.[k]?.rune_status||{}).map(x=>k+':'+x));
 const previousEffects=effectKeys(packet?.snapshot);
 packet=result;
 window.recordComfortOutput?.(added.map(line=>line.textContent),added);
 if(effectKeys(packet?.snapshot).some(x=>!previousEffects.includes(x)))tone();
 if(result.snapshot?.player?.source_story?.season_one_complete&&!packet?.snapshot?.player?.expansion?.season_three?.complete)chronicleRun(result.snapshot.player,'Chapter One completed');
 if(result.snapshot?.player?.expansion?.season_three?.complete)chronicleRun(result.snapshot.player,'Season Three completed');
 if(newlyDead){chronicleRun(result.snapshot.player,'fallen');checkpoint=null;localStorage.removeItem(STORE);notice("Your character has died. Begin a new journey.");$('#new-dialog').showModal();}
 if(canSave()){checkpoint=safeSave();writeStore(STORE,checkpoint);}
 if(result.snapshot?.player){renderSidebar();theme();}
 renderGameControls();
 accessibleCombat();
 followShortJournalUpdate(terminal,added,follow);

 if(result.error)notice('The game reported an error: '+result.error+'. Your last saved checkpoint is kept.');
}
function show(next){view=next;$('#game-screen').hidden=next!=='play';$('#page-screen').hidden=next==='play';if(next!=='play')renderPage();else {renderGameControls();}renderSidebar();theme();}
async function start(config){
 if(busy)return;if(!config.save&&packet?.snapshot?.player&&packet.snapshot.phase!=='dead')chronicleRun(packet.snapshot.player,'retired');busy=true;epoch++;
 try{const result=await api('start',config);packet=null;cursor=0;$('#terminal').replaceChildren();apply(result);show('play');if(!window.buttonsOnly?.())$('#command').focus();}
 catch(e){notice(e.message);}finally{busy=false;renderGameControls();}
}
function play(){if(packet?.alive&&packet?.snapshot?.phase!=='dead'){show('play');return;}if(checkpoint?.player){start({save:checkpoint});return;}$('#new-dialog').showModal();}
async function respond(text,group){
 if(busy||!packet?.waiting)return;
 if(window.buttonsOnly?.()&&text.trim().toUpperCase()==='DAMAR')return;
 if(!group&&text&& !['DAMAR','SAMAR'].includes(text.toUpperCase())){if(commandHistory.at(-1)!==text)commandHistory.push(text);commandHistory=commandHistory.slice(-100);historyPosition=commandHistory.length;historyDraft='';}
 const journal=$('#terminal'),follow=journalNearBottom(journal),previousTop=journal.scrollTop;
 busy=true;epoch++;renderGameControls();
 try{if(!group)append('> '+(text||'(Enter)'),'player-response');const result=await api('input',{text,group,prompt_id:packet.prompt_id,since:cursor});apply(result,follow&&Math.abs(journal.scrollTop-previousTop)<2);}
 catch(e){notice(e.message);}finally{busy=false;renderGameControls();if(view==='play'&&!window.buttonsOnly?.())$('#command').focus();}
}
function renderAssignment(){const host=$('#village-assignment'),plan=packet?.snapshot?.assignment;if(!host)return;host.hidden=!plan;if(!plan){host.replaceChildren();return;}const worker=plan.workers[plan.current],enabled=packet.waiting&&!busy;host.innerHTML=`<div class="assignment-heading"><div><span class="eyebrow">VILLAGE DEFENCE · ${esc(plan.threat_count)} MONSTERS</span><h2>Assign ${esc(worker.name)}</h2><p>Choose a role card. Each villager gets one job; the raid begins after the final assignment.</p></div><button data-response="0" ${!enabled?'disabled':''}>Cancel raid</button></div><div class="assignment-roster">${plan.workers.map((w,i)=>`<span class="assignment-worker ${i===plan.current?'current':''}"><b>${esc(w.name)}</b> · Lv. ${esc(w.level)}<small>${i<plan.current?'✓ '+esc(plan.assigned[i]?.role||'Assigned'):i===plan.current?'Choosing role now':'Awaiting assignment'}</small></span>`).join('')}</div><div class="assignment-roles">${plan.roles.map(role=>`<button data-assign-role="${esc(role.name)}" data-response="${esc(role.answer)}" ${!enabled?'disabled':''}><b>${esc(role.icon)} ${esc(role.name)}</b><small>${esc(role.detail)}</small></button>`).join('')}</div><p class="assignment-note">Repair costs 1 Timber for the whole team. Surviving attackers can each act every round.</p>`;}
function renderGameControls(){
 if(!catalog)return;renderAssignment();window.renderComfortControls?.();const main=['main','category'].includes(packet?.snapshot?.phase),enabled=Boolean(packet?.waiting&&packet.alive&&packet?.snapshot?.phase!=='dead'&&!busy),group=packet?.snapshot?.group||'';
 $('#categories').innerHTML=catalog.groups.map(g=>`<button data-group="${g.id}" class="${g.id===group?'active':''}" ${!enabled||!main?'disabled':''}>${esc(g.name)}</button>`).join('');
 const options=group?(catalog.groups.find(g=>g.id===group)?.options||[]).map(([,label],i)=>[i+1,label]):catalog.groups.map((g,i)=>[i+1,g.name]);
 $('#action-buttons').innerHTML=main?options.map(([n,label])=>`<button data-response="${n}" ${!enabled?'disabled':''}><b>${n}</b>${esc(label)}</button>`).join('')+(group?`<button data-response="0" ${!enabled?'disabled':''}>0 · Back to main menu</button>`:''):'<small style="color:var(--muted)">Answer the question in the story panel.</small>';
 $('#prompt').textContent=packet?.alive?(packet.prompt||'Waiting for the game…'):'Press Play / Continue to resume your saved character.';
 $('#command').disabled=!enabled;$('#send').disabled=!enabled;$('#back').disabled=!enabled||Boolean(packet?.snapshot?.enemy?.hp>0);
 $('#connection').textContent=busy?'Sending…':packet?.alive?(packet.waiting?'● Awaiting your choice':'● The story continues…'):'● Ready to play';
 const location=packet?.snapshot?.location,region=packet?.snapshot?.player?.region;
 $('#scene-name').textContent=location?region+' / '+location.name:(region||'YOUR JOURNEY');
 const p=packet?.snapshot?.player,low=p&&p.hp>0&&p.hp/p.max_hp<=.25;
 $('#health-warning').textContent=low?'⚠ LOW HEALTH — '+Math.ceil(p.hp)+' HP':'';
 document.body.classList.toggle('low-health',Boolean(low));
 $('#recall-command').disabled=!enabled||!commandHistory.length;
 $('#quick-keys').querySelectorAll('button').forEach(b=>b.disabled=!enabled);
}
function bar(label,value,max,cls=''){return `<div class="bar-label"><span>${esc(label)}</span><span>${Math.max(0,Math.round(value))} / ${max}</span></div><div class="bar ${cls}"><i style="width:${Math.max(0,Math.min(100,value/max*100))}%"></i></div>`;}
function effects(p){const pairs=[...Object.entries(p.status||{}).map(([k,v])=>[k,v,true]),...Object.entries(p.rune_status||{}).map(([k,v])=>[k,v,true]),...Object.entries(p.active_buffs||{}).map(([k,v])=>[k,v,false]),...Object.entries(p.active_effects||{}).map(([k,v])=>[k,v.turns_remaining,true])];return pairs.length?pairs.map(([k,v,harm])=>{const e=p.rune_abilities?.[k]||catalog.content.effects[k];if(e?.target==='self')harm=false;return `<span class="effect-chip ${harm?'harm':''}" title="${esc(e?.description||'An effect from your original game')}">${esc(e?.name||k.replaceAll('_',' '))} · ${esc(v)}</span>`;}).join(''):'<small>No active effects</small>';}
function slots(){const value=stored(SLOTS,[]);return Array.isArray(value)?value.slice(0,6):[];}
function slotControls(index,compact=false){const s=slots()[index];return `<div class="${compact?'slot-row':'page-card'}"><span>${compact?'Slot '+(index+1)+' · ':''}${esc(s?.label||'Empty slot')}</span>${!compact?`<h2>Slot ${index+1}</h2><p>${s?esc(s.save.player.name)+' · Lv. '+s.save.player.level+'<br>'+esc(s.save.player.region)+'<br>'+esc(new Date(s.savedAt).toLocaleString()):'Keep a separate character or a checkpoint here.'}</p>`:''}<div class="buttons"><button data-slot="${index}" data-slot-action="save" ${!canSave()?'disabled':''}>Save here</button>${s?`<button data-slot="${index}" data-slot-action="load">Load</button><button data-slot="${index}" data-slot-action="delete">Delete</button>`:''}</div></div>`;}
function renderSidebar(){
 if(!catalog)return;const sidebar=$('#status-sidebar'),sidebarTop=sidebar.scrollTop;const snapshot=packet?.snapshot,p=snapshot?.player||checkpoint?.player;
 if(!p){$('#status-sidebar').innerHTML='<div class="side-card"><h2>CHARACTER</h2><h3>A story unwritten.</h3><p>Press Play to choose a name and one of your original five classes.</p></div><div class="side-card"><h2>YOUR SAVES</h2><p>Six separate characters or checkpoints. Export a file to take your journey to another device.</p><button data-view="saves">Open saves</button></div>';sidebar.scrollTop=sidebarTop;return;}
 const cls=catalog.classes[p.class_id],e=snapshot?.enemy,location=snapshot?.location;
 const stats=[['Mana',p.mana],['Gold',p.gold],['Attack',p.atk+(p.weapon?.atk||0)],['Defense',p.def+(p.armour?.def||0)],['Speed',p.speed],['Skill points',p.skill_points||0],['Toxicity',(p.expansion?.food?.toxicity||0)+'/100']];
 $('#status-sidebar').innerHTML=villageCards(snapshot,p)+`<section class="side-card"><h2>CHARACTER</h2><div class="identity"><div class="portrait" data-skin="${esc(p.expansion?.systems?.equipped_cosmetics?.character_skins||'default')}">${esc(cls?.icon||'♙')}</div><div><h3>${esc(p.name)}</h3><small>Level ${p.level} · ${esc(cls?.name||'Adventurer')} · ${p.difficulty==='easy'?'Easy':'Normal'}</small></div></div>${bar('HEALTH',p.hp,p.max_hp,'hp')}${bar('HUNGER',p.hunger??100,100,'hunger')}<small>Start a wander at full hunger to recover up to 3 HP.</small>${bar('EXPERIENCE',p.xp,p.level*50,'xp')}<div class="stats-grid">${stats.map(([k,v])=>`<div class="stat">${k}<b>${typeof v==='string'?esc(v):Math.round((v||0)*10)/10}</b></div>`).join('')}</div></section><section class="side-card"><h2>REGION & JOURNEY</h2><h3 style="font-size:18px">${esc(p.region)}</h3>${location?`<p>Inside ${esc(location.name)}</p>`:''}<p>${esc(p.weather||'Clear')} · ${p.is_night?'☽ Night':'☼ Day'}<br>Chapter ${p.chapter||1} · ${p.chapter>=3?'Season Three':p.chapter===2?'Season Two':p.source_story?.season_one_complete?'Interlude · rebuilding':'The original journey'}<br>${p.unlocked_regions?.length||1} regions unlocked · ${new Set(p.bosses_defeated||[]).size} guardians beaten<br>Corruption ${p.corruption||0}% · Resonance ${p.resonance_streak||0}</p>${p.title?`<p>Title: ${esc(p.title)}</p>`:''}</section>${e&&e.hp>0?`<section class="side-card enemy-card"><h2>${e.phases?'GUARDIAN':'ENEMY'}</h2><h3 style="font-size:18px">${esc(e.name)}</h3>${bar('HEALTH',e.hp,e.max_hp||e.hp,'hp')}<div class="effect-chips">${effects(e)}</div></section>`:''}<section class="side-card"><h2>EQUIPMENT & SATCHEL</h2><p class="weapon-appearance" data-weapon-skin="${esc(p.expansion?.systems?.equipped_cosmetics?.weapon_skins||'default')}">⚔ ${esc(p.weapon?.name||'No weapon equipped')}<br>🛡 ${esc(p.armour?.name||'No armour equipped')}</p><div class="stats-grid">${[['Weapons',p.weapons],['Armour',p.armours],['Runes',p.runes],['Staffs',p.staffs],['Ingredients',p.ingredients],['Potions',p.potions],['Food',(p.inventory||[]).filter(x=>x.food||'hunger' in x)],['Scrolls',(p.inventory||[]).filter(x=>'turns' in x)],['Loot',(p.inventory||[]).filter(x=>!x.food&&!('hunger' in x)&&!('turns' in x))],['Forge cores',p.forge_cores],['Charged weapon cores',p.charged_cores],['Elemental cores',p.elemental_cores],['Protected ancient finds',p.protected_relics]].map(([k,v])=>`<div class="stat">${k}<b>${v?.length||0}</b></div>`).join('')}</div><p>${p.weapon?.rune?'Bound: '+esc(p.weapon.rune.name):''}</p><label class="sidebar-select">Equip weapon<select id="sidebar-weapon" aria-label="Weapon to equip">${(p.weapons||[]).map((w,i)=>`<option value="${i}" ${w.name===p.weapon?.name?'selected':''}>${esc(w.name)} · ATK ${esc(w.atk||0)}</option>`).join('')}</select></label><button id="sidebar-equip" ${!quickReady()?'disabled':''}>Equip selected weapon</button><label class="sidebar-select">Use potion<select id="sidebar-potion" aria-label="Potion to drink">${(p.potions||[]).map((name,i)=>`<option value="${i}">${esc(name)}</option>`).join('')}</select></label><button id="sidebar-drink" ${!quickReady()||!p.potions?.length?'disabled':''}>Drink selected potion</button><p>Quick actions work at category and village menus. ${p.home_companions?.length||0} companions are staying in Old Village.</p></section><section class="side-card"><h2>ACTIVE EFFECTS & BUFFS</h2><div class="effect-chips">${effects(p)}</div></section><section class="side-card"><h2>COMPANIONS & QUESTS</h2><p>${p.companions?.length?p.companions.map(c=>esc(c.form_name||c.name)+' · Stage '+(c.stage||0)+' · Hunger '+(c.hunger??100)+'/100<br><small>'+esc(c.home_region||'Home region')+((c.hunger??100)<30?' · Hungry: resting':'')+'</small>').join('<br>'):'No companions yet'}<br>${(p.quests||[]).filter(q=>!q.completed).length} active quests · ${(p.achievements||[]).length} achievements<br>${Object.values(p.kill_counts||{}).reduce((n,k)=>n+Number(k||0),0)} enemies defeated · ${p.wander_count||0} explorations</p></section><section class="side-card"><h2>SAVE SLOTS</h2>${Array.from({length:6},(_,i)=>slotControls(i,true)).join('')}<p>Save at a category menu. Submenus and battles stay in the running session.</p><div class="side-actions"><button data-export>↧ Export</button><button data-import>↥ Import</button></div></section>`;
 sidebar.scrollTop=sidebarTop;
}
function home(){return `<div class="title-hero"><span class="eyebrow">SOULES · THE ORIGINAL TEXT ADVENTURE</span><h1>Your world.<br>Your next choice.</h1><p class="intro">Your original actions and new adventures, grouped into clear menus. Follow the story in text, choose a number, and keep your character close in the sidebar.</p><button class="primary" data-play>▶ Play / Continue</button></div><div class="home-options">${[['dictionary','1','Dictionary','Every catalogue: equipment, loot odds, creatures, places, recipes and systems.'],['tutorial','2','Tutorial','Learn the controls without losing your adventure.'],['customise','3','Customise','Region scenery, structure colours, or your own theme.'],['saves','4','Saves','Keep separate characters and portable backups.']].map(([page,n,title,desc])=>`<button data-view="${page}"><b>${n}.</b><span><strong>${title}</strong><small>${desc}</small></span></button>`).join('')}</div><p class="section-note">Your original exploration, equipment, food, companions, crafting, quests, elemental villages, and challenge menus run behind this interface. Open World & Social → Adventures, projects & research for the expanded activities and Season Three.</p>`;}
function tutorial(){
 const guide=catalog.guide;
 return `<span class="eyebrow">YOUR COMPLETE FIELD GUIDE</span><h1>Learn your way around Soules.</h1><p class="intro">Start with the first steps, or open a topic below. The action reference covers every menu, including crafting, village workers and the new adventures.</p><nav class="guide-contents" aria-label="Tutorial topics">${guide.sections.map(s=>`<a href="#guide-${esc(s.id)}">${esc(s.title)}</a>`).join('')}<a href="#guide-actions">All 48 actions</a></nav>${guide.sections.map((s,i)=>`<details class="page-card guide-section" id="guide-${esc(s.id)}" ${i===0?'open':''}><summary>${esc(s.title)}</summary>${s.paragraphs.map(p=>`<p>${esc(p)}</p>`).join('')}</details>`).join('')}<section class="page-card" id="guide-actions"><h2>Every category and action</h2><p>Numbers below match each category’s secondary menu. Read the current in-game question when a submenu opens.</p>${catalog.groups.map(g=>`<h3>${esc(g.name)}</h3><ol>${g.options.map(([id,label])=>`<li><b>${esc(label)}</b> — ${esc(guide.actions[id])}</li>`).join('')}</ol>`).join('')}</section><button class="primary" data-play>Ready to play</button>`;
}
function customise(){return `<span class="eyebrow">YOUR COLOURS, YOUR WORLD</span><h1>Make yourself at home.</h1><section class="page-card"><h2>Background behaviour</h2><label>How should the game look?<select id="theme-mode"><option value="auto" ${preferences.mode==='auto'?'selected':''}>Automatic · match region and structure</option><option value="fixed" ${preferences.mode==='fixed'?'selected':''}>Fixed · keep my chosen theme</option><option value="custom" ${preferences.mode==='custom'?'selected':''}>Custom · choose my own colours</option></select></label><p>Automatic mode gives woods, coasts, tundra, forges, libraries, caves, and other places their own palette. Entering a structure changes its background; leaving restores the region.</p></section><section class="page-card"><h2>Pick a theme</h2><div class="buttons">${Object.entries(presets).map(([k,[name,bg,accent]])=>`<button class="preset" data-preset="${k}" aria-pressed="${preferences.mode==='fixed'&&preferences.preset===k}"><span class="swatch" style="background:${bg};border-color:${accent}"></span>${name}</button>`).join('')}</div></section><section class="page-card"><h2>Choose your own colours</h2><label>Background<input id="background-colour" type="color" value="${validHex(preferences.bg)?preferences.bg:'#100d1c'}"></label><label>Accent<input id="accent-colour" type="color" value="${validHex(preferences.accent)?preferences.accent:'#b998f0'}"></label><p>Colours save in this browser. Text contrast is adjusted automatically so your choices stay readable.</p><button id="reset-theme">Restore automatic scenery</button></section>`;}
function referenceValue(value){if(value===null)return 'None';if(Array.isArray(value))return value.map(referenceValue).join('; ');if(typeof value==='object')return Object.entries(value).map(([key,entry])=>key.replaceAll('_',' ')+': '+referenceValue(entry)).join('; ');return String(value);}
function ownedReference(){const p=packet?.snapshot?.player||checkpoint?.player;if(!p)return [];const found=new Map();for(const bag of ['weapons','armours','staffs','runes','inventory','potions','charged_cores','protected_relics'])for(let item of p[bag]||[]){if(typeof item==='string'&&bag==='potions')item={name:item,...(p.expansion?.food?.blends?.[item]||{}),use:'Inventory & Equip → Use carried potions'};if(typeof item!=='object'||!item?.name)continue;const description='Owned item · '+bag.replaceAll('_',' ')+'\n'+Object.entries(item).filter(([key])=>key!=='name').map(([key,value])=>key.replaceAll('_',' ')+': '+referenceValue(value)).join('\n');found.set(bag+'::'+JSON.stringify(item),{name:item.name,description,type:'Your items'});}return [...found.values()];}
function dictionary(){
 const c=catalog.content,q=dictionarySearch.toLowerCase();let entries=[];
 if(dictionaryTab==='all'){entries=[...(c.encyclopedia?.entries||[]),...ownedReference()].filter(x=>!dictionaryCategory||x.type===dictionaryCategory).map(x=>[x.name,x.description,x.type]);}
 if(dictionaryTab==='runes')entries=c.runes.map(r=>[r.name,(c.effects[r.effect]?.name||r.effect)+' · '+(c.effects[r.effect]?.description||'Original rune effect'),r.element]);
 if(dictionaryTab==='fusions')entries=c.recipes.map(r=>[r.name,r.inputs.join(' + ')+' → '+r.components.map(k=>c.effects[k]?.name||k).join(', '),'Named fusion']);
 if(dictionaryTab==='effects')entries=Object.values(c.effects).map(e=>[e.name,e.description,e.duration+' turns · '+(e.target==='self'?'Blessing':'Affliction')]);
 if(dictionaryTab==='potions')entries=c.potions.map(p=>[p.name,p.ingredients.join(' + ')+' → '+p.desc,'Potion recipe']);
 if(dictionaryTab==='ingredients')entries=c.alchemy.ingredients.map(i=>[i.name,'Found in '+i.region,'Ingredient']);
 if(['wandering','weather','world','loot'].includes(dictionaryTab)){entries=c.exploration[dictionaryTab].map(x=>[x.name,x.description,x.type]);if(dictionaryTab==='wandering')entries.unshift(wanderChanceSummary(c.exploration));}
 entries=entries.filter(r=>r.join(' ').toLowerCase().includes(q));
 return `<span class="eyebrow">THE WORLD, IN WORDS</span><h1>Dictionary</h1><div class="dictionary-tools">${['all','runes','fusions','effects','ingredients','potions','wandering','weather','world','loot'].map(tab=>`<button data-dictionary="${tab}" class="${dictionaryTab===tab?'active':''}">${tab[0].toUpperCase()+tab.slice(1)}</button>`).join('')}</div><input id="dictionary-search" type="search" placeholder="Search names, materials, regions, abilities or rarity…" aria-label="Search dictionary" value="${esc(dictionarySearch)}">${dictionaryTab==='all'?`<label class="dictionary-filter">Reference category <select id="dictionary-category"><option value="">Everything</option>${[...(c.encyclopedia?.categories||[]),'Your items'].map(name=>`<option value="${esc(name)}" ${dictionaryCategory===name?'selected':''}>${esc(name)}</option>`).join('')}</select></label>`:''}${dictionaryTab==='fusions'?fusionFinder():''}<p class="section-note">${entries.length} matching entries${entries.length>dictionaryLimit?', showing '+dictionaryLimit:''}. ${dictionaryTab==='all'?'Complete catalogue reference: search everything or choose a category. Drop percentages are conditional on the stated loot roll; crafted and shop-only items have no invented drop rate. Generated custom items follow their recipes. ':''}${['wandering','weather','world','loot'].includes(dictionaryTab)?'Exploration reference: chances are labelled per check, per full wander or per chosen activity. One weighted roll selects the main wander outcome.':'Every listed effect has combat mechanics. Fusions retain component abilities and gain their own synergy. Active effects appear in the sidebar.'}</p><div class="cards">${entries.slice(0,dictionaryLimit).map(([name,desc,type])=>`<article class="page-card">${dictionaryTab==='runes'?runeSeal(name):''}<span class="eyebrow">${esc(type)}</span><h2>${esc(name)}</h2><p>${esc(desc)}</p></article>`).join('')||'<p>No matching entries.</p>'}</div>${entries.length>dictionaryLimit?'<button id="dictionary-more">Show next 60 entries</button>':''}`;
}
function saves(){return `<span class="eyebrow">SIX DIFFERENT STORIES</span><h1>Your saved journeys.</h1><p class="intro">Slots keep independent original-game characters in this browser. Save at a category menu, outside a battle or submenu. Loading replaces the current running adventure; other slots stay safe.</p><div class="buttons"><button data-new>New character</button><button data-export>Export checkpoint</button><button data-import>Import save</button>${(packet?.snapshot?.player||checkpoint?.player)?.beta_legacy_recovery?'<button id="export-beta-recovery">Export older testing recovery</button>':''}</div><div class="save-grid">${Array.from({length:6},(_,i)=>slotControls(i)).join('')}</div><p class="section-note">Clearing browser storage removes local slots. Keep exported backups. The earlier browser edition and its saves remain available at <a href="/edition">Earlier edition</a>.</p>`;}
function renderPage(){if(!catalog)return;$('#page-screen').innerHTML=({home,tutorial,customise,dictionary,saves}[view]||home)()+(view==='customise'?(window.comfortSettings?.()||'')+expandedSettings():view==='saves'?expandedSaveTools():'');}
async function slotAction(button){const list=slots(),index=Number(button.dataset.slot),action=button.dataset.slotAction;
 try{if(action==='save'){if(!canSave())return notice('Return to a category menu before saving.');if(list[index]&&!confirm('Replace this save slot? Other slots stay safe.'))return;const label=window.buttonsOnly?.()?(list[index]?.label||packet.snapshot.player.name):prompt('Name this saved journey:',list[index]?.label||packet.snapshot.player.name);if(label===null)return;list[index]={label:label.trim().slice(0,60)||'My journey',savedAt:new Date().toISOString(),save:safeSave()};if(writeStore(SLOTS,list)){rememberCheckpoint(list[index]);notice('Saved in slot '+(index+1)+'.');}}
 else if(action==='load'){if(!list[index])return;if(packet?.alive&&!confirm('Load this journey? Save your current character in another slot first if you want to keep it.'))return;await start({save:list[index].save});}
 else if(action==='delete'){if(!confirm('Delete this save slot? Your running character will stay safe.'))return;list[index]=null;writeStore(SLOTS,list);}
 renderSidebar();if(view==='saves')renderPage();}catch(e){notice(e.message);}
}
function exportSave(){const saved=safeSave();if(!saved)return notice('Start an adventure first.');const url=URL.createObjectURL(new Blob([JSON.stringify(saved,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='soules-original-save.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notice('Your category-menu checkpoint was exported.');}
function savePreferences(){writeStore(PREFS,preferences);theme();}
$('#quick-keys').innerHTML=['0','1','2','3','4','5','6','7','8','9','y','n','yes','no'].map(k=>`<button data-response="${k}" disabled>${k}</button>`).join('');
$('#command-form').onsubmit=event=>{event.preventDefault();const value=$('#command').value;$('#command').value='';respond(value);};
$('#back').onclick=()=>respond('/back');$('#play').onclick=play;
$('#font-down').onclick=()=>{if(preferences.comfort)preferences.comfortFont=Math.max(18,(preferences.comfortFont||22)-1);else preferences.font=Math.max(12,(preferences.font||15)-1);savePreferences();};$('#font-up').onclick=()=>{if(preferences.comfort)preferences.comfortFont=Math.min(28,(preferences.comfortFont||22)+1);else preferences.font=Math.min(22,(preferences.font||15)+1);savePreferences();};
$('#cancel-new').onclick=()=>$('#new-dialog').close();
$('#new-character').onsubmit=event=>{event.preventDefault();if(packet?.alive&&packet?.snapshot?.phase!=='dead'&&!confirm('Start a new character? Your stored slots will remain safe.'))return;const config=Object.fromEntries(new FormData(event.target));$('#new-dialog').close();start(config);};
$('#import-file').onchange=async event=>{const file=event.target.files[0];if(!file)return;try{if(file.size>2*1024*1024)throw new Error('Choose a save smaller than 2 MB.');const value=JSON.parse(await file.text());if(packet?.alive&&!confirm('Import this character? Your running adventure will be replaced.'))return;await start({save:value});}catch(e){notice(e.message);}event.target.value='';};
document.addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;
 if(b.dataset.view){show(b.dataset.view);return;}
 if(b.hasAttribute('data-play')){play();return;}
 if(b.hasAttribute('data-new')){$('#new-dialog').showModal();return;}
 if(b.dataset.group){respond('',b.dataset.group);return;}
 if(b.hasAttribute('data-response')){respond(b.dataset.response);return;}
 if(b.dataset.slotAction){slotAction(b);return;}
 if(b.hasAttribute('data-export')){exportSave();return;}
 if(b.hasAttribute('data-import')){$('#import-file').click();return;}
 if(b.dataset.dictionary){dictionaryTab=b.dataset.dictionary;dictionarySearch='';dictionaryLimit=dictionaryTab==='all'?60:10000;renderPage();return;}
 if(b.dataset.preset){preferences.mode='fixed';preferences.preset=b.dataset.preset;savePreferences();renderPage();return;}
 if(b.id==='export-beta-recovery'){const p=(packet?.snapshot?.player||checkpoint?.player)?.beta_legacy_recovery;if(p){const url=URL.createObjectURL(new Blob([JSON.stringify({format:'soules-original-v1',player:p},null,2)],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='soules-older-testing-recovery.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}return;}
 if(b.id==='tablet-mode'){preferences.tablet=!document.body.classList.contains('tablet-mode');savePreferences();}
 if(b.id==='sidebar-equip'){respond('/equip '+$('#sidebar-weapon').value);return;}
 if(b.id==='sidebar-drink'){respond('/drink '+$('#sidebar-potion').value);return;}
 if(b.id==='dictionary-more'){dictionaryLimit+=60;const scroll=$('#page-screen').scrollTop;renderPage();$('#page-screen').scrollTop=scroll;}
 if(b.id==='reset-theme'){preferences.mode='auto';savePreferences();renderPage();}
});
document.addEventListener('input',event=>{const e=event.target;
 if(e.id==='dictionary-search'){dictionarySearch=e.value;dictionaryLimit=dictionaryTab==='all'?60:10000;const pos=e.selectionStart;renderPage();$('#dictionary-search').focus();$('#dictionary-search').setSelectionRange(pos,pos);}
 if(e.id==='background-colour'||e.id==='accent-colour'){preferences.mode='custom';preferences[e.id==='background-colour'?'bg':'accent']=e.value;savePreferences();$('#theme-mode').value='custom';}
});
document.addEventListener('change',event=>{if(event.target.id==='dictionary-category'){dictionaryCategory=event.target.value;dictionaryLimit=60;renderPage();}if(event.target.id==='theme-mode'){preferences.mode=event.target.value;savePreferences();}});
setInterval(async()=>{if(view!=='play'||!packet?.alive||busy||pollBusy)return;pollBusy=true;const before=epoch;try{const data=await api('session?since='+cursor);if(before===epoch)apply(data);}catch(e){notice('Connection interrupted. Your saved checkpoint is kept.');}finally{pollBusy=false;}},650);
api('catalog').then(async c=>{catalog=c;$('#class-choice').innerHTML=Object.entries(c.classes).map(([k,v])=>`<option value="${k}">${esc(v.name)}</option>`).join('');const updateClass=()=>{$('#class-description').textContent=c.classes[$('#class-choice').value].desc;};$('#class-choice').value='warrior';$('#class-choice').onchange=updateClass;updateClass();const existing=await api('session');if(existing.snapshot)apply(existing);show('home');}).catch(e=>{$('#page-screen').textContent='Unable to open Soules. '+e.message;});
theme();

// Local conveniences: these do not spend turns or change game state.
$('#latest-output').onclick=()=>{$('#terminal').scrollTop=$('#terminal').scrollHeight;};
$('#clear-journal').onclick=()=>{$('#terminal').replaceChildren();notice('Journal display cleared. Your progress and saves are unchanged.');};
$('#copy-journal').onclick=async()=>{try{await navigator.clipboard.writeText($('#terminal').innerText);notice('Journal copied.');}catch(_){notice('Clipboard unavailable. Select the journal text to copy it.');}};
$('#compact-status').onclick=()=>{preferences.compact=!preferences.compact;savePreferences();};
$('#recall-command').onclick=()=>{if(commandHistory.length){$('#command').value=commandHistory.at(-1);$('#command').focus();}};
document.addEventListener('keydown',event=>{
 if(window.buttonsOnly?.()||view!=='play'||document.querySelector('dialog[open]')||event.ctrlKey||event.metaKey||event.altKey)return;
 const input=$('#command'),editing=['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName);
 const bindings={focus:'/',latest:'End',back:'Escape',...(preferences.bindings||{})};
 if(event.key===bindings.latest&&!editing){event.preventDefault();$('#latest-output').click();return;}
 if(event.key===bindings.focus&&!editing&&!input.disabled){event.preventDefault();input.focus();return;}
 if(event.key===bindings.back&&(!editing||event.key==='Escape')&&!$('#back').disabled){event.preventDefault();$('#back').click();return;}
 if(event.target!==input||!commandHistory.length)return;
 if(event.key==='ArrowUp'){event.preventDefault();if(historyPosition===commandHistory.length)historyDraft=input.value;historyPosition=Math.max(0,historyPosition-1);input.value=commandHistory[historyPosition];}
 if(event.key==='ArrowDown'){event.preventDefault();historyPosition=Math.min(commandHistory.length,historyPosition+1);input.value=historyPosition===commandHistory.length?historyDraft:commandHistory[historyPosition];}
});

function villageCards(snapshot,p){
 const v=snapshot?.village,clanReady=packet?.waiting&&packet?.prompt==='Elemental village > ',ready=packet?.waiting&&packet?.prompt==='Village > ',canOpen=packet?.waiting&&['main','category'].includes(snapshot?.phase),bookmarks=Object.values(p.saved_villages||{});
 let html=storyCard(snapshot,p);
 if(v){
  const names={forge:'Blacksmith / Forge',loom:'Loom',tower:'Enchantment Tower',alchemy:'Alchemy Lab',disenchantry:'Disenchantry',temple:'Imbuing Temple',restaurant:'Restaurant',inn:'Inn',farm:'Farm',trade:'Trading Post'};
  html+=`<section class="side-card village-card"><h2>LOCAL VILLAGE</h2><h3>${esc(v.name)}</h3><p>${esc(v.kind)} · Reputation ${v.reputation}<br>Food reputation discount ${v.discount}%<br>${esc(v.development)}<br>${v.projects} community projects built<br>${v.work_orders?.length||0} local work orders</p>${v.work_orders?.length?`<p>${v.work_orders.slice(0,5).map(x=>esc(x.kind)+' · '+x.remaining+' shifts'+(x.remaining===0?' · Ready':'')).join('<br>')}</p>`:''}<ul class="village-services">${v.services.map(key=>`<li><b>${esc(names[key]||key)} · Lv. ${v.levels[key]} · ${['','Basic','Skilled','Excellent'][v.quality[key]]}</b><small>${esc(v.service_details[key])}</small></li>`).join('')}</ul>${v.foods.length?`<h2>RESTAURANT STOCK</h2><p>${v.foods.map(f=>`${esc(f.name)} · ${f.price} souls · ${f.left} left`).join('<br>')}</p>`:'<p>No restaurant here.</p>'}${v.wares?.length?`<h2>MATERIAL STOCK</h2><p>${v.wares.map(x=>`${esc(x.name)} · ${x.price} souls · ${x.left} left`).join('<br>')}</p>`:''}<p>Building supplies: ${Object.entries(v.materials||{}).map(([name,n])=>esc(name)+' '+n).join(', ')||'None yet'}</p><p>Restock / farm regrowth: ${v.restock_in} wanders<br>${v.services.includes('farm')?(v.farm_ready?'Farm ready to harvest':'Farm regrowing')+'<br>':''}${v.errand_ready?'Local request available':'Local request completed this cycle'}</p>${clanReady?`<div class="side-actions"><button data-response="3">Clan shop</button><button data-response="5">Warrior history</button><button data-response="6">Local services</button><button data-response="7">Defend clan</button><button data-response="8">Woods quest</button></div>`:''}${v.note?`<blockquote>${esc(v.note)}</blockquote>`:''}<div class="effect-chips">${v.tags.map(tag=>`<span class="effect-chip">${esc(tag)}</span>`).join('')}</div><div class="side-actions"><button data-response="save" ${!ready?'disabled':''}>${v.saved?'★ Saved':'☆ Save village'}</button><button data-response="note" ${!ready?'disabled':''}>Edit note</button><button data-response="tags" ${!ready?'disabled':''}>Tags</button><button data-response="20" ${!ready?'disabled':''}>Build projects</button><button data-response="21" ${!ready?'disabled':''}>Development</button><button data-response="22" ${!ready?'disabled':''}>Workers</button><button data-response="23" ${!ready?'disabled':''}>Activities</button></div></section>`;
 }
 html+=`<section class="side-card"><h2>SAVED VILLAGES · ${bookmarks.length}</h2>${bookmarks.slice(0,4).map(b=>`<p><b>${esc(b.name)}</b><br>${esc(b.region)}${b.note?'<br>'+esc(b.note):''}</p>`).join('')||'<p>Save a discovered village with notes and tags to remember its specialties.</p>'}<button data-village-directory ${!canOpen?'disabled':''}>Village directory / revisit</button></section>`;
 return html;
}
document.addEventListener('click',async event=>{
 if(!event.target.closest('[data-village-directory]'))return;
 await respond('','explore');
 const index=catalog.groups.find(g=>g.id==='explore').options.findIndex(([id])=>id===47);
 if(packet?.snapshot?.phase==='category'&&packet.snapshot.group==='explore'&&index>=0)await respond(String(index+1));
});

function storyCard(snapshot,p){
 const s=p.source_story,available=packet?.waiting&&['main','category'].includes(snapshot?.phase);
 if(!s&&!snapshot?.objective)return '';
 return `<section class="side-card"><h2>STORY & JOURNEY</h2><p>${esc(snapshot?.objective||'Continue your journey.')}</p>${p.expansion?.activities?.woods_defence?`<p>Whispering Woods defence: ${p.expansion.activities.woods_defence.complete?'Complete':p.expansion.activities.woods_defence.waves+'/3 waves repelled'}</p>`:''}${s?.clues?.length?`<small>${esc(s.clues.at(-1).text)}</small>`:''}${s?.rumours?.length?`<p>Latest rumour: ${esc(s.rumours.at(-1))}</p>`:''}<button data-story-journal ${!available?'disabled':''}>Story journal / professions</button></section>`;
}
document.addEventListener('click',async event=>{
 if(!event.target.closest('[data-story-journal]'))return;
 await respond('','challenges');
 const index=catalog.groups.find(g=>g.id==='challenges').options.findIndex(([id])=>id===33);
 if(packet?.snapshot?.phase==='category'&&packet.snapshot.group==='challenges'&&index>=0)await respond(String(index+1));
});

function fusionFinder(){const options=catalog.content.runes.map(r=>`<option value="${esc(r.name)}">${esc(r.name)}</option>`).join('');return `<article class="page-card"><h2>Two-rune fusion finder</h2><p>All 8,778 pairs of normal runes work, including two copies of one type. Fused runes cannot be ingredients for another fusion. They can charge a core when both components match its elemental energy; the preview lists accepting cores. Each pair keeps its component abilities and gains a named synergy.</p><label>First rune<select id="fusion-first">${options}</select></label><label>Second rune<select id="fusion-second">${options}</select></label><button id="fusion-preview">Show abilities</button><div id="fusion-result" aria-live="polite"></div></article>`;}
document.addEventListener('click',async event=>{if(event.target.id!=='fusion-preview')return;try{const data=await api('fusion?first='+encodeURIComponent($('#fusion-first').value)+'&second='+encodeURIComponent($('#fusion-second').value));const r=data.result;$('#fusion-result').innerHTML=`<h3>${esc(r.name)}</h3><p>${esc(r.ability.name)}: ${esc(r.ability.description)}</p>${data.components.map(c=>`<p><b>${esc(c.name)}</b> · ${esc(c.description)}</p>`).join('')}<p><b>Matching-energy cores:</b> ${data.compatible_cores?.length?data.compatible_cores.map(esc).join(', '):'None — the combined elemental energy does not match a core.'}</p>`;}catch(error){notice(error.message);}});


const TIMELINE='soules-save-timeline',CHRONICLES='soules-run-chronicles';
function rememberCheckpoint(entry){const history=stored(TIMELINE,[]);history.unshift(structuredClone(entry));writeStore(TIMELINE,history.slice(0,5));}
function chronicleRun(p,outcome){if(!p)return;const list=stored(CHRONICLES,[]),id=p.expansion?.character_id||p.name+':'+p.level;const entry={id,name:p.name,level:p.level,region:p.region,chapter:p.chapter||1,outcome,at:new Date().toISOString(),bosses:(p.bosses_defeated||[]).length,companions:(p.companions||[]).map(c=>c.form_name||c.name)};if(list.some(x=>x.id===id&&x.outcome===outcome))return;list.unshift(entry);writeStore(CHRONICLES,list.slice(0,10));}
function expandedSaveTools(){const history=stored(TIMELINE,[]),chronicles=stored(CHRONICLES,[]);return `<section class="page-card"><h2>Save timeline</h2><p>Your five most recent explicit saves. Loading restores that checkpoint; other slots stay safe.</p>${history.map((x,i)=>`<p>${esc(x.label)} · ${esc(new Date(x.savedAt).toLocaleString())} <button data-timeline-load="${i}">Restore</button></p>`).join('')||'<p>No explicit checkpoints yet.</p>'}</section><section class="page-card"><h2>Run chronicles</h2>${chronicles.map(x=>`<p><b>${esc(x.name)}</b> · Level ${x.level} · ${esc(x.outcome)}<br>${esc(x.region)} · ${x.bosses} guardians · ${esc(x.companions.join(', '))}</p>`).join('')||'<p>Fallen and retired runs will be remembered here without restoring their characters.</p>'}<button data-sheet-export>Export character sheet</button></section>`;}
function expandedSettings(){const keys=preferences.bindings||{};return `<section class="page-card keyboard-settings"><h2>Keyboard controls</h2><p>Use a single key or Escape. Numbered choices remain unchanged.</p>${[['focus','Focus answer box','/'],['latest','Jump to latest','End'],['back','Back to category','Escape']].map(([key,label,fallback])=>`<label>${label}<input data-key-binding="${key}" maxlength="16" value="${esc(keys[key]||fallback)}"></label>`).join('')}</section><section class="page-card"><h2>Combat accessibility and rune sounds</h2><label><input id="reader-combat" type="checkbox" ${preferences.readerCombat?'checked':''}> Concise screen-reader combat announcements</label><label>Rune effect volume (0 is muted)<input id="rune-volume" type="range" min="0" max="100" value="${preferences.runeVolume||0}"></label><p>Sounds are optional and start muted. Combat mode announces health and the current question without repeatedly reading the full journal.</p></section>`;}
function runeSeal(name){const index=catalog.content.runes.findIndex(x=>x.name===name)+1;return `<svg class="rune-seal" viewBox="0 0 64 64" role="img" aria-label="${esc(name)} seal"><circle cx="32" cy="32" r="24" fill="none" stroke="currentColor"/>${Array.from({length:8},(_,i)=>{const angle=i*Math.PI/4,x=32+Math.cos(angle)*21,y=32+Math.sin(angle)*21;return index&(1<<i)?`<path d="M32 32 L${x.toFixed(2)} ${y.toFixed(2)}" stroke="currentColor" stroke-width="3"/>`:'';}).join('')}<circle cx="32" cy="32" r="5" fill="currentColor"/></svg>`;}
let runeAudio=null,lastSpoken='';
function tone(){if(!(preferences.runeVolume>0))return;try{const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return;runeAudio??=new Audio();runeAudio.resume().catch(()=>{});const oscillator=runeAudio.createOscillator(),gain=runeAudio.createGain();oscillator.type='sine';oscillator.frequency.value=420;gain.gain.setValueAtTime((preferences.runeVolume/100)*.08,runeAudio.currentTime);gain.gain.exponentialRampToValueAtTime(.001,runeAudio.currentTime+.16);oscillator.connect(gain);gain.connect(runeAudio.destination);oscillator.start();oscillator.stop(runeAudio.currentTime+.17);}catch(_){}}
function accessibleCombat(){const e=packet?.snapshot?.enemy,p=packet?.snapshot?.player;$('#terminal').setAttribute('aria-live',preferences.readerCombat?'off':'polite');const key=epoch+':'+packet?.prompt_id;if(preferences.readerCombat&&e&&p&&lastSpoken!==key){lastSpoken=key;$('#combat-announcer').textContent=`${p.name}: ${Math.ceil(p.hp)} health. ${e.name}: ${Math.ceil(e.hp)} health. ${packet.prompt}`;}}
function exportCharacterSheet(){const p=packet?.snapshot?.player||checkpoint?.player;if(!p)return notice('Start a character first.');const lines=[`SOULES · ${p.name}`,`Level ${p.level} · Chapter ${p.chapter||1}`,`Region: ${p.region}`,`Health ${p.hp}/${p.max_hp} · Hunger ${p.hunger}/100 · Mana ${p.mana}`,`Attack ${p.atk+(p.weapon?.atk||0)} · Defence ${p.def+(p.armour?.def||0)} · Souls ${p.gold}`,`Weapon: ${p.weapon?.name||'none'}`,`Armour: ${p.armour?.name||'none'}`,`Companions: ${(p.companions||[]).map(c=>`${c.form_name||c.name} (stage ${c.stage||0}, hunger ${c.hunger??100})`).join(', ')}`,`Defeated guardians: ${(p.bosses_defeated||[]).join(', ')}`];const url=URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/plain'})),link=document.createElement('a');link.href=url;link.download='soules-character-sheet.txt';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
document.addEventListener('change',event=>{const e=event.target;if(e.dataset.keyBinding){const value=e.value.trim();if(!(value.length===1||['Escape','End','Home','F1','F2','F3'].includes(value)))return notice('Choose a single key, Escape, End, Home or F1–F3.');const all={focus:'/',latest:'End',back:'Escape',...(preferences.bindings||{}),[e.dataset.keyBinding]:value};if(new Set(Object.values(all)).size!==3)return notice('Give each action a different key.');preferences.bindings=all;savePreferences();}if(e.id==='reader-combat'){preferences.readerCombat=e.checked;savePreferences();accessibleCombat();}if(e.id==='rune-volume'){preferences.runeVolume=Number(e.value);savePreferences();tone();}});
document.addEventListener('click',async event=>{const b=event.target.closest('button');if(!b)return;if(b.hasAttribute('data-sheet-export'))exportCharacterSheet();if(b.dataset.timelineLoad!==undefined){const entry=stored(TIMELINE,[])[Number(b.dataset.timelineLoad)];if(entry&&confirm('Restore this checkpoint? Save the current character first if needed.'))await start({save:entry.save});}});

function wanderChanceSummary(reference){
 const p=packet?.snapshot?.player||checkpoint?.player,region=p?.region||'Whispering Woods',profile=reference.regions[region],difficulty=p?.difficulty||'normal';
 const remaining=profile.structures.some(name=>!(p?.discovered_structures?.[region]||[]).includes(name)),bounty=!!profile.bounty&&!(p?.bounties_claimed||[]).includes(profile.bounty),tracked=p?.expansion?.field?.tracked_target?.region===region;
 const labels={structure:'Ordinary structure',elemental_village:'Hidden-clan visit',bounty:'Bounty',ingredient:'Regional ingredient',building_supply:'Building supply',special_event:'Special event',companion:'Companion opportunity',merchant:'Ordinary merchant',peaceful:'Peaceful wandering',monster:'Ordinary monster'};
 const odds=profile.difficulty_scenarios[difficulty][Number(remaining)+':'+Number(bounty)];
 const desc=tracked?'Tracked target: 100%. The weighted random outcome is replaced.':Object.entries(odds).map(([key,value])=>labels[key]+': '+(value*100).toFixed(4).replace(/\.?0+$/,'')+'%').join(' · ');
 return [p?'Your next wander — '+region:'Example wander — '+region,difficulty.toUpperCase()+' · '+desc+' One main roll; listed outcomes are exclusive and sum to 100%. Rare clans and bounties are included, not additional rolls. Estimates assume survival through hunger. Based on your discoveries and bounty record; reopening this tab refreshes the estimate.','Full-wander chances'];
}
