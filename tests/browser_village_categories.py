"""Real tablet category menus and new combat reaction buttons."""

import data
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

    def answer(value):
        previous = page.evaluate("packet.prompt_id")
        page.locator('#comfort-choices [data-response="' + str(value) + '"]').click()
        page.wait_for_function(
            "previous=>packet.prompt_id>previous&&!busy", arg=previous
        )
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    assert (
        page.locator(
            '#comfort-choices [data-response]:not([data-response="/back"])'
        ).count()
        == 7
    )
    answer(1)
    assert page.evaluate("packet.prompt") == "Village [Food & rest] > "
    assert "Harvest farm" in page.locator("#comfort-choices").inner_text()
    assert "Blacksmith" not in page.locator("#comfort-choices").inner_text()
    answer(5)
    assert len(page.evaluate("packet.snapshot.player.ingredients")) == 5
    assert page.evaluate("packet.prompt") == "Village [Food & rest] > "
    answer(0)
    answer(3)
    assert "Build / upgrade" in page.locator("#comfort-choices").inner_text()
    answer(0)
    answer(7)
    saved = page.evaluate("safeSave()")
    saved["player"].update(hp=5000, max_hp=5000, speed=0, mana=20, atk=0)
    saved["player"]["expansion"]["field"]["tracked_target"] = {
        "enemy": data.NORMAL_MONSTERS["Whispering Woods"][0],
        "region": "Whispering Woods",
    }
    page.evaluate("async save=>await start({save})", saved)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator('[data-group="explore"]').click()
    page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
    old = page.evaluate("packet.prompt_id")
    page.evaluate("async()=>await respond('1')")
    page.wait_for_function(
        "old=>packet.prompt_id>old&&packet.prompt.includes('1 atk')&&!busy", arg=old
    )
    assert page.locator(".enemy-intent").is_visible()
    assert "Guard (free)" in page.locator("#comfort-choices").inner_text()
    assert "Interrupt (3 mana)" in page.locator("#comfort-choices").inner_text()
    mana = page.evaluate("packet.snapshot.player.mana")
    answer(10)
    assert page.evaluate("packet.snapshot.player.mana") == mana
    for _ in range(30):
        if page.evaluate(
            "['heavy','pounce'].includes(packet.snapshot.enemy.intent.key)"
        ):
            break
        answer(10)
    if page.evaluate("['heavy','pounce'].includes(packet.snapshot.enemy.intent.key)"):
        hp = page.evaluate("packet.snapshot.player.hp")
        answer(11)
        assert page.evaluate("packet.snapshot.player.hp") == hp
        assert page.evaluate("packet.snapshot.player.mana") == mana - 3
    answer(4)
    assert not errors, errors
    browser.close()
print(
    "PASS: short village categories, tablet submenus/back, harvest, build category, visible intents and Guard/Interrupt controls in an actual tracked fight"
)
