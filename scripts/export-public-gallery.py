#!/usr/bin/env python3
"""Build a complete public gallery snapshot; never export administrative tabs."""
import csv
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQvPPaZazUa43TBu127nq74y-UMDRRMKdQpOCWOWT6cc5YnsRwcTrzGA7NYM-QbYEnFSkMbdkgkaOn8/pub?output=csv'
NATIVE = 'https://docs.google.com/spreadsheets/d/1peZ5Mf2T_3H1n9UOts7H2u9XQ_osMOgT3mg1Ax7VBaE/export?format=csv'

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read().decode('utf-8-sig')

def sheet_rows(tab):
    gid = str(tab['gid'])
    errors = []
    for url in (PUBLISHED + '&gid=' + gid, NATIVE + '&gid=' + gid):
        try:
            rows = list(csv.reader(io.StringIO(get(url))))
            if len(rows) < 2 or not any('foto' in str(v).lower() for v in rows[0]):
                raise ValueError('Unexpected photo sheet structure')
            # The app parser expects rawRows[0] to be spreadsheet row 2 (A2),
            # because row 1 is only the column header. Including row 1 shifted
            # A2/A3/A4/A5 and made team names, logos and colors cross over.
            headers = rows[0]
            converted = []
            for row in rows[1:]:
                record = {}
                for i, value in enumerate(row):
                    record['Col ' + str(i + 1)] = value
                    if i < len(headers) and headers[i].strip():
                        record[headers[i].strip()] = value
                converted.append(record)
            print('Photo tab', gid, 'rows', len(converted), flush=True)
            return {'name':tab['name'], 'hidden':bool(tab['hidden']), 'rows':converted}
        except Exception as error:
            errors.append(type(error).__name__ + ': ' + str(error)[:120])
    raise RuntimeError('Photo tab ' + gid + ' could not be read: ' + '; '.join(errors))

def export():
    manifest = json.loads((ROOT/'scripts/gallery-source-manifest.json').read_text(encoding='utf-8'))
    assert len(manifest) == 28 and all(not tab['name'].startswith('__') for tab in manifest)
    with ThreadPoolExecutor(max_workers=4) as pool:
        albums = list(pool.map(sheet_rows, manifest))
    assert len(albums) == len(manifest)
    assert sum(len(a['rows']) for a in albums) > 100
    output = {'ok':True,'albums':albums}
    (ROOT/'gallery-snapshot.json').write_text(json.dumps(output, ensure_ascii=False, separators=(',',':')), encoding='utf-8')
    print('Complete gallery snapshot:', len(albums), 'sheets', flush=True)

if __name__ == '__main__': export()
