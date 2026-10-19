"""Exercise the standalone HTML with offline browser routing; no server or assets."""

from pathlib import Path
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    context = browser.new_context(
        offline=True, viewport={"width": 1366, "height": 900}, accept_downloads=True
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    # Managed Chromium blocks file:// navigation. Serve the exact HTML from memory
    # with networking disabled; every request must be satisfied by this one file.
    html = (
        Path(__file__).resolve().parents[1] / "simple/Play Soules Simple.html"
    ).read_text()
    context.route(
        "http://127.0.0.1:8044/**",
        lambda route: route.fulfill(body=html, content_type="text/html"),
    )
    page.goto("http://127.0.0.1:8044/")
    page.locator("input[name=name]").fill("Tester")
    page.get_by_role("button", name="Begin adventure").click()
    assert page.locator("#heading").inner_text() == "Old Village"
    assert page.evaluate("g.weapons[0].name") == "Rusty Sword"
    assert page.evaluate("g.runes.length+g.gold+g.potions+g.cores+g.metal+g.wood") == 0
    page.get_by_role("button", name="Leave village", exact=True).click()
    page.get_by_role("button", name="Gather wood & metal", exact=True).click()
    assert page.evaluate("[g.wood,g.metal]") == [1, 1]
    # Genuine fight with deterministic rolls, rewards and level progression.
    page.evaluate("Math.random=()=>0")
    page.get_by_role("button", name="Wander", exact=True).click()
    assert page.evaluate("g.enemy!==null")
    hp = page.evaluate("g.hp")
    page.get_by_role("button", name="Attack", exact=True).click()
    assert page.evaluate("g.hp") < hp
    for _ in range(8):
        if not page.evaluate("!!g.enemy"):
            break
        page.get_by_role("button", name="Attack", exact=True).click()
    assert page.evaluate("g.kills") == 1
    assert page.evaluate("g.gold") == 10
    # All non-monster branches of the single roll.
    for roll in (0.5, 0.72, 0.82, 0.95):
        page.evaluate('(n)=>{Math.random=()=>n;screen="play";draw()}', roll)
        page.get_by_role("button", name="Wander", exact=True).click()
        assert not page.evaluate("g.enemy")
    assert page.evaluate("g.cores") == 1
    # Prepare a paid smith commission and verify exact costs/equipment.
    page.evaluate('g.gold=60;g.metal=3;g.wood=3;g.cores=1;screen="village";draw()')
    page.get_by_role("button", name="Forge sword", exact=False).click()
    assert page.evaluate("[g.gold,g.metal,g.wood,g.cores,g.equipped]") == [
        30,
        1,
        2,
        0,
        1,
    ]
    page.get_by_role("button", name="Buy healing potion", exact=False).click()
    assert page.evaluate("[g.gold,g.potions]") == [18, 1]
    page.evaluate('g.runes=["Flame Rune"];screen="bag";draw()')
    page.get_by_role("button", name="Bind Flame Rune", exact=False).click()
    assert page.evaluate("weapon().rune") == "Flame Rune"
    assert page.evaluate("g.runes") == []
    # Permanent bindings, consumable potion and guardian cannot be repeated.
    page.evaluate("g.hp=40;draw()")
    page.get_by_role("button", name="Drink healing potion", exact=True).click()
    assert page.evaluate("[g.hp,g.potions]") == [80, 0]
    page.evaluate('g.hp=g.maxHp;screen="play";Math.random=()=>0;draw()')
    page.get_by_role("button", name="Challenge guardian", exact=True).click()
    for _ in range(15):
        if not page.evaluate("!!g?.enemy"):
            break
        page.get_by_role("button", name="Attack", exact=True).click()
    assert page.evaluate("g!==null && g.bosses.includes(0) && g.unlocked===1")
    assert page.get_by_role(
        "button", name="Challenge guardian", exact=True
    ).is_disabled()
    page.get_by_role("button", name="Travel", exact=True).click()
    page.get_by_role("button", name="Ashen Wastes", exact=True).click()
    assert page.evaluate("g.region") == 1
    # Offline local file autosave, slots, JSON portability, foreign save rejection.
    page.get_by_role("button", name="Saves", exact=True).click()
    page.get_by_role("button", name="Save slot 1", exact=True).click()
    with page.expect_download() as dl:
        page.get_by_role("button", name="Export save", exact=True).click()
    saved = json.loads(Path(dl.value.path()).read_text())
    assert saved["edition"] == "soules-simple"
    page.reload()
    assert page.evaluate("g.region") == 1
    page.get_by_role("button", name="Saves", exact=True).click()
    page.locator("#import").set_input_files(
        {"name": "bad.json", "mimeType": "application/json", "buffer": b'{"version":2}'}
    )
    page.wait_for_function(
        'document.getElementById("message").textContent.includes("Could not import")'
    )
    assert page.evaluate("g.region") == 1
    page.locator("#import").set_input_files(
        {
            "name": "good.json",
            "mimeType": "application/json",
            "buffer": json.dumps(saved).encode(),
        }
    )
    page.wait_for_function('screen==="play"')
    # Death clears only active autosave. Manual slot remains loadable.
    page.evaluate(
        'g.hp=1;g.enemy={name:"Test",hp:10000,maxHp:10000,atk:999,boss:false,burn:0};screen="play";draw()'
    )
    page.get_by_role("button", name="Attack", exact=True).click()
    assert page.evaluate("g===null && read(KEY)===null")
    page.get_by_role("button", name="Saves", exact=True).click()
    page.get_by_role("button", name="Load slot 1", exact=True).click()
    assert page.evaluate("g.name") == "Tester"
    page.get_by_role("button", name="Dictionary", exact=True).click()
    assert "45% monster" in page.locator("#detail").inner_text()
    assert "The Dreaming God" in page.locator("#detail").inner_text()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors, errors
    browser.close()
print(
    "PASS: standalone offline launch, core loop, smith costs, binding, healing, boss progression, local saves, import/export, death and dictionary"
)
