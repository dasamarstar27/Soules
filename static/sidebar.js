'use strict';
// Update values in place so polling does not replace focused controls or reading anchors.
function sidebarKey(node){
 if(node.nodeType!==1)return null;
 if(node.id)return 'id:'+node.id;
 if(node.dataset.villagePanel)return 'panel:'+node.dataset.villagePanel;
 if(node.classList.contains('side-card'))return 'card:'+node.querySelector('h2')?.textContent;
 return null;
}
function syncSidebarNode(current,next){
 if(current.nodeType===3){if(current.nodeValue!==next.nodeValue)current.nodeValue=next.nodeValue;return;}
 if(current.nodeType!==1)return;
 for(const attr of [...current.attributes])if(!next.hasAttribute(attr.name))current.removeAttribute(attr.name);
 for(const attr of [...next.attributes])if(current.getAttribute(attr.name)!==attr.value)current.setAttribute(attr.name,attr.value);
 syncSidebarChildren(current,next);
}
function syncSidebarChildren(parent,next){
 const wanted=[...next.childNodes];
 for(let index=0;index<wanted.length;index++){
  const incoming=wanted[index],key=sidebarKey(incoming);let current=parent.childNodes[index];
  if(key){const found=[...parent.childNodes].find(child=>sidebarKey(child)===key);if(found&&found!==current){parent.insertBefore(found,current||null);current=found;}else if(!found){parent.insertBefore(incoming.cloneNode(true),current||null);continue;}}
  else if(current&&sidebarKey(current)){parent.insertBefore(incoming.cloneNode(true),current);continue;}
  if(!current){parent.append(incoming.cloneNode(true));continue;}
  if(current.nodeType!==incoming.nodeType||current.nodeName!==incoming.nodeName){current.replaceWith(incoming.cloneNode(true));continue;}
  syncSidebarNode(current,incoming);
 }
 while(parent.childNodes.length>wanted.length)parent.lastChild.remove();
}
window.updateSidebar=function(sidebar,html){
 const top=sidebar.scrollTop,rect=sidebar.getBoundingClientRect();
 let anchor=null;
 for(const offset of [8,24,48]){const candidate=document.elementFromPoint(Math.max(0,rect.left+20),Math.max(0,rect.top+offset));if(candidate&&candidate!==sidebar&&sidebar.contains(candidate)){anchor=candidate;break;}}
 const anchorTop=anchor?.getBoundingClientRect().top;
 const template=document.createElement('template');template.innerHTML=html;
 const cards=[...template.content.children],heading=card=>card.querySelector('h2')?.textContent;
 const priority=['CHARACTER','ENEMY','GUARDIAN','LOCAL VILLAGE','REGION & JOURNEY'];
 for(const title of [...priority].reverse()){const card=cards.find(card=>heading(card)===title);if(card)template.content.prepend(card);}
 syncSidebarChildren(sidebar,template.content);
 if(anchor?.isConnected&&sidebar.contains(anchor))sidebar.scrollTop+=anchor.getBoundingClientRect().top-anchorTop;
 else sidebar.scrollTop=top;
};
