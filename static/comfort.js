'use strict';
// Presentation helpers only: every choice still goes through the original prompt.
let comfortOutput='', comfortChoices=[], comfortPrompt='', comfortSpeech=null, comfortNodes=[], readingRevision=0;

function updateComfortAppearance(){
 const on=Boolean(preferences.comfort),root=document.documentElement;
 document.body.classList.toggle('comfort-mode',on);
 $('#command').placeholder='Type an answer… ↑↓ history · / focus';
 $('#command').setAttribute('aria-label',on?'Your answer':'Game command');
 $('#back').textContent=on?'Back to choices':'↶ Back to category';
 $('.topbar [data-view="customise"]').textContent=on?'Settings':'◈ Theme';
 $('#easy-reading')?.setAttribute('aria-pressed',String(on));
 $('#easy-reading')?.setAttribute('aria-label','Easy reading '+(on?'on':'off'));
 if(on){
  root.style.setProperty('--font-size',Math.max(18,Math.min(28,Number(preferences.comfortFont)||22))+'px');
  const bg=root.style.getPropertyValue('--bg'),text=root.style.getPropertyValue('--text');
  let accent=root.style.getPropertyValue('--accent');
  if(contrast(accent,bg)<4.5)accent=mix(accent,text,.75);
  root.style.setProperty('--accent',accent);
  root.style.setProperty('--muted',mix(bg,text,.85));
  root.style.setProperty('--line',mix(bg,accent,.65));
  root.style.setProperty('--button-text',contrast(accent,'#101018')>contrast(accent,'#fffdf6')?'#101018':'#fffdf6');
 }
 window.updateButtonAppearance?.();
}

function recordComfortOutput(lines,nodes=[]){
 const text=lines.join('\n');
 if(!text.trim())return;
 comfortOutput=text;comfortNodes=nodes;
 stopComfortReading();
 const next=comfortOptions(text,packet?.prompt||'');
 comfortChoices=next;
 comfortPrompt=packet?.prompt||'';
}

function comfortOptions(text,prompt){
 if(/yes\s*\/\s*no/i.test(prompt))return [['yes','Yes'],['no','No']];
 if(/\by\s*\/\s*n\b/i.test(prompt))return [['y','Yes'],['n','No']];
 if(/press enter/i.test(prompt))return [['','Continue']];
 if(/quantity|how many|amount|\bname your|\bweapon name|\bnote\b|\btags?\b|\bsearch\b|filter text/i.test(prompt))return [];
 if(/1 atk/.test(prompt)){
  const rows=[['1','Attack'],['2','Use a scroll'],['3','Use a staff'],['4','Try to run away']];
  if(/5 /.test(prompt))rows.push(['5','Use class skill']);
  if(/6 /.test(prompt))rows.push(['6','Companion move']);
  if(/7 /.test(prompt))rows.push(['7','Drink a potion']);
  rows.push(['8','Use a loose rune'],['9','Elemental art']);return rows;
 }
 // Discard earlier menus, so a saved journal cannot offer stale choices.
 const headers=[...text.matchAll(/^\s*(?:[-=]{3,}|[^\n]*[─═]{3,})[^\n]*$/gm)];
 if(headers.length)text=text.slice(headers.at(-1).index);
 const choices=new Map();
 for(const match of text.matchAll(/^\s*(-?\d+|[A-Za-z])[.):]\s+([^\n]+)$/gm)){
  if(choices.size>300)break;
  choices.set(match[1],match[2].trim());
 }
 for(const match of text.matchAll(/(?:^|[·\n])\s*([A-Za-z]|-?\d+)[:.)]\s*([^·\n]+)/g))choices.set(match[1],match[2].trim());
 return [...choices];
}

function renderComfortControls(){
 if(window.renderButtonAnswers)return renderButtonAnswers();
 const host=$('#comfort-choices');if(!host)return;
 const on=Boolean(preferences.comfort),main=['main','category'].includes(packet?.snapshot?.phase);
 host.hidden=!on||main||!packet?.waiting||Boolean(packet?.snapshot?.assignment)||!comfortChoices.length||comfortPrompt!==packet.prompt;
 if(host.hidden){host.replaceChildren();return;}
 host.innerHTML='<p>Choose by clicking a button. You can also type the number or letter.</p><div>'+comfortChoices.map(([answer,label])=>`<button data-response="${esc(answer)}" ${busy?'disabled':''}><b>${esc(answer||'↵')}</b> ${esc(label)}</button>`).join('')+'</div>';
}

function narrationStatus(text){$('#narration-status').textContent=text;}

function stopComfortReading(){
 readingRevision++;
 narrationStatus('');
 if('speechSynthesis' in window)window.speechSynthesis.cancel();
 comfortSpeech=null;
 $('#stop-reading')?.setAttribute('disabled','');
}

async function readComfortText(){
 if(!('speechSynthesis' in window)||!('SpeechSynthesisUtterance' in window))return notice('Read-aloud is unavailable in this browser.');
 const selected=window.getSelection()?.toString().trim();
 const visible=comfortNodes.filter(node=>node.isConnected).map(node=>node.textContent).join('\n');
 const text=selected||[visible||comfortOutput,$('#prompt').textContent].filter(Boolean).join('\n');
 if(!text)return notice('Start an adventure to read its latest text.');
 stopComfortReading();
 const revision=readingRevision,language=preferences.readLanguage==='hi'?'hi':'en';
 let passage=text.slice(0,6000),voice;
 $('#stop-reading').removeAttribute('disabled');
 try{
  if(language==='hi'){
   voice=hindiVoice();
   if(!voice)throw new Error('No Hindi voice is installed or loaded. Open Hindi setup help to add one, then try again.');
   narrationStatus('Preparing Hindi narration…');
   passage=await translateForHindi(passage,revision);
   if(revision!==readingRevision)return;
  }else{
   const id=preferences.readVoices?.en||preferences.readVoice;
   voice=window.speechSynthesis.getVoices().find(v=>v.voiceURI===id);
  }
  comfortSpeech=new SpeechSynthesisUtterance(passage);
  comfortSpeech.lang=language==='hi'?'hi-IN':'en';
  comfortSpeech.rate=Math.max(.6,Math.min(1.2,Number(preferences.readRate)||.9));
  if(voice)comfortSpeech.voice=voice;
  comfortSpeech.onend=()=>{if(revision===readingRevision){$('#stop-reading').setAttribute('disabled','');narrationStatus('');}};
  comfortSpeech.onerror=()=>{if(revision===readingRevision){$('#stop-reading').setAttribute('disabled','');narrationStatus('');notice('The browser could not read this passage. Try another installed voice.');}};
  window.speechSynthesis.speak(comfortSpeech);
  narrationStatus(language==='hi'?'हिंदी में पढ़ रहे हैं · Reading in Hindi':'Reading aloud');
 }catch(error){
  if(revision!==readingRevision)return;
  $('#stop-reading').setAttribute('disabled','');narrationStatus(error.message);notice(error.message);
 }
}

function comfortSettings(){
 const supported='speechSynthesis' in window&&'SpeechSynthesisUtterance' in window;
 const language=preferences.readLanguage==='hi'?'hi':'en';
 const voices=supported?window.speechSynthesis.getVoices().filter(v=>language==='hi'?/^hi(?:-|_|$)/i.test(v.lang):!/^hi(?:-|_|$)/i.test(v.lang)):[];
 return `<section class="page-card"><h2>Easy reading</h2><p>Use larger, clearer text, spacious buttons, stronger contrast and button answers without typing. Scenery colours stay yours. Choices wait until you are ready.</p><button id="comfort-setting" aria-pressed="${Boolean(preferences.comfort)}">${preferences.comfort?'Turn easy reading off':'Turn easy reading on'}</button><p>Your preference stays in this browser. A− and A+ adjust easy-reading text separately from standard text.</p><label>Narration language<select id="reading-language"><option value="en" ${language==='en'?'selected':''}>English</option><option value="hi" ${language==='hi'?'selected':''}>हिंदी · Hindi</option></select></label><p>Hindi narration needs a Hindi voice and translated Hindi text. Supported browsers can translate automatically; otherwise use the browser’s Translate page → Hindi first.</p><button id="hindi-setup">Hindi setup help · हिंदी सहायता</button><label>Read-aloud speed<select id="reading-speed"><option value="0.7" ${Number(preferences.readRate)===.7?'selected':''}>Slower</option><option value="0.9" ${!preferences.readRate||Number(preferences.readRate)===.9?'selected':''}>Comfortable</option><option value="1.1" ${Number(preferences.readRate)===1.1?'selected':''}>Faster</option></select></label><label>Read-aloud voice<select id="reading-voice" ${!supported?'disabled':''}><option value="">Browser default</option>${voices.map(v=>`<option value="${esc(v.voiceURI)}" ${(preferences.readVoices?.[language]||(language==='en'?preferences.readVoice:''))===v.voiceURI?'selected':''}>${esc(v.name)} · ${esc(v.lang)}</option>`).join('')}</select></label><p>Read latest aloud speaks only when you press it. Select a passage first to read that selection. Stop reading ends speech. Long passages read up to 6,000 characters at a time. ${supported?'Voices depend on this device and browser.':'Read-aloud is unavailable in this browser.'}</p></section>`;
}

function toggleComfort(){
 preferences.comfort=!preferences.comfort;
 savePreferences();renderGameControls();renderSidebar();
 if(view!=='play')renderPage();
 notice(preferences.comfort?'Easy reading is on. Use A− or A+ to change the text size.':'Standard reading restored.');
}

document.addEventListener('click',event=>{
 const b=event.target.closest('button');if(!b)return;
 if(['easy-reading','comfort-setting'].includes(b.id))toggleComfort();
 if(b.id==='read-latest')readComfortText();
 if(b.id==='stop-reading')stopComfortReading();
 if(b.id==='word-help')$('#word-help-dialog').showModal();
 if(b.id==='close-word-help')$('#word-help-dialog').close();
});
document.addEventListener('change',event=>{
 if(event.target.id==='reading-speed'){preferences.readRate=Number(event.target.value);savePreferences();}
 if(event.target.id==='reading-language'){stopComfortReading();preferences.readLanguage=event.target.value;savePreferences();renderPage();}
 if(event.target.id==='reading-voice'){preferences.readVoices={...(preferences.readVoices||{}),[preferences.readLanguage==='hi'?'hi':'en']:event.target.value};savePreferences();}
});
if('speechSynthesis' in window)window.speechSynthesis.addEventListener?.('voiceschanged',()=>{if(view==='customise')renderPage();});
$('#read-latest').disabled=!('speechSynthesis' in window&&'SpeechSynthesisUtterance' in window);
window.addEventListener('pagehide',stopComfortReading);
updateComfortAppearance();
