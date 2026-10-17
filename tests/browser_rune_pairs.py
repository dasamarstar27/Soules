from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator('.home-options [data-view="dictionary"]').click()
    page.locator('[data-dictionary="fusions"]').click()
    page.locator("#fusion-first").select_option("Flame Rune")
    page.locator("#fusion-second").select_option("Ice Rune")
    page.locator("#fusion-preview").click()
    page.wait_for_function(
        "document.querySelector('#fusion-result').textContent.includes('Thermal Shock')"
    )
    assert "immediate damage" in page.locator("#fusion-result").inner_text()
    page.locator('[data-dictionary="effects"]').click()
    page.locator("#dictionary-search").fill("berserk")
    assert "+50%" in page.locator(".cards").inner_text()
    assert "-30%" in page.locator(".cards").inner_text()
    assert not errors, errors
    print(
        "PASS: two-normal-rune preview, pair synergy, component abilities and Rage mechanics dictionary"
    )
    browser.close()
