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

UAS = {
    'ytdlp_chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'lynx': 'Lynx/2.9.2 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/3.0.13',
    'w3m': 'w3m/0.5.3+git20230121',
    'links': 'Links (2.29; Linux 6.1.0 x86_64; GNU C 12.2; text)',
    'opera_mini': 'Opera/9.80 (J2ME/MIDP; Opera Mini/9.80 (S60; SymbOS; Opera Mobi/23.348; U; en) Presto/2.5.25 Version/10.54',
    'nokia': 'Nokia6230i/2.0 (03.80) Profile/MIDP-2.0 Configuration/CLDC-1.1',
}
VARIANTS = {
    'vid': {'tbm': 'vid', 'q': Q, 'hl': 'en', 'num': '10'},
    'vid_gbv1': {'tbm': 'vid', 'q': Q, 'hl': 'en', 'num': '10', 'gbv': '1'},
    'udm7': {'udm': '7', 'q': Q, 'hl': 'en'},
}


def summarize(name, r):
    t = r.text
    path = os.path.join(OUT, name + '.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(t)
    marks = {m: (m in t) for m in ('enablejs', '/sorry/', 'unusual traffic', 'dXiKIc', 'pnnext',
                                     '/url?q=', 'consent.google', 'Please click', 'noscript')}
    hrefs = re.findall(r'href="([^"]+)"', t)
    ext = []
    for h in hrefs:
        h = h.replace('&amp;', '&')
        if h.startswith('/url?'):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
            h = (q.get('q') or q.get('url') or [''])[0]
        if h.startswith('http') and not re.match(r'https?://([^/]+\.)?(google|gstatic|googleusercontent|schema)\.', h):
            ext.append(h)
    classes = re.findall(r'<a[^>]* class="([^"]+)"', t)
    print(f'== {name}: status={r.status_code} url={r.url[:120]} len={len(t)}')
    print('   marks:', {k: v for k, v in marks.items() if v})
    print('   ext links:', len(ext))
    for e in dict.fromkeys(ext):
        print('     ', e[:150])
    print('   a-classes:', sorted(set(classes))[:15])
    for m in re.finditer(r'href="(/url\?[^"]+|https?://(?:www\.)?youtube\.com/watch[^"]+)"', t):
        s = max(0, m.start() - 300)
        print('   CONTEXT:', re.sub(r'\s+', ' ', t[s:m.end() + 100])[:500])
        break


for vn, params in VARIANTS.items():
    for un, ua in UAS.items():
        try:
            r = requests.get('https://www.google.com/search', params=params, timeout=20,
                             headers={'User-Agent': ua, 'Accept-Language': 'en-US,en;q=0.9'},
                             cookies={'CONSENT': 'YES+'})
            summarize(f'{vn}__{un}', r)
        except Exception as e:
            print(f'== {vn}__{un}: EXC {e}')
