"""Browser integration for consumables, village work, party housing and raid controls."""

from copy import deepcopy
import data
import village_life as villages
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")

    def send(value):
        page.wait_for_function("packet.waiting&&!busy")
        old = page.evaluate("packet.prompt_id")
        page.evaluate(
            "async text=>await respond(packet.prompt==='Village > '&&/^[1-6]$/.test(text)?'v:'+text:text)",
            str(value),
        )
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=old)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    def clicked(selector):
        old = page.evaluate("packet.prompt_id")
        page.locator(selector).click()
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=old)

    def action(number):
        page.locator('[data-group="explore"]').click()
        page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
        index = page.evaluate(
            "id=>catalog.groups.find(g=>g.id==='explore').options.findIndex(x=>x[0]===id)+1",
            number,
        )
        send(index)

    def restore(save):
        page.evaluate("async save=>await start({save})", save)
        page.wait_for_function("packet.snapshot.phase==='main'&&!busy")

    send(7)
    base = page.evaluate("safeSave()")
    fixture = deepcopy(base)
    p = fixture["player"]
    p.update(gold=10000, hp=1, max_hp=100, atk=100, **{"def": 50})
    p["weapons"].append(dict(name="Sidebar Test Blade", atk=30))
    p["potions"] = ["Health Potion"] * 3
    pets = [pet for pool in data.COMPANIONS.values() for pet in pool][:5]
    p["companions"] = pets[:3]
    p["home_companions"] = pets[3:]
    v = villages.profile("Whispering Woods", "Old Village")
    p["village_records"].setdefault(v["id"], {})["reputation"] = 10
    restore(fixture)
    action(17)
    send(0)
    page.locator("#sidebar-weapon").select_option("1")
    page.wait_for_timeout(1500)
    assert page.locator("#sidebar-weapon").input_value() == "1"
    clicked("#sidebar-equip")
    assert page.evaluate("packet.snapshot.player.weapon.name") == "Sidebar Test Blade"
    page.locator("#sidebar-potion").select_option("1")
    page.wait_for_timeout(1500)
    assert page.locator("#sidebar-potion").input_value() == "1"
    page.locator("#sidebar-potion").select_option("0")
    clicked("#sidebar-drink")
    assert page.evaluate("packet.snapshot.player.hp") == 51
    assert page.evaluate("packet.snapshot.player.potions.length") == 2
    gold = page.evaluate("packet.snapshot.player.gold")
    send(1)
    send(1)
    send(3)
    assert page.evaluate("packet.snapshot.player.inventory.length") == 3
    assert page.evaluate("packet.snapshot.player.gold") < gold
    gold = page.evaluate("packet.snapshot.player.gold")
    rest_heal = 20 + page.evaluate("packet.snapshot.village.quality.inn") * 10
    send(4)
    assert "0 souls" in page.evaluate("packet.prompt")
    send("y")
    assert page.evaluate("packet.snapshot.player.gold") == gold
    assert page.evaluate("packet.snapshot.player.hp") == min(100, 51 + rest_heal)
    send(24)
    send(1)
    send(1)
    send(1)
    assert page.evaluate("packet.prompt") == "Press Enter to return to the village > "
    assert "BREW COMPLETE" in page.locator("#terminal").inner_text()
    assert page.evaluate("packet.snapshot.player.potions.length") == 1
    assert (
        page.locator("#terminal").evaluate(
            "el=>el.scrollHeight-el.scrollTop-el.clientHeight"
        )
        < 8
    )
    send("")
    send(26)
    send(1)
    send(1)
    send(2)
    send(1)
    send(0)
    assert page.evaluate("packet.snapshot.player.companions.length") == 3
    assert page.evaluate("packet.snapshot.player.home_companions.length") == 2
    # Clickable assignment cards are driven by live worker metadata, not guessed text.
    send(23)
    send(2)
    send(4)
    send(2)
    page.wait_for_selector("#village-assignment:not([hidden])")
    assert page.locator("[data-assign-role]").count() == 4
    assert "3 MONSTERS" in page.locator("#village-assignment").inner_text()
    while page.evaluate("Boolean(packet.snapshot.assignment)"):
        clicked('[data-assign-role="Defend"]')
    assert page.evaluate("packet.prompt") == "Tactical action > "
    assert "RAID INCOMING · 3 monsters" in page.locator("#terminal").inner_text()
    send(0)
    send(0)
    send(7)
    # Testing rollback restores all supplies, not just the mode flag.
    send(0)  # Hidden testing entry is accepted at the main category menu only.
    before = page.evaluate("safeSave()")
    send("DAMAR")
    assert page.evaluate("packet.snapshot.player.weapons.length") > 60
    send("SAMAR")
    assert (
        page.evaluate("packet.snapshot.player.weapons") == before["player"]["weapons"]
    )
    assert (
        page.evaluate("packet.snapshot.player.potions") == before["player"]["potions"]
    )
    # Worker can supply its own finite core, wood and metal stock at a quoted premium.
    fixture = deepcopy(base)
    p = fixture["player"]
    p.update(region="Crimson Depths", gold=10000, hp=1000, max_hp=1000)
    p["unlocked_regions"] = ["Whispering Woods", "Crimson Depths"]
    p["discovered_structures"]["Crimson Depths"] = ["Smiths' Quarter"]
    restore(fixture)
    action(17)
    send(0)
    send(22)
    send(1)
    send(2)
    send(1)
    send(1)
    send(1)
    send("y")
    jobs = page.evaluate(
        "Object.values(packet.snapshot.player.village_records).flatMap(x=>x.work_orders||[])"
    )
    assert (
        len(jobs) == 1
        and jobs[0]["materials"] == ["Iron", "Molten Core", "Oak"]
        and jobs[0]["fee"] > 35
    ), (
        jobs,
        page.evaluate("packet.prompt"),
        page.locator("#terminal").inner_text()[-3500:],
    )
    remaining = jobs[0]["remaining"]
    send(0)
    send(7)
    action(1)
    jobs = page.evaluate(
        "Object.values(packet.snapshot.player.village_records).flatMap(x=>x.work_orders||[])"
    )
    assert jobs[0]["remaining"] == max(0, remaining - 1)
    page.set_viewport_size({"width": 820, "height": 1180})
    page.locator("#tablet-mode").click()
    assert page.locator("body").evaluate("el=>el.classList.contains('tablet-mode')")
    assert (
        page.locator("#tablet-mode").evaluate("el=>el.getBoundingClientRect().height")
        >= 44
    )
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    page.screenshot(path="/tmp/soules-tablet-qol.png")
    browser.close()
print(
    "PASS: sidebar equip/drink, bulk food, free reputation rest, blending feedback/follow, party sanctuary, raid role cards/group, beta rollback, paid village materials, wander work shift and tablet layout"
)
