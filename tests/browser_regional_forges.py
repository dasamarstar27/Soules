"""Real browser: dwarf supplies, charged-core crafting, regional trade and clan palettes."""

from copy import deepcopy
import data
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")

    def send(value):
        page.wait_for_function("packet.waiting&&!busy")
        previous = page.evaluate("packet.prompt_id")
        page.evaluate("async value=>await respond(value)", str(value))
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=previous)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    def group(name):
        page.locator(f'[data-group="{name}"]').click()
        page.wait_for_function("name=>packet.snapshot.group===name&&!busy", arg=name)

    def action(group_name, number):
        group(group_name)
        index = page.evaluate(
            "([group,id])=>catalog.groups.find(x=>x.id===group).options.findIndex(x=>x[0]===id)+1",
            [group_name, number],
        )
        assert index > 0
        send(index)

    def restore(save):
        page.evaluate("async save=>await start({save})", save)
        page.wait_for_function("packet.snapshot.phase==='main'&&!busy")

    send(7)
    base = page.evaluate("safeSave()")
    save = deepcopy(base)
    p = save["player"]
    p.update(
        region="Ironpeak Mountains", gold=10000, hp=1000, max_hp=1000, atk=100, level=12
    )
    p["unlocked_regions"] = [
        "Whispering Woods",
        "Crimson Depths",
        "Ironpeak Mountains",
        "Riftlands",
    ]
    p["cores"] = ["Molten Core"]
    p["runes"] = [next(r for r in data.RUNES if r["name"] == "Flame Rune")]
    p["metals"] = ["Iron"]
    p["woods"] = ["Oak"]
    quarry = next(
        s for s in data.REGION_STRUCTURES["Ironpeak Mountains"] if s["type"] == "quarry"
    )
    p["discovered_structures"]["Ironpeak Mountains"] = [quarry["name"]]
    restore(save)
    action("explore", 17)
    send(0)
    assert "Bromm" in page.locator("#terminal").inner_text()
    send(2)
    send(1)
    send(3)
    assert page.evaluate("packet.snapshot.player.gold") == 9985
    assert (
        page.evaluate("packet.snapshot.player.metals.filter(x=>x==='Iron').length") == 4
    )
    send(0)
    send(0)
    action("explore", 2)
    send("f")
    assert page.evaluate("packet.snapshot.location.name") == "Crimson Forge"
    send(2)
    assert len(page.evaluate("packet.snapshot.player.cores")) == 1
    for _ in range(3):
        send(1)
        for attack in range(20):
            if page.evaluate("packet.prompt") != "Tactical action > ":
                break
            send(1)
        assert page.evaluate("packet.prompt") == "Choice > ", page.evaluate(
            "packet.prompt"
        )
    assert page.evaluate(
        "packet.snapshot.player.expansion.activities.crimson_forge.cleared"
    )
    send(5)
    send(1)
    send(1)
    assert page.evaluate("packet.snapshot.player.charged_cores.length") == 1
    assert page.evaluate("packet.snapshot.player.runes.length") == 0
    send(2)
    send(1)
    send(1)
    send(1)
    send("Ember Test Blade")
    w = page.evaluate("packet.snapshot.player.weapons.at(-1)")
    assert (
        w["forge_core_effect"] == "burn"
        and w["forge_core_rune"]["name"] == "Flame Rune"
    )
    assert page.evaluate("packet.snapshot.player.charged_cores.length") == 0
    assert page.evaluate("packet.snapshot.player.metals.length") == 3
    send(0)
    saved = page.evaluate("safeSave()")
    restore(saved)
    assert (
        page.evaluate("packet.snapshot.player.weapons.at(-1).name")
        == "Ember Test Blade"
    )
    assert page.evaluate(
        "packet.snapshot.player.expansion.activities.crimson_forge.cleared"
    )
    # All four clans have their own automatic palette, also inside local services.
    expected = {
        "fire": "#2a120d",
        "ice": "#101f30",
        "storm": "#241d0d",
        "nature": "#0e2619",
    }
    for region, clan in data.ELEMENTAL_VILLAGES.items():
        fixture = deepcopy(base)
        p = fixture["player"]
        p.update(region=region, gold=1000, beta_mode=True)
        p["unlocked_regions"] = list(data.REGIONS)
        p["discovered_structures"][region] = [clan["name"]]
        restore(fixture)
        action("explore", 17)
        send(0)
        assert (
            page.evaluate(
                "getComputedStyle(document.documentElement).getPropertyValue('--bg')"
            ).strip()
            == expected[clan["element"]]
        ), clan
        send(3)
        send(1)
        text = page.locator("#terminal").inner_text()
        assert "ATK +28" in text and "DEF +16" in text and "Power +18" in text
        assert "Price: 450 souls | Stock: 1" in text
        send(0)
        send(6)
        assert page.evaluate("packet.prompt") == "Elemental village > "
        send(6)
        assert (
            page.evaluate(
                "getComputedStyle(document.documentElement).getPropertyValue('--bg')"
            ).strip()
            == expected[clan["element"]]
        )
        send(7)
        send(4)
    # Riftlands specialist is a distinct non-dwarven core dealer.
    fixture = deepcopy(base)
    p = fixture["player"]
    p.update(region="Riftlands", gold=1000)
    p["unlocked_regions"] = list(data.REGIONS)
    village = next(
        s for s in data.REGION_STRUCTURES["Riftlands"] if s["type"] == "village"
    )
    p["discovered_structures"]["Riftlands"] = [village["name"]]
    restore(fixture)
    action("explore", 17)
    send(0)
    send(25)
    assert "Mara" in page.locator("#terminal").inner_text()
    assert "25%" in page.locator("#terminal").inner_text()
    send(1)
    send(2)
    assert (
        page.evaluate(
            "packet.snapshot.player.cores.filter(x=>x==='Molten Core').length"
        )
        == 2
    )
    assert page.evaluate("packet.snapshot.player.gold") == 940
    assert not errors, errors
    page.screenshot(path="/tmp/soules-regional-forges.png")
    browser.close()
print(
    "PASS: dwarf bulk purchases, three live forge battles, charged-core sacrifice/crafting/save, four clan palettes/shops and Riftlands core dealer"
)
