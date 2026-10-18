"""Real browser flows for worker escrow, addons, rewards and interface controls."""

from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(
        viewport={"width": 1440, "height": 1050}, accept_downloads=True
    )
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on(
        "dialog",
        lambda d: (
            d.accept("Expansion checkpoint") if d.type == "prompt" else d.accept()
        ),
    )
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator('[data-view="dictionary"]').click()
    assert page.locator(".rune-seal").count() == 132
    seals = page.locator(".rune-seal").evaluate_all("(xs)=>xs.map(x=>x.innerHTML)")
    assert len(set(seals)) == 132
    page.locator('[data-dictionary="potions"]').click()
    page.locator("#dictionary-search").fill("Forest Salve")
    assert "Thorn Petal" in page.locator(".cards").inner_text()
    assert "Dew Blossom" in page.locator(".cards").inner_text()
    page.locator('[data-view="customise"]').first.click()
    page.locator('[data-key-binding="focus"]').fill("f")
    page.locator('[data-key-binding="focus"]').press("Tab")
    page.locator("#reader-combat").check()
    page.locator("#rune-volume").fill("12")
    page.locator("#rune-volume").dispatch_event("change")
    assert page.evaluate("preferences.bindings.focus") == "f"
    assert page.evaluate("preferences.readerCombat") is True
    assert page.evaluate("preferences.runeVolume") == 12
    page.locator("#play").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")

    def send(text):
        page.wait_for_function("packet?.waiting&&!busy")
        previous = page.evaluate("packet.prompt_id")
        page.evaluate("async text=>{await respond(text)}", str(text))
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=previous)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    # Give this test character carried ingredients without using the hidden grant command.
    send("7")
    save = page.evaluate("safeSave()")
    save["player"]["gold"] = 1000
    save["player"]["ingredients"] = ["Thorn Petal", "Dew Blossom", "Thorn Petal"]
    save["player"]["discovered_structures"] = {"Whispering Woods": ["Old Village"]}
    page.evaluate("async save=>await start({save})", save)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator('[data-group="explore"]').click()
    page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
    # Use discovered-village directory and return to Old Village.
    index = page.evaluate(
        "catalog.groups.find(x=>x.id==='explore').options.findIndex(x=>x[0]===47)+1"
    )
    send(index)
    send("1")
    assert page.evaluate("packet.prompt") == "Village > "
    send("22")
    send("4")
    send("1")
    send("2")
    send("y")
    assert "Workers >" in page.locator("#prompt").inner_text()
    jobs = page.evaluate(
        "Object.values(packet.snapshot.player.village_records).flatMap(x=>x.work_orders||[])"
    )
    assert len(jobs) == 1 and jobs[0]["kind"] == "potion"
    shifts = jobs[0]["remaining"]
    for _ in range(shifts):
        send("7")
    send("6")
    send("1")
    assert page.evaluate("packet.snapshot.player.potions.includes('Forest Salve')")
    send("0")
    send("7")
    send("0")  # Return from the enclosing Village Directory.
    page.locator('[data-group="character"]').click()
    page.wait_for_function("packet.snapshot.group==='character'&&!busy")
    index = page.evaluate(
        "catalog.groups.find(x=>x.id==='character').options.findIndex(x=>x[0]===42)+1"
    )
    send(index)
    send("y")
    assert page.evaluate("packet.snapshot.player.expansion.daily.total_claims") == 1
    send(index)
    send("y")
    assert page.evaluate("packet.snapshot.player.expansion.daily.total_claims") == 1
    page.locator('[data-group="world"]').click()
    page.wait_for_function("packet.snapshot.group==='world'&&!busy")
    send("8")
    send("4")
    send("1")
    assert any(
        "Fish" in x["name"] for x in page.evaluate("packet.snapshot.player.inventory")
    )
    send("0")
    page.locator('[data-slot-action="save"]').first.click()
    page.wait_for_function(
        "JSON.parse(localStorage.getItem('soules-save-timeline'))?.length===1"
    )
    page.locator('.topbar [data-view="home"]').first.click()
    page.locator('[data-view="saves"]').first.click()
    page.wait_for_selector('[data-timeline-load="0"]')
    with page.expect_download() as download:
        page.locator("[data-sheet-export]").click()
    assert download.value.suggested_filename == "soules-character-sheet.txt"
    assert "SOULES" in Path(download.value.path()).read_text()
    page.locator('[data-timeline-load="0"]').click()
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    assert page.evaluate("packet.snapshot.player.expansion.daily.total_claims") == 1
    assert page.evaluate("packet.snapshot.player.potions.includes('Forest Salve')")
    # Trigger a tactical practice fight through the actual addon menu, then withdraw.
    page.locator('[data-group="world"]').click()
    page.wait_for_function("packet.snapshot.group==='world'&&!busy")
    send("8")
    send("5")
    send("3")
    assert "health" in page.locator("#combat-announcer").text_content()
    assert page.locator("#terminal").get_attribute("aria-live") == "off"
    send("0")
    send("0")
    page.locator("body").click(position={"x": 800, "y": 110})
    page.keyboard.press("f")
    assert page.locator("#command").evaluate("x=>x===document.activeElement")
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    Path("/tmp/soules-checks").mkdir(exist_ok=True)
    page.screenshot(path="/tmp/soules-checks/expansion-mobile.png", full_page=True)
    assert not errors, errors
    print(
        "PASS: potion dictionary, 132 unique seals, remapping, sound, reader combat, worker order/shift/collection, daily once, fishing, timeline restore, character export, mobile"
    )
    browser.close()
