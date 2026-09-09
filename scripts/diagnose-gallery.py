#!/usr/bin/env python3
"""Check public gallery sources without printing customer or photo records."""
import json
import re
import time
import urllib.request
from pathlib import Path

s = Path('index.html').read_text(encoding='utf-8')
def constant(name):
    return re.search(r'const ' + name + r' = "([^"]+)";', s).group(1)

def check(label, url, parse):
    started = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
            text = raw.decode('utf-8-sig')
            result = parse(text)
            print(json.dumps({'source': label, 'status': response.status, 'bytes': len(raw), 'seconds': round(time.monotonic()-started, 2), 'content_type': response.headers.get('Content-Type'), **result}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'source': label, 'seconds': round(time.monotonic()-started, 2), 'error': type(e).__name__, 'detail': str(e)[:250]}, ensure_ascii=False))

def script_result(text):
    text = re.sub(r'^\s*[\w.]+\s*\(', '', text, count=1).rstrip().rstrip(';')
    if text.endswith(')'): text = text[:-1]
    data = json.loads(text)
    albums = data.get('albums', []) if isinstance(data, dict) else data
    return {'ok': data.get('ok') if isinstance(data, dict) else None, 'error': str(data.get('error', ''))[:250] if isinstance(data, dict) else '', 'sheets': len(albums) if isinstance(albums, list) else 0, 'rows': sum(len(a.get('rows', a.get('photos', a.get('data', [])))) for a in albums if isinstance(a, dict)) if isinstance(albums, list) else 0}

def gviz_result(text):
    match = re.search(r'google\.visualization\.Query\.setResponse\((.*)\);?\s*$', text, re.S)
    data = json.loads(match.group(1) if match else text)
    return {'status': data.get('status'), 'rows': len(data.get('table', {}).get('rows', [])), 'errors': [str(e.get('reason', '')) for e in data.get('errors', [])]}

check('apps-script', constant('APPS_SCRIPT_URL') + '?action=getGalleryData&callback=diagnostic', script_result)
check('published-csv', constant('FALLBACK_PUBLISHED_SHEET_URL'), lambda t: {'rows': len(t.splitlines())})
check('published-gviz', constant('FALLBACK_PUBLISHED_SHEET_URL').replace('/pub?output=csv', '/gviz/tq') + '?tqx=out:json', gviz_result)
