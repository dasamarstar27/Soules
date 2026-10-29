"""Player-readable prompts, searchable content, rarity and matching fusion charging."""

from copy import deepcopy
import data
from rune_pairs import fusion, BASE
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator('.home-options [data-view="dictionary"]').click()
    assert page.locator(".cards article").count() == 60
    page.locator("#dictionary-more").click()
    assert page.locator(".cards article").count() == 120
    page.locator("#dictionary-category").select_option("Materials")
    assert page.locator(".cards article").count() == 54
    page.locator("#dictionary-search").fill("Iron")
    assert "ATK: 5" in page.locator(".cards").inner_text()
    page.locator("#dictionary-category").select_option("")
    page.locator("#dictionary-search").fill("Sea Pearl")
    text = page.locator(".cards").inner_text()
    assert "Sunken Coast:" in text and "ordinary loot roll" in text
    page.locator("#dictionary-search").fill("Phoenix Core")
    assert "Fusion requires BOTH" in page.locator(".cards").inner_text()
    page.locator("#dictionary-search").fill("Old Village")
    assert "Starting services:" in page.locator(".cards").inner_text()
    page.locator('.topbar [data-view="home"]').first.click()
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")

    def send(value):
        page.wait_for_function("packet.waiting&&!busy")
        prev = page.evaluate("packet.prompt_id")
        page.evaluate("async value=>await respond(packet.prompt==='Village > '&&/^[1-6]$/.test(value)?'v:'+value:value)", str(value))
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=prev)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    send(23)
    assert "number you should type" in page.locator("#terminal").inner_text()
    send(2)
    text = page.locator("#terminal").inner_text()
    assert "30 souls, 3 Timber and 3 Stone" in text
    assert "0 to go back without choosing" in text
    assert page.evaluate("packet.prompt") == "Option number (0 = back) > "
    send(0)
    send(0)
    send(7)
    base = page.evaluate("safeSave()")
    p = base["player"]
    p.update(
        region="Crimson Depths", cores=["Phoenix Core"], metals=["Iron"], woods=["Oak"]
    )
    p["unlocked_regions"] = ["Whispering Woods", "Crimson Depths"]
    p["runes"] = [
        fusion(BASE["Flame Rune"], BASE["Water Rune"]),
        fusion(BASE["Flame Rune"], BASE["Magma Rune"]),
    ]
    p["expansion"]["activities"]["crimson_forge"] = {"waves": 3, "cleared": True}
    page.evaluate("async save=>await start({save})", base)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator('[data-group="explore"]').click()
    page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
    travel = page.evaluate(
        "catalog.groups.find(g=>g.id==='explore').options.findIndex(x=>x[0]===2)+1"
    )
    send(travel)
    send("f")
    send(5)
    send(1)
    # Only the compatible fusion appears in the sacrifice list.
    latest = (
        page.locator("#terminal")
        .inner_text()
        .split("SACRIFICE A COMPATIBLE LOOSE RUNE")[-1]
    )
    assert "Flame Rune + Magma Rune" in latest
    assert "Water Rune" not in latest
    send(1)
    assert page.evaluate("packet.snapshot.player.runes.length") == 1
    assert page.evaluate(
        'packet.snapshot.player.runes[0].inputs.includes("Water Rune")'
    )
    assert (
        page.evaluate("packet.snapshot.player.charged_cores[0].rune.effect") == "fusion"
    )
    send(2)
    send(1)
    send(1)
    send(1)
    send("Phoenix Test Fusion")
    send(0)
    save = page.evaluate("safeSave()")
    assert save["player"]["weapons"][-1]["forge_core_rune"]["inputs"] == [
        "Flame Rune",
        "Magma Rune",
    ]
    page.evaluate("async save=>await start({save})", save)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator('.topbar [data-view="home"]').first.click()
    page.locator('.home-options [data-view="dictionary"]').click()
    page.locator('[data-dictionary="all"]').click()
    page.locator("#dictionary-search").fill("Phoenix Test Fusion")
    assert "Owned item" in page.locator(".cards").inner_text()
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    browser.close()
print(
    "PASS: extensive reference/categories/paging/loot odds, readable community costs, matching fusion sacrifice/crafting/save, owned-item reference and mobile"
)
