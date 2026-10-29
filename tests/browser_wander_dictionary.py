"""Sidebar reader position survives live updates; all exploration references render."""

from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")

    def send(text):
        page.wait_for_function("packet.waiting&&!busy")
        previous = page.evaluate("packet.prompt_id")
        page.evaluate("async text=>await respond(packet.prompt==='Village > '&&/^[1-6]$/.test(text)?'v:'+text:text)", text)
        page.wait_for_function(
            "previous=>packet.prompt_id>previous&&!busy", arg=previous
        )

    sidebar = page.locator("#status-sidebar")
    assert sidebar.evaluate("x=>getComputedStyle(x).overflowY") == "auto"
    assert sidebar.evaluate("x=>x.scrollHeight>x.clientHeight")
    for position in (350, 650, 0):
        sidebar.evaluate("(x,top)=>x.scrollTop=top", position)
        before = sidebar.evaluate("x=>x.scrollTop")
        send("21")
        page.wait_for_timeout(700)
        assert abs(sidebar.evaluate("x=>x.scrollTop") - before) < 1, (
            position,
            before,
            sidebar.evaluate("x=>x.scrollTop"),
        )
    send("/difficulty easy")
    page.locator('.topbar [data-view="home"]').first.click()
    page.locator('[data-view="dictionary"]').click()
    page.locator('[data-dictionary="wandering"]').click()
    assert "Your next wander" in page.locator(".cards").inner_text()
    assert "EASY" in page.locator(".cards article").first.inner_text()
    assert "Ordinary monster: 35.28%" in page.locator(".cards article").first.inner_text()
    assert "51%" in page.locator(".cards").inner_text()
    assert "36%" in page.locator(".cards").inner_text()
    assert "combat 57.00%, structures/clans 21.00%" in page.locator(".cards article").first.inner_text()
    assert "keep the item, then 70% monster / 30%" in page.locator(".cards article").first.inner_text()
    assert "One weighted main roll" in page.locator(".cards").inner_text()
    page.locator("#dictionary-search").fill("cursed chest")
    assert "1/3" in page.locator(".cards").inner_text()
    page.locator('[data-dictionary="weather"]').click()
    assert page.locator(".cards article").count() == 6
    assert "Void Storm" in page.locator(".cards").inner_text()
    assert "3.3333%" in page.locator(".cards").inner_text()
    page.locator('[data-dictionary="world"]').click()
    assert page.locator(".cards article").count() == 8
    assert "Blood Moon" in page.locator(".cards").inner_text()
    page.locator('[data-dictionary="loot"]').click()
    assert "Ancient ruins" in page.locator(".cards").inner_text()
    assert "Sea Pearls" in page.locator(".cards").inner_text()
    page.set_viewport_size({"width": 390, "height": 844})
    page.locator('[data-dictionary="wandering"]').click()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    print(
        "PASS: sidebar stays at manual positions after live/poll updates, scrollbar retained, wander odds, event search, six weather types, eight world events, loot/ruins and mobile"
    )
    browser.close()
