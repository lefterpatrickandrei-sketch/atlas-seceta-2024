"""Contextul meteo al verii 2024: ERA5-Land zilnic (ECMWF/ERA5_LAND/DAILY_AGGR), aprilie–septembrie, 2024 față de normala 1991–2020.

Model: extragerea ERA5-Land din 01_extract_oltenia.py. Zona: AOI_BBOX tăiat la granița României (data/interim/aoi_3844.gpkg, ca în
harta-erou). Media pe zonă e ponderată cu suprafața celulelor: mean(valoare × aria pixelului) / mean(aria pixelului), cu ponderile
de acoperire parțială pe care Earth Engine le dă reducerii `mean` la marginea zonei.
Pe lună: precipitații (sumă zilnică, m → mm), Tmax medie (K → °C), zile cu Tmax ≥ 35 °C (pe seria zilnică mediată pe zonă).

Rezultate: data/out/final/meteo_2024.json (toate cifrele lunare) și data/out/final/meteo_2024.png (1920×1080).
Seria zilnică brută se păstrează în data/interim/era5l_zilnic_aoi_1991_2024.parquet (reluabil fără Earth Engine).
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/meteo_2024.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import ImageDraw  # noqa: E402

from common import (CARD, GRID, LINE, MUTED, ORANGE, TXT, TXT2, F, Layer, card, draw_footer, draw_header, fmt_dec, new_canvas,  # noqa: E402
                    section_label)
from gisday_config import GEE_PROJECT, INTERIM, OUT  # noqa: E402

YEAR, REF = 2024, (1991, 2020)
MONTHS = [4, 5, 6, 7, 8, 9]
NAMES = {4: 'apr.', 5: 'mai', 6: 'iun.', 7: 'iul.', 8: 'aug.', 9: 'sep.'}
HOT = 35.0
CACHE = INTERIM / 'era5l_zilnic_aoi_1991_2024.parquet'
FINAL = OUT / 'final'
RAIN_RGB, NORMAL_RGB = (42, 120, 214), (138, 148, 152)     # albastrul validat; gri neutru pentru normală
TMAX_RGB = ORANGE


def daily_series():
    """Seria zilnică aprilie–septembrie, 1991–2020 și 2024, mediată pe zonă cu ponderare pe suprafață."""
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    import ee
    ee.Initialize(project=GEE_PROJECT)
    aoi = gpd.read_file(INTERIM / 'aoi_3844.gpkg').to_crs(4326)
    region = ee.Geometry(json.loads(aoi.geometry.to_json())['features'][0]['geometry'])
    area = ee.Image.pixelArea()

    def aoi_mean(img):
        weighted = img.select(['temperature_2m_max', 'total_precipitation_sum']).multiply(area).addBands(area.rename('area'))
        vals = weighted.reduceRegion(ee.Reducer.mean(), region, 11132)
        return ee.Feature(None, vals).set('date', img.date().format('YYYY-MM-dd'))

    rows = []
    for y in list(range(REF[0], REF[1] + 1)) + [YEAR]:
        col = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').filterDate(f'{y}-04-01', f'{y}-10-01')
        for f in col.map(aoi_mean).getInfo()['features']:
            p = f['properties']
            rows.append({'date': p['date'], 'tmax_c': p['temperature_2m_max'] / p['area'] - 273.15,
                         'precip_mm': p['total_precipitation_sum'] / p['area'] * 1000})
        print(y, len(rows), flush=True)
    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df.date)
    df.to_parquet(CACHE)
    return df


def monthly(df):
    df = df.assign(year=df.date.dt.year, month=df.date.dt.month)
    expected = {(y, m): pd.Period(f'{y}-{m:02d}').days_in_month for y in df.year.unique() for m in MONTHS}
    counts = df.groupby(['year', 'month']).size()
    assert all(counts[k] == v for k, v in expected.items()), 'lipsesc zile în seria ERA5-Land'
    g = df.groupby(['year', 'month'])
    m = pd.DataFrame({'precip_mm': g.precip_mm.sum(), 'tmax_c': g.tmax_c.mean(), 'zile_35': g.tmax_c.apply(lambda s: int((s >= HOT).sum()))}).reset_index()
    ref = m[m.year.between(*REF)].groupby('month').mean(numeric_only=True)
    cur = m[m.year == YEAR].set_index('month')
    rows = []
    for mo in MONTHS:
        rows.append({'luna': mo, 'nume': NAMES[mo],
                     'precip_2024_mm': round(float(cur.precip_mm[mo]), 1), 'precip_normala_mm': round(float(ref.precip_mm[mo]), 1),
                     'precip_pct_din_normala': round(float(100 * cur.precip_mm[mo] / ref.precip_mm[mo]), 0),
                     'tmax_2024_c': round(float(cur.tmax_c[mo]), 1), 'tmax_normala_c': round(float(ref.tmax_c[mo]), 1),
                     'tmax_anomalie_c': round(float(cur.tmax_c[mo] - ref.tmax_c[mo]), 1),
                     'zile_tmax_35_2024': int(cur.zile_35[mo]), 'zile_tmax_35_normala': round(float(ref.zile_35[mo]), 1)})
    season = {'precip_2024_mm': round(float(cur.precip_mm.sum()), 1), 'precip_normala_mm': round(float(ref.precip_mm.sum()), 1),
              'precip_pct_din_normala': round(float(100 * cur.precip_mm.sum() / ref.precip_mm.sum()), 0),
              'tmax_anomalie_medie_c': round(float((cur.tmax_c - ref.tmax_c).mean()), 1),
              'zile_tmax_35_2024': int(cur.zile_35.sum()), 'zile_tmax_35_normala': round(float(ref.zile_35.sum()), 1)}
    return rows, season


def doy(date):
    return (date - dt.date(YEAR, 1, 1)).days + 1


X0_DAY, X1_DAY = doy(dt.date(YEAR, 4, 1)), doy(dt.date(YEAR, 10, 1))


def month_span(mo):
    return doy(dt.date(YEAR, mo, 1)), doy(dt.date(YEAR, mo + 1, 1))


def signed(v, nd=1):
    return ('+' if v > 0 else '−' if v < 0 else '±') + fmt_dec(abs(v), nd)


def eos_lines():
    eos = json.loads((OUT / 'eos_metrics.json').read_text(encoding='utf-8'))['pe_grupe']
    out = []
    for key, name in (('toamna', 'toamnă'), ('primavara', 'primăvară')):
        day, month = (int(v) for v in eos[key]['eosd']['data_2024'].split('.'))
        out.append((name, dt.date(YEAR, month, day)))
    return out


def panel(img, box, title, rows, kind, eos):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    card(img, box)
    section_label(d, x0 + 24, y0 + 16, title)
    px0, px1, py0, py1 = x0 + 84, x1 - 28, y0 + 120, y1 - 150

    def X(day):
        return px0 + (day - X0_DAY) / (X1_DAY - X0_DAY) * (px1 - px0)

    if kind == 'precip':
        top = max(max(r['precip_2024_mm'], r['precip_normala_mm']) for r in rows) * 1.25
        lo, ticks, unit = 0.0, [t for t in range(0, int(top) + 1, 20)], 'mm'
    else:
        vals = [v for r in rows for v in (r['tmax_2024_c'], r['tmax_normala_c'])]
        lo, top = np.floor(min(vals) / 5) * 5 - 5, np.ceil(max(vals) / 5) * 5 + 5
        ticks, unit = list(range(int(lo), int(top) + 1, 5)), '°C'

    def Y(v):
        return py1 - (v - lo) / (top - lo) * (py1 - py0)

    for t in ticks:
        d.line((px0, Y(t), px1, Y(t)), fill=LINE if t == lo else GRID, width=2 if t == lo else 1)
        d.text((px0 - 12 - F(14).getlength(str(t)), Y(t) - 9), str(t), font=F(14), fill=MUTED)
    d.text((px0 - 12 - F(13).getlength(unit), py0 - 30), unit, font=F(13), fill=MUTED)

    # legenda panoului
    lx, ly = x0 + 24, y0 + 50
    if kind == 'precip':
        items = ((RAIN_RGB, 'bară', 'Precipitații 2024'), (TXT, 'linie', 'Normala 1991–2020'))
    else:
        items = ((TMAX_RGB, 'punct', 'Tmax medie 2024'), (NORMAL_RGB, 'punct', 'Normala 1991–2020'))
    for color, shape, text in items:
        if shape == 'bară':
            d.rounded_rectangle((lx, ly + 3, lx + 22, ly + 15), radius=3, fill=color)
        elif shape == 'linie':
            d.line((lx, ly + 9, lx + 22, ly + 9), fill=color, width=3)
        else:
            d.ellipse((lx + 5, ly + 3, lx + 17, ly + 15), fill=color)
        d.text((lx + 30, ly), text, font=F(15, 'Medium'), fill=TXT)
        lx += 30 + F(15, 'Medium').getlength(text) + 28

    layer = Layer(1920, 1080)
    for i, r in enumerate(rows):
        a, b = month_span(r['luna'])
        cx, w = (X(a) + X(b)) / 2, (X(b) - X(a)) * 0.56
        if kind == 'precip':
            layer.rect((cx - w / 2, Y(r['precip_2024_mm']), cx + w / 2, Y(0)), fill=RAIN_RGB + (255,), radius=4)
            layer.rect((cx - w / 2, Y(r['precip_2024_mm']) + 5, cx + w / 2, Y(0)), fill=RAIN_RGB + (255,))
            layer.line([(cx - w / 2 - 8, Y(r['precip_normala_mm'])), (cx + w / 2 + 8, Y(r['precip_normala_mm']))], fill=TXT + (255,), width=3)
        else:
            layer.circle(cx, Y(r['tmax_normala_c']), 7, fill=NORMAL_RGB + (255,))
            layer.circle(cx, Y(r['tmax_2024_c']), 8, fill=TMAX_RGB + (255,), outline=TXT + (255,), width=1.5)
    if kind == 'tmax':
        for key, color in (('tmax_normala_c', NORMAL_RGB), ('tmax_2024_c', TMAX_RGB)):
            pts = [((X(month_span(r['luna'])[0]) + X(month_span(r['luna'])[1])) / 2, Y(r[key])) for r in rows]
            layer.line(pts, fill=color + (200,), width=2.5)
    img.alpha_composite(layer.get())

    # sfârșitul mediu al sezonului de vegetație 2024: linii punctate
    for name, date in eos:
        x = X(doy(date))
        for yy in range(int(py0 - 6), int(py1), 12):
            d.line((x, yy, x, min(yy + 6, py1)), fill=TXT2, width=2)
        label = f'{name} {date.day} {NAMES[date.month].rstrip(".")}'
        d.text((x + 6, py0 - 26), label, font=F(13, 'SemiBold'), fill=TXT2)

    for r in rows:
        a, b = month_span(r['luna'])
        cx = (X(a) + X(b)) / 2
        if kind == 'precip':
            text = f"{r['precip_pct_din_normala']:.0f}%"
            ytop = min(Y(r['precip_2024_mm']), Y(r['precip_normala_mm']))
            tx = cx - F(17, 'Bold').getlength(text) / 2
            d.rectangle((tx - 4, ytop - 30, tx + F(17, 'Bold').getlength(text) + 4, ytop - 8), fill=CARD)   # linia punctată rămâne în spate
            d.text((tx, ytop - 30), text, font=F(17, 'Bold'), fill=TXT)
            sub = f"{fmt_dec(r['precip_2024_mm'], 0)} / {fmt_dec(r['precip_normala_mm'], 0)} mm"
            d.text((cx - F(13).getlength(sub) / 2, py1 + 40), sub, font=F(13), fill=TXT2)
        else:
            text = f"{signed(r['tmax_anomalie_c'])} °C"
            ytop = min(Y(r['tmax_2024_c']), Y(r['tmax_normala_c']))
            tx = cx - F(17, 'Bold').getlength(text) / 2
            d.rectangle((tx - 4, ytop - 36, tx + F(17, 'Bold').getlength(text) + 4, ytop - 14), fill=CARD)
            d.text((tx, ytop - 36), text, font=F(17, 'Bold'), fill=TXT)
            sub = f"≥ 35 °C: {r['zile_tmax_35_2024']} zile"
            sub2 = f"normală {fmt_dec(r['zile_tmax_35_normala'], 1)}"
            d.text((cx - F(13, 'SemiBold').getlength(sub) / 2, py1 + 40), sub, font=F(13, 'SemiBold'), fill=TXT)
            d.text((cx - F(12).getlength(sub2) / 2, py1 + 60), sub2, font=F(12), fill=TXT2)
        name = r['nume'].rstrip('.')
        d.text((cx - F(15, 'Medium').getlength(name) / 2, py1 + 12), name, font=F(15, 'Medium'), fill=TXT)
    note = ('sub lună: 2024 / normală' if kind == 'precip' else 'sub lună: zile cu Tmax ≥ 35 °C în 2024 și media 1991–2020')
    d.text((px0, y1 - 46), note, font=F(13), fill=MUTED)


def main():
    rows, season = monthly(daily_series())
    eos = eos_lines()
    FINAL.mkdir(parents=True, exist_ok=True)
    out = {'sursa': 'ERA5-Land (C3S), ECMWF/ERA5_LAND/DAILY_AGGR în Earth Engine; total_precipitation_sum (m → mm), temperature_2m_max (K → °C)',
           'zona': 'AOI_BBOX tăiat la granița României; medie ponderată pe suprafața celulelor',
           'normala': '1991–2020, aceleași luni', 'prag_zile_calde_c': HOT,
           'zile_calde_definitie': 'zile în care Tmax mediată pe zonă ≥ 35 °C',
           'sfarsit_sezon_vegetatie_2024': {name: date.isoformat() for name, date in eos},
           'lunar': rows, 'aprilie_septembrie': season}
    (FINAL / 'meteo_2024.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

    img = new_canvas()
    title = (f"Aprilie–septembrie 2024: {season['precip_pct_din_normala']:.0f}% din precipitațiile normale, "
             f"Tmax {signed(season['tmax_anomalie_medie_c'])} °C")
    draw_header(img, 'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei', title,
                f"Pe luni, față de normala 1991–2020 · zile cu Tmax ≥ 35 °C: {season['zile_tmax_35_2024']} în 2024, "
                f"{fmt_dec(season['zile_tmax_35_normala'], 1)} în medie 1991–2020", badge=False)
    panel(img, (64, 200, 944, 988), '(a) Precipitații lunare', rows, 'precip', eos)
    panel(img, (976, 200, 1856, 988), '(b) Temperatura maximă zilnică, media lunii', rows, 'tmax', eos)
    d = ImageDraw.Draw(img)
    d.text((64, 1008), 'Linii punctate: sfârșitul mediu al sezonului de vegetație în 2024 (HR-VPP EOSD), toamnă și primăvară; nu e data recoltei.',
           font=F(14), fill=MUTED)
    draw_footer(img, 'ERA5-Land (C3S), medie pe zona de studiu; normala 1991–2020')
    img.convert('RGB').save(FINAL / 'meteo_2024.png', optimize=True)
    print('scris:', FINAL / 'meteo_2024.png')
    for r in rows:
        print(r)
    print('sezon', season)


if __name__ == '__main__':
    main()
