"""New village arrival, actual project benefits and independent finite wares."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1050})
    errors = []
    page.on('pageerror', lambda err: errors.append(str(err)))
    page.goto('http://127.0.0.1:5000')
    page.locator('[data-play]').click()
    page.get_by_role('button', name='Begin adventure').click()
    page.wait_for_function("packet?.prompt === 'Village > ' && !busy")

    def send(text):
        page.wait_for_function('packet.waiting && !busy')
        previous = page.evaluate('packet.prompt_id')
        page.evaluate('async text=>{await respond(text);}', text)
        page.wait_for_function('previous=>packet.prompt_id>previous && !busy', arg=previous)

    assert page.evaluate('packet.snapshot.village.name') == 'Old Village'
    assert 'Elian welcomes you' in page.locator('#terminal').inner_text()
    assert page.locator('.village-card').get_by_role('button', name='Edit note').count() == 1
    assert 'next resident improvement' in page.locator('.village-card').inner_text()
    send('18')
    assert page.evaluate('packet.prompt') == 'Mentor > '
    send('1')
    assert page.evaluate('packet.prompt') == 'Village > '
    send('7')
    page.evaluate('''async()=>{
      const save=safeSave();save.player.gold=10000;
      save.player.building_materials={Timber:100,Stone:100,"Iron fittings":100};
      save.player.village_records['Whispering Woods::Old Village'].next_development=2;
      await start({save});
    }''')
    page.wait_for_function("packet.snapshot.phase === 'main' && !busy")
    page.locator('[data-village-directory]').click()
    page.wait_for_function("packet.prompt === 'Directory > ' && !busy")
    send('1')
    assert page.evaluate('packet.snapshot.village.levels') != {'restaurant':2,'inn':1,'farm':2,'alchemy':2,'loom':1,'trade':1}
    assert 'Village development!' in page.locator('#terminal').inner_text()
    send('19')
    page.wait_for_function("packet.prompt === 'Material number (0 back) > '")
    before = page.evaluate('packet.snapshot.village.wares[0].left')
    send('1')
    assert page.evaluate('packet.snapshot.village.wares[0].left') == before-1
    page.locator('.village-card').get_by_role('button', name='Build projects').click()
    page.wait_for_function("packet.prompt === 'Project > ' && !busy")
    send('1'); send('y')
    assert len(page.evaluate("packet.snapshot.player.village_records['Whispering Woods::Old Village'].projects")) == 1
    assert page.evaluate('packet.snapshot.village.reputation') == 1
    assert 'BUILT' in page.locator('#terminal').inner_text()
    send('0')
    assert page.evaluate('packet.prompt') == 'Village > '
    send('7'); send('0')
    page.wait_for_function("packet.snapshot.phase === 'category'")
    saved = page.evaluate('safeSave()')
    page.evaluate('async save=>{await start({save});}', saved)
    page.wait_for_function("packet.snapshot.phase === 'main' && !busy")
    assert page.evaluate("packet.snapshot.player.village_records['Whispering Woods::Old Village'].visits") == 2
    assert len(page.evaluate("packet.snapshot.player.village_records['Whispering Woods::Old Village'].projects")) == 1
    assert not errors, errors
    print('PASS: real village spawn/mentor, random local development, finite metal stock, building project, saved progression')
    browser.close()
