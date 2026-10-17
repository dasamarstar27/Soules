"""Prominent story question, complete guide, companion care, mode removal."""
from copy import deepcopy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
import data

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1050})
    errors = []
    page.on('pageerror', lambda err: errors.append(str(err)))
    page.goto('http://127.0.0.1:5000')
    page.locator('[data-view="tutorial"]').click()
    page.wait_for_selector('.guide-section')
    assert page.locator('#guide-actions li').count() == 47
    for phrase in ['Companion food, hunger and evolution', '100 community projects', '8,778', '20 additional side quests', 'not connected multiplayer']:
        assert phrase in page.locator('#page-screen').text_content(), phrase
    assert 'DAMAR' not in page.locator('#page-screen').text_content()
    assert 'SAMAR' not in page.locator('#page-screen').text_content()
    page.locator('[data-play]').click()
    page.get_by_role('button', name='Begin adventure').click()
    page.wait_for_function("packet?.prompt === 'Village > ' && !busy")

    def send(text):
        page.wait_for_function('packet.waiting && !busy')
        previous = page.evaluate('packet.prompt_id')
        page.evaluate('async text=>{await respond(text);}', text)
        page.wait_for_function('previous=>packet.prompt_id>previous && !busy', arg=previous)

    assert page.locator('.story-panel #prompt').inner_text().strip() == 'Village >'
    assert page.locator('.command-dock #prompt').count() == 0
    assert page.locator('#prompt').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)') >= 15
    prompt_box = page.locator('#prompt').bounding_box()
    input_box = page.locator('#command').bounding_box()
    assert prompt_box['y'] + prompt_box['height'] <= input_box['y']
    send('7'); send('DAMAR')
    page.locator('[data-group="inventory"]').click()
    page.wait_for_function("packet.snapshot.group === 'inventory' && !busy")
    send('samar')
    assert page.evaluate('packet.snapshot.player.beta_mode') is False
    assert page.evaluate('packet.snapshot.group') == 'inventory'
    save = page.evaluate('safeSave()')
    companion = deepcopy(data.COMPANIONS['Ashen Wastes'][0])
    companion.update(stage=0, xp=2, hunger=20, home_region='Ashen Wastes')
    food = next(f for f in data.FOOD_ITEMS if f['name'] == 'Ember Bread')
    save['player']['companions'] = [companion]
    save['player']['inventory'] = [deepcopy(food) for _ in range(4)]
    page.evaluate('async save=>{await start({save});}', save)
    page.wait_for_function("packet.snapshot.phase === 'main' && !busy")
    page.locator('[data-group="character"]').click()
    page.wait_for_function("packet.snapshot.group === 'character' && !busy")
    send('5')
    assert page.evaluate('packet.prompt') == 'Companions > '
    assert 'Ember Bread' in page.locator('#terminal').inner_text()
    send('1'); send('1'); send('1')
    assert page.evaluate('packet.snapshot.player.companions[0].stage') == 1
    assert page.evaluate('packet.snapshot.player.companions[0].form_name') == 'Awakened Ember Fox'
    assert page.evaluate('packet.snapshot.player.companions[0].hunger') == 20 + food['hunger']
    assert page.evaluate('packet.snapshot.player.inventory.length') == 3
    assert f"Hunger {20 + food['hunger']}/100" in page.locator('#status-sidebar').inner_text()
    send('0')
    save = page.evaluate('safeSave()')
    save['player']['companions'][0]['xp'] = 5
    save['player']['companions'][0]['hunger'] = 20
    page.evaluate('async save=>{await start({save});}', save)
    page.wait_for_function("packet.snapshot.phase === 'main' && !busy")
    page.locator('[data-group="character"]').click()
    page.wait_for_function("packet.snapshot.group === 'character' && !busy")
    send('5'); send('1'); send('1'); send('1')
    assert page.evaluate('packet.snapshot.player.companions[0].form_name') == 'Sunfire Ember Fox'
    assert 'Sunfire Ember Fox' in page.locator('#status-sidebar').inner_text()
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.locator('#prompt').is_visible()
    Path('/tmp/soules-checks').mkdir(exist_ok=True)
    page.screenshot(path='/tmp/soules-checks/companion-care-mobile.png', full_page=True)
    assert not errors, errors
    print('PASS: large question in story area, comprehensive 47-action tutorial, mode off in category, regional feeding, named evolutions, finite food, sidebar and mobile')
    browser.close()
