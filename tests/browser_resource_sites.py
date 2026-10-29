"""Full text UI work-site yields and saved finite stock, using tablet buttons."""

from copy import deepcopy
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

    def send(value):
        old = page.evaluate("packet.prompt_id")
        page.evaluate("async value=>await respond(packet.prompt==='Village > '&&/^[1-6]$/.test(value)?'v:'+value:value)", str(value))
        page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    send(7)
    base = page.evaluate("safeSave()")
    for kind, bag, build, resource in [
        ("quarry", "metals", "Stone", "Iron"),
        ("lumberyard", "woods", "Timber", "Oak"),
    ]:
        saved = deepcopy(base)
        p = saved["player"]
        site = next(
            s for s in data.REGION_STRUCTURES["Whispering Woods"] if s["type"] == kind
        )
        p["discovered_structures"]["Whispering Woods"] = [site["name"]]
        page.evaluate("async save=>await start({save})", saved)
        page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
        page.locator('[data-group="explore"]').click()
        page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
        n = page.evaluate(
            "catalog.groups.find(x=>x.id==='explore').options.findIndex(x=>x[0]===17)+1"
        )
        send(n)
        send(0)
        assert (
            "2 " + build + " + 1 " + resource in page.locator("#terminal").inner_text()
        )
        # The new prompt must still offer an actual numeric button in tablet mode.
        old = page.evaluate("packet.prompt_id")
        page.locator('#comfort-choices [data-response="1"]').click()
        page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
        assert page.evaluate("(bag)=>packet.snapshot.player[bag]", bag) == [resource]
        assert (
            page.evaluate(
                "(key)=>packet.snapshot.player.building_materials[key]", build
            )
            == 2
        )
        assert "goes into crafting materials" in page.locator("#terminal").inner_text()
        send(n)
        send(0)
        send(1)
        assert page.evaluate("(bag)=>packet.snapshot.player[bag].length", bag) == 1
        assert "replenish" in page.locator("#terminal").inner_text()
    assert not errors, errors
    browser.close()
print(
    "PASS: full quarry and timber menus, tablet work buttons, dual resource bags and finite repeat visits"
)
