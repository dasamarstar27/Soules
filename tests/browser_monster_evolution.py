"""All four forms reach real battles, with visible stats and Easy health adjustment."""

from copy import deepcopy
import data
from monster_evolution import form
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")
    page.evaluate("async()=>await respond('7')")
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    base = page.evaluate("safeSave()")
    for difficulty in ("normal", "easy"):
        for stage, level in enumerate((1, 5, 10, 15), 1):
            save = deepcopy(base)
            p = save["player"]
            p.update(
                level=level, difficulty=difficulty, hp=1000, max_hp=1000, wander_count=0
            )
            p["expansion"].setdefault("field", {})["tracked_target"] = dict(
                region=p["region"], enemy=data.NORMAL_MONSTERS[p["region"]][0]
            )
            page.evaluate("async save=>await start({save})", save)
            page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
            page.locator('[data-group="explore"]').click()
            page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
            page.locator('#action-buttons [data-response="1"]').click()
            page.wait_for_function("packet.snapshot.enemy?.evolution&&!busy")
            enemy = page.evaluate("packet.snapshot.enemy")
            expected = form(p["region"], 0, level)
            assert enemy["name"] == expected["name"]
            assert enemy["evolution"]["stage"] == stage
            assert enemy["evolution"]["level"] == level
            assert enemy["hp"] == round(
                expected["hp"] * (0.75 if difficulty == "easy" else 1)
            )
            assert enemy["hp"] == enemy["max_hp"]
            card = page.locator(".enemy-card").inner_text()
            assert "Stage " + str(stage) + "/4" in card
            assert "Level " + str(level) in card
            assert "ATK" in card and "DEF" in card
    page.locator('.topbar [data-view="home"]').first.click()
    page.locator('[data-view="dictionary"]').click()
    page.locator('[data-dictionary="evolutions"]').click()
    assert page.locator(".cards article").count() == 120
    assert "Apex Corrupted Thorn Wolf" in page.locator(".cards").inner_text()
    assert "Lv 5: Empowered Thorn Wolf" in page.locator(".cards").inner_text()
    page.set_viewport_size({"width": 820, "height": 1180})
    page.locator("#tablet-mode").click()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    browser.close()
print(
    "PASS: all four stages in Normal and Easy real tracked fights, enemy stat/sidebar display, correct HP modifiers, 120-form dictionary and tablet layout"
)
