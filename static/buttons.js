'use strict';
// Button adapters submit the same answers as the text interface, without a keyboard.
function buttonsOnly(){return Boolean(preferences.comfort||document.body.classList.contains('tablet-mode'));}
let buttonQuantity=1,buttonPromptId=null;
const choiceButtons=rows=>rows.map(([answer,label])=>`<button type="button" data-response="${esc(answer)}" ${busy?'disabled':''}>${esc(label)}</button>`).join('');
function ownedNames(){const p=packet?.snapshot?.player||{};return [...new Set(['weapons','armours','staffs','runes','inventory','ingredients','potions'].flatMap(key=>(p[key]||[]).map(item=>typeof item==='string'?item:item.name)).filter(Boolean))];}
function buttonInputChoices(text,prompt){
 // The active question takes priority over old menu text and item names.
 const answers=promptAnswerOptions(prompt);
 if(answers)return answers;
 const context=text.trim().split('\n').slice(-3).join('\n')+'\n'+prompt;
 if(/prestige\/cancel/i.test(prompt))return [['prestige','Begin prestige journey'],['cancel','Cancel']];
 if(/quantity|how many|amount|asking price/i.test(prompt))return 'quantity';
 if(/favourite \/ unfavourite/i.test(prompt))return ownedNames().map(name=>[name,name]).concat([['','Cancel']]);
 if(/\bnote\b|\btags?\b/i.test(prompt))return ['Cheap food','Good blacksmith','Farming village','Good alchemist','Rare materials','Visit again',''].map(value=>[value,value||'Clear note / tags']);
 if(/\bsearch\b|filter text|find name, element/i.test(prompt))return ['','fire','ice','storm','nature','wood','metal','food','potion'].map(value=>[value,value||'Show everything']);
 if(/signature|guild name|name your|weapon name|name.*weapon|name.*staff/i.test(context))return ['Wanderer','Nanu','Dawnblade','Starfall','Guardians',''].map(value=>[value,value||'Use default / cancel']);
 if(/then sort by/i.test(prompt))return ['None','Name','Attack','Defence','Element','Sell value'].map((name,i)=>[String(i),name]);
 if(/bind to 1\./i.test(prompt))return [['1','Staff'],['2','Weapon']];
 return null;
}
function renderButtonAnswers(){
 const host=$('#comfort-choices');if(!host)return;
 const main=['main','category'].includes(packet?.snapshot?.phase);
 host.hidden=!buttonsOnly()||main||!packet?.waiting||Boolean(packet?.snapshot?.assignment);
 if(host.hidden){host.replaceChildren();return;}
 const prompt=packet.prompt||'',special=buttonInputChoices(comfortOutput,prompt);
 if(buttonPromptId!==packet.prompt_id){buttonPromptId=packet.prompt_id;buttonQuantity=1;}
 let body;
 if(special==='quantity'){
  const bound=prompt.match(/\(1\s*[–-]\s*(\d+)/),max=bound?Number(bound[1]):100000;
  buttonQuantity=Math.max(1,Math.min(max,buttonQuantity));
  body=`<div class="quantity-controls"><button data-quantity="-5" ${busy?'disabled':''}>−5</button><button data-quantity="-1" ${busy?'disabled':''}>−1</button><output aria-live="polite">${buttonQuantity}</output><button data-quantity="1" ${busy?'disabled':''}>+1</button><button data-quantity="5" ${busy?'disabled':''}>+5</button></div>`+choiceButtons([[String(buttonQuantity),'Confirm '+buttonQuantity],['0','Cancel']]);
 }else{
  let rows=special||comfortChoices;
  if(!rows.length)rows=Array.from({length:10},(_,i)=>[String(i),'Choose '+i]);
  if(/(?:or ['‘]?done|\bdone\b)/i.test(prompt)&&!rows.some(r=>r[0]==='done'))rows=[...rows,['done','Finish selecting']];
  if(/0.*(?:cancel|back)|(?:cancel|back).*0/i.test(prompt)&&!rows.some(r=>r[0]==='0'))rows=[...rows,['0','Cancel']];
  if(/-1.*(?:cancel|pass)|(?:cancel|pass).*-1/i.test(prompt)&&!rows.some(r=>r[0]==='-1'))rows=[...rows,['-1','Cancel']];
  body=choiceButtons(rows);
 }
 host.innerHTML='<p>Choose an answer below.</p><div class="button-answer-grid">'+body+'</div>';
 if(!(packet?.snapshot?.enemy?.hp>0))host.insertAdjacentHTML('beforeend',choiceButtons([['/back','Back to categories']]));
}
function updateButtonAppearance(){
 document.body.classList.toggle('buttons-only',buttonsOnly());
 if(buttonsOnly()&&dictionarySearch){dictionarySearch='';}
 const form=$('#new-character'),name=form?.elements.name;
 if(form&&!$('#preset-names')){
  const section=document.createElement('div');section.id='preset-names';
  section.innerHTML='<p>Choose your character’s name.</p><div class="buttons">'+['Wanderer','Nanu','Asha','Arjun','Mira'].map(value=>`<button type="button" data-character-name="${value}">${value}</button>`).join('')+'</div>';
  name.closest('label').after(section);
 }
 document.querySelectorAll('[data-character-name]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.characterName===name?.value)));
 renderButtonAnswers();
}
document.addEventListener('click',event=>{
 const button=event.target.closest('button');if(!button)return;
 if(button.hasAttribute('data-quantity')){buttonQuantity+=Number(button.dataset.quantity);renderButtonAnswers();}
 if(button.dataset.characterName){$('#new-character').elements.name.value=button.dataset.characterName;updateButtonAppearance();}
});
updateButtonAppearance();

function difficultySettings(){
 const player=packet?.snapshot?.player,current=player?.difficulty||'normal';
 return `<section class="page-card"><h2>Adventure difficulty</h2><p>Normal uses the standard combat balance. Easy gives enemies 25% less health and reduces their direct attack damage by 40%. Rewards, starting equipment and the story stay the same. Easy has fewer monster encounters and more gathering; see Dictionary → Wandering. Status effects and hazards remain dangerous, and death still ends your character.</p>${player?`<p>Current character: <b>${current==='easy'?'Easy':'Normal'}</b>. Change at a category or village menu, outside combat and purchases.</p><div class="buttons">${['easy','normal'].map(value=>`<button data-difficulty="${value}" aria-pressed="${current===value}" ${!quickReady()||busy?'disabled':''}>${value==='easy'?'Easy · beginners':'Normal · standard balance'}</button>`).join('')}</div>`:'<p>Choose Easy or Normal when creating your character.</p>'}<p>Reading and tablet settings are separate: either difficulty works with either layout.</p></section>`;
}
document.addEventListener('click',async event=>{
 const button=event.target.closest('[data-difficulty]');if(!button)return;
 await respond('/difficulty '+button.dataset.difficulty);
 if(view!=='play')renderPage();
});
