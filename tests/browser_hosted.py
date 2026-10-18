"""Real hosted-server tablet play, checkpoint recovery and small-host session limit.

Install requirements-hosted.txt and Playwright/Chromium before running.
The test owns its Gunicorn server; it does not deploy a public service.
"""

from pathlib import Path
import os
import secrets
import subprocess
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "http://127.0.0.1:5055"
environment = dict(
    os.environ,
    SOULES_HOSTED="1",
    SOULES_MAX_SESSIONS="4",
    SESSION_SECRET=secrets.token_hex(32),
)


def launch():
    process = subprocess.Popen(
        [
            str(ROOT / ".venv/bin/gunicorn"),
            "--bind",
            "127.0.0.1:5055",
            "--workers",
            "1",
            "--threads",
            "8",
            "--timeout",
            "120",
            "app:app",
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        if process.poll() is not None:
            raise AssertionError("Hosted server exited before readiness")
        try:
            with urlopen(ADDRESS + "/health", timeout=1) as response:
                if response.status == 200:
                    return process
        except OSError:
            pass
        time.sleep(0.1)
    process.terminate()
    process.wait(timeout=10)
    raise AssertionError("Hosted server never became healthy")


server = launch()
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 820, "height": 1180}, has_touch=True, is_mobile=True
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(ADDRESS)
        page.wait_for_selector(".home-options")
        assert page.locator("body").evaluate("el=>el.classList.contains('tablet-mode')")
        page.locator("[data-play]").click()
        page.locator('[data-character-name="Nanu"]').click()
        page.locator("#difficulty-choice").select_option("easy")
        page.get_by_role("button", name="Begin adventure").click()
        page.wait_for_function("packet?.prompt==='Village > '&&!busy")
        assert page.evaluate("packet.snapshot.player.difficulty") == "easy"
        assert not page.locator("#command").is_visible()
        page.locator('#comfort-choices [data-response="7"]').click()
        page.wait_for_function("packet.snapshot.phase==='main'&&!busy")
        page.locator('[data-slot-action="save"]').first.click()
        assert (
            page.evaluate("JSON.parse(localStorage.getItem(SLOTS))[0].save.player.name")
            == "Nanu"
        )
        assert any(
            cookie["secure"]
            for cookie in context.cookies()
            if cookie["name"] == "session"
        )
        server.terminate()
        server.wait(timeout=10)
        server = launch()
        page.reload()
        page.wait_for_selector(".home-options")
        page.locator("[data-play]").click()
        page.wait_for_function("packet?.snapshot?.player?.name==='Nanu'&&!busy")
        assert page.evaluate("packet.snapshot.player.difficulty") == "easy"
        assert page.evaluate("packet.snapshot.player.weapons[0].name") == "Rusty Sword"
        assert page.locator('[data-slot-action="load"]').first.is_visible()
        # Browser sessions remain isolated; the configured cap prevents unbounded workers.
        for _ in range(3):
            other = browser.new_context()
            assert (
                other.request.post(
                    ADDRESS + "/api/original/start", data={"name": "Guest"}
                ).status
                == 200
            )
        other = browser.new_context()
        assert (
            other.request.post(
                ADDRESS + "/api/original/start", data={"name": "Extra"}
            ).status
            == 503
        )
        assert not errors, errors
        browser.close()
finally:
    server.terminate()
    server.wait(timeout=10)
print(
    "PASS: hosted Gunicorn tablet start, button-only Easy play, secure cookie, browser saves surviving host restart, isolated sessions and configured capacity"
)
