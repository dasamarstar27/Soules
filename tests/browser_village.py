"""Village hub and chapter transition smoke test; run the app first."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from game import new_game,encounter
Path('/tmp/soules-checks').mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1050})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:5000/edition');page.wait_for_selector('.menu-hero')
    game=new_game();game['player']['gold']=500;game['shards']=10
    page.evaluate("async g=>{await fetch('/api/load',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(g)});localStorage.setItem('soules-autosave',JSON.stringify(g));}",game)
    page.reload();page.wait_for_selector('.menu-hero')
    page.locator('.nav[data-page="village"]').click()
    assert page.locator('.workshop').count()==6
    page.locator('[data-station="forge"]').click()
    page.wait_for_function("JSON.parse(localStorage.getItem('soules-autosave')).player.atk===16")
    page.locator('[data-station="loom"]').click()
    page.wait_for_function("JSON.parse(localStorage.getItem('soules-autosave')).player.def===5")
    inputs=[r['id'] for r in game['runes'][:2]]
    tower=page.locator('[data-workshop="enchantment_tower"]')
    tower.locator('select').nth(0).select_option(inputs[0]);tower.locator('select').nth(1).select_option(inputs[1])
    tower.locator('button').click()
    page.wait_for_function("JSON.parse(localStorage.getItem('soules-autosave')).runes.some(r=>r.kind==='staff')")
    staff=page.evaluate("JSON.parse(localStorage.getItem('soules-autosave')).runes.find(r=>r.kind==='staff')")
    ice=next(r for r in game['runes'] if r['name']=='Ice Rune')
    temple=page.locator('[data-workshop="source_temple"]')
    temple.locator('[data-craft-staff]').select_option(staff['id'])
    temple.locator('[data-craft-rune]').select_option(ice['id'])
    temple.locator('button').click()
    page.wait_for_function("JSON.parse(localStorage.getItem('soules-autosave')).runes.find(r=>r.kind==='staff').components.includes('freeze')")
    salvage=page.locator('[data-workshop="disenchantry"]')
    salvage.locator('select').select_option(game['runes'][2]['id'])
    salvage.locator('button').click()
    page.wait_for_function("JSON.parse(localStorage.getItem('soules-autosave')).runes.length===3")
    page.screenshot(path='/tmp/soules-checks/village.png',full_page=True)
    page.locator('[data-workshop="alchemy_lab"] button').click()
    page.wait_for_selector('#mix-one')
    page.locator('.nav[data-page="village"]').click()
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    # The final main-game guardian opens Chapter 2 with no Creator fight.
    ending=new_game();ending['region']=ending['unlocked']=14
    encounter(ending,boss=True);ending['enemy']['hp']=1
    page.evaluate("async g=>{await fetch('/api/load',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(g)});localStorage.setItem('soules-autosave',JSON.stringify(g));}",ending)
    page.reload();page.wait_for_selector('.menu-hero')
    page.get_by_role('button',name='Play / Continue').click()
    page.wait_for_selector('.hero-content h2:has-text("The Dreaming God")')
    page.locator('[data-action="attack"]').click()
    page.wait_for_selector('.victory:has-text("Chapter 2")')
    page.locator('.nav[data-page="menu"]').click()
    assert 'CHAPTER 2' in page.locator('.menu-copy .eyebrow').inner_text()
    page.screenshot(path='/tmp/soules-checks/chapter-two-mobile.png',full_page=True)
    assert not errors,errors
    print('PASS: all six village stations, weapon/armor upgrades, staff crafting, infusion, salvage, alchemy link, mobile layout, Dreamscape victory, and Chapter 2 menu')
    browser.close()
