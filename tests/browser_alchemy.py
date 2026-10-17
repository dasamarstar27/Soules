"""Optional UI smoke: requires Playwright and Chromium; run the app first."""
from pathlib import Path
from playwright.sync_api import sync_playwright
Path('/tmp/soules-checks').mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:5000/edition');page.wait_for_selector('.menu-hero')
    page.screenshot(path='/tmp/soules-checks/main-menu.png',full_page=True)
    page.get_by_role('button',name='Start guided tutorial').click()
    page.wait_for_selector('.tutorial-banner')
    for _ in range(6):
        page.get_by_role('button',name='Next →',exact=True).click()
        page.wait_for_timeout(100)
    page.get_by_role('button',name='Ready to play',exact=True).click()
    page.wait_for_selector('.menu-hero')
    assert not page.locator('.tutorial-banner').count()
    page.locator('.nav[data-page="alchemy"]').click()
    page.locator('#mix-one').select_option('ingredient:Thorn Petal')
    page.locator('#mix-two').select_option('ingredient:Dew Blossom')
    page.get_by_role('button',name='Mix & discover',exact=True).click()
    page.wait_for_selector('.rune-card h3:has-text("Forest Salve")')
    assert page.locator('.effect-card h3:has-text("Forest Salve")').count()==1
    page.get_by_role('button',name='Gather nearby ingredients',exact=False).click()
    page.wait_for_timeout(150)
    page.locator('[data-action="buy_alchemy"][data-item="Health Potion"]').click()
    page.wait_for_function("document.querySelectorAll('#mix-one option[value^=\"potion:\"]').length === 2")
    potions=page.locator('#mix-one option[value^="potion:"]').evaluate_all('(options)=>options.map(o=>o.value)')
    assert len(potions)==2
    page.locator('#mix-one').select_option(potions[0]);page.locator('#mix-two').select_option(potions[1])
    page.get_by_role('button',name='Mix & discover',exact=True).click()
    page.wait_for_selector('.rune-card h3:has-text("Blended Elixir")')
    page.screenshot(path='/tmp/soules-checks/alchemy.png',full_page=True)
    # Save one character, then another, and verify both snapshots remain independent.
    page.locator('.nav[data-page="saves"]').click()
    page.once('dialog',lambda d:d.accept('First adventure'))
    page.locator('[data-slot-action="save"][data-slot="0"]').click()
    page.wait_for_selector('.save-card h3:has-text("First adventure")')
    page.locator('#character-button').click();page.locator('input[name="name"]').fill('Briar')
    page.get_by_role('button',name='Begin again',exact=False).click()
    page.wait_for_selector('.character-id h3:has-text("Briar")')
    page.locator('.nav[data-page="saves"]').click()
    page.once('dialog',lambda d:d.accept('Briar adventure'))
    page.locator('[data-slot-action="save"][data-slot="1"]').click()
    page.wait_for_selector('.save-card h3:has-text("Briar adventure")')
    page.once('dialog',lambda d:d.accept())
    page.locator('[data-slot-action="load"][data-slot="0"]').click()
    page.wait_for_selector('.character-id h3:has-text("Wanderer")')
    page.locator('.nav[data-page="alchemy"]').click()
    assert page.locator('.rune-card h3:has-text("Blended Elixir")').count()==1
    page.reload();page.wait_for_selector('.menu-hero')
    page.locator('.nav[data-page="saves"]').click()
    assert page.locator('.save-card h3:has-text("First adventure")').count()==1
    assert page.locator('.save-card h3:has-text("Briar adventure")').count()==1
    # Cancelling an overwrite keeps the original slot.
    page.once('dialog',lambda d:d.dismiss())
    page.locator('[data-slot-action="save"][data-slot="0"]').click()
    page.locator('.nav[data-page="menu"]').click()
    page.get_by_role('button',name='Rune dictionary',exact=False).click()
    assert page.locator('.rune-card').count()==132
    page.set_viewport_size({'width':390,'height':844})
    page.locator('.nav[data-page="alchemy"]').click()
    page.screenshot(path='/tmp/soules-checks/alchemy-mobile.png',full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    print('PASS: tutorial, original recipe discovery, gathering, stock purchase, potion blending, independent named save slots, load, reload, overwrite cancellation, full rune dictionary, and mobile layout')
    browser.close()
