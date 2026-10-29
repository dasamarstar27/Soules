'use strict';
let mapRegion=null;
function mapPlayer(){return packet?.snapshot?.player||checkpoint?.player;}
function mapPlaces(region,p){const world=catalog.content.world_map;const known=p?.discovered_structures?.[region]||[];const sites=[...(world.structures[region]||[])];const clan=world.elemental[region];if(clan&&known.includes(clan.name))sites.push({name:clan.name,type:'elemental',icon:clan.icon});return sites.filter(s=>known.includes(s.name));}
function mapLines(name){const words=name.split(' '),mid=Math.ceil(words.length/2);return `<tspan x="0">${esc(words.slice(0,mid).join(' '))}</tspan><tspan x="0" dy="18">${esc(words.slice(mid).join(' '))}</tspan>`;}
window.worldMapPage=function(){
 const p=mapPlayer(),world=catalog.content.world_map;if(!world)return '<p>Loading map…</p>';
 const selected=mapRegion&&world.regions.includes(mapRegion)?mapRegion:(p?.region||world.regions[0]);mapRegion=selected;
 const points=world.regions.map((name,i)=>({name,x:130+(Math.floor(i/4)%2?3-i%4:i%4)*250,y:70+Math.floor(i/4)*135}));
 const path=points.map((v,i)=>(i?'L':'M')+v.x+','+v.y).join(' ');
 const nodes=points.map(v=>{const current=p?.region===v.name,unlocked=p?.unlocked_regions?.includes(v.name),won=p?.bosses_defeated?.includes(v.name);return `<g role="button" tabindex="0" aria-label="${esc(v.name)}${current?', current region':''}${unlocked?'':', locked'}" aria-pressed="${selected===v.name}" data-map-region="${esc(v.name)}" class="map-node ${current?'current':''} ${unlocked?'':'locked'} ${selected===v.name?'selected':''}" transform="translate(${v.x},${v.y})"><circle r="23"/><text text-anchor="middle" y="6">${current?'●':won?'✓':unlocked?'◇':'🔒'}</text><text class="map-label" text-anchor="middle" y="43">${mapLines(v.name)}</text></g>`}).join('');
 const sites=mapPlaces(selected,p),unlocked=!!p?.unlocked_regions?.includes(selected),ready=canSave()&&!busy;
 const local=sites.length?`<svg class="local-map" viewBox="0 0 1000 ${Math.ceil(sites.length/4)*120+30}" aria-label="Discovered structures in ${esc(selected)}">${sites.map((s,i)=>`<g role="button" tabindex="0" aria-label="Visit ${esc(s.name)}" aria-disabled="${!ready||!unlocked}" data-map-site="${i}" transform="translate(${125+i%4*250},${40+Math.floor(i/4)*120})"><circle r="24"/><text text-anchor="middle" y="7">${esc(s.icon||'◇')}</text><text class="map-label" text-anchor="middle" y="48">${mapLines(s.name)}</text></g>`).join('')}</svg>`:'<p>No structures discovered here yet. Wander to find places and add their markers.</p>';
 return `<span class="eyebrow">YOUR WORLD AT A GLANCE</span><h1>World map</h1><p>Select a region, then a discovered place. ● You are here · ✓ Guardian defeated · 🔒 Locked. Roads show the region-unlock order.</p><label class="map-region-picker">Choose a region<select id="map-region-select">${world.regions.map(name=>`<option value="${esc(name)}" ${name===selected?'selected':''}>${esc(name)}${p?.unlocked_regions?.includes(name)?'':' · locked'}</option>`).join('')}</select></label><div class="world-map-frame"><svg class="world-map" viewBox="0 0 1020 560" aria-label="World regions and connecting routes"><path d="${path}"/>${nodes}</svg></div><section class="page-card"><h2>${esc(selected)}</h2><p>${unlocked?(p.region===selected?'Current region':'Unlocked region'):'Defeat earlier guardians to unlock this region.'} · ${sites.length} discovered places</p><button data-map-travel ${!ready||!unlocked||p.region===selected?'disabled':''}>Travel here</button><button data-play>${p?'Return to adventure':'Play / Continue'}</button>${!ready?'<p>To travel or enter a place, leave the current village, submenu or fight and return to a category menu. Browsing the map is always safe.</p>':''}${local}<div class="map-place-list">${sites.map((s,i)=>{const note=p?.saved_villages?.[selected+'::'+s.name]?.note;return `<div><b>${esc(s.icon||'◇')} ${esc(s.name)}</b><small>${esc(s.type)}${note?' · '+esc(note):''}</small><button data-map-site="${i}" ${!ready||!unlocked?'disabled':''}>Visit ${esc(s.name)}</button></div>`}).join('')}</div></section>`;
};
async function mapNavigate(index){
 if(!canSave()||busy)return notice('Return to a category menu before travelling.');
 const p=mapPlayer(),region=mapRegion,site=index===undefined?null:mapPlaces(region,p)[index];
 if(!p.unlocked_regions.includes(region)||index!==undefined&&!site)return notice('That destination is not available.');
 const world=catalog.content.world_map,ordered=world.regions.filter(r=>p.unlocked_regions.includes(r));
 show('play');
 await respond('','explore');
 if(p.region!==region){await respond(String(catalog.groups.find(g=>g.id==='explore').options.findIndex(v=>v[0]===2)+1));if(packet.prompt!=='Destination > ')return;await respond(String(ordered.indexOf(region)+1));}
 if(site){await respond('','explore');await respond(String(catalog.groups.find(g=>g.id==='explore').options.findIndex(v=>v[0]===17)+1));if(packet.prompt!=='> ')return;const places=mapPlaces(region,mapPlayer());const i=places.findIndex(s=>s.name===site.name);if(i>=0)await respond(String(i));}
}
document.addEventListener('click',event=>{const region=event.target.closest('[data-map-region]'),site=event.target.closest('[data-map-site]');if(region){mapRegion=region.dataset.mapRegion;renderPage();}else if(site){mapNavigate(Number(site.dataset.mapSite)).catch(e=>notice(e.message));}else if(event.target.closest('[data-map-travel]'))mapNavigate().catch(e=>notice(e.message));});
document.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)&&event.target.matches('g[data-map-region],g[data-map-site]')){event.preventDefault();event.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
// Replit embeds can resize their preview or wrap the toolbar after a response.
// Measure the real toolbar rather than assuming a fixed 66-pixel header.
const headerObserver=new ResizeObserver(entries=>{document.documentElement.style.setProperty('--topbar-height',entries[0].target.getBoundingClientRect().height+'px');});
headerObserver.observe(document.querySelector('.topbar'));
for(const event of ['wheel','touchstart','pointerdown','keydown'])document.querySelector('#terminal').addEventListener(event,()=>{journalReadingRevision++;},{passive:true});

document.addEventListener('change',event=>{if(event.target.id==='map-region-select'){mapRegion=event.target.value;renderPage();}});
