"""Grafic 1920×1080 (stilul render/): sfârșitul sezonului de vegetație (HR-VPP EOSD, sezonul 1) pe ani, primăvară și toamnă,
plus diferența 2024 față de anii comparabili cu ambele referințe (2017–2023 și 2021–2023). Doar date reale.

Cifrele vin din data/out/eos_metrics.json; banda P25–P75 pe ani se calculează din data/out/parcel_eos.parquet
și medianele se verifică față de JSON.
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 render/sfarsit_sezon.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import ImageDraw  # noqa: E402

from common import (AMBER, GRID, LINE, MUTED, ORANGE, TXT, TXT2, F, Layer, card, doy_label, draw_footer, draw_header, fmt_dec,  # noqa: E402
                    fmt_int, new_canvas, section_label)
from gisday_config import BASE_YEARS, OUT, YEAR  # noqa: E402
from gisday_lib import crop_group  # noqa: E402

YEARS = list(BASE_YEARS) + [YEAR]
SPRING_RGB, AUTUMN_RGB = ORANGE, (64, 178, 148)       # aceleași culori ca în tprod_pe_ani.png
GROUPS = (('primavara', 'Primăvară', SPRING_RGB), ('toamna', 'Toamnă', AUTUMN_RGB))
DAY_MIN, DAY_MAX = 121, 274                            # 1 mai – 1 octombrie (zi într-un an nebisect)
TICKS = (121, 152, 182, 213, 244, 274)


def date_text(day):
    return doy_label(int(round(day)), year=2023, short=True)


def signed(v):
    return ('−' if v < 0 else '+' if v > 0 else '') + fmt_dec(abs(v), 1)


def yearly_bands(metrics):
    """Mediana și P25–P75 ale EOSD pe ani, pe parcelele din set care au avut grupa respectivă în acel an (ca în eos_metrics.json)."""
    T = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'is_arable', 'tip_cultura_2024', 'loss_rel']]
    Fe = pd.read_parquet(OUT / 'parcel_features.parquet', columns=['parcel_id', 'ndvi_04'] + [f'ndvi_apr_{y}' for y in BASE_YEARS])
    E = pd.read_parquet(OUT / 'parcel_eos.parquet')[['parcel_id'] + [f'eosd_{y}' for y in YEARS]]
    D = T.merge(Fe, on='parcel_id').merge(E, on='parcel_id')
    sample = D.is_arable & D.loss_rel.notna() & D.tip_cultura_2024.isin([g for g, _, _ in GROUPS])
    out = {}
    for g, _, _ in GROUPS:
        rows = []
        for y in YEARS:
            grp = crop_group(D['ndvi_04'] if y == YEAR else D[f'ndvi_apr_{y}'])
            v = D.loc[sample & grp.eq(g), f'eosd_{y}'].dropna()
            p25, p50, p75 = np.percentile(v, [25, 50, 75])
            assert round(float(p50), 1) == metrics['pe_an'][g][str(y)]['eosd_mediana'], f'mediana {g} {y} nu se potrivește cu JSON'
            rows.append({'year': y, 'p25': p25, 'p50': p50, 'p75': p75, 'n': len(v)})
        out[g] = rows
    return out


def draw_chart(img, box, bands, versions):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    cx0, cy0, cx1, cy1 = x0 + 96, y0 + 96, x1 - 52, y1 - 92

    def px_x(i):
        return cx0 + 36 + i * (cx1 - cx0 - 72) / (len(YEARS) - 1)     # punctele nu ating axa și etichetele ei

    def px_y(day):
        return cy1 - (day - DAY_MIN) / (DAY_MAX - DAY_MIN) * (cy1 - cy0)

    section_label(d, x0 + 24, y0 + 16, 'Data mediană a sfârșitului sezonului de vegetație')
    lx = x0 + 24
    for _, name, color in GROUPS[::-1]:
        text = f'{name} (mediană și P25–P75)'
        d.rounded_rectangle((lx, y0 + 52, lx + 22, y0 + 63), radius=3, fill=color)
        d.text((lx + 30, y0 + 48), text, font=F(14, 'Medium'), fill=TXT)
        lx += 30 + F(14, 'Medium').getlength(text) + 28

    for day in TICKS:
        y = px_y(day)
        d.line((cx0, y, cx1, y), fill=GRID, width=1)
        label = f'1 {date_text(day).split()[1]}'
        d.text((cx0 - 14 - F(14).getlength(label), y - 9), label, font=F(14), fill=MUTED)

    x24 = px_x(len(YEARS) - 1)
    d.rounded_rectangle((x24 - 40, cy0 - 10, x24 + 36, cy1 + 8), radius=8, fill=(44, 28, 28), outline=(185, 82, 64), width=2)
    split = (px_x(3) + px_x(4)) / 2                    # între 2020 (V101) și 2021 (V105)
    for y in range(int(cy0), int(cy1), 14):
        d.line((split, y, split, min(y + 7, cy1)), fill=LINE, width=1)

    for g, _, color in GROUPS:          # fiecare bandă în stratul ei: în același strat PIL suprascrie, nu amestecă
        band = Layer(x1 - x0, y1 - y0)
        upper = [(px_x(i) - x0, px_y(r['p75']) - y0) for i, r in enumerate(bands[g])]
        lower = [(px_x(i) - x0, px_y(r['p25']) - y0) for i, r in enumerate(bands[g])][::-1]
        band.poly(upper + lower, fill=color + (46,))
        img.alpha_composite(band.get(), (x0, y0))
    layer = Layer(x1 - x0, y1 - y0)
    for g, _, color in GROUPS:
        rows = bands[g]
        med = [(px_x(i) - x0, px_y(r['p50']) - y0) for i, r in enumerate(rows)]
        layer.line(med, fill=color + (255,), width=4)
        for i, (mx, my) in enumerate(med):
            last = i == len(YEARS) - 1
            layer.circle(mx, my, 7 if last else 5, fill=color + (255,), outline=TXT + (255,), width=2 if last else 1)
    img.alpha_composite(layer.get(), (x0, y0))

    for i in range(len(YEARS)):
        for g, _, _ in GROUPS:
            r = bands[g][i]
            other = bands['toamna' if g == 'primavara' else 'primavara'][i]
            dy = -26 if r['p50'] >= other['p50'] else 10
            text = date_text(r['p50'])
            font = F(15, 'Bold') if YEARS[i] == YEAR else F(14, 'SemiBold')
            d.text((px_x(i) - font.getlength(text) / 2, px_y(r['p50']) + dy), text, font=font, fill=TXT)

    d.line((cx0, cy1, cx1, cy1), fill=LINE, width=2)
    for i, y in enumerate(YEARS):
        xx = px_x(i)
        font = F(16, 'Bold') if y == YEAR else F(15, 'Medium')
        d.text((xx - font.getlength(str(y)) / 2, cy1 + 14), str(y), font=font, fill=AMBER if y == YEAR else TXT)
        tag = versions[str(y)]
        d.text((xx - F(11).getlength(tag) / 2, cy1 + 36), tag, font=F(11), fill=MUTED)
    note = 'linia punctată: schimbarea versiunii HR-VPP (V101 → V105)'
    d.text((cx1 - F(13).getlength(note), cy1 + 58), note, font=F(13), fill=MUTED)


def draw_difference(img, metrics):
    d = ImageDraw.Draw(img)
    x, xr = 1300, 1836
    card(img, (1280, 200, 1856, 610))
    section_label(d, x, 216, '2024 față de anii comparabili')
    spring = metrics['pe_grupe']['primavara']['eosd']
    v105 = metrics['versiuni_v101_v105']
    prudent = v105['primavara']['eosd']
    big = F(56, 'Bold', True)
    headline = f"−{round(abs(prudent['mediana_ref_doar_v105_2021_2023'])):d} zile"
    d.text((x, 244), headline, font=big, fill=AMBER)
    tx = x + big.getlength(headline) + 18
    d.text((tx, 254), 'primăvară, față de 2021–2023', font=F(16, 'SemiBold'), fill=TXT)
    d.text((tx, 276), '(aceeași versiune HR-VPP ca 2024)', font=F(14), fill=TXT2)
    ci = prudent['ic95_ref_doar_v105']
    d.text((tx, 296), f"{signed(prudent['mediana_ref_doar_v105_2021_2023'])} zile, IC 95%: {signed(ci[0])}…{signed(ci[1])}", font=F(14), fill=TXT2)

    rows = (
        ('Primăvară · ref. 2021–2023', prudent['mediana_ref_doar_v105_2021_2023'], ci, prudent['n_parcele_comune'], SPRING_RGB, True),
        ('Primăvară · ref. 2017–2023', spring['mediana_zile'], spring['ic95_zile'], spring['n'], SPRING_RGB, False),
        ('Toamnă · ref. 2021–2023', v105['toamna']['eosd']['mediana_ref_doar_v105_2021_2023'], v105['toamna']['eosd']['ic95_ref_doar_v105'],
         v105['toamna']['eosd']['n_parcele_comune'], AUTUMN_RGB, False),
        ('Toamnă · ref. 2017–2023', metrics['pe_grupe']['toamna']['eosd']['mediana_zile'], metrics['pe_grupe']['toamna']['eosd']['ic95_zile'],
         metrics['pe_grupe']['toamna']['eosd']['n'], AUTUMN_RGB, False),
    )
    px0, px1, lo, hi = 1530, 1772, -25.0, 0.0

    def to_x(v):
        return px0 + (v - lo) / (hi - lo) * (px1 - px0)

    top = 352
    d.text((xr - F(12, 'SemiBold').getlength('mediana'), top - 22), 'mediana', font=F(12, 'SemiBold'), fill=MUTED)
    for tick in (-25, -20, -15, -10, -5, 0):
        xx = to_x(tick)
        d.line((xx, top - 4, xx, top + 4 * 46 - 10), fill=LINE if tick == 0 else GRID, width=2 if tick == 0 else 1)
        label = '0' if tick == 0 else f'−{abs(tick)}'
        d.text((xx - F(12).getlength(label) / 2, top + 4 * 46 - 4), label, font=F(12), fill=MUTED)
    d.text((px0, top + 4 * 46 + 14), 'zile față de referință (IC 95%)', font=F(12), fill=MUTED)
    layer = Layer(1920, 1080)
    for i, (name, med, interval, n, color, highlight) in enumerate(rows):
        yc = top + 14 + i * 46
        if highlight:
            d.rounded_rectangle((x - 8, yc - 20, xr + 6, yc + 20), radius=6, outline=AMBER, width=1)
        d.text((x, yc - 17), name, font=F(14, 'SemiBold' if highlight else 'Medium'), fill=TXT)
        d.text((x, yc + 1), f'{fmt_int(n)} parcele', font=F(12), fill=MUTED)
        layer.line([(to_x(interval[0]), yc), (to_x(interval[1]), yc)], fill=TXT + (255,), width=2)
        layer.circle(to_x(med), yc, 6, fill=color + (255,), outline=TXT + (255,), width=1)
        value = signed(med)
        d.text((xr - F(15, 'Bold').getlength(value), yc - 10), value, font=F(15, 'Bold'), fill=TXT)
    img.alpha_composite(layer.get())


def draw_reading(img, metrics):
    d = ImageDraw.Draw(img)
    x = 1300
    card(img, (1280, 626, 1856, 988))
    section_label(d, x, 642, 'Durata sezonului și citire')
    sp, au = metrics['pe_grupe']['primavara']['length'], metrics['pe_grupe']['toamna']['length']
    v105 = metrics['versiuni_v101_v105']
    sp5, au5 = v105['primavara']['length'], v105['toamna']['length']
    lines = (
        (0, 'Durata sezonului de vegetație (LENGTH), 2024 față de referință:', 'SemiBold', 15, TXT),
        (26, f"primăvară {signed(sp['mediana_zile'])} zile (2017–2023), dar {signed(sp5['mediana_ref_doar_v105_2021_2023'])}", 'Regular', 15, TXT2),
        (48, f"față de 2021–2023 (IC 95%: {signed(sp5['ic95_ref_doar_v105'][0])}…{signed(sp5['ic95_ref_doar_v105'][1])}): scurtarea nu e sigură;", 'Regular', 15, TXT2),
        (70, f"toamnă {signed(au['mediana_zile'])} și {signed(au5['mediana_ref_doar_v105_2021_2023'])} zile.", 'Regular', 15, TXT2),
        (112, 'La ambele grupe, 2024 e cel mai devreme an din serie.', 'SemiBold', 17, TXT),
        (140, 'Cu referința 2017–2023 diferența e mai mare, fiindcă anii', 'Regular', 15, TXT2),
        (162, '2017–2019 au avut sfârșituri mai târzii. Pe vegetația', 'Regular', 15, TXT2),
        (184, 'permanentă nu apare un salt între versiuni, dar cifra prudentă', 'Regular', 15, TXT2),
        (206, 'compară 2024 doar cu anii din aceeași versiune (2021–2023).', 'Regular', 15, TXT2),
    )
    for offset, text, weight, size, color in lines:
        d.text((x, 674 + offset), text, font=F(size, weight), fill=color)


def main():
    metrics = json.loads((OUT / 'eos_metrics.json').read_text(encoding='utf-8'))
    bands = yearly_bands(metrics)
    img = new_canvas()
    draw_header(
        img,
        'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei',
        'În 2024, sezonul de vegetație s-a încheiat mai devreme',
        f"Sfârșitul sezonului de vegetație (HR-VPP EOSD, sezonul 1) pe cele {fmt_int(metrics['parcele_in_set'])} de parcele cu țintă, pe ani și pe grupe de cultură",
        badge=False,
    )
    card(img, (64, 200, 1256, 988))
    draw_chart(img, (64, 200, 1256, 988), bands, metrics['versiuni'])
    draw_difference(img, metrics)
    draw_reading(img, metrics)
    d = ImageDraw.Draw(img)
    d.text((64, 1008), 'Notă: sfârșitul sezonului de vegetație, nu data recoltei; abatere față de teren ~22 de zile (manualul HR-VPP).', font=F(14), fill=MUTED)
    draw_footer(img, 'Contains modified Copernicus Sentinel data 2017–2024 · CLMS HR-VPP (EOSD, LENGTH, sezonul 1) · Fields of The World · IC 95%: bootstrap pe blocuri de 5 km')
    target = OUT / 'sfarsit_sezon.png'
    img.convert('RGB').save(target, optimize=True)
    print('scris:', target)


if __name__ == '__main__':
    main()
