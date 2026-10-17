"""Opening canon, starting balance and the journal are visible in the browser."""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt === 'Village > ' && !busy")
    assert page.evaluate("packet.snapshot.village.name") == "Old Village"
    page.evaluate("async()=>{await respond('7');}")
    page.wait_for_function("packet?.snapshot?.phase === 'main'")
    text = page.locator("#terminal").inner_text()
    for phrase in [
        "Riftlands separated",
        "Sacred Temple",
        "gave their lives",
        "rift has opened again",
    ]:
        assert phrase in text, phrase
    assert page.evaluate("packet.snapshot.player.hp") == 70
    assert page.evaluate("packet.snapshot.player.atk") == 7
    page.locator("[data-story-journal]").click()
    page.wait_for_function("packet.prompt === 'Journal > '")
    assert "Survive your first encounter" in page.locator("#terminal").inner_text()
    assert "4. Investigate the Source Temple" not in page.locator("#terminal").inner_text()
    page.evaluate("async()=>{await respond('2');}")
    page.wait_for_function(
        "document.querySelector('#terminal').textContent.includes('Smithing: rank 1/5')"
    )
    assert not errors, errors
    print(
        "PASS: canonical opening, weaker starting character, sidebar journal, professions, Chapter Two gating"
    )
    browser.close()
