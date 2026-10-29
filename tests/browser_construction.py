"""Build and upgrade a missing forge through tablet controls; sidebar and revisit."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1280, "height": 1000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("#tablet-mode").click()
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")

    def send(value, button=False):
        old = page.evaluate("packet.prompt_id")
        if button:
            page.locator(
                '#comfort-choices [data-response="' + str(value) + '"]'
            ).click()
        else:
            page.evaluate(
                "async value=>await respond(packet.prompt==='Village > '&&/^[1-6]$/.test(value)?'v:'+value:value)",
                str(value),
            )
        page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    send(7)
    save = page.evaluate("safeSave()")
    save["player"].update(
        gold=1000, building_materials={"Timber": 30, "Stone": 30, "Iron fittings": 30}
    )
    page.evaluate("async save=>await start({save})", save)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator("[data-village-directory]").click()
    page.wait_for_function("packet.prompt==='Directory > '&&!busy")
    send(1)
    assert "forge" not in page.evaluate("packet.snapshot.village.services")
    send(3, True)
    send(1, True)
    assert "NOT BUILT" in page.locator("#terminal").inner_text()
    # Existing six services stay first; the new forge is option seven.
    send(7, True)
    assert "(y/n)" in page.evaluate("packet.prompt")
    send("y", True)
    assert page.evaluate("packet.snapshot.player.gold") == 900
    assert "forge" in page.evaluate("packet.snapshot.village.services")
    send(7, True)
    send("y", True)
    assert page.evaluate("packet.snapshot.village.levels.forge") == 2
    assert page.evaluate("packet.snapshot.player.gold") == 850
    send(0, True)
    assert "Blacksmith" in page.locator("#terminal").inner_text()
    assert "Forge" in page.locator("#status-sidebar").inner_text()
    send(8)
    assert "Forge weapons" in page.locator("#terminal").inner_text()
    send(0)
    send(0, True)
    send(7)
    # A village opened from the Directory returns there; leave it to checkpoint.
    page.wait_for_function("packet.prompt==='Directory > '&&!busy")
    send(0)
    page.wait_for_function("['main','category'].includes(packet.snapshot.phase)&&!busy")
    stored = page.evaluate("safeSave()")
    page.evaluate("async save=>await start({save})", stored)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator("[data-village-directory]").click()
    page.wait_for_function("packet.prompt==='Directory > '&&!busy")
    send(1)
    assert page.evaluate("packet.snapshot.village.levels.forge") == 2
    assert "forge" in page.evaluate("packet.snapshot.village.services")
    assert not errors, errors
    browser.close()
print(
    "PASS: tablet construction/confirmation, exact costs, Level 2 upgrade, live menu/sidebar/bench and save revisit"
)
