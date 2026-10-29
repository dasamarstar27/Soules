"""Shop questions with no new output must replace stale numeric menu buttons."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    for mode in ("tablet", "comfort"):
        page = browser.new_page(viewport={"width": 820, "height": 1180})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector(".home-options")
        page.locator("#tablet-mode" if mode == "tablet" else "#easy-reading").click()
        page.locator("[data-play]").click()
        page.get_by_role("button", name="Begin adventure").click()
        page.wait_for_function("packet?.prompt==='Village > '&&!busy")

        def choose(value):
            old = page.evaluate("packet.prompt_id")
            page.locator(
                '#comfort-choices [data-response="' + str(value) + '"]'
            ).click()
            page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
            assert not page.evaluate("packet.error")

        choose(7)
        save = page.evaluate("safeSave()")
        save["player"]["gold"] = 5000
        page.evaluate("async save=>await start({save})", save)
        page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
        page.locator('[data-group="explore"]').click()
        page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
        number = page.evaluate(
            "catalog.groups.find(g=>g.id==='explore').options.findIndex(x=>x[0]===17)+1"
        )
        page.locator('#action-buttons [data-response="' + str(number) + '"]').click()
        page.wait_for_function("packet.snapshot.phase==='action'&&!busy")
        choose(0)
        page.wait_for_function("packet.prompt==='Village > '&&!busy")
        choose(2)
        choose(1)
        assert page.evaluate("packet.prompt") == "Buy item number > "
        gold = page.evaluate("packet.snapshot.player.gold")
        count = page.evaluate("packet.snapshot.player.weapons.length")
        before = page.locator("#terminal").text_content()
        choose(1)
        assert "(y/n)" in page.evaluate("packet.prompt")
        assert page.locator("#terminal").text_content().replace(
            "> 1", ""
        ) == before.replace("> 1", "")
        assert page.locator('#comfort-choices [data-response="y"]').is_enabled()
        assert page.locator('#comfort-choices [data-response="n"]').is_enabled()
        assert page.locator('#comfort-choices [data-response="1"]').count() == 0
        choose("n")
        assert page.evaluate("packet.snapshot.player.gold") == gold
        assert page.evaluate("packet.snapshot.player.weapons.length") == count
        choose(1)
        choose("y")
        assert page.evaluate("packet.snapshot.player.gold") < gold
        assert page.evaluate("packet.snapshot.player.weapons.length") == count + 1
        assert "Purchased Rust-Eaten Blade!" in page.locator("#terminal").text_content()
        assert page.locator('#comfort-choices [data-response="y"]').count() == 0
        choose(0)
        # Confirmation wording must win over quantity/note/name text in item titles.
        assert page.evaluate(
            "buttonInputChoices('Name your weapon:', 'Buy Weapon Name Note amount for 20 souls? (y/n) > ')"
        ) == [["y", "Yes"], ["n", "No"]]
        assert page.evaluate("buttonInputChoices('', 'Forge it? (yes/no) > ')") == [
            ["yes", "Yes"],
            ["no", "No"],
        ]
        assert page.evaluate("buttonInputChoices('', 'Press Enter to return > ')") == [
            ["", "Continue"]
        ]
        assert not errors, errors
        page.close()
    browser.close()
print(
    "PASS: tablet/Easy reading shop confirmations without printed output, No cancels, Yes purchases, stale menu removed, active question priority and Continue"
)
