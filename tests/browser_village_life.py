"""Local village services, notes, stock, travel and sidebar end to end."""

from playwright.sync_api import sync_playwright
from pathlib import Path

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt === 'Village > ' && !busy")
    assert page.evaluate("packet.snapshot.village.name") == "Old Village"
    page.evaluate("async()=>{await respond('7');}")
    page.wait_for_function("packet?.snapshot?.phase === 'main'")

    def send(text):
        page.wait_for_function("packet.waiting && !busy")
        previous = page.evaluate("packet.prompt_id")
        page.evaluate(
            "async text=>{await respond(packet.prompt==='Village > '&&/^[1-6]$/.test(text)?'v:'+text:text);}",
            text,
        )
        page.wait_for_function("previous=>packet.prompt_id>previous", arg=previous)

    send("DAMAR")
    page.locator("[data-village-directory]").click()
    page.wait_for_function("packet.prompt === 'Directory > '")
    send("1")
    page.wait_for_function(
        "packet.prompt === 'Village > ' && packet.snapshot.village?.name === 'Old Village'"
    )
    assert "forge" not in page.evaluate("packet.snapshot.village.services")
    assert "temple" not in page.evaluate("packet.snapshot.village.services")
    assert "Lv. 2" in page.locator(".village-card").inner_text()
    assert page.evaluate("packet.snapshot.village.quality.farm") == 3
    page.locator('.village-card [data-response="note"]').click()
    page.wait_for_function("packet.prompt.includes('Village note')")
    send("cheap food <farm>")
    assert page.locator(".village-card blockquote").inner_text() == "cheap food <farm>"
    page.locator('.village-card [data-response="tags"]').click()
    send("cheap food,farming")
    assert "farming" in page.locator(".village-card .effect-chips").inner_text()
    before = page.evaluate("packet.snapshot.player.ingredients.length")
    send("10")
    assert page.evaluate("packet.snapshot.player.ingredients.length") == before + 5
    assert "Farm regrowing" in page.locator(".village-card").inner_text()
    send("10")
    assert page.evaluate("packet.snapshot.player.ingredients.length") == before + 5
    send("8")
    page.wait_for_function("packet.prompt === 'Workstation > '")
    assert "forge" not in page.evaluate("packet.snapshot.village.services")
    send("0")
    send("7")
    page.wait_for_function("packet.prompt === 'Directory > '")
    send("f")
    send("cheap food")
    send("1")
    page.wait_for_function("packet.prompt === 'Village > '")
    send("7")
    send("0")
    page.wait_for_function("packet.snapshot.phase === 'category'")
    page.evaluate(
        'async()=>{const save=safeSave();save.player.building_materials={Timber:20,Stone:20,"Iron fittings":20};save.player.gold=500;await start({save});}'
    )
    page.wait_for_function("packet.snapshot.phase === 'main'")
    assert (
        page.evaluate(
            "packet.snapshot.player.saved_villages['Whispering Woods::Old Village'].note"
        )
        == "cheap food <farm>"
    )
    page.locator("[data-village-directory]").click()
    page.wait_for_function("packet.prompt === 'Directory > '")
    send("1")
    page.wait_for_function("packet.prompt === 'Village > '")
    assert page.evaluate("packet.snapshot.village.farm_ready") is False
    send("17")
    page.wait_for_function("packet.prompt === 'Building > '")
    send("1")
    send("y")
    send("0")
    assert page.evaluate("packet.snapshot.village.levels.restaurant") == 3
    assert page.evaluate("packet.snapshot.player.gold") == 400
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    Path("/tmp/soules-checks").mkdir(exist_ok=True)
    page.screenshot(path="/tmp/soules-checks/village-life-mobile.png", full_page=True)
    assert not errors, errors
    print(
        "PASS: village services/quality, sidebar, notes/tags, farm limits, directory search/revisit, reload persistence, mobile"
    )
    browser.close()
