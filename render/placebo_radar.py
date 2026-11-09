"""Grafic 1920×1080 (stilul render/): frecvența evenimentelor radar din august 2024 pe culturile de primăvară și pe miriștile de toamnă,
cu IC 95%, plus cele 4 tipare radar. Toate cifrele vin din data/out/s1_events_diagnostic.json.

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 render/placebo_radar.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

from PIL import ImageDraw  # noqa: E402

from common import (AQUA, GRID, H, LINE, MUTED, ORANGE, TXT, TXT2, W, F, Layer, card, draw_footer, draw_header, fmt_dec, fmt_int,  # noqa: E402
                    new_canvas, section_label)
from gisday_config import OUT  # noqa: E402

SPRING_RGB, STUBBLE_RGB = ORANGE, AQUA     # perechea validată cu validate_palette.js pe fundalul BG
PLOT_X0, PLOT_X1, X_MAX = 470, 1040, 5.0   # axa frecvenței, în %
ROW_H, BAR_H, FIRST_ROW = 118, 18, 290
PATTERNS_GAP = 44
TOTAL = 'toate'
ROWS = (
    (TOTAL, 'Toate evenimentele', 'VV crește cu cel puțin 1,5 dB, fără ploaie', 'Toate'),
    ('A_vh_scade', 'VV crește, VH scade', 'compatibil cu tăiere sau recoltare', 'VV crește, VH scade'),
    ('B_ca_martorul_ploaie', 'VV și VH cresc împreună', 'ca la ploaia din 21 iulie (martor)', 'VV și VH împreună'),
    ('C_dcr_peste_martor', 'VH crește mult peste VV', 'compatibil cu arătură', 'VH mult peste VV'),
    ('D_dcr_sub_martor', 'VV crește mult, VH puțin', 'fără o cauză clară', 'VV mult, VH puțin'),
)


def x_of(value):
    return PLOT_X0 + value / X_MAX * (PLOT_X1 - PLOT_X0)


def signed(value):
    sign = '+' if value > 0 else '−' if value < 0 else ''
    return f'{sign}{fmt_dec(abs(value), 2)}'


def row_top(index):
    return FIRST_ROW + index * ROW_H + (PATTERNS_GAP if index else 0)


def bar_with_interval(layer, y, value, interval, color):
    """Bară ancorată în 0, cu mustața IC 95% peste ea."""
    x0, x1 = x_of(0), x_of(value)
    layer.rect((x0, y, x1, y + BAR_H), fill=color + (255,), radius=4)
    layer.rect((x0, y, x0 + 5, y + BAR_H), fill=color + (255,))
    mid, low, high = y + BAR_H / 2, x_of(interval[0]), x_of(interval[1])
    layer.line([(low, mid), (high, mid)], fill=TXT + (255,), width=2)
    for cap in (low, high):
        layer.line([(cap, mid - 5), (cap, mid + 5)], fill=TXT + (255,), width=2)


def legend(img, d, y):
    x = PLOT_X0
    for color, text in ((SPRING_RGB, 'Culturi de primăvară'), (STUBBLE_RGB, 'Miriști de toamnă (placebo)')):
        d.rounded_rectangle((x, y + 3, x + 22, y + 15), radius=3, fill=color)
        d.text((x + 30, y), text, font=F(15, 'Medium'), fill=TXT)
        x += 30 + F(15, 'Medium').getlength(text) + 28
    d.line((x, y + 9, x + 26, y + 9), fill=TXT, width=2)
    for cap in (x, x + 26):
        d.line((cap, y + 4, cap, y + 14), fill=TXT, width=2)
    d.text((x + 34, y), 'IC 95%', font=F(15, 'Medium'), fill=TXT)


def draw_chart(img, placebo):
    d = ImageDraw.Draw(img)
    card(img, (64, 200, 1256, 988))
    section_label(d, 88, 216, 'Frecvența evenimentelor radar, august 2024')
    legend(img, d, 248)

    bottom = row_top(len(ROWS))
    for tick in range(0, int(X_MAX) + 1):
        x = x_of(tick)
        for y0, y1 in ((FIRST_ROW, row_top(1) - 44), (row_top(1), bottom)):      # axa nu trece prin titlul tiparelor
            d.line((x, y0, x, y1), fill=LINE if tick == 0 else GRID, width=2 if tick == 0 else 1)
        label = f'{tick}%'
        d.text((x - F(14).getlength(label) / 2, bottom + 8), label, font=F(14), fill=MUTED)
    counts = placebo[TOTAL]['n_observatii']
    axis_note = (f"% din observațiile parcelă × tranziție uscată: {fmt_int(counts['primavara'])} pe primăvară, {fmt_int(counts['toamna'])} pe miriști, "
                 f"{counts['blocuri']} de blocuri de 5 km")
    d.text((88, bottom + 36), axis_note, font=F(14), fill=TXT2)

    head_y = FIRST_ROW - 22
    d.text((1056, head_y), 'valoare · IC 95%', font=F(13, 'SemiBold'), fill=MUTED)
    section_label(d, 88, row_top(1) - 32, 'Cele 4 tipare radar (împreună dau totalul)')
    d.line((88, row_top(1) - 42, 1232, row_top(1) - 42), fill=LINE, width=1)

    layer = Layer(W, H)
    for i, (key, title, sub, _) in enumerate(ROWS):
        top = row_top(i)
        mid = top + ROW_H / 2
        values = placebo[key]
        d.text((88, mid - 25), title, font=F(19, 'SemiBold'), fill=TXT)
        d.text((88, mid + 3), sub, font=F(14), fill=MUTED)
        rows = ((mid - BAR_H - 4, values['primavara_pct'], values['ic95_primavara_pct'], SPRING_RGB),
                (mid + 4, values['toamna_pct'], values['ic95_toamna_pct'], STUBBLE_RGB))
        for y, value, interval, color in rows:
            bar_with_interval(layer, y, value, interval, color)
            number = f'{fmt_dec(value, 2)}%'
            d.text((1056, y - 3), number, font=F(18, 'Bold'), fill=TXT)
            d.text((1056 + 66, y + 1), f'{fmt_dec(interval[0], 2)}…{fmt_dec(interval[1], 2)}', font=F(14), fill=TXT2)
    img.alpha_composite(layer.get())


def draw_test(img):
    d = ImageDraw.Draw(img)
    x, y = 1300, 248
    card(img, (1280, 200, 1856, 470))
    section_label(d, x, 216, 'Testul placebo')
    lines = (
        (0, 'Regula caută umezire fără ploaie: VV crește cu cel puțin', TXT2),
        (25, '1,5 dB între două treceri la 12 zile, pe aceeași orbită,', TXT2),
        (50, 'cu sub 2 mm de ploaie în 5 zile și sub 5 mm în interval.', TXT2),
        (88, 'Am aplicat aceeași regulă pe miriștile de toamnă, deja', TXT2),
        (113, 'recoltate, unde irigarea nu e de așteptat în august.', TXT2),
        (151, 'Dacă regula ar vedea irigarea, pe primăvară ar apărea', TXT),
        (176, 'vizibil mai multe evenimente decât pe miriști.', TXT),
    )
    for offset, text, color in lines:
        d.text((x, y + offset), text, font=F(16, 'Medium' if color == TXT else 'Regular'), fill=color)


def draw_table(img, placebo, signatures, n_events):
    d = ImageDraw.Draw(img)
    x0, x1 = 1300, 1836
    card(img, (1280, 488, 1856, 988))
    section_label(d, x0, 504, 'Diferența: primăvară − miriști')
    columns = ((1500, 'din ev.'), (1612, 'dif. (pp)'), (x1, 'IC 95% (pp)'))
    d.text((x0, 536), 'Tipar', font=F(13, 'SemiBold'), fill=MUTED)
    for right, head in columns:
        d.text((right - F(13, 'SemiBold').getlength(head), 536), head, font=F(13, 'SemiBold'), fill=MUTED)
    d.line((x0, 558, x1, 558), fill=LINE, width=1)
    for i, (key, _, _, short) in enumerate(ROWS):
        y = 570 + i * 40
        values = placebo[key]
        share = '100%' if key == TOTAL else f"{signatures[key]['pct_din_evenimente']:.0f}%"
        low, high = values['ic95_pp']
        weight = 'SemiBold' if key == TOTAL else 'Regular'
        cells = (share, signed(values['diferenta_pp']), f'{signed(low)}…{signed(high)}')
        d.text((x0, y), short, font=F(16, weight), fill=TXT)
        for (right, _), cell in zip(columns, cells):
            d.text((right - F(16, weight).getlength(cell), y), cell, font=F(16, weight), fill=TXT)
    d.line((x0, 778, x1, 778), fill=LINE, width=1)
    message = (
        (0, 'Pe primăvară nu apar mai multe evenimente decât', 'SemiBold', 19, TXT),
        (28, 'pe miriști: intervalul diferenței include zero.', 'SemiBold', 19, TXT),
        (68, 'Singurul tipar mai frecvent pe primăvară este VH în scădere,', 'Regular', 15, TXT2),
        (91, 'compatibil cu tăierea, nu cu umezirea. Pe VH mult peste VV,', 'Regular', 15, TXT2),
        (114, 'miriștile au mai multe evenimente.', 'Regular', 15, TXT2),
        (148, f'„din ev.”: partea din cele {fmt_int(n_events)} de evenimente de primăvară.', 'Regular', 13, MUTED),
    )
    for offset, text, weight, size, color in message:
        d.text((x0, 794 + offset), text, font=F(size, weight), fill=color)


def main():
    diagnostic = json.loads((OUT / 's1_events_diagnostic.json').read_text(encoding='utf-8'))
    placebo = diagnostic['placebo_toamna']
    img = new_canvas()
    draw_header(
        img,
        'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei',
        'Semnalul radar din august nu separă irigarea',
        'Aceeași regulă radar pe culturile de primăvară și pe miriștile de toamnă: cele 4 tranziții uscate din august 2024',
        badge=False,
    )
    draw_chart(img, placebo)
    draw_test(img)
    draw_table(img, placebo, diagnostic['semnaturi'], diagnostic['evenimente']['total'])
    d = ImageDraw.Draw(img)
    d.text((64, 1008), 'Limite: pe miriști există și arături, deci placebo-ul nu e perfect; martorul de ploaie e din iulie; cauza evenimentelor nu e verificată pe teren.', font=F(14), fill=MUTED)
    draw_footer(img, 'Contains modified Copernicus Sentinel data 2024 · ERA5-Land · Fields of The World · IC 95%: bootstrap pe blocuri de 5 km')
    target = OUT / 'placebo_radar.png'
    img.convert('RGB').save(target, optimize=True)
    print('scris:', target)


if __name__ == '__main__':
    main()
