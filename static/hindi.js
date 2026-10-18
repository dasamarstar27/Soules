'use strict';
// No English text is passed off as a Hindi translation. Chrome's optional
// on-device translator or an already translated visible passage provides Hindi.
let hindiTranslator=null;
let hindiTranslationPromise=null;

function hindiVoice(){
 const voices=window.speechSynthesis?.getVoices()||[];
 const selected=voices.find(voice=>voice.voiceURI===preferences.readVoices?.hi&&/^hi(?:-|_|$)/i.test(voice.lang));
 return selected||voices.find(voice=>/^hi(?:-|_|$)/i.test(voice.lang));
}

function isHindiPassage(text){const devanagari=(text.match(/[\u0900-\u097f]/g)||[]).length,english=(text.match(/[a-z]/gi)||[]).length;return devanagari>0&&english<=devanagari*2;}

async function translateForHindi(text,revision){
 if(isHindiPassage(text))return text;
 if(typeof window.Translator?.availability!=='function')throw new Error('Hindi translation is not available in this browser. Translate the page to Hindi first, then select a Hindi passage and press Read latest aloud. Open Hindi setup help for instructions.');
 const options={sourceLanguage:'en',targetLanguage:'hi'};
 const availability=await window.Translator.availability(options);
 if(availability==='unavailable')throw new Error('This browser cannot translate English to Hindi on this device. Use the browser’s Translate page → Hindi option; Hindi setup help explains how.');
 if(!hindiTranslator){
  if(!hindiTranslationPromise){
   hindiTranslationPromise=window.Translator.create({...options,monitor(monitor){monitor.addEventListener('downloadprogress',event=>{const progress=event.total?Math.round(event.loaded/event.total*100):Math.round(event.loaded*100);if(revision===readingRevision)narrationStatus('Preparing Hindi translation'+(Number.isFinite(progress)?' · '+progress+'%':'')+'…');});}}).then(translator=>{hindiTranslator=translator;return translator;}).finally(()=>{hindiTranslationPromise=null;});
  }
  await hindiTranslationPromise;
 }
 const translated=await hindiTranslator.translate(text);
 if(typeof translated!=='string'||!/[\u0900-\u097f]/.test(translated))throw new Error('No Hindi translation was returned. Translate the page with your browser or select a Hindi passage.');
 return translated;
}

function hindiSetup(){
 const dialog=$('#hindi-setup-dialog');if(dialog.open)return;dialog.showModal();
}

document.addEventListener('click',event=>{
 const button=event.target.closest('button');if(!button)return;
 if(button.id==='hindi-setup')hindiSetup();
 if(button.id==='close-hindi-setup')$('#hindi-setup-dialog').close();
 if(button.id==='read-hindi'){
  preferences.readLanguage='hi';savePreferences();readComfortText();
 }
});
