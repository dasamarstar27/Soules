'use strict';
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let catalog, packet=null, view='home', cursor=0, busy=false, pollBusy=false, epoch=0, dictionaryTab='runes', dictionarySearch='';
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
const structures={village:['#201b13','#d5be8c'],library:['#1d1726','#c1a9e0'],forge:['#251512','#ecaf7a'],loom:['#231a24','#e0b4d1'],alchemy:['#12231e','#99d6b5'],temple:['#191d2a','#b5cbee'],shrine:['#242010','#e4d08c'],ruins:['#1c211a','#b7c6a1'],cave:['#191b23','#aab6d4'],graveyard:['#181626','#baa7d3'],dungeon:['#201518','#dca3ae'],tower:['#1d192c','#bda9ed'],camp:['#231a12','#dfb58b'],arena:['#241719','#e7b2a8'],elemental:['#241625','#ddb1ed']};
const validHex=x=>typeof x==='string'&&/^#[0-9a-f]{6}$/i.test(x);
function mix(a,b,amount){return '#'+[1,3,5].map(i=>Math.round(parseInt(a.slice(i,i+2),16)*(1-amount)+parseInt(b.slice(i,i+2),16)*amount).toString(16).padStart(2,'0')).join('');}
function light(hex){const c=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return c[0]*.2126+c[1]*.7152+c[2]*.0722;}
function contrast(a,b){const x=light(a),y=light(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
function theme(){
 let bg,accent;const p=packet?.snapshot?.player||checkpoint?.player,location=packet?.snapshot?.location;
 if(preferences.mode==='custom'&&validHex(preferences.bg)&&validHex(preferences.accent)){bg=preferences.bg;accent=preferences.accent;}
 else if(preferences.mode==='fixed'){[,bg,accent]=presets[preferences.preset]||presets.crypt;}
 else [bg,accent]=(location&&structures[location.kind])||regions[p?.region]||presets.crypt.slice(1);
 const text=contrast(bg,'#eeeaf5')>contrast(bg,'#18201c')?'#eeeaf5':'#18201c';
 if(contrast(accent,bg)<3)accent=mix(accent,text,.65);
 const props={'--bg':bg,'--accent':accent,'--text':text,'--muted':mix(bg,text,.68),'--panel':mix(bg,text,.035),'--raised':mix(bg,text,.08),'--line':mix(bg,accent,.27),'--button-text':contrast(accent,'#101018')>contrast(accent,'#fffdf6')?'#101018':'#fffdf6','--font-size':Math.max(12,Math.min(22,Number(preferences.font)||15))+'px'};
 for(const [k,v]of Object.entries(props))document.documentElement.style.setProperty(k,v);
 document.body.classList.toggle('scene-structure',Boolean(location));
 document.documentElement.dataset.themeMode=preferences.mode||'auto';
 document.documentElement.dataset.scene=location?.kind||p?.region||'title';
}
function notice(text){$('#notice').textContent=text;$('#notice').classList.add('show');clearTimeout(notice.timer);notice.timer=setTimeout(()=>$('#notice').classList.remove('show'),5500);}
async function api(path,body){const response=await fetch('/api/original/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const result=await response.json();if(!response.ok)throw new Error(result.error||'The game could not complete that request.');return result;}
function writeStore(key,value){try{localStorage.setItem(key,JSON.stringify(value));return true;}catch(_){notice('Browser storage is unavailable or full. Export a save to keep your progress.');return false;}}
function canSave(){return Boolean(packet?.snapshot?.player&&packet.waiting&&packet.snapshot.phase==='main');}
function safeSave(){return canSave()?{format:'soules-original-v1',player:structuredClone(packet.snapshot.player)}:checkpoint;}
function append(text,cls=''){const line=document.createElement('p');line.textContent=text;line.className=cls;$('#terminal').append(line);while($('#terminal').children.length>650)$('#terminal').firstChild.remove();}
function apply(result){
 if(packet&&result.prompt_id&&result.prompt_id<packet.prompt_id)return;
 const terminal=$('#terminal'),nearBottom=terminal.scrollHeight-terminal.scrollTop-terminal.clientHeight<90;
 for(const line of result.output||[]){if(line.id<cursor)continue;append(line.text,line.text.includes('could not finish')?'error-line':line.text.trim().startsWith('---')?'menu-heading':'');cursor=line.id+1;}
 const newlyDead=result.snapshot?.phase==='dead'&&packet?.snapshot?.phase!=='dead';
 packet=result;
 if(newlyDead){checkpoint=null;localStorage.removeItem(STORE);notice("Your character has died. Begin a new journey.");$('#new-dialog').showModal();}
 if(canSave()){checkpoint=safeSave();writeStore(STORE,checkpoint);}
 if(result.snapshot?.player){renderSidebar();theme();}
 renderGameControls();
 if(nearBottom||busy)terminal.scrollTop=terminal.scrollHeight;
 if(result.error)notice('The game reported an error: '+result.error+'. Your last saved checkpoint is kept.');
}
function show(next){view=next;$('#game-screen').hidden=next!=='play';$('#page-screen').hidden=next==='play';if(next!=='play')renderPage();else {renderGameControls();$('#terminal').scrollTop=$('#terminal').scrollHeight;}renderSidebar();theme();}
async function start(config){
 if(busy)return;busy=true;epoch++;
 try{const result=await api('start',config);cursor=0;$('#terminal').replaceChildren();apply(result);show('play');$('#command').focus();}
 catch(e){notice(e.message);}finally{busy=false;renderGameControls();}
}
function play(){if(packet?.alive&&packet?.snapshot?.phase!=='dead'){show('play');return;}if(checkpoint?.player){start({save:checkpoint});return;}$('#new-dialog').showModal();}
async function respond(text,group){
 if(busy||!packet?.waiting)return;
 busy=true;epoch++;renderGameControls();
 try{if(!group)append('> '+(text||'(Enter)'),'player-response');const result=await api('input',{text,group,prompt_id:packet.prompt_id,since:cursor});apply(result);}
 catch(e){notice(e.message);}finally{busy=false;renderGameControls();if(view==='play')$('#command').focus();}
}
function renderGameControls(){
 if(!catalog)return;const main=packet?.snapshot?.phase==='main',enabled=Boolean(packet?.waiting&&packet.alive&&packet?.snapshot?.phase!=='dead'&&!busy),group=packet?.snapshot?.group||'explore';
 $('#categories').innerHTML=catalog.groups.map(g=>`<button data-group="${g.id}" class="${g.id===group?'active':''}" ${!enabled||!main?'disabled':''}>${esc(g.name)}</button>`).join('');
 $('#action-buttons').innerHTML=main?(catalog.groups.find(g=>g.id===group)?.options||[]).map(([n,label])=>`<button data-response="${n}" ${!enabled?'disabled':''}><b>${n}</b>${esc(label)}</button>`).join(''):'<small style="color:var(--muted)">Answer the current prompt below. Categories unlock when you return.</small>';
 $('#prompt').textContent=packet?.alive?(packet.prompt||'Waiting for the game…'):'Press Play / Continue to resume your saved character.';
 $('#command').disabled=!enabled;$('#send').disabled=!enabled;$('#back').disabled=!enabled||Boolean(packet?.snapshot?.enemy?.hp>0);
 $('#connection').textContent=busy?'Sending…':packet?.alive?(packet.waiting?'● Awaiting your choice':'● The story continues…'):'● Ready to play';
 const location=packet?.snapshot?.location,region=packet?.snapshot?.player?.region;
 $('#scene-name').textContent=location?region+' / '+location.name:(region||'YOUR JOURNEY');
 $('#quick-keys').querySelectorAll('button').forEach(b=>b.disabled=!enabled);
}
function bar(label,value,max,cls=''){return `<div class="bar-label"><span>${esc(label)}</span><span>${Math.max(0,Math.round(value))} / ${max}</span></div><div class="bar ${cls}"><i style="width:${Math.max(0,Math.min(100,value/max*100))}%"></i></div>`;}
function effects(p){const pairs=[...Object.entries(p.status||{}).map(([k,v])=>[k,v,true]),...Object.entries(p.active_buffs||{}).map(([k,v])=>[k,v,false]),...Object.entries(p.active_effects||{}).map(([k,v])=>[k,v.turns_remaining,true])];return pairs.length?pairs.map(([k,v,harm])=>{const e=catalog.content.effects[k];if(e?.target==='self')harm=false;return `<span class="effect-chip ${harm?'harm':''}" title="${esc(e?.description||'An effect from your original game')}">${esc(e?.name||k.replaceAll('_',' '))} · ${esc(v)}</span>`;}).join(''):'<small>No active effects</small>';}
function slots(){const value=stored(SLOTS,[]);return Array.isArray(value)?value.slice(0,6):[];}
function slotControls(index,compact=false){const s=slots()[index];return `<div class="${compact?'slot-row':'page-card'}"><span>${compact?'Slot '+(index+1)+' · ':''}${esc(s?.label||'Empty slot')}</span>${!compact?`<h2>Slot ${index+1}</h2><p>${s?esc(s.save.player.name)+' · Lv. '+s.save.player.level+'<br>'+esc(s.save.player.region)+'<br>'+esc(new Date(s.savedAt).toLocaleString()):'Keep a separate character or a checkpoint here.'}</p>`:''}<div class="buttons"><button data-slot="${index}" data-slot-action="save" ${!canSave()?'disabled':''}>Save here</button>${s?`<button data-slot="${index}" data-slot-action="load">Load</button><button data-slot="${index}" data-slot-action="delete">Delete</button>`:''}</div></div>`;}
function renderSidebar(){
 if(!catalog)return;const snapshot=packet?.snapshot,p=snapshot?.player||checkpoint?.player;
 if(!p){$('#status-sidebar').innerHTML='<div class="side-card"><h2>CHARACTER</h2><h3>A story unwritten.</h3><p>Press Play to choose a name and one of your original five classes.</p></div><div class="side-card"><h2>YOUR SAVES</h2><p>Six separate characters or checkpoints. Export a file to take your journey to another device.</p><button data-view="saves">Open saves</button></div>';return;}
 const cls=catalog.classes[p.class_id],e=snapshot?.enemy,location=snapshot?.location;
 const stats=[['Mana',p.mana],['Gold',p.gold],['Attack',p.atk+(p.weapon?.atk||0)],['Defense',p.def+(p.armour?.def||0)],['Speed',p.speed],['Skill points',p.skill_points||0]];
 $('#status-sidebar').innerHTML=`<section class="side-card"><h2>CHARACTER</h2><div class="identity"><div class="portrait">${esc(cls?.icon||'♙')}</div><div><h3>${esc(p.name)}</h3><small>Level ${p.level} · ${esc(cls?.name||'Adventurer')}</small></div></div>${bar('HEALTH',p.hp,p.max_hp,'hp')}${bar('HUNGER',p.hunger??100,100,'hunger')}${bar('EXPERIENCE',p.xp,p.level*50,'xp')}<div class="stats-grid">${stats.map(([k,v])=>`<div class="stat">${k}<b>${Math.round((v||0)*10)/10}</b></div>`).join('')}</div></section><section class="side-card"><h2>REGION & JOURNEY</h2><h3 style="font-size:18px">${esc(p.region)}</h3>${location?`<p>Inside ${esc(location.name)}</p>`:''}<p>${esc(p.weather||'Clear')} · ${p.is_night?'☽ Night':'☼ Day'}<br>Chapter ${p.chapter||1} · ${p.chapter===2?'Postgame':'The original journey'}<br>${p.unlocked_regions?.length||1} regions unlocked · ${new Set(p.bosses_defeated||[]).size} guardians beaten<br>Corruption ${p.corruption||0}% · Resonance ${p.resonance_streak||0}</p>${p.title?`<p>Title: ${esc(p.title)}</p>`:''}</section>${e&&e.hp>0?`<section class="side-card enemy-card"><h2>${e.phases?'GUARDIAN':'ENEMY'}</h2><h3 style="font-size:18px">${esc(e.name)}</h3>${bar('HEALTH',e.hp,e.max_hp||e.hp,'hp')}<div class="effect-chips">${effects(e)}</div></section>`:''}<section class="side-card"><h2>EQUIPMENT & SATCHEL</h2><p>⚔ ${esc(p.weapon?.name||'No weapon equipped')}<br>🛡 ${esc(p.armour?.name||'No armour equipped')}</p><div class="stats-grid">${[['Weapons',p.weapons],['Armour',p.armours],['Runes',p.runes],['Staffs',p.staffs],['Ingredients',p.ingredients],['Potions',p.potions],['Loot & food',p.inventory],['Forge cores',p.forge_cores],['Elemental cores',p.elemental_cores]].map(([k,v])=>`<div class="stat">${k}<b>${v?.length||0}</b></div>`).join('')}</div><p>${p.weapon?.rune?'Bound: '+esc(p.weapon.rune.name):''}</p></section><section class="side-card"><h2>ACTIVE EFFECTS & BUFFS</h2><div class="effect-chips">${effects(p)}</div></section><section class="side-card"><h2>COMPANIONS & QUESTS</h2><p>${p.companions?.length?p.companions.map(c=>esc(c.name)+(c.stage?' · Stage '+c.stage:'')).join('<br>'):'No companions yet'}<br>${(p.quests||[]).filter(q=>!q.completed).length} active quests · ${(p.achievements||[]).length} achievements<br>${Object.values(p.kill_counts||{}).reduce((n,k)=>n+Number(k||0),0)} enemies defeated · ${p.wander_count||0} explorations</p></section><section class="side-card"><h2>SAVE SLOTS</h2>${Array.from({length:6},(_,i)=>slotControls(i,true)).join('')}<p>Save at a category menu. Submenus and battles stay in the running session.</p><div class="side-actions"><button data-export>↧ Export</button><button data-import>↥ Import</button></div></section>`;
}
function home(){return `<div class="title-hero"><span class="eyebrow">SOULES · THE ORIGINAL TEXT ADVENTURE</span><h1>Your world.<br>Your next choice.</h1><p class="intro">All 46 of your original actions, grouped into clear menus. Follow the story in text, choose a number, and keep your character close in the sidebar.</p><button class="primary" data-play>▶ Play / Continue</button></div><div class="home-options">${[['dictionary','1','Dictionary','Runes, fusions, effects, and ingredients.'],['tutorial','2','Tutorial','Learn the controls without losing your adventure.'],['customise','3','Customise','Region scenery, structure colours, or your own theme.'],['saves','4','Saves','Keep separate characters and portable backups.']].map(([page,n,title,desc])=>`<button data-view="${page}"><b>${n}.</b><span><strong>${title}</strong><small>${desc}</small></span></button>`).join('')}</div><p class="section-note">Your original exploration, equipment, food, companions, crafting, quests, elemental villages, and challenge menus run behind this interface. Some original side systems remain works in progress; this preserves their original menus rather than substituting different mechanics.</p>`;}
function tutorial(){return `<span class="eyebrow">YOUR FIELD GUIDE</span><h1>A text adventure, with room to breathe.</h1><ol class="tutorial-steps"><li><b>Choose a category at the top.</b>Explore, Inventory & Equip, Crafting, Character, Quests & Challenges, World & Social, or System. Each shows the original numbered actions in that group.</li><li><b>Click an action or type its number.</b>The game still tells its story in text. Answer the prompt at the bottom. Quick buttons help with numbers and yes/no choices. Press Enter to submit.</li><li><b>Read the current prompt.</b>While shopping, equipping, or fighting, your response belongs to that submenu. Categories become available again when it ends. Back to category leaves a submenu; it cannot escape an active battle.</li><li><b>Watch the sidebar.</b>Health, hunger, mana, gold, region, weather, equipment, effects, enemies, companions, and saves update as you play. You begin with only a Rusty Sword equipped: no runes, potions, or extra gear. Supplies are finite. In combat, option 8 chooses one rune and consumes it. Weapon-bound runes are permanent and cannot be removed, replaced, or used up. Staff rune charges are finite; normal attacks do not spend carried runes.</li><li><b>Look for structures and hidden villages.</b>Your original discovery system is preserved. Structures are under Explore. Crafting opens your original crafting hub. After Chapter 1, hidden elemental villages offer shops, people, quests, libraries and elemental arts.</li><li><b>Keep more than one character.</b>Six slots store independent snapshots at category menus. The game autosaves there too. Export makes a portable file; reloading restores that checkpoint, not a half-finished battle. Earlier browser-edition saves remain separate.</li><li><b>Make the world yours.</b>Automatic scenery changes by region or structure. Customise can lock a theme or use your own background and accent colours. A− and A+ adjust the adventure text size.</li></ol><button class="primary" data-play>Ready to play</button>`;}
function customise(){return `<span class="eyebrow">YOUR COLOURS, YOUR WORLD</span><h1>Make yourself at home.</h1><section class="page-card"><h2>Background behaviour</h2><label>How should the game look?<select id="theme-mode"><option value="auto" ${preferences.mode==='auto'?'selected':''}>Automatic · match region and structure</option><option value="fixed" ${preferences.mode==='fixed'?'selected':''}>Fixed · keep my chosen theme</option><option value="custom" ${preferences.mode==='custom'?'selected':''}>Custom · choose my own colours</option></select></label><p>Automatic mode gives woods, coasts, tundra, forges, libraries, caves, and other places their own palette. Entering a structure changes its background; leaving restores the region.</p></section><section class="page-card"><h2>Pick a theme</h2><div class="buttons">${Object.entries(presets).map(([k,[name,bg,accent]])=>`<button class="preset" data-preset="${k}" aria-pressed="${preferences.mode==='fixed'&&preferences.preset===k}"><span class="swatch" style="background:${bg};border-color:${accent}"></span>${name}</button>`).join('')}</div></section><section class="page-card"><h2>Choose your own colours</h2><label>Background<input id="background-colour" type="color" value="${validHex(preferences.bg)?preferences.bg:'#100d1c'}"></label><label>Accent<input id="accent-colour" type="color" value="${validHex(preferences.accent)?preferences.accent:'#b998f0'}"></label><p>Colours save in this browser. Text contrast is adjusted automatically so your choices stay readable.</p><button id="reset-theme">Restore automatic scenery</button></section>`;}
function dictionary(){
 const c=catalog.content,q=dictionarySearch.toLowerCase();let entries=[];
 if(dictionaryTab==='runes')entries=c.runes.map(r=>[r.name,(c.effects[r.effect]?.name||r.effect)+' · '+(c.effects[r.effect]?.description||'Original rune effect'),r.element]);
 if(dictionaryTab==='fusions')entries=c.recipes.map(r=>[r.name,r.inputs.join(' + ')+' → '+r.components.map(k=>c.effects[k]?.name||k).join(', '),'Named fusion']);
 if(dictionaryTab==='effects')entries=Object.values(c.effects).map(e=>[e.name,e.description,e.duration+' turns · '+(e.target==='self'?'Blessing':'Affliction')]);
 if(dictionaryTab==='ingredients')entries=c.alchemy.ingredients.map(i=>[i.name,'Found in '+i.region,'Ingredient']);
 entries=entries.filter(r=>r.join(' ').toLowerCase().includes(q));
 return `<span class="eyebrow">THE WORLD, IN WORDS</span><h1>Dictionary</h1><div class="dictionary-tools">${['runes','fusions','effects','ingredients'].map(tab=>`<button data-dictionary="${tab}" class="${dictionaryTab===tab?'active':''}">${tab[0].toUpperCase()+tab.slice(1)}</button>`).join('')}</div><input id="dictionary-search" type="search" placeholder="Search the dictionary…" aria-label="Search dictionary" value="${esc(dictionarySearch)}"><p class="section-note">${entries.length} entries. This reference includes the extended effect catalog; active combat uses your original rune handlers and displays their actual effects in the sidebar.</p><div class="cards">${entries.map(([name,desc,type])=>`<article class="page-card"><span class="eyebrow">${esc(type)}</span><h2>${esc(name)}</h2><p>${esc(desc)}</p></article>`).join('')||'<p>No matching entries.</p>'}</div>`;
}
function saves(){return `<span class="eyebrow">SIX DIFFERENT STORIES</span><h1>Your saved journeys.</h1><p class="intro">Slots keep independent original-game characters in this browser. Save at a category menu, outside a battle or submenu. Loading replaces the current running adventure; other slots stay safe.</p><div class="buttons"><button data-new>New character</button><button data-export>Export checkpoint</button><button data-import>Import save</button></div><div class="save-grid">${Array.from({length:6},(_,i)=>slotControls(i)).join('')}</div><p class="section-note">Clearing browser storage removes local slots. Keep exported backups. The earlier browser edition and its saves remain available at <a href="/edition">Earlier edition</a>.</p>`;}
function renderPage(){if(!catalog)return;$('#page-screen').innerHTML=({home,tutorial,customise,dictionary,saves}[view]||home)();}
async function slotAction(button){const list=slots(),index=Number(button.dataset.slot),action=button.dataset.slotAction;
 try{if(action==='save'){if(!canSave())return notice('Return to a category menu before saving.');if(list[index]&&!confirm('Replace this save slot? Other slots stay safe.'))return;const label=prompt('Name this saved journey:',list[index]?.label||packet.snapshot.player.name);if(label===null)return;list[index]={label:label.trim().slice(0,60)||'My journey',savedAt:new Date().toISOString(),save:safeSave()};if(writeStore(SLOTS,list))notice('Saved in slot '+(index+1)+'.');}
 else if(action==='load'){if(!list[index])return;if(packet?.alive&&!confirm('Load this journey? Save your current character in another slot first if you want to keep it.'))return;await start({save:list[index].save});}
 else if(action==='delete'){if(!confirm('Delete this save slot? Your running character will stay safe.'))return;list[index]=null;writeStore(SLOTS,list);}
 renderSidebar();if(view==='saves')renderPage();}catch(e){notice(e.message);}
}
function exportSave(){const saved=safeSave();if(!saved)return notice('Start an adventure first.');const url=URL.createObjectURL(new Blob([JSON.stringify(saved,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='soules-original-save.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notice('Your category-menu checkpoint was exported.');}
function savePreferences(){writeStore(PREFS,preferences);theme();}
$('#quick-keys').innerHTML=['0','1','2','3','4','5','6','7','8','9','y','n','yes','no'].map(k=>`<button data-response="${k}" disabled>${k}</button>`).join('');
$('#command-form').onsubmit=event=>{event.preventDefault();const value=$('#command').value;$('#command').value='';respond(value);};
$('#back').onclick=()=>respond('/back');$('#play').onclick=play;
$('#font-down').onclick=()=>{preferences.font=Math.max(12,(preferences.font||15)-1);savePreferences();};$('#font-up').onclick=()=>{preferences.font=Math.min(22,(preferences.font||15)+1);savePreferences();};
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
 if(b.dataset.dictionary){dictionaryTab=b.dataset.dictionary;dictionarySearch='';renderPage();return;}
 if(b.dataset.preset){preferences.mode='fixed';preferences.preset=b.dataset.preset;savePreferences();renderPage();return;}
 if(b.id==='reset-theme'){preferences.mode='auto';savePreferences();renderPage();}
});
document.addEventListener('input',event=>{const e=event.target;
 if(e.id==='dictionary-search'){dictionarySearch=e.value;const pos=e.selectionStart;renderPage();$('#dictionary-search').focus();$('#dictionary-search').setSelectionRange(pos,pos);}
 if(e.id==='background-colour'||e.id==='accent-colour'){preferences.mode='custom';preferences[e.id==='background-colour'?'bg':'accent']=e.value;savePreferences();$('#theme-mode').value='custom';}
});
document.addEventListener('change',event=>{if(event.target.id==='theme-mode'){preferences.mode=event.target.value;savePreferences();}});
setInterval(async()=>{if(view!=='play'||!packet?.alive||busy||pollBusy)return;pollBusy=true;const before=epoch;try{const data=await api('session?since='+cursor);if(before===epoch)apply(data);}catch(e){notice('Connection interrupted. Your saved checkpoint is kept.');}finally{pollBusy=false;}},650);
api('catalog').then(async c=>{catalog=c;$('#class-choice').innerHTML=Object.entries(c.classes).map(([k,v])=>`<option value="${k}">${esc(v.name)}</option>`).join('');const updateClass=()=>{$('#class-description').textContent=c.classes[$('#class-choice').value].desc;};$('#class-choice').value='warrior';$('#class-choice').onchange=updateClass;updateClass();const existing=await api('session');if(existing.snapshot)apply(existing);show('home');}).catch(e=>{$('#page-screen').textContent='Unable to open Soules. '+e.message;});
theme();
