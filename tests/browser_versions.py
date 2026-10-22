"""Corner version, older download links, checkpoint backup and no gameplay side effects."""

import json
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1100})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    assert page.locator("#release-version").inner_text() == "V25.11 ▾"
    page.locator("#release-version").click()
    assert page.locator("#versions-dialog").is_visible()
    assert page.locator(".version-download").count() == 10
    assert page.locator("#version-export").is_disabled()
    for old in (
        "25.10",
        "25.9",
        "25.8",
        "25.7",
        "25.6",
        "25.5",
        "25.4",
        "25.3",
        "25.2",
    ):
        assert "/releases/Soules-V" + old + ".zip" in page.get_by_role(
            "link", name="Download V" + old, exact=True
        ).get_attribute("href")
    page.keyboard.press("Escape")
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")
    page.evaluate("async()=>await respond('7')")
    page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
    before = page.evaluate("safeSave()")
    prompt = page.evaluate("packet.prompt_id")
    page.locator("#release-version").click()
    with page.expect_download() as download:
        page.locator("#version-export").click()
    assert json.loads(open(download.value.path()).read()) == before
    page.locator("#close-versions").click()
    assert page.evaluate("safeSave()") == before
    assert page.evaluate("packet.prompt_id") == prompt
    for comfort in (False, True):
        if comfort:
            page.locator("#easy-reading").click()
        for width in (820, 390):
            page.set_viewport_size({"width": width, "height": 1100})
            assert page.locator("#release-version").is_visible()
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            page.locator("#release-version").click()
            assert page.locator("#versions-dialog").evaluate(
                "el=>el.getBoundingClientRect().width<=innerWidth"
            )
            page.locator("#close-versions").click()
    assert not errors, errors
    browser.close()
print(
    "PASS: current corner badge, pinned archived links, checkpoint download, unchanged gameplay, keyboard/button close and desktop/tablet/phone layouts"
)
