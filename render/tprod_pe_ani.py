"""Grafic 1920×1080 (stilul render/): evoluția TPROD pe fiecare an 2017–2024, separat primăvară și toamnă,
pe cele 11.971 de parcele arabile cu țintă like-for-like, cu banda intercuartilică P25–P75 și marcarea anului 2024.

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 render/tprod_pe_ani.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import ImageDraw  # noqa: E402

from common import (AMBER, AQUA, BG, CARD, CYAN, GRID, LINE, MUTED, ORANGE, TXT, TXT2, F, Layer, card, draw_footer,  # noqa: E402
                    draw_header, fmt_dec, fmt_int, new_canvas, section_label)
from gisday_config import BASE_YEARS, OUT, YEAR  # noqa: E402
from gisday_lib import crop_group  # noqa: E402

YEARS = list(BASE_YEARS) + [YEAR]
SPRING_RGB = ORANGE           # (217, 89, 38) — culturi de primăvară
AUTUMN_RGB = (64, 178, 148)   # verde-turcoaz — culturi de toamnă


def compute_yearly_stats():
    F_df = pd.read_parquet(OUT / 'parcel_features.parquet')
    T_df = pd.read_parquet(OUT / 'parcel_target.parquet')
    D = F_df.merge(T_df[['parcel_id', 'is_arable', 'tip_cultura_2024', 'loss_rel', 'n_ref_years']], on='parcel_id')
    for y in BASE_YEARS:
        D[f'grp_{y}'] = crop_group(D[f'ndvi_apr_{y}'])
    D[f'grp_{YEAR}'] = crop_group(D['ndvi_04'])

    ok = D[D.is_arable & D.loss_rel.notna()].copy()
    stats = {'primavara': [], 'toamna': []}
    for grp in ('primavara', 'toamna'):
        for y in YEARS:
            # Like-for-like: în anul y intră parcelele din setul de 11.971 care au avut grupul `grp` în anul y
            sub = ok.loc[ok[f'grp_{y}'] == grp, f'tprod_{y}'].dropna()
            p25, p50, p75 = np.percentile(sub, [25, 50, 75])
            stats[grp].append({
                'year': y,
                'n': len(sub),
                'p25': float(p25),
                'p50': float(p50),
                'p75': float(p75),
            })
    return len(ok), stats


def draw_chart(img, box, stats):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    pad_l, pad_r, pad_t, pad_b = 88, 48, 64, 68
    cx0, cy0, cx1, cy1 = x0 + pad_l, y0 + pad_t, x1 - pad_r, y1 - pad_b
    cw, ch = cx1 - cx0, cy1 - cy0

    y_min, y_max = 200.0, 1800.0

    def px_x(i):
        return cx0 + i * (cw / (len(YEARS) - 1))

    def px_y(val):
        return cy1 - (val - y_min) / (y_max - y_min) * ch

    # Grilă orizontală
    for tick in range(400, 1801, 200):
        yy = px_y(tick)
        d.line((cx0, yy, cx1, yy), fill=GRID, width=1)
        lbl = fmt_int(tick)
        d.text((cx0 - 14 - F(14).getlength(lbl), yy - 9), lbl, font=F(14), fill=MUTED)

    d.text((x0 + 24, y0 + 20), 'TPROD sezonul 1 (unități HR-VPP · mediană și banda P25–P75)', font=F(15, 'SemiBold'), fill=TXT2)

    # Bandă verticală de evidențiere pentru anul secetei 2024 (index 7)
    x_2024 = px_x(len(YEARS) - 1)
    d.rounded_rectangle((x_2024 - 38, cy0 - 12, x_2024 + 34, cy1 + 8), radius=8, fill=(44, 28, 28), outline=(140, 62, 54), width=1)
    tag_2024 = 'SECETA 2024'
    d.text((x_2024 - F(12, 'Bold').getlength(tag_2024) / 2, cy0 - 32), tag_2024, font=F(12, 'Bold'), fill=AMBER)

    # Desenare benzi P25–P75 și linii mediane (supraeșantionate prin Layer)
    L = Layer(x1 - x0, y1 - y0)
    for grp, col, alpha_band in (('toamna', AUTUMN_RGB, 46), ('primavara', SPRING_RGB, 54)):
        rows = stats[grp]
        upper = [(px_x(i) - x0, px_y(r['p75']) - y0) for i, r in enumerate(rows)]
        lower = [(px_x(i) - x0, px_y(r['p25']) - y0) for i, r in enumerate(rows)][::-1]
        L.poly(upper + lower, fill=col + (alpha_band,))
        L.line(upper, fill=col + (120,), width=1.5)
        L.line(lower[::-1], fill=col + (120,), width=1.5)

        med_pts = [(px_x(i) - x0, px_y(r['p50']) - y0) for i, r in enumerate(rows)]
        L.line(med_pts, fill=col + (255,), width=4)
        for i, (mx, my) in enumerate(med_pts):
            is_last = (i == len(YEARS) - 1)
            r_dot = 7 if is_last else 5
            L.circle(mx, my, r_dot, fill=col + (255,), outline=TXT + (255,), width=2 if is_last else 1)

    img.alpha_composite(L.get(), (x0, y0))

    # Etichete de valoare pe puncte și axa X (anii 2017–2024)
    d.line((cx0, cy1, cx1, cy1), fill=LINE, width=2)
    for i, y in enumerate(YEARS):
        xx = px_x(i)
        d.line((xx, cy1, xx, cy1 + 7), fill=LINE, width=1)
        y_str = str(y)
        f_yr = F(16, 'Bold') if y == YEAR else F(15, 'Medium')
        col_yr = AMBER if y == YEAR else TXT
        d.text((xx - f_yr.getlength(y_str) / 2, cy1 + 14), y_str, font=f_yr, fill=col_yr)
        v_tag = 'V101' if y <= 2020 else 'V105'
        d.text((xx - F(11).getlength(v_tag) / 2, cy1 + 36), v_tag, font=F(11), fill=MUTED)

    # Valori numerice ale medianei pe grafic
    for grp, col, dy_off in (('toamna', AUTUMN_RGB, -26), ('primavara', SPRING_RGB, 12)):
        for i, r in enumerate(stats[grp]):
            xx = px_x(i)
            yy = px_y(r['p50'])
            val_txt = fmt_int(r['p50'])
            f_val = F(15, 'Bold') if r['year'] in (2020, 2022, 2024) else F(14, 'SemiBold')
            d.text((xx - f_val.getlength(val_txt) / 2, yy + dy_off), val_txt, font=f_val, fill=TXT if r['year'] == 2024 else col)

    # Legendă în colțul dreapta-sus al graficului
    lx = cx1 - 520
    ly = y0 + 18
    d.rounded_rectangle((lx, ly + 4, lx + 24, ly + 16), radius=3, fill=AUTUMN_RGB)
    d.text((lx + 32, ly), 'Toamnă (NDVI apr. ≥ 0,40) · mediană și P25–P75', font=F(14, 'Medium'), fill=TXT)
    d.rounded_rectangle((lx + 310, ly + 4, lx + 334, ly + 16), radius=3, fill=SPRING_RGB)
    d.text((lx + 342, ly), 'Primăvară (NDVI apr. < 0,40)', font=F(14, 'Medium'), fill=TXT)


def main():
    n_total, stats = compute_yearly_stats()
    img = new_canvas()
    draw_header(
        img,
        'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei',
        'Productivitatea vegetației (TPROD) pe ani, 2017–2024',
        f'Mediana și banda intercuartilică P25–P75 pe cele {fmt_int(n_total)} de parcele arabile cu țintă like-for-like, separat pe grupe de cultură',
        badge=False,
    )
    d = ImageDraw.Draw(img)

    # Graficul principal în stânga
    chart_box = (64, 200, 1256, 988)
    card(img, chart_box)
    draw_chart(img, chart_box, stats)

    # Coloana din dreapta: sinteză anii cei mai slabi + tabel complet 2017–2024
    rx, rw = 1280, 576
    card(img, (rx, 200, rx + rw, 470))
    section_label(d, rx + 20, 216, 'Anii cei mai slabi din perioada de bază (2017–2023) vs 2024')

    d.text((rx + 20, 248), 'Culturi de primăvară (porumb, floarea-soarelui, soia):', font=F(16, 'SemiBold'), fill=SPRING_RGB)
    d.text((rx + 20, 274), '• Cei mai slabi ani din bază: 2020 (mediană 645, P25–P75: 477–857)', font=F(15, 'Medium'), fill=TXT)
    d.text((rx + 32, 298), 'și 2022 (mediană 751, P25–P75: 525–1.026).', font=F(15, 'Medium'), fill=TXT2)
    d.text((rx + 20, 322), '• 2024 coboară sub toți anii din bază: mediană 530 (P25–P75: 350–800).', font=F(15, 'Bold'), fill=AMBER)

    d.line((rx + 20, 354, rx + rw - 20, 354), fill=LINE, width=1)
    d.text((rx + 20, 366), 'Culturi de toamnă (grâu, orz, rapiță):', font=F(16, 'SemiBold'), fill=AUTUMN_RGB)
    d.text((rx + 20, 392), '• Cei mai slabi ani din bază: 2022 (mediană 781, P25–P75: 601–1.052)', font=F(15, 'Medium'), fill=TXT)
    d.text((rx + 32, 416), 'și 2020 (mediană 820, P25–P75: 632–1.063), urmați de 2018 (835).', font=F(15, 'Medium'), fill=TXT2)
    d.text((rx + 20, 440), '• În 2024 toamna rezistă: mediană 904 (P25–P75: 655–1.248).', font=F(15, 'SemiBold'), fill=TXT)

    # Tabel anual 2017–2024
    card(img, (rx, 488, rx + rw, 988))
    section_label(d, rx + 20, 504, 'Valori anuale TPROD: mediană (P25–P75) și număr de parcele')
    headers = [('An', rx + 20), ('Primăvară: med. (P25–P75) · N', rx + 88), ('Toamnă: med. (P25–P75) · N', rx + 334)]
    for h_txt, hx in headers:
        d.text((hx, 534), h_txt, font=F(13, 'SemiBold'), fill=MUTED)
    d.line((rx + 20, 556, rx + rw - 20, 556), fill=LINE, width=1)

    for i, y in enumerate(YEARS):
        ry = 568 + i * 50
        sp = stats['primavara'][i]
        au = stats['toamna'][i]
        if y == YEAR:
            d.rounded_rectangle((rx + 12, ry - 6, rx + rw - 12, ry + 36), radius=6, fill=(44, 28, 28), outline=(140, 62, 54), width=1)
        f_row = F(14, 'Bold') if y in (2020, 2022, 2024) else F(14, 'Regular')
        col_y = AMBER if y == YEAR else TXT
        d.text((rx + 20, ry + 4), str(y), font=f_row, fill=col_y)

        sp_txt = f"{fmt_int(sp['p50'])} ({fmt_int(sp['p25'])}–{fmt_int(sp['p75'])}) · {fmt_int(sp['n'])}"
        au_txt = f"{fmt_int(au['p50'])} ({fmt_int(au['p25'])}–{fmt_int(au['p75'])}) · {fmt_int(au['n'])}"
        d.text((rx + 88, ry + 4), sp_txt, font=f_row, fill=AMBER if y == YEAR else TXT)
        d.text((rx + 334, ry + 4), au_txt, font=f_row, fill=TXT)

    d.text((64, 1008), 'Limită: TPROD măsoară productivitatea vegetației, nu recolta în t/ha. Anii 2017–2020 sunt procesați în HR-VPP V101, iar 2021–2024 în V105.', font=F(14), fill=MUTED)
    draw_footer(img, 'Contains modified Copernicus Sentinel data 2017–2024 · CLMS HR-VPP · Fields of The World · EPSG:3844')

    out_path = OUT / 'tprod_pe_ani.png'
    img.convert('RGB').save(out_path, optimize=True)
    print('scris:', out_path)


if __name__ == '__main__':
    main()
