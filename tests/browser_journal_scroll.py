"""Follow short responses, preserve long passages and earlier reading positions."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1050})
    errors = []
    page.on('pageerror', lambda err: errors.append(str(err)))
    page.goto('http://127.0.0.1:5000')
    page.locator('[data-play]').click()
    page.get_by_role('button', name='Begin adventure').click()
    page.wait_for_function("packet?.prompt === 'Village > ' && !busy")
    page.evaluate("()=>{for(let i=0;i<45;i++)append('Journal entry '+i);document.querySelector('#terminal').scrollTop=document.querySelector('#terminal').scrollHeight;}")

    def top():
        return page.locator('#terminal').evaluate('e=>e.scrollTop')

    def at_bottom():
        return page.locator('#terminal').evaluate('e=>e.scrollHeight-e.scrollTop-e.clientHeight<3')

    def output(text):
        page.evaluate('text=>apply({...packet,output:[{id:cursor,text}]})', text)

    before = top()
    output('You found one herb.')
    assert top() > before
    assert at_bottom()

    before = top()
    output('\n'.join('A long story passage, line '+str(i) for i in range(25)))
    assert abs(top()-before) < 2
    assert not at_bottom()

    page.evaluate("document.querySelector('#terminal').scrollTop=100")
    before = top()
    output('One brief reply while reading earlier text.')
    assert abs(top()-before) < 2
    page.locator('#latest-output').click()
    assert at_bottom()

    # A response containing many short lines is still a long response.
    before = top()
    page.evaluate("apply({...packet,output:Array.from({length:20},(_,i)=>({id:cursor+i,text:'Menu option '+i}))})")
    assert abs(top()-before) < 2

    page.set_viewport_size({'width': 390, 'height': 844})
    page.locator('#latest-output').click()
    before = top()
    output('This is one long printed line that wraps into many visible lines on a phone. '*30)
    assert abs(top()-before) < 2
    page.locator('#latest-output').click()
    before = top()
    output('Found a herb.')
    assert top() > before
    assert at_bottom()

    # The player's echoed answer must not accidentally stop short following.
    page.evaluate("""()=>{
      const original=window.fetch;
      window.fetch=async(url,...args)=>{
        if(String(url).endsWith('/input'))return {ok:true,json:async()=>({...packet,output:[{id:cursor,text:'Purchase complete.'}]})};
        return original(url,...args);
      };
    }""")
    page.evaluate("async()=>{await respond('1');}")
    page.wait_for_function("(()=>{const e=document.querySelector('#terminal');return e.scrollHeight-e.scrollTop-e.clientHeight<3;})()")

    # Scrolling up while a response is in flight must win over auto-follow.
    page.evaluate("""()=>{
      const original=window.fetch;
      window.fetch=async(url,...args)=>{
        if(String(url).endsWith('/input')){
          await new Promise(resolve=>setTimeout(resolve,250));
          return {ok:true,json:async()=>({...packet,output:[{id:cursor,text:'Another short reply.'}]})};
        }
        return original(url,...args);
      };
      respond('1');
    }""")
    page.evaluate("document.querySelector('#terminal').scrollTop=100")
    page.wait_for_function('!busy')
    assert abs(top()-100) < 2
    assert not errors, errors
    print('PASS: short replies follow, long text stays, reading history stays, response batches and mobile wrapping count, Latest works, command echoes and in-flight reading respected')
    browser.close()
