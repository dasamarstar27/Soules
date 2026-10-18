'use strict';
$('#release-version').addEventListener('click',()=>{
 $('#version-export').disabled=!safeSave();
 $('#versions-dialog').showModal();
});
$('#close-versions').addEventListener('click',()=>$('#versions-dialog').close());
$('#version-export').addEventListener('click',exportSave);
document.addEventListener('click',async event=>{
 const button=event.target.closest('[data-copy-release]');if(!button)return;
 try{await navigator.clipboard.writeText(button.dataset.copyRelease);notice('Release commit copied. Use it in your hosting dashboard to deploy this version.');}
 catch(_){notice('Clipboard unavailable. The commit is printed below the release.');}
});
