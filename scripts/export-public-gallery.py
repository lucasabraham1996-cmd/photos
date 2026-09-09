#!/usr/bin/env python3
"""Build a public gallery snapshot from the published Google Sheets tabs."""
import csv
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

HTML_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQvPPaZazUa43TBu127nq74y-UMDRRMKdQpOCWOWT6cc5YnsRwcTrzGA7NYM-QbYEnFSkMbdkgkaOn8/pubhtml'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'gid=' in attrs.get('href', ''):
            self.current = {'href': attrs['href'], 'text': ''}
    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8-sig')

def discover(html):
    parser = Links(); parser.feed(html)
    found = []
    for link in parser.links:
        gid = urllib.parse.parse_qs(urllib.parse.urlsplit(link['href']).query).get('gid', [''])[0]
        if gid and gid.isdigit() and gid not in [v['gid'] for v in found]:
            found.append({'gid': gid, 'name': link['text'].strip()})
    return found

def export():
    html = get(HTML_URL)
    tabs = discover(html)
    print('Published tabs:', json.dumps(tabs, ensure_ascii=False))
    if not tabs:
        raise RuntimeError('No published sheet tabs were found; refusing to publish a partial gallery.')
    albums = []
    for tab in tabs:
        url = HTML_URL.replace('/pubhtml', '/pub') + '?output=csv&gid=' + tab['gid']
        rows = list(csv.reader(io.StringIO(get(url))))
        if not rows:
            continue
        # Keep both positional and named columns to match the existing parser.
        headers = rows[0]
        converted = []
        for row in rows:
            record = {}
            for i, value in enumerate(row):
                record['Col ' + str(i+1)] = value
                if i < len(headers) and headers[i].strip():
                    record[headers[i].strip()] = value
            converted.append(record)
        albums.append({'name': tab['name'], 'rows': converted})
        print('Tab', tab['gid'], 'rows:', len(converted), 'columns:', max(map(len, rows)))
    if not albums:
        raise RuntimeError('All published tabs were empty; refusing to replace a good snapshot.')
    Path('gallery-snapshot.json').write_text(json.dumps({'ok': True, 'albums': albums}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('Snapshot sheets:', len(albums))

if __name__ == '__main__':
    export()
