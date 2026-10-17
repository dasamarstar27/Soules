from playwright.sync_api import sync_playwright
from pathlib import Path
Path("/tmp/soules-checks").mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:5000/edition');page.wait_for_selector('.menu-hero')
    page.get_by_role('button',name='Play / Continue').click();page.wait_for_selector('.hero')
    page.screenshot(path='/tmp/soules-checks/desktop.png',full_page=True)
    page.get_by_role('button',name='Rune collection',exact=False).click()
    page.locator('[data-action="equip"]').first.click()
    page.wait_for_selector('button:has-text("Unbind rune")')
    page.get_by_role('button',name='Adventure',exact=False).click()
    page.locator('[data-action="explore"]').click()
    page.wait_for_selector('#cast-rune')
    page.locator('[data-action="cast"]').click()
    page.wait_for_timeout(150)
    for _ in range(15):
        if not page.locator('[data-action="attack"]').count():break
        page.locator('[data-action="attack"]').click();page.wait_for_timeout(100)
    assert not page.locator('[data-action="attack"]').count(),'first battle must end'
    page.get_by_role('button',name='Fusion altar',exact=False).click()
    page.locator('[data-select]').nth(0).click();page.locator('[data-select]').nth(1).click()
    page.wait_for_selector('.altar h3:has-text("Steam Cataclysm")')
    page.screenshot(path='/tmp/soules-checks/fusion.png',full_page=True)
    page.locator('[data-action="fuse"]').click()
    page.wait_for_selector('.rune-card h3:has-text("Steam Cataclysm")')
    page.get_by_role('button',name='The codex',exact=False).click()
    page.locator('#search').fill('poison')
    assert page.locator('.effect-card').count()>=2
    page.get_by_role('button',name='World map',exact=False).click()
    assert page.locator('.region-card').count()==15
    page.set_viewport_size({'width':390,'height':844})
    page.get_by_role('button',name='Adventure',exact=False).click()
    page.screenshot(path='/tmp/soules-checks/mobile.png',full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),'mobile overflow'
    page.locator('#character-button').click();page.wait_for_selector('dialog[open]')
    page.locator('input[name="name"]').fill('Ash')
    page.get_by_role('button',name='Begin again').click();page.wait_for_selector('.character-id h3:has-text("Ash")')
    # Reload restores the browser autosave, including the newly chosen character.
    page.reload();page.wait_for_selector('.menu-hero')
    page.get_by_role('button',name='Play / Continue').click()
    page.wait_for_selector('.character-id h3:has-text("Ash")')
    with page.expect_download() as download:
        page.locator('#save-button').evaluate('(button) => button.click()')
    save_path='/tmp/soules-checks/exported-save.json'
    download.value.save_as(save_path)
    page.locator('#character-button').click()
    page.locator('input[name="name"]').fill('Other')
    page.get_by_role('button',name='Begin again').click()
    page.wait_for_selector('.character-id h3:has-text("Other")')
    page.locator('#load-file').set_input_files(save_path)
    page.wait_for_selector('.character-id h3:has-text("Ash")')
    assert not errors,errors
    print('PASS: desktop/mobile navigation, bindings, combat, fusion, codex search, map, new character; no JavaScript errors')
    browser.close()
