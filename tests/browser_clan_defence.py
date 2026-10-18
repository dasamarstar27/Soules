"""Clan history/shop stays open, Structures revisits, raids and the Woods quest."""

from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
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
        page.evaluate("async text=>await respond(text)", str(text))
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=previous)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    def group(name):
        page.locator(f'[data-group="{name}"]').click()
        page.wait_for_function("name=>packet.snapshot.group===name&&!busy", arg=name)

    send("7")
    save = page.evaluate("safeSave()")
    save["player"]["gold"] = 1000
    save["player"]["building_materials"] = {
        "Timber": 10,
        "Stone": 10,
        "Iron fittings": 0,
    }
    save["player"]["discovered_structures"]["Whispering Woods"].append("Sylvar Circle")
    page.evaluate("async save=>await start({save})", save)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    group("explore")
    structures = page.evaluate(
        "catalog.groups.find(x=>x.id==='explore').options.findIndex(x=>x[0]===17)+1"
    )
    send(structures)
    send("1")
    assert page.evaluate("packet.prompt") == "Elemental village > "
    page.locator("#status-sidebar").evaluate("x=>x.scrollTop=300")
    send("5")
    assert page.evaluate("packet.prompt") == "Elemental village > "
    assert page.evaluate("packet.snapshot.village.name") == "Sylvar Circle"
    assert "Miren of Sylvar" in page.locator("#terminal").inner_text()
    assert abs(page.locator("#status-sidebar").evaluate("x=>x.scrollTop") - 300) < 1
    send("3")
    send("1")
    send("0")
    assert page.evaluate("packet.prompt") == "Elemental village > "
    assert page.evaluate("packet.snapshot.player.gold") == 975
    assert page.evaluate("packet.snapshot.player.inventory.length") == 1
    # Explicit raid defence opens worker assignments and lets the player withdraw.
    send("7")
    send("1")
    send("1")
    send("1")
    assert page.evaluate("packet.prompt") == "Tactical action > "
    send("0")
    assert page.evaluate("packet.prompt") == "Elemental village > "
    send("8")
    send("2")
    send("3")
    send("1")
    send("1")
    assert (
        page.evaluate(
            "packet.snapshot.player.expansion.activities.woods_defence.assignments['Whispering Woods']"
        )
        == "Defend the barricades"
    )
    for wave in range(3):
        send("4")
        turns = 0
        while page.evaluate("packet.prompt") == "Tactical action > ":
            send("1")
            turns += 1
            assert turns < 15
        assert (
            page.evaluate(
                "packet.snapshot.player.expansion.activities.woods_defence.waves"
            )
            == wave + 1
        )
    send("0")
    send("4")
    assert page.evaluate("packet.snapshot.phase") == "category"
    # Structures still contains the discovered clan after leaving.
    send(structures)
    send("1")
    assert page.evaluate("packet.prompt") == "Elemental village > "
    send("4")
    directory = page.evaluate(
        "catalog.groups.find(x=>x.id==='explore').options.findIndex(x=>x[0]===47)+1"
    )
    send(directory)
    send("1")
    assert page.evaluate("packet.snapshot.village.name") == "Old Village"
    send("18")
    send("4")
    gold = page.evaluate("packet.snapshot.player.gold")
    send("5")
    assert (
        page.evaluate(
            "packet.snapshot.player.expansion.activities.woods_defence.complete"
        )
        is True
    )
    assert page.evaluate("packet.snapshot.player.gold") == gold + 100
    send("5")
    assert page.evaluate("packet.snapshot.player.gold") == gold + 100
    send("0")
    send("7")
    send("0")
    saved = page.evaluate("safeSave()")
    page.evaluate("async save=>await start({save})", saved)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    assert (
        page.evaluate(
            "packet.snapshot.player.expansion.activities.woods_defence.complete"
        )
        is True
    )
    assert page.evaluate(
        "packet.snapshot.player.discovered_structures['Whispering Woods'].includes('Sylvar Circle')"
    )
    assert page.evaluate("packet.snapshot.player.chapter") == 1
    assert page.evaluate("packet.snapshot.player.elemental_cores.length") == 0
    assert not errors, errors
    print(
        "PASS: clan history/shop remains open, scrollbar stays, Season One purchases, raid worker assignments, three real Woods waves with clan help, Structures revisit and unique report/save persistence"
    )
    browser.close()
