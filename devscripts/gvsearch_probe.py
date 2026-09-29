#!/usr/bin/env python3
# Temporary probe: load Google video search in a real headless Chromium from a
# GitHub runner and report whether results or a CAPTCHA come back.
import os
import re
import urllib.parse

from playwright.sync_api import sync_playwright

Q = 'big buck bunny'
OUT = 'probe_out'
os.makedirs(OUT, exist_ok=True)

URLS = {
    'vid': 'https://www.google.com/search?' + urllib.parse.urlencode({'q': Q, 'tbm': 'vid', 'hl': 'en', 'num': '20'}),
    'web': 'https://www.google.com/search?' + urllib.parse.urlencode({'q': Q, 'hl': 'en'}),
}

with sync_playwright() as p:
    for headless in (True, False):
        browser = p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
        ctx = browser.new_context(locale='en-US', viewport={'width': 1280, 'height': 900})
        ctx.add_cookies([{'name': 'SOCS', 'value': 'CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg', 'domain': '.google.com', 'path': '/'}])
        page = ctx.new_page()
        for name, url in URLS.items():
            tag = f'{name}_{"headless" if headless else "headed"}'
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(3000)
                html = page.content()
            except Exception as e:
                print(f'== {tag}: EXC {e}')
                continue
            open(os.path.join(OUT, tag + '.html'), 'w', encoding='utf-8').write(html)
            page.screenshot(path=os.path.join(OUT, tag + '.png'))
            hrefs = page.eval_on_selector_all('a[href]', 'els => els.map(e => e.href)')
            ext = [h for h in hrefs if h.startswith('http') and not re.match(
                r'https?://([^/]+\.)?(google|gstatic|googleusercontent|schema|youtube\.com/(about|t/|howyoutubeworks))', h)]
            print(f'== {tag}: url={page.url[:150]} len={len(html)} title={page.title()!r}')
            print('   marks:', [m for m in ('/sorry/', 'unusual traffic', 'recaptcha', 'enablejs', 'Update your browser') if m in html or m in page.url])
            print('   ext links:', len(set(ext)))
            for e in list(dict.fromkeys(ext))[:20]:
                print('     ', e[:160])
            # structure hints around the first external link
            m = re.search(r'<a[^>]+href="https?://(?!(?:[^/"]+\.)?(?:google|gstatic))[^"]+"[^>]*>', html)
            if m:
                s0 = max(0, m.start() - 800)
                print('   CONTEXT:', re.sub(r'\s+', ' ', html[s0:m.end() + 300])[:1500])
        browser.close()
