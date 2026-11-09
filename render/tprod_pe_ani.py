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

    # Bandă verticală de evidențiere și marcaj pentru anul 2024 (index 7)
    x_2024 = px_x(len(YEARS) - 1)
    d.rounded_rectangle((x_2024 - 40, cy0 - 12, x_2024 + 36, cy1 + 8), radius=8, fill=(44, 28, 28), outline=(185, 82, 64), width=2)
    d.rounded_rectangle((x_2024 - 48, cy0 - 38, x_2024 + 44, cy0 - 16), radius=5, fill=(76, 36, 28), outline=AMBER, width=1)
    tag_2024 = 'SECETĂ 2024'
    d.text((x_2024 - 2 - F(12, 'Bold').getlength(tag_2024) / 2, cy0 - 35), tag_2024, font=F(12, 'Bold'), fill=AMBER)

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

    # Valori numerice ale medianei pe grafic (seria mai sus primește eticheta deasupra, cea mai jos dedesubt)
    for i in range(len(YEARS)):
        sp_v = stats['primavara'][i]['p50']
        au_v = stats['toamna'][i]['p50']
        sp_dy = -24 if sp_v > au_v else 12
        au_dy = -24 if au_v >= sp_v else 12
        for grp, col, val, dy_off in (('toamna', AUTUMN_RGB, au_v, au_dy), ('primavara', SPRING_RGB, sp_v, sp_dy)):
            xx = px_x(i)
            yy = px_y(val)
            val_txt = fmt_int(val)
            yr = YEARS[i]
            f_val = F(15, 'Bold') if yr in (2020, 2022, 2024) else F(14, 'SemiBold')
            d.text((xx - f_val.getlength(val_txt) / 2, yy + dy_off), val_txt, font=f_val, fill=TXT if yr == 2024 else col)

    # Legendă în partea de sus a graficului (fără suprapunere cu eticheta 2024)
    lx = cx1 - 580
    ly = y0 + 19
    d.rounded_rectangle((lx, ly + 4, lx + 22, ly + 15), radius=3, fill=AUTUMN_RGB)
    d.text((lx + 30, ly), 'Toamnă (mediană și P25–P75)', font=F(14, 'Medium'), fill=TXT)
    d.rounded_rectangle((lx + 258, ly + 4, lx + 280, ly + 15), radius=3, fill=SPRING_RGB)
    d.text((lx + 288, ly), 'Primăvară (mediană și P25–P75)', font=F(14, 'Medium'), fill=TXT)


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

    sp_base = sorted(stats['primavara'][:-1], key=lambda r: r['p50'])
    sp_w1, sp_w2 = sp_base[0], sp_base[1]
    sp_24 = stats['primavara'][-1]
    d.text((rx + 20, 248), 'Culturi de primăvară (porumb, floarea-soarelui, soia):', font=F(16, 'SemiBold'), fill=SPRING_RGB)
    d.text((rx + 20, 274), f"• Cel mai slab an din bază: {sp_w1['year']} (mediană {fmt_int(sp_w1['p50'])}, P25–P75: {fmt_int(sp_w1['p25'])}–{fmt_int(sp_w1['p75'])})", font=F(15, 'Medium'), fill=TXT)
    d.text((rx + 32, 298), f"urmat de {sp_w2['year']} (mediană {fmt_int(sp_w2['p50'])}, P25–P75: {fmt_int(sp_w2['p25'])}–{fmt_int(sp_w2['p75'])}).", font=F(15, 'Medium'), fill=TXT2)
    d.text((rx + 20, 322), f"• Anul 2024 (sub toți anii din bază): mediană {fmt_int(sp_24['p50'])} (P25–P75: {fmt_int(sp_24['p25'])}–{fmt_int(sp_24['p75'])}).", font=F(15, 'Bold'), fill=AMBER)

    au_base = sorted(stats['toamna'][:-1], key=lambda r: r['p50'])
    au_w1, au_w2, au_w3 = au_base[0], au_base[1], au_base[2]
    au_24 = stats['toamna'][-1]
    d.line((rx + 20, 354, rx + rw - 20, 354), fill=LINE, width=1)
    d.text((rx + 20, 366), 'Culturi de toamnă (grâu, orz, rapiță):', font=F(16, 'SemiBold'), fill=AUTUMN_RGB)
    d.text((rx + 20, 392), f"• Cel mai slab an din bază: {au_w1['year']} (mediană {fmt_int(au_w1['p50'])}, P25–P75: {fmt_int(au_w1['p25'])}–{fmt_int(au_w1['p75'])})", font=F(15, 'Medium'), fill=TXT)
    d.text((rx + 32, 416), f"urmat de {au_w2['year']} (mediană {fmt_int(au_w2['p50'])}, P25–P75: {fmt_int(au_w2['p25'])}–{fmt_int(au_w2['p75'])}) și {au_w3['year']} ({fmt_int(au_w3['p50'])}).", font=F(15, 'Medium'), fill=TXT2)
    d.text((rx + 20, 440), f"• Anul 2024 pe culturile de toamnă: mediană {fmt_int(au_24['p50'])} (P25–P75: {fmt_int(au_24['p25'])}–{fmt_int(au_24['p75'])}).", font=F(15, 'SemiBold'), fill=TXT)

    # Tabel anual 2017–2024
    card(img, (rx, 488, rx + rw, 988))
    section_label(d, rx + 20, 504, 'Valori anuale TPROD: mediană (P25–P75) și N parcele')
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
    draw_footer(img, 'Contains modified Copernicus Sentinel data 2017–2024 · CLMS HR-VPP · Fields of The World · EPSG:3844 · Secetă 2024: AGERPRES, Retrospectiva 2024 (22.12.2024)')

    out_path = OUT / 'tprod_pe_ani.png'
    img.convert('RGB').save(out_path, optimize=True)
    print('scris:', out_path)


if __name__ == '__main__':
    main()

