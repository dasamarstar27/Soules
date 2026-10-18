"""Easy selection, safe live changes, rejected mid-purchase changes and portable saves."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1280, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("#easy-reading").click()
    page.locator("[data-play]").click()
    assert page.locator("#difficulty-choice option").count() == 2
    assert page.locator("#difficulty-choice").input_value() == "normal"
    page.locator("#difficulty-choice").select_option("easy")
    page.locator('[data-character-name="Nanu"]').click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")
    assert page.evaluate("packet.snapshot.player.difficulty") == "easy"
    assert "Easy" in page.locator("#status-sidebar .identity").inner_text()
    assert page.evaluate("packet.snapshot.player.weapons.length") == 1
    assert page.evaluate("packet.snapshot.player.runes.length") == 0

    def choose(value):
        old = page.evaluate("packet.prompt_id")
        page.locator('#comfort-choices [data-response="' + str(value) + '"]').click()
        page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
        assert not page.evaluate("packet.error")

    def setting(value):
        page.locator('.topbar [data-view="customise"]').click()
        page.locator('[data-difficulty="' + value + '"]').click()
        page.wait_for_function(
            "value=>packet.snapshot.player.difficulty===value&&!busy", arg=value
        )
        page.locator("#play").click()

    setting("normal")
    assert page.evaluate("preferences.comfort") is True
    setting("easy")
    choose(1)
    assert page.evaluate("packet.prompt") == "Food number (0 cancel) > "
    page.locator('.topbar [data-view="customise"]').click()
    assert page.locator('[data-difficulty="normal"]').is_disabled()
    page.evaluate("async()=>await respond('/difficulty normal')")
    assert page.evaluate("packet.snapshot.player.difficulty") == "easy"
    assert page.evaluate("packet.prompt") == "Food number (0 cancel) > "
    assert "outside combat and purchases" in page.locator("#terminal").text_content()
    page.locator("#play").click()
    choose(0)
    choose(7)
    page.locator('[data-slot-action="save"]').first.click()
    save = page.evaluate("JSON.parse(localStorage.getItem(SLOTS))[0].save")
    assert save["player"]["difficulty"] == "easy"
    save["player"].pop("difficulty")
    page.evaluate("async save=>await start({save})", save)
    page.wait_for_function("packet?.snapshot.phase==='main'&&!busy")
    assert page.evaluate("packet.snapshot.player.difficulty") == "normal"
    assert not errors, errors
    browser.close()
print(
    "PASS: two difficulty choices, Easy creation, unchanged supplies, sidebar, safe Settings switch, purchase protection, exported difficulty and old-save Normal default"
)
