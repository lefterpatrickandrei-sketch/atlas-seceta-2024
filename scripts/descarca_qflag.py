"""T4 (ticket robustețe), pasul 1: descarcă QFLAG HR-VPP, sezonul 1, tile T34TGP, 2017–2024.

Aceeași logică ca notebooks/03a_download_hrvpp.ipynb (celulele 1–5), doar cu parametrul QFLAG.
Credențialele se citesc din .env și nu se afișează. Termenii CLMS nu se acceptă de aici: dacă nu sunt
acceptați, scriptul se oprește. Fișierele merg în data/raw/hrvpp/, lângă TPROD.

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/descarca_qflag.py [--doar-cautare]
"""
import json
import logging
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT)]
os.chdir(ROOT)

import requests  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from hda.api import SearchResults  # noqa: E402

from gisday_config import AOI_BBOX, BASE_YEARS, RAW, YEAR  # noqa: E402
from gisday_lib import is_complete, wekeo_client  # noqa: E402

load_dotenv(ROOT / '.env', override=True)
logging.basicConfig(level=logging.INFO)
logging.getLogger('hda').setLevel(logging.INFO)   # niciodată DEBUG: la DEBUG, hda scrie tokenul în log

DATASET_ID = 'EO:EEA:DAT:CLMS_HRVPP_VPP'
PARAM_VAL, SEASON_VAL, TILE = 'QFLAG', 's1', 'T34TGP'
YEARS = list(BASE_YEARS) + [YEAR]
HRVPP_DIR = RAW / 'hrvpp'
VERSION = {y: ('V101' if y <= 2020 else 'V105') for y in YEARS}   # aceleași versiuni ca TPROD de pe disc


def valori(schema):
    out = []
    if isinstance(schema, dict):
        for k, x in schema.items():
            out += [str(x)] if k == 'const' else valori(x)
    elif isinstance(schema, list):
        for x in schema:
            out += valori(x)
    return out


def main():
    c = wekeo_client(os.environ)
    try:
        terms = c.dataset(DATASET_ID)['terms']
    except requests.HTTPError as e:
        raise SystemExit(f'Oprire: autentificare/acces WEkEO eșuat (HTTP {e.response.status_code}). '
                         'Verifică WEKEO_TOKEN sau WEKEO_USER/WEKEO_PASSWORD în .env.') from None
    for t in terms:
        try:
            ok = bool(c.get('termsaccepted', t).get('accepted'))
        except requests.HTTPError:
            ok = False
        if not ok:
            raise SystemExit(f'Oprire: termenul {t} nu e acceptat în contul WEkEO.')

    props = c.metadata(DATASET_ID).get('properties', {})
    product_param = next((n for n, s in props.items() if PARAM_VAL in valori(s)), None)
    season_param = next((n for n, s in props.items() if SEASON_VAL in [v.lower() for v in valori(s)]), None)
    if not product_param or not season_param:
        raise SystemExit(f'Oprire: QFLAG nu apare printre valorile permise ale dataset-ului {DATASET_ID}.')
    season_value = next(v for v in valori(props[season_param]) if v.lower() == SEASON_VAL)
    as_value = lambda n, v: [v] if props[n].get('type') == 'array' else v  # noqa: E731

    found, problems = {}, []
    for y in YEARS:
        q = {'dataset_id': DATASET_ID, 'bbox': list(AOI_BBOX),
             'startdate': f'{y}-01-01T00:00:00.000Z', 'enddate': f'{y}-12-31T23:59:59.999Z',
             product_param: as_value(product_param, PARAM_VAL), season_param: as_value(season_param, season_value)}
        res = c.search(q)
        hits = [r for r in res.results if str(r['properties'].get('startdate', ''))[:4] == str(y) and TILE in r['id']]
        good = [r for r in hits if f'_{VERSION[y]}_' in r['id']]
        found[y] = good
        print(y, VERSION[y], 'găsite:', [r['id'] for r in hits])
        if not good:
            problems.append(f'{y}: nu există QFLAG {VERSION[y]} pentru {TILE}')
    (HRVPP_DIR / 'search_results_qflag.json').write_text(json.dumps(
        {y: [{'id': r['id'], 'size': r['properties'].get('size')} for r in v] for y, v in found.items()}, indent=1), encoding='utf-8')
    if problems:
        raise SystemExit('Oprire: ' + '; '.join(problems))
    if '--doar-cautare' in sys.argv:
        return

    todo = [r for v in found.values() for r in v if not is_complete(HRVPP_DIR, r['id'], r['properties'].get('size'))]
    print(len(todo), 'de descărcat')
    if todo:
        SearchResults(c, todo, DATASET_ID).download(str(HRVPP_DIR))
    for z in HRVPP_DIR.glob('*QFLAG*.zip'):
        with zipfile.ZipFile(z) as zf:
            zf.extractall(HRVPP_DIR)
    lipsa = [r['id'] for v in found.values() for r in v if not is_complete(HRVPP_DIR, r['id'], r['properties'].get('size'))]
    print('lipsă după descărcare:', lipsa or 'nimic')
    print(sorted(p.name for p in HRVPP_DIR.glob('*QFLAG*.tif')))


if __name__ == '__main__':
    main()
