"""Default text edition: startup, input, grouping, slots, themes and mobile."""

from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    page.on(
        "dialog",
        lambda dialog: dialog.accept("Sable slot") if dialog.type == "prompt" else dialog.accept(),
    )
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    assert "DAMAR" not in page.locator("body").inner_text()
    assert page.locator(".home-options button").count() == 4
    page.locator("[data-play]").click()
    page.wait_for_selector("dialog[open]")
    page.locator('input[name="name"]').fill("Sable")
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt === 'Village > ' && !busy")
    assert page.evaluate("packet.snapshot.village.name") == "Old Village"
    page.evaluate("async()=>{await respond('7');}")
    page.wait_for_selector('#action-buttons [data-response="1"]')
    assert "Rusty Sword" in page.locator("#status-sidebar").inner_text()
    assert page.locator("#categories button").count() == 7
    page.locator("#command").fill("DAMAR")
    page.locator("#command-form").press("Enter")
    page.wait_for_function(
        "JSON.parse(localStorage.getItem('soules-original-autosave')).player.beta_mode === true"
    )
    assert (
        page.evaluate(
            "JSON.parse(localStorage.getItem('soules-original-autosave')).player.runes.length"
        )
        == 132
    )
    page.locator('[data-group="inventory"]').click()
    page.wait_for_selector('#action-buttons [data-response="1"]')
    page.locator('#action-buttons [data-response="1"]').click()
    page.wait_for_function("packet.snapshot.phase === 'action' && packet.waiting")
    page.locator("#back").click()
    page.wait_for_selector('#action-buttons [data-response="1"]:enabled')
    page.locator('[data-slot-action="save"]').first.click()
    page.wait_for_function(
        "JSON.parse(localStorage.getItem('soules-original-slots'))?.[0]?.save.player.name==='Sable'"
    )
    page.locator('[data-view="customise"]').first.click()
    page.locator('[data-preset="ember"]').click()
    assert page.evaluate("document.documentElement.dataset.themeMode") == "fixed"
    page.locator("#reset-theme").click()
    assert page.evaluate("document.documentElement.dataset.themeMode") == "auto"
    page.locator("#play").click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    Path("/tmp/soules-checks").mkdir(exist_ok=True)
    page.screenshot(path="/tmp/soules-checks/original-mobile.png", full_page=True)
    await_death = """async () => {
        const save = JSON.parse(localStorage.getItem('soules-original-autosave'));
        save.player.hp = 0;
        await start({save});
    }"""
    page.evaluate(await_death)
    page.wait_for_selector("#new-dialog[open]")
    assert page.evaluate("localStorage.getItem('soules-original-autosave')") is None
    page.locator('input[name="name"]').fill("New Soul")
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt === 'Village > ' && !busy")
    assert page.evaluate("packet.snapshot.village.name") == "Old Village"
    page.evaluate("async()=>{await respond('7');}")
    page.wait_for_function(
        "packet.snapshot?.player?.name === 'New Soul' && packet.snapshot.phase === 'main'"
    )
    assert page.evaluate("packet.snapshot.player.runes.length") == 0
    assert page.evaluate("packet.snapshot.player.weapons.length") == 1
    assert (
        page.evaluate(
            "JSON.parse(localStorage.getItem('soules-original-slots'))[0].save.player.name"
        )
        == "Sable"
    )
    page.locator('[data-group="inventory"]').click()
    page.wait_for_selector('#action-buttons [data-response="3"]:enabled')
    page.locator('#action-buttons [data-response="3"]').click()
    page.wait_for_function("packet.prompt.includes('Inventory option')")
    page.evaluate("async () => { await respond('4'); await respond('2'); await respond('6'); }")
    page.wait_for_function(
        "packet.snapshot.player.inventory_sort === 'element' && packet.snapshot.player.auto_sell_duplicates === true"
    )
    assert page.evaluate("packet.snapshot.player.inventory_sort_secondary") == "atk"
    page.evaluate("async () => { await respond('0'); }")
    page.wait_for_function("packet.snapshot.phase === 'category'")
    page.locator("#terminal").focus()
    page.keyboard.press("/")
    assert page.locator("#command").evaluate("(e)=>e===document.activeElement")
    page.keyboard.press("ArrowUp")
    assert page.locator("#command").input_value() == "0"
    page.keyboard.press("ArrowDown")
    assert page.locator("#command").input_value() == ""
    page.locator("#recall-command").click()
    assert page.locator("#command").input_value() == "0"
    page.keyboard.press("Escape")
    page.wait_for_function("packet.snapshot.phase === 'main'")
    page.evaluate(
        "()=>{for(let i=0;i<30;i++)append('Scroll position check '+i);document.querySelector('#terminal').scrollTop=100;}"
    )
    scroll_before = page.locator("#terminal").evaluate("e=>e.scrollTop")
    page.evaluate("async()=>{await respond('1');}")
    page.wait_for_function("packet.snapshot.phase === 'category' && !busy")
    # Choosing a new short menu resumes following; passive history stays covered
    # by browser_journal_scroll.py and browser_embedded_scroll.py.
    assert page.locator("#terminal").evaluate("e=>e.scrollTop") > scroll_before
    assert page.locator("#terminal").evaluate("e=>e.scrollHeight-e.scrollTop-e.clientHeight<3")
    page.evaluate("async()=>{await respond('0');}")
    page.wait_for_function("packet.snapshot.phase === 'main' && !busy")
    page.locator("#compact-status").click()
    assert page.locator("body").evaluate("e=>e.classList.contains('compact-sidebar')")
    assert page.evaluate("JSON.parse(localStorage.getItem('soules-appearance')).compact")
    page.evaluate(
        "Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedJournal=text;}}})"
    )
    page.locator("#copy-journal").click()
    page.wait_for_function("window.copiedJournal?.includes('MAIN MENU')")
    page.locator("#latest-output").click()
    page.wait_for_function(
        "(()=>{const e=document.querySelector('#terminal');return e.scrollHeight-e.scrollTop-e.clientHeight<5;})()"
    )
    page.locator("#clear-journal").click()
    assert page.locator("#terminal p").count() == 0
    page.evaluate("async()=>{const save=safeSave();save.player.hp=1;await start({save});}")
    page.wait_for_function(
        "document.querySelector('#health-warning').textContent.includes('LOW HEALTH')"
    )
    assert not errors, errors
    print("Original UI: start, hidden code, groups, submenus, save slots, themes, mobile passed")
    browser.close()
