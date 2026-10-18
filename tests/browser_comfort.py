"""Readable controls, safe labelled choices, optional speech and local services."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    page.add_init_script(
        """window.readings=[];window.stopCount=0;
      Object.defineProperty(window,'speechSynthesis',{value:{speak(u){window.readings.push({text:u.text,rate:u.rate});},cancel(){window.stopCount++;},getVoices(){return [];},addEventListener(){}}});
      window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};"""
    )
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("#easy-reading").click()
    assert page.locator("#easy-reading").get_attribute("aria-pressed") == "true"
    assert (
        page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--font-size').trim()"
        )
        == "22px"
    )
    assert (
        page.evaluate(
            "contrast(getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(),getComputedStyle(document.documentElement).getPropertyValue('--bg').trim())"
        )
        >= 4.5
    )
    page.locator("#font-up").click()
    assert page.evaluate("preferences.comfortFont") == 23
    page.locator("#font-down").click()
    page.reload()
    page.wait_for_selector(".home-options")
    assert page.locator("body").evaluate("el=>el.classList.contains('comfort-mode')")
    assert page.evaluate("preferences.comfortFont") == 22
    page.locator("#easy-reading").click()
    assert not page.locator("body").evaluate(
        "el=>el.classList.contains('comfort-mode')"
    )
    assert (
        page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--font-size').trim()"
        )
        == "15px"
    )
    page.locator("#easy-reading").click()
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")

    def send(text):
        page.wait_for_function("packet.waiting&&!busy")
        prev = page.evaluate("packet.prompt_id")
        page.evaluate("async text=>await respond(text)", str(text))
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=prev)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    def choose(answer):
        prev = page.evaluate("packet.prompt_id")
        page.locator(f'#comfort-choices [data-response="{answer}"]').click()
        page.wait_for_function("id=>packet.prompt_id>id&&!busy", arg=prev)
        assert not page.evaluate("packet.error"), page.evaluate("packet.error")

    assert page.locator("#comfort-choices").is_visible()
    assert page.locator('#comfort-choices [data-response="10"]').count() == 1
    assert page.locator('#comfort-choices [data-response="9"]').count() == 0
    assert (
        page.locator("#comfort-choices button").first.evaluate(
            "el=>el.getBoundingClientRect().height"
        )
        >= 48
    )
    assert page.evaluate("readings.length") == 0
    page.locator("#read-latest").click()
    assert page.evaluate("readings.length") == 1
    assert "Village >" in page.evaluate("readings[0].text")
    page.locator("#stop-reading").click()
    assert page.locator("#stop-reading").is_disabled()
    page.locator("#word-help").click()
    assert page.locator("#word-help-dialog").is_visible()
    assert "HP · Health" in page.locator("#word-help-dialog").inner_text()
    page.locator("#close-word-help").click()
    choose(22)
    assert page.locator('#comfort-choices [data-response="1"]').count() == 0
    assert page.locator('#comfort-choices [data-response="4"]').count() == 1
    choose(0)
    choose(7)
    saved = page.evaluate("safeSave()")
    saved["player"]["region"] = "Crimson Depths"
    saved["player"]["unlocked_regions"] = ["Whispering Woods", "Crimson Depths"]
    saved["player"]["discovered_structures"]["Crimson Depths"] = ["Smiths' Quarter"]
    page.evaluate("async save=>await start({save})", saved)
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    page.locator('[data-group="explore"]').click()
    page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
    structures = page.evaluate(
        "catalog.groups.find(g=>g.id==='explore').options.findIndex(x=>x[0]===17)+1"
    )
    send(structures)
    choose(0)
    assert page.evaluate("packet.snapshot.village.name") == "Smiths' Quarter"
    for unavailable in (1, 6, 10, 13, 18, 24, 26):
        assert (
            page.locator(f'#comfort-choices [data-response="{unavailable}"]').count()
            == 0
        ), unavailable
    assert page.locator('#comfort-choices [data-response="9"]').count() == 1
    choose(22)
    assert page.locator('#comfort-choices [data-response="1"]').count() == 1
    assert page.locator('#comfort-choices [data-response="4"]').count() == 0
    choose(0)
    choose(7)
    # Current question and speech controls also handle numeric quantities safely.
    assert (
        page.evaluate(
            "comfortOptions('1. Iron\\n2. Steel','How many? Enter a quantity > ').length"
        )
        == 0
    )
    assert page.evaluate(
        "comfortOptions('1. Old choice','Pay 30 souls? (y/n) > ')"
    ) == [["y", "Yes"], ["n", "No"]]
    # Reading has no gameplay side effects and is explicitly triggered each time.
    state = page.evaluate("safeSave().player")
    page.locator("#read-latest").click()
    page.locator("#stop-reading").click()
    assert page.evaluate("safeSave().player") == state
    page.locator('.topbar [data-view="customise"]').first.click()
    page.locator("#reading-speed").select_option("0.7")
    assert page.evaluate("preferences.readRate") == 0.7
    page.locator("#play").click()
    for width, height in ((820, 1180), (390, 844)):
        page.set_viewport_size({"width": width, "height": height})
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth"), width
    page.set_viewport_size({"width": 1440, "height": 1100})
    page.screenshot(path="/tmp/soules-easy-reading.png")
    assert not errors, errors
    browser.close()
print(
    "PASS: easy-reading size/contrast/persistence/restoration, labelled choices, supported village/worker facilities, explicit read/stop, glossary, unchanged gameplay and tablet/mobile layout"
)
