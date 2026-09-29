#!/usr/bin/env python3
# Temporary probe: fetch Google video search with several client profiles and
# report what comes back. Not part of yt-dlp proper.
import os
import re
import urllib.parse

import requests

Q = 'big buck bunny'
OUT = 'probe_out'
os.makedirs(OUT, exist_ok=True)

import random
import string

def arc():
    return ''.join(random.choices(string.ascii_letters + string.digits + '_-', k=23))

GSA = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/383.0.797833943 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/360.0.642133296 Mobile/15E148 Safari/604.1',
]
LYNX = 'Lynx/2.9.2 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/3.0.13'
A = arc()
CASES = {
    'lynx_vid': (LYNX, {'tbm': 'vid', 'q': Q, 'hl': 'en'}),
    'gsa0_vid_arc': (GSA[0], {'tbm': 'vid', 'q': Q, 'hl': 'en', 'asearch': 'arc', 'async': f'arc_id:srp_{A}_100,use_ac:true,_fmt:prog'}),
    'gsa0_web_arc': (GSA[0], {'q': Q + ' video', 'hl': 'en', 'filter': '0', 'asearch': 'arc', 'async': f'arc_id:srp_{A}_100,use_ac:true,_fmt:prog'}),
    'gsa1_vid_arc': (GSA[1], {'tbm': 'vid', 'q': Q, 'hl': 'en', 'asearch': 'arc', 'async': f'arc_id:srp_{A}_100,use_ac:true,_fmt:prog'}),
    'gsa0_vid_plain': (GSA[0], {'tbm': 'vid', 'q': Q, 'hl': 'en'}),
    'gsa0_udm7_arc': (GSA[0], {'udm': '7', 'q': Q, 'hl': 'en', 'asearch': 'arc', 'async': f'arc_id:srp_{A}_100,use_ac:true,_fmt:prog'}),
}


def summarize(name, r):
    t = r.text
    path = os.path.join(OUT, name + '.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(t)
    marks = {m: (m in t) for m in ('enablejs', '/sorry/', 'unusual traffic', 'dXiKIc', 'pnnext',
                                     '/url?q=', 'consent.google', 'Please click', 'noscript', 'MjjYud', '<h3')}
    hrefs = re.findall(r'href="([^"]+)"', t)
    ext = []
    for h in hrefs:
        h = h.replace('&amp;', '&')
        if h.startswith('/url?'):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
            h = (q.get('q') or q.get('url') or [''])[0]
        if h.startswith('http') and not re.match(r'https?://([^/]+\.)?(google|gstatic|googleusercontent|schema)\.', h):
            ext.append(h)
    print(f'== {name}: status={r.status_code} url={r.url[:160]} len={len(t)}')
    print('   marks:', {k: v for k, v in marks.items() if v})
    print('   ext links:', len(ext))
    for e in list(dict.fromkeys(ext))[:15]:
        print('     ', e[:150])
    if len(t) < 5000:
        print('   BODY:', re.sub(r'\s+', ' ', t)[:2500])
    m = re.search(r'href="(/url\?[^"]+|https?://(?:www\.)?youtube\.com/watch[^"]+)"', t)
    if m:
        s0 = max(0, m.start() - 600)
        print('   CONTEXT:', re.sub(r'\s+', ' ', t[s0:m.end() + 400])[:1200])


for name, (ua, params) in CASES.items():
    try:
        r = requests.get('https://www.google.com/search', params=params, timeout=20,
                         headers={'User-Agent': ua, 'Accept-Language': 'en-US,en;q=0.9', 'Accept': '*/*'},
                         cookies={'CONSENT': 'YES+'})
        summarize(name, r)
    except Exception as e:
        print(f'== {name}: EXC {e}')
