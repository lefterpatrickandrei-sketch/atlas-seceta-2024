"""Test local pentru web/: pagina se deschide, parcelele apar, atingerea deschide fereastra, nu există scroll orizontal la 390 px.

Pornește un server static local pe web/, deschide pagina în Microsoft Edge prin Playwright (ecran de telefon 390 × 844, atingere),
numără octeții transferați la încărcare și salvează o captură mică în data/interim/preview/.
Testul e „din exterior”: parcelele se recunosc după culorile claselor din web/date/meta.json, nu prin codul paginii.

Cere Playwright, care nu e în .venv-ul proiectului; în orice mediu cu `pip install playwright` și cu Edge instalat:
  python -X utf8 scripts/test_web.py                 # local, pe web/
  python -X utf8 scripts/test_web.py https://...     # pe adresa publică
"""
import functools
import http.server
import io
import json
import sys
import threading
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
SHOT = ROOT / 'data' / 'interim' / 'preview' / 'web_390.png'
WIDTH, HEIGHT = 390, 844


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(QuietHandler, directory=str(WEB))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def class_pixels(png, colors):
    """Câți pixeli din hartă au exact culoarea (±12) uneia dintre clasele de umplere, amestecată cu fundalul la opacitatea 0,9."""
    a = np.asarray(Image.open(io.BytesIO(png)).convert('RGB'), dtype=int)
    hits = {}
    for code, hexc in colors.items():
        rgb = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)])
        target = rgb * 0.9 + np.array([12, 12, 12]) * 0.1
        hits[code] = np.argwhere(np.abs(a - target).max(axis=2) <= 12)
    return hits


def main():
    meta = json.loads((WEB / 'date' / 'meta.json').read_text(encoding='utf-8'))
    fill = {c['cod']: c['culoare'] for c in meta['legenda'] if c['tip'] == 'umplere'}
    server = None if len(sys.argv) > 1 else serve()
    url = sys.argv[1] if server is None else f'http://127.0.0.1:{server.server_address[1]}/'
    report_url = {'adresa_testata': url}
    report, errors, transfer = {}, [], {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True,
                                    args=['--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--ignore-gpu-blocklist'])
        context = browser.new_context(viewport={'width': WIDTH, 'height': HEIGHT}, device_scale_factor=1, is_mobile=True, has_touch=True,
                                      locale='ro-RO')
        page = context.new_page()
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        cdp = context.new_cdp_session(page)
        cdp.send('Network.enable')
        urls = {}
        cdp.on('Network.responseReceived', lambda e: urls.__setitem__(e['requestId'], e['response']['url']))
        cdp.on('Network.loadingFinished', lambda e: transfer.__setitem__(urls.get(e['requestId'], '?'), transfer.get(urls.get(e['requestId'], '?'), 0) + e['encodedDataLength']))

        page.goto(url, wait_until='load')
        page.wait_for_function("document.getElementById('stare').hidden === true", timeout=90000)
        page.wait_for_timeout(1500)
        report['titlu'] = page.title()

        # Parcelele apar: pixeli în culorile claselor, în afara legendei
        png = page.screenshot()
        legend_box = page.locator('.legenda').bounding_box()
        map_box = page.locator('#harta').bounding_box()
        hits = class_pixels(png, fill)
        report['pixeli_pe_clase'] = {k: int(len(v)) for k, v in hits.items()}

        # Atingere în interiorul unei parcele colorate (nu gri: grii se confundă cu drumurile de pe fundal), departe de legendă și de controale
        colored = [k for k in (3, 4, 5, 2, 0) if k in hits]
        best = max(colored, key=lambda k: len(hits[k]))
        mask = np.zeros((HEIGHT, WIDTH), bool)
        mask[hits[best][:, 0], hits[best][:, 1]] = True
        candidates = [(y, x) for y, x in hits[best]
                      if map_box['y'] + 20 < y < map_box['y'] + map_box['height'] - 40 and 20 < x < WIDTH - 60
                      and not (legend_box['x'] <= x <= legend_box['x'] + legend_box['width'] and legend_box['y'] <= y <= legend_box['y'] + legend_box['height'] + 10)
                      and mask[y - 2:y + 3, x - 2:x + 3].all()]
        report['candidati_atingere'] = len(candidates)
        y, x = candidates[len(candidates) // 2]
        page.touchscreen.tap(float(x), float(y))
        popup = page.locator('.maplibregl-popup-content')
        try:
            popup.wait_for(timeout=10000)
        except Exception:
            print(json.dumps(report, ensure_ascii=False), '| fara fereastra dupa atingere | erori', errors[:5])
            raise
        lines = popup.locator('p').all_inner_texts()
        report['atingere'] = {'punct': [int(x), int(y)], 'clasa_atinsa': int(best), 'randuri': lines}
        report['fereastra_ok'] = (len(lines) in (2, 3) and lines[-1].startswith('Suprafață: ') and lines[-1].endswith(' ha')
                                  and any(l.startswith('Grup de cultură 2024: ') for l in lines) == (best <= 6))

        # Scroll orizontal: documentul și fiecare element vizibil trebuie să încapă în 390 px
        report['latime'] = page.evaluate("""() => {
            const w = window.innerWidth;
            const over = [...document.querySelectorAll('body *')].filter(el => {
                const r = el.getBoundingClientRect();
                return r.width > 0 && (r.right > w + 0.5 || r.left < -0.5);
            }).map(el => el.tagName + '.' + el.className);
            return {innerWidth: w, scrollWidth: document.documentElement.scrollWidth, bodyScrollWidth: document.body.scrollWidth, elemente_in_afara: over.slice(0, 5)};
        }""")
        page.screenshot(path=str(SHOT))
        browser.close()
    if server is not None:
        server.shutdown()

    by_host = {}
    for u, n in transfer.items():
        host = u.split('/')[2] if '://' in u else u
        by_host[host] = by_host.get(host, 0) + n
    report['transfer_mb'] = round(sum(transfer.values()) / 1e6, 2)
    report['transfer_pe_gazda_kb'] = {h: round(n / 1e3) for h, n in sorted(by_host.items(), key=lambda kv: -kv[1])}
    report['erori_consola'] = errors
    report.update(report_url)
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
