"""Actual Bandit Camp story/level-up and ingredient trade in all control layouts."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    for mode in ("desktop", "tablet", "comfort"):
        page = browser.new_page(viewport={"width": 1280, "height": 1100})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:5000")
        page.wait_for_selector(".home-options")
        if mode != "desktop":
            page.locator(
                "#tablet-mode" if mode == "tablet" else "#easy-reading"
            ).click()
        page.locator("[data-play]").click()
        page.get_by_role("button", name="Begin adventure").click()
        page.wait_for_function("packet?.prompt==='Village > '&&!busy")

        def answer(value):
            old = page.evaluate("packet.prompt_id")
            if mode == "desktop":
                page.locator("#command").fill(str(value))
                page.locator("#command-form").press("Enter")
            else:
                page.locator(
                    '#comfort-choices [data-response="' + str(value) + '"]'
                ).click()
            page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
            assert not page.evaluate("packet.error"), page.evaluate("packet.error")

        answer(7)
        save = page.evaluate("safeSave()")
        save["player"].update(xp=45, ingredients=["Thorn Petal"], hp=30, hunger=90)
        save["player"]["discovered_structures"]["Whispering Woods"] = ["Bandit Camp"]
        page.evaluate("async save=>await start({save})", save)
        page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
        page.locator('[data-group="explore"]').click()
        page.wait_for_function("packet.snapshot.group==='explore'&&!busy")
        number = page.evaluate(
            "catalog.groups.find(g=>g.id==='explore').options.findIndex(x=>x[0]===17)+1"
        )

        def camp():
            page.locator(
                '#action-buttons [data-response="' + str(number) + '"]'
            ).click()
            page.wait_for_function("packet.snapshot.phase==='action'&&!busy")
            answer(0)
            assert page.evaluate("packet.prompt") == "Camp > "
            assert page.evaluate("packet.snapshot.location.name") == "Bandit Camp"

        camp()
        answer(2)
        assert page.evaluate("packet.snapshot.player.level") == 2
        assert page.evaluate("packet.snapshot.player.skill_points") == 1
        assert "XP from the conversation" in page.locator("#terminal").text_content()
        assert "LEVEL UP!" in page.locator("#terminal").text_content()
        camp()
        gold = page.evaluate("packet.snapshot.player.gold")
        answer(3)
        assert page.evaluate("packet.snapshot.player.ingredients.length") == 0
        assert page.evaluate("packet.snapshot.player.gold") > gold
        assert "You trade [Thorn Petal]" in page.locator("#terminal").text_content()
        camp()
        answer(4)
        assert page.evaluate("packet.snapshot.phase") == "category"
        assert "leave the camp" in page.locator("#terminal").text_content()
        assert not errors, errors
        page.close()
    browser.close()
print(
    "PASS: Bandit Camp stories award XP and level up; trades consume/pay once with feedback; exit returns safely; desktop, Tablet and Easy reading"
)
