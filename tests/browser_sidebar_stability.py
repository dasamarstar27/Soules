"""Polling must retain sidebar controls, focus, disclosures and reading anchors."""

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
    page.locator("[data-play]").click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")
    page.locator(".village-services details").first.locator("summary").click()
    page.evaluate(
        "()=>{window.keptSelect=$('#sidebar-weapon');window.keptPanel=document.querySelector('.village-services details');keptSelect.focus({preventScroll:true});$('#status-sidebar').scrollTop=350;}"
    )
    before = page.locator("#status-sidebar").evaluate("e=>e.scrollTop")
    for _ in range(5):
        page.evaluate(
            "()=>{packet.snapshot.player.hp--;packet.snapshot.village.reputation++;renderSidebar()}"
        )
    assert page.evaluate("keptSelect===$('#sidebar-weapon')")
    assert page.evaluate("document.activeElement===keptSelect")
    assert page.evaluate(
        "keptPanel===document.querySelector('.village-services details')&&keptPanel.open"
    )
    assert abs(page.locator("#status-sidebar").evaluate("e=>e.scrollTop") - before) < 2
    # Grow content above an actual reading point; keep that paragraph at its position.
    page.evaluate(
        "()=>{const target=[...document.querySelectorAll('#status-sidebar .side-card')].find(x=>x.querySelector('h2')?.textContent==='EQUIPMENT & SATCHEL');window.readingAnchor=target.querySelector('h2');$('#status-sidebar').scrollTop+=readingAnchor.getBoundingClientRect().top-$('#status-sidebar').getBoundingClientRect().top-24;window.readingY=readingAnchor.getBoundingClientRect().top;packet.snapshot.village.note='A long village note '.repeat(30);renderSidebar();}"
    )
    assert page.evaluate(
        "Math.abs(readingAnchor.getBoundingClientRect().top-readingY)<2"
    )
    page.wait_for_timeout(1400)
    assert page.evaluate("keptSelect===$('#sidebar-weapon')")
    assert not errors, errors
    browser.close()
print(
    "PASS: stable sidebar nodes/focus, open panels, repeated live updates, visible reading anchor and delayed polls"
)
