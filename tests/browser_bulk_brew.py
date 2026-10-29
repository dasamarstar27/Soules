"""Actual tablet batch brewing and restored automatic region/village colours."""

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
    assert (
        page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()"
        )
        == "#101b16"
    )
    async_code = "async value=>await respond(value)"

    def send(value):
        old = page.evaluate("packet.prompt_id")
        page.evaluate(async_code, str(value))
        page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    def answer(value):
        old = page.evaluate("packet.prompt_id")
        page.locator('#comfort-choices [data-response="' + str(value) + '"]').click()
        page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)

    send(7)
    saved = page.evaluate("safeSave()")
    saved["player"]["ingredients"] = ["Dew Blossom"] * 4 + ["Thorn Petal"] * 4
    page.evaluate("async save=>await start({save})", saved)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator("[data-village-directory]").click()
    page.wait_for_function("packet.prompt==='Directory > '&&!busy")
    send(1)
    answer(2)
    page.locator("#comfort-choices").get_by_role(
        "button", name="Brew potions", exact=True
    ).click()
    page.wait_for_function("packet.prompt.includes('First ingredient')&&!busy")
    answer("B")
    answer(0)
    answer(1)
    assert page.locator(".quantity-controls").is_visible()
    page.locator('[data-quantity="5"]').click()
    assert page.locator(".quantity-controls output").inner_text() == "4"
    page.locator('[data-quantity="-1"]').click()
    answer(3)
    answer("y")
    assert page.evaluate("packet.snapshot.player.potions") == ["Forest Salve"] * 3
    assert (
        page.evaluate(
            "packet.snapshot.player.ingredients.filter(x=>x==='Dew Blossom').length"
        )
        == 1
    )
    assert "BREW COMPLETE · 3 Forest Salve" in page.locator("#terminal").inner_text()
    assert page.evaluate("packet.prompt") == "Village [Shops & crafting] > "
    assert (
        page.locator("#status-sidebar>.side-card").first.locator("h2").inner_text()
        == "CHARACTER"
    )
    # Automatic palettes follow scene changes, while custom choices still win.
    page.evaluate(
        "()=>{packet.snapshot.player.region='Ashen Wastes';packet.snapshot.location=null;theme()}"
    )
    assert (
        page.evaluate("document.documentElement.style.getPropertyValue('--bg')")
        == "#201b13"
    )
    page.evaluate(
        "()=>{preferences.mode='custom';preferences.bg='#111122';preferences.accent='#ddddff';theme()}"
    )
    assert (
        page.evaluate("document.documentElement.style.getPropertyValue('--bg')")
        == "#111122"
    )
    assert not errors, errors
    browser.close()
print(
    "PASS: tablet bulk entry, finite quantity clamp, confirmation, three bottled potions, feedback, submenu return, character-first sidebar and restored Woods/Ashen/custom colours"
)
