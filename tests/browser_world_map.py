"""World/local maps, discovered markers, ordinary travel and real structure visit."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:5000")
    page.locator('.topbar [data-view="map"]').click()
    page.wait_for_selector(".world-map [data-map-region]")
    assert page.locator(".world-map [data-map-region]").count() == 16
    assert page.locator("[data-map-travel]").is_disabled()
    page.locator("#play").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")
    page.evaluate("async()=>await respond('7')")
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    saved = page.evaluate("safeSave()")
    saved["player"]["unlocked_regions"] = ["Whispering Woods", "Ashen Wastes"]
    saved["player"]["discovered_structures"]["Whispering Woods"] = [
        "Old Village",
        "Whispering Woods Quarry",
    ]
    page.evaluate("async save=>await start({save})", saved)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator('.topbar [data-view="map"]').click()
    assert page.locator(".local-map [data-map-site]").count() == 2
    assert "Sylvar Circle" not in page.locator("#page-screen").inner_text()
    page.locator('[data-map-region="Crimson Depths"]').click()
    assert page.locator("[data-map-travel]").is_disabled()
    page.locator('[data-map-region="Ashen Wastes"]').click()
    page.locator("[data-map-travel]").click()
    page.wait_for_function("packet.snapshot.player.region==='Ashen Wastes'&&!busy")
    page.locator('.topbar [data-view="map"]').click()
    page.locator('[data-map-region="Whispering Woods"]').click()
    page.locator('.local-map [data-map-site="0"]').click()
    page.wait_for_function("packet.prompt==='Village > '&&!busy")
    assert page.evaluate("packet.snapshot.village.name") == "Old Village"
    page.locator('.topbar [data-view="map"]').click()
    assert page.locator('button[data-map-site="0"]').is_disabled()
    for width in (820, 390):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    browser.close()
print(
    "PASS: graphical routes, local markers, hidden discoveries, lock checks, travel, real village visit, pending-menu safety and mobile"
)
