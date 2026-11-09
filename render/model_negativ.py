"""Grafic 1920×1080 (stilul render/): R² spațial al modelului 04, global și în interiorul grupelor, față de modelul de bază.
Toate cifrele vin din data/out/model_metrics.json și data/out/vulnerability.parquet.

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 render/model_negativ.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import pandas as pd  # noqa: E402
from PIL import ImageDraw  # noqa: E402

from common import AMBER, GRID, H, LINE, MUTED, TXT, TXT2, W, F, Layer, card, draw_footer, draw_header, fmt_dec, fmt_int, new_canvas, section_label  # noqa: E402
from gisday_config import OUT  # noqa: E402

MODEL_RGB, BASE_RGB = (42, 120, 214), (138, 148, 152)   # albastrul validat cu validate_palette.js și gri neutru pentru reper
PLOT_X0, PLOT_X1, PLOT_Y0, PLOT_Y1 = 150, 1216, 304, 876
Y_MIN, Y_MAX = -0.02, 0.12
BAR_W, BAR_GAP = 76, 8
GATE = 0.10                                              # poarta din D21, cerută în interiorul fiecărei grupe


def y_of(value):
    return PLOT_Y1 - (value - Y_MIN) / (Y_MAX - Y_MIN) * (PLOT_Y1 - PLOT_Y0)


def num(value, nd):
    sign = '−' if value < 0 else ''
    return f'{sign}{fmt_dec(abs(value), nd)}'


def metrics_table():
    """Rândurile graficului: (nume, N, R² model, R² bază, RMSE model, RMSE bază), direct din rezultatele modelului."""
    m = json.loads((OUT / 'model_metrics.json').read_text(encoding='utf-8'))
    vulnerability = pd.read_parquet(OUT / 'vulnerability.parquet', columns=['are_tinta', 'tip_cultura_2024'])
    counts = vulnerability[vulnerability.are_tinta.eq('da')].tip_cultura_2024.value_counts()
    assert counts[['primavara', 'toamna']].sum() == m['n_parcels_train'], 'N pe grupe nu dă totalul modelului'
    rows = [('Global', m['n_parcels_train'], m['r2_spatial'], m['r2_baseline_mean'], m['rmse'], m['rmse_baseline_mean'])]
    for key, name in (('primavara', 'Primăvară'), ('toamna', 'Toamnă')):
        rows.append((name, int(counts[key]), m['r2_by_group'][key], m['r2_baseline_by_group'][key], m['rmse_by_group'][key], m['rmse_baseline_by_group'][key]))
    return rows, m


def draw_bar(layer, x, value, color):
    zero, end = y_of(0), y_of(value)
    top, bottom = min(zero, end), max(zero, end)
    layer.rect((x, top, x + BAR_W, bottom), fill=color + (255,), radius=min(4, (bottom - top) / 2))
    if bottom - top > 5:          # capătul de la linia de zero rămâne drept
        anchored = (x, bottom - 5, x + BAR_W, bottom) if value >= 0 else (x, top, x + BAR_W, top + 5)
        layer.rect(anchored, fill=color + (255,))


def draw_chart(img, rows):
    d = ImageDraw.Draw(img)
    card(img, (64, 200, 1256, 988))
    section_label(d, 88, 216, 'R² spațial, validare pe blocuri de 5 km')
    x = PLOT_X0
    for color, text in ((MODEL_RGB, 'Modelul cu terenul (LightGBM, 11 factori)'), (BASE_RGB, 'Modelul de bază (media din blocurile de antrenare)')):
        d.rounded_rectangle((x, 251, x + 22, 263), radius=3, fill=color)
        d.text((x + 30, 248), text, font=F(15, 'Medium'), fill=TXT)
        x += 30 + F(15, 'Medium').getlength(text) + 32

    for tick in (-0.02, 0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12):
        y = y_of(tick)
        d.line((PLOT_X0, y, PLOT_X1, y), fill=LINE if tick == 0 else GRID, width=2 if tick == 0 else 1)
        label = '0' if tick == 0 else num(tick, 2)
        d.text((PLOT_X0 - 14 - F(14).getlength(label), y - 9), label, font=F(14), fill=MUTED)

    width = (PLOT_X1 - PLOT_X0) / len(rows)
    layer = Layer(W, H)
    labels = []
    for i, (name, n, r2_model, r2_base, _, _) in enumerate(rows):
        center = PLOT_X0 + width * (i + 0.5)
        for x, value, color in ((center - BAR_GAP / 2 - BAR_W, r2_model, MODEL_RGB), (center + BAR_GAP / 2, r2_base, BASE_RGB)):
            draw_bar(layer, x, value, color)
            text = num(value, 3)
            font = F(20, 'Bold')
            y = y_of(value) - 30 if value >= 0 else y_of(value) + 6
            labels.append((x + (BAR_W - font.getlength(text)) / 2, y, text, font))
        d.text((center - F(21, 'SemiBold').getlength(name) / 2, PLOT_Y1 + 14), name, font=F(21, 'SemiBold'), fill=TXT)
        caption = f'{fmt_int(n)} parcele'
        d.text((center - F(15).getlength(caption) / 2, PLOT_Y1 + 44), caption, font=F(15), fill=TXT2)
    img.alpha_composite(layer.get())
    for x, y, text, font in labels:
        d.text((x, y), text, font=font, fill=TXT)

    # Poarta se aplică doar în interiorul grupelor, deci linia acoperă doar primele două grupe de cultură
    gate_y, gate_x0, gate_x1 = y_of(GATE), PLOT_X0 + width + 16, PLOT_X1
    for x in range(int(gate_x0), int(gate_x1), 18):
        d.line((x, gate_y, min(x + 10, gate_x1), gate_y), fill=AMBER, width=2)
    d.text((gate_x0, gate_y - 26), f'Pragul cerut în fiecare grupă: R² ≥ {fmt_dec(GATE, 2)}', font=F(16, 'Medium'), fill=TXT)


def draw_factors(img):
    d = ImageDraw.Draw(img)
    x = 1300
    card(img, (1280, 200, 1856, 470))
    section_label(d, x, 216, 'Ce a avut la dispoziție modelul')
    lines = ('Sol: carbon, nisip, argilă (SoilGrids 250 m)', 'Relief: altitudine, pantă (Copernicus DEM)', 'Expunerea la vânt (ERA5-Land, elemente lemnoase)',
             'Distanța la canale și la rețeaua de apă (OSM)', 'Suprafața parcelei', 'Tipul de cultură din 2024', 'Productivitatea medie 2017–2023 (HR-VPP)')
    for i, text in enumerate(lines):
        d.ellipse((x, 256 + i * 30, x + 6, 262 + i * 30), fill=MUTED)
        d.text((x + 18, 248 + i * 30), text, font=F(16), fill=TXT2)


def draw_table(img, rows):
    d = ImageDraw.Draw(img)
    x0, x1 = 1300, 1836
    card(img, (1280, 488, 1856, 988))
    section_label(d, x0, 504, 'Cifrele din validare')
    columns = ((1474, 'R² model'), (1584, 'R² bază'), (1710, 'RMSE model'), (x1, 'RMSE bază'))
    d.text((x0, 536), 'Grupă', font=F(13, 'SemiBold'), fill=MUTED)
    for right, head in columns:
        d.text((right - F(13, 'SemiBold').getlength(head), 536), head, font=F(13, 'SemiBold'), fill=MUTED)
    d.line((x0, 558, x1, 558), fill=LINE, width=1)
    for i, (name, _, r2_model, r2_base, rmse_model, rmse_base) in enumerate(rows):
        y = 572 + i * 40
        d.text((x0, y), name, font=F(16, 'Medium'), fill=TXT)
        for (right, _), cell in zip(columns, (num(r2_model, 4), num(r2_base, 4), num(rmse_model, 4), num(rmse_base, 4))):
            d.text((right - F(16).getlength(cell), y), cell, font=F(16), fill=TXT)
    d.line((x0, 698, x1, 698), fill=LINE, width=1)
    message = (
        (0, 'R² = 0 înseamnă: modelul nu prezice mai bine', 'SemiBold', 19, TXT),
        (28, 'decât media.', 'SemiBold', 19, TXT),
        (70, 'Valoarea globală vine din diferența dintre primăvară', 'Regular', 16, TXT2),
        (95, 'și toamnă, pe care modelul o primește ca factor.', 'Regular', 16, TXT2),
        (133, 'În interiorul fiecărei grupe, R² rămâne aproape zero:', 'Regular', 16, TXT2),
        (158, 'solul, relieful, vântul și canalele nu explică de ce', 'Regular', 16, TXT2),
        (183, 'o parcelă a pierdut mai mult decât alta.', 'Regular', 16, TXT2),
    )
    for offset, text, weight, size, color in message:
        d.text((x0, 716 + offset), text, font=F(size, weight), fill=color)


def main():
    rows, m = metrics_table()
    img = new_canvas()
    draw_header(
        img,
        'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei',
        'Terenul nu explică pierderea din 2024',
        'R² spațial al modelului cu sol, relief, vânt și canale, față de modelul de bază',
        badge=False,
    )
    draw_chart(img, rows)
    draw_factors(img)
    draw_table(img, rows)
    d = ImageDraw.Draw(img)
    d.text((64, 1008), f"Limită: modelul a rulat pe {fmt_int(m['n_parcels_train'])} de parcele arabile cu țintă și {m['n_blocks']} de blocuri de 5 km, înainte ca grupul incert să fie scos din țintă.", font=F(14), fill=MUTED)
    draw_footer(img, 'Contains modified Copernicus Sentinel data 2017–2024 · CLMS HR-VPP · ERA5-Land · SoilGrids · Copernicus DEM · © OpenStreetMap · Fields of The World')
    target = OUT / 'model_negativ.png'
    img.convert('RGB').save(target, optimize=True)
    print('scris:', target)


if __name__ == '__main__':
    main()
