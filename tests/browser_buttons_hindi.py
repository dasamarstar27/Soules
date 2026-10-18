"""Keyboard-free play and explicit Hindi speech, including unavailable-device paths."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1280, "height": 1000})
    page.add_init_script(
        """window.readings=[];
    window.voices=[{voiceURI:'en-test',lang:'en-US',name:'English'}, {voiceURI:'hi-test',lang:'hi-IN',name:'Hindi'}];
    Object.defineProperty(window,'speechSynthesis',{value:{speak(u){readings.push({text:u.text,lang:u.lang,voice:u.voice?.voiceURI});},cancel(){},getVoices(){return voices;},addEventListener(){}}});
    window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
    window.Translator={availability:async()=> 'available',create:async()=>({translate:async text=>'आपका गाँव सुरक्षित है। आगे बढ़ने के लिए एक विकल्प चुनें।'})};"""
    )
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on(
        "dialog",
        lambda d: (_ for _ in ()).throw(AssertionError("Unexpected dialog: " + d.type)),
    )
    page.goto("http://127.0.0.1:5000")
    page.wait_for_selector(".home-options")
    page.locator("#tablet-mode").click()
    page.locator("[data-play]").click()
    assert not page.locator('input[name="name"]').is_visible()
    page.locator('[data-character-name="Nanu"]').click()
    page.get_by_role("button", name="Begin adventure").click()
    page.wait_for_function("packet?.prompt==='Village > '&&!busy")
    assert page.evaluate("packet.snapshot.player.name") == "Nanu"
    assert not page.locator("#command").is_visible()
    assert page.locator("#comfort-choices").is_visible()

    def choose(answer):
        old = page.evaluate("packet.prompt_id")
        page.locator('#comfort-choices [data-response="' + str(answer) + '"]').click()
        page.wait_for_function("old=>packet.prompt_id>old&&!busy", arg=old)
        assert not page.evaluate("packet.error")

    choose(1)  # Buy food through the real game prompt.
    choose(1)
    assert page.locator(".quantity-controls output").inner_text() == "1"
    choose(1)
    assert page.evaluate("packet.prompt") == "Village > "
    assert "portions packed for your journey" in page.locator("#terminal").inner_text()
    choose(7)
    page.locator('[data-slot-action="save"]').first.click()
    assert page.evaluate("JSON.parse(localStorage.getItem(SLOTS))[0].label") == "Nanu"
    old = page.evaluate("packet.prompt_id")
    page.evaluate("async()=>await respond('DAMAR')")
    assert page.evaluate("packet.prompt_id") == old
    assert not page.evaluate("Boolean(packet.snapshot.player.beta_mode)")
    # Regression: numeric and free-text prompts become controls without editing fields.
    assert (
        page.evaluate("buttonInputChoices('', 'How many portions? > ')") == "quantity"
    )
    page.evaluate(
        "packet.snapshot.phase='action';packet.prompt='Quantity (1–8, 0 cancels) > ';packet.prompt_id++;renderGameControls()"
    )
    page.locator('[data-quantity="5"]').click()
    assert page.locator(".quantity-controls output").inner_text() == "6"
    page.locator('[data-quantity="5"]').click()
    assert page.locator(".quantity-controls output").inner_text() == "8"
    page.evaluate("packet.prompt='Village note (blank clears) > ';renderGameControls()")
    assert page.locator('#comfort-choices [data-response="Cheap food"]').is_visible()
    page.evaluate("packet.prompt='Name your elemental weapon > ';renderGameControls()")
    assert page.locator('#comfort-choices [data-response="Dawnblade"]').is_visible()
    assert page.evaluate("comfortOptions('', 'Forge it? (yes/no) > ')") == [
        ["yes", "Yes"],
        ["no", "No"],
    ]
    assert page.evaluate(
        "comfortOptions('1. Copper\\nC: Charge a core\\n0. Back','Specialist > ')"
    ) == [["1", "Copper"], ["C", "Charge a core"], ["0", "Back"]]
    # Return to genuine state before testing narration.
    page.reload()
    page.wait_for_selector(".home-options")
    page.locator("#play").click()
    page.wait_for_function("packet?.waiting&&!busy")
    page.locator("#read-hindi").click()
    page.wait_for_function("readings.length===1")
    assert page.evaluate("readings[0].lang") == "hi-IN"
    assert page.evaluate("readings[0].voice") == "hi-test"
    assert "गाँव" in page.evaluate("readings[0].text")
    page.locator("#stop-reading").click()
    page.evaluate("window.voices=[]")
    page.locator("#read-hindi").click()
    page.wait_for_function(
        "document.querySelector('#narration-status').textContent.includes('No Hindi voice')"
    )
    assert page.evaluate("readings.length") == 1
    # Already-translated text works without a translation service; English gives setup help.
    page.evaluate("window.Translator=undefined")
    assert (
        page.evaluate(
            "async()=>await translateForHindi('आपका गाँव सुरक्षित है।',readingRevision)"
        )
        == "आपका गाँव सुरक्षित है।"
    )
    assert "Translate the page" in page.evaluate(
        "async()=>{try{await translateForHindi('English story',readingRevision);}catch(e){return e.message;}}"
    )
    # Stop must prevent pending translation from speaking later.
    page.evaluate(
        "() => {window.voices=[{voiceURI:'hi-test',lang:'hi-IN',name:'Hindi'}];window.translateForHindi=()=>new Promise(resolve=>window.resolveHindi=resolve);}"
    )
    page.locator("#read-hindi").click()
    page.locator("#stop-reading").click()
    page.evaluate("resolveHindi('आपका गाँव सुरक्षित है।')")
    page.wait_for_timeout(100)
    assert page.evaluate("readings.length") == 1
    page.locator("#tablet-mode").click()
    assert page.locator("#command").is_visible()
    page.locator("#easy-reading").click()
    assert not page.locator("#command").is_visible()
    assert page.locator("#action-buttons button").first.is_visible()
    assert not errors, errors
    browser.close()
print(
    "PASS: buttons-only tablet/easy reading, preset names/notes, quantities, automatic saves, hidden activation, Hindi voice/translation, missing voice and stop during translation"
)
