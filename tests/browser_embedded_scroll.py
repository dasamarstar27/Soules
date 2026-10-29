"""Replit-style iframe and resized toolbar; short actions resume after long text."""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"]
    )
    page = browser.new_page(viewport={"width": 1200, "height": 1000})
    page.set_content(
        '<iframe src="http://127.0.0.1:5000" style="width:900px;height:700px;border:0"></iframe>'
    )
    frame = page.frames[1]
    frame.locator("[data-play]").click()
    frame.get_by_role("button", name="Begin adventure").click()
    frame.wait_for_function("packet?.prompt==='Village > '&&!busy")
    frame.evaluate(
        "()=>{for(let i=0;i<60;i++)append('Earlier line '+i);$('#terminal').scrollTop=$('#terminal').scrollHeight;}"
    )
    frame.evaluate(
        "apply({...packet,output:[{id:cursor,text:Array.from({length:100},(_,i)=>'Long story '+i).join('\\n')}]})"
    )
    assert frame.evaluate("!journalNearBottom($('#terminal'))")
    frame.evaluate(
        """()=>{const original=window.fetch;window.fetch=async(url,...args)=>String(url).endsWith('/input')?{ok:true,json:async()=>({...packet,output:[{id:cursor,text:'1. Attack\\n2. Defend\\n0. Back'}]})}:original(url,...args);}"""
    )
    frame.evaluate("async()=>await respond('1')")
    frame.wait_for_function("journalNearBottom($('#terminal'))")
    before = page.evaluate("scrollY")
    frame.locator("#command").focus()
    assert page.evaluate("scrollY") == before
    page.locator("iframe").evaluate("el=>el.style.width='780px'")
    frame.wait_for_timeout(100)
    assert frame.evaluate(
        "Math.abs($('.layout').getBoundingClientRect().bottom-innerHeight)<3"
    )
    frame.evaluate("$('#terminal').scrollTop=60")
    frame.evaluate(
        "apply({...packet,output:[{id:cursor,text:'Passive polling update.'}]})"
    )
    assert frame.evaluate("Math.abs($('#terminal').scrollTop-60)<2")
    browser.close()
print(
    "PASS: embedded preview, long-text preservation, next-action follow, no outer focus jump, toolbar resize and passive reading position"
)
