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
    page.wait_for_selector('#action-buttons [data-response="4"]')
    page.locator('#action-buttons [data-response="4"]').click()
    page.wait_for_function("packet.snapshot.phase === 'action' && packet.waiting")
    page.locator("#back").click()
    page.wait_for_selector('#action-buttons [data-response="4"]:enabled')
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
    page.wait_for_selector('#new-dialog[open]')
    assert page.evaluate("localStorage.getItem('soules-original-autosave')") is None
    page.locator('input[name="name"]').fill('New Soul')
    page.get_by_role('button', name='Begin adventure').click()
    page.wait_for_function("packet.snapshot?.player?.name === 'New Soul' && packet.snapshot.phase === 'main'")
    assert page.evaluate('packet.snapshot.player.runes.length') == 0
    assert page.evaluate('packet.snapshot.player.weapons.length') == 1
    assert page.evaluate("JSON.parse(localStorage.getItem('soules-original-slots'))[0].save.player.name") == 'Sable'
    assert not errors, errors
    print("Original UI: start, hidden code, groups, submenus, save slots, themes, mobile passed")
    browser.close()
