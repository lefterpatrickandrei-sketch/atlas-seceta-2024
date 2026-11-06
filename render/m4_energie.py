"""Mockup 4 — Hrană sau energie (synthetic data). 15 s video + poster."""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from common import *

MW, MH, PXM = MAP[2], MAP[3], 10.0
OUT = str(__import__('pathlib').Path(__file__).resolve().parent / 'out') + '/'
YEARS = list(range(2017, 2027))
PLAN = [(2019, 38, 'arabil'), (2021, 26, 'pajiste'), (2023, 62, 'arabil'), (2023, 92, 'arabil'),
        (2023, 34, 'pajiste'), (2024, 118, 'arabil'), (2024, 48, 'arabil'), (2025, 146, 'arabil'),
        (2025, 70, 'arabil'), (2025, 44, 'pajiste'), (2026, 84, 'arabil')]
HOT = (255, 92, 196)
ARABLE_C = YELLOW
PAST_C = AQUA


def build(seed=41):
    rng = np.random.default_rng(seed)
    fd = make_fields(MH, MW, PXM, theta=-8, seed=seed, bu=(900, 2000), bv=(800, 1700), strip=(130, 460),
                     big_p=0.35, road_p=0.6)
    f = fd['field']
    rv_m, rv_d, _ = river(MH, MW, seed + 1, x0=150, amp=60, wl=900, width=10, vertical=False, extra=0.4)
    water = rv_m
    n1 = fbm(MH, MW, seed + 2, cells=(16, 32, 64))
    forest = (rv_d < 10 + 26 * n1) & ~water
    forest |= blobs(MH, MW, [(1000, 560)], [60], seed + 3)
    village = blobs(MH, MW, [(260, 420), (820, 330)], [56, 44], seed + 4, rough=0.45)
    nonag = water | forest | village
    nf = fd['nf']
    ag_frac = np.bincount(f.ravel(), weights=(~nonag).ravel(), minlength=nf) / np.maximum(fd['area_px'], 1)
    is_ag = ag_frac > 0.98
    pasture = (rng.random(nf) < 0.12) & is_ag
    # adjacency through shared edges
    pairs = set()
    a, b = f[:, 1:].ravel(), f[:, :-1].ravel()
    m = a != b
    pairs |= set(zip(a[m].tolist(), b[m].tolist()))
    a, b = f[1:, :].ravel(), f[:-1, :].ravel()
    m = a != b
    pairs |= set(zip(a[m].tolist(), b[m].tolist()))
    nbr = {i: set() for i in range(nf)}
    for x, y in pairs:
        nbr[x].add(y)
        nbr[y].add(x)
    area_ha = fd['area_px'] * PXM * PXM / 1e4
    used = np.zeros(nf, bool)
    parks = []
    order = rng.permutation(nf)
    for year, target, prev in PLAN:
        best = None
        for s in order:
            if used[s] or not is_ag[s] or (prev == 'pajiste') != bool(pasture[s]):
                continue
            if any(used[t] for t in nbr[s]):
                continue
            cy, cx = fd['cy'][s], fd['cx'][s]
            if cy < 60 or cy > MH - 120 or cx < 40 or cx > MW - 40:
                continue
            grp, tot = [s], area_ha[s]
            frontier = [t for t in nbr[s] if is_ag[t] and fd['blockof'][t] == fd['blockof'][s]]
            while tot < target * 0.85 and frontier:
                t = frontier.pop(0)
                if t in grp or used[t]:
                    continue
                grp.append(t)
                tot += area_ha[t]
                frontier += [u for u in nbr[t] if is_ag[u] and fd['blockof'][u] == fd['blockof'][s] and u not in grp]
            if abs(tot - target) / target < 0.3:
                best = (grp, tot)
                break
        if best is None:
            continue
        grp, tot = best
        for g in grp:
            used[g] = True
            for t in nbr[g]:
                used[t] = used[t] or False
        mask = np.isin(f, grp)
        mask = ndimage.binary_erosion(mask, iterations=2)
        parks.append(dict(year=year, mask=mask, ha=mask.sum() * PXM * PXM / 1e4, prev=prev,
                          cy=float(np.nonzero(mask)[0].mean()), cx=float(np.nonzero(mask)[1].mean())))
        for g in grp:
            for t in nbr[g]:
                used[t] = True
    tex = 0.93 + 0.14 * fbm(MH, MW, seed + 5, cells=(64, 128, 256))
    rngc = np.random.default_rng(seed + 6)
    crops = rngc.choice(4, (len(YEARS), nf), p=[0.36, 0.40, 0.16, 0.08])
    bright = rngc.normal(1, 0.04, (len(YEARS), nf))
    vcls = np.kron(rngc.choice(4, (MH // 3 + 1, MW // 3 + 1), p=[0.5, 0.22, 0.16, 0.12]), np.ones((3, 3), int))[:MH, :MW]
    street = village & ((np.mod(fd['U'], 130) < 11) | (np.mod(fd['V'], 150) < 11))
    return dict(f=f, nf=nf, fd=fd, water=water, forest=forest, village=village, nonag=nonag, is_ag=is_ag,
                pasture=pasture, parks=parks, tex=tex, crops=crops, bright=bright, edges=fd['edge'],
                road=fd['road'], vcls=vcls, street=street)


CROP_RGB = np.array([(186, 164, 92), (70, 112, 56), (112, 90, 70), (150, 140, 96)], np.float32)
PASTURE = np.array((104, 124, 74), np.float32)


def year_rgb(S, yi):
    year = YEARS[yi]
    col = CROP_RGB[S['crops'][yi]] * S['bright'][yi][:, None]
    col[S['pasture']] = PASTURE * S['bright'][yi][S['pasture']][:, None]
    rgb = col[S['f']] * S['tex'][..., None]
    rgb[S['forest']] = np.array((33, 60, 38)) * (0.8 + 0.3 * S['tex'][S['forest']][:, None] - 0.1)
    pal = np.array([(62, 88, 54), (150, 98, 80), (170, 166, 158), (116, 112, 104)], np.float32)
    vm = S['village']
    rgb[vm] = pal[S['vcls'][vm]] * S['tex'][vm][:, None]
    rgb[S['street']] = (128, 124, 116)
    rgb[S['water']] = (28, 52, 70)
    ag = ~S['nonag']
    rgb[S['edges'] & ag] *= 0.82
    rgb[S['road'] & ag] = (156, 150, 140)
    yy, xx = np.mgrid[0:MH, 0:MW]
    stripes = (yy % 3 == 0)
    for p in S['parks']:
        m = p['mask']
        if year == p['year'] - 1:
            rgb[m] = np.array((196, 178, 146)) * S['tex'][m][:, None]
        elif year >= p['year']:
            pv = np.where(stripes[m][:, None], (74, 86, 100), (36, 46, 58)).astype(np.float32)
            rgb[m] = pv
            inner = m & ((xx - int(p['cx'])) % 34 == 0)
            rgb[inner] = (120, 120, 116)
            ol = outline(m, 1)
            rgb[ol] = (150, 146, 138)
    return np.clip(rgb, 0, 255)


def base_chrome():
    img = new_canvas()
    draw_header(img, 'GIS Day 2026 · Ideea 4 · neutralitate climatică vs. hrană',
                'Hrană sau energie: câmpurile devenite parcuri solare',
                'Fiecare parc fotovoltaic, detectat de un model U-Net pe compozite anuale Sentinel-2, 2017–2026',
                accent=HOT)
    draw_footer(img, 'Date simulate pentru design · versiunea finală: compozite anuale Sentinel-2 L2A, etichete OSM '
                     '(plant:source=solar), EUCROPMAP 2018, ESA WorldCover · EPSG:3844')
    x = PX0
    card(img, (x, 200, x + PW, 330))
    card(img, (x, 350, x + PW, 760))
    card(img, (x, 780, x + PW, 996))
    d = ImageDraw.Draw(img)
    section_label(d, x + 20, 366, 'Teren agricol convertit în parc solar · ha / an')
    section_label(d, x + 20, 796, 'Cum lucrează modelul')
    lines = ['1. Etichete: poligoanele OSM cu plant:source=solar', '2. U-Net pe compozite Sentinel-2 de vară, 10 m',
             '3. Anul construirii = prima apariție a parcului', '4. „Ce era înainte” din EUCROPMAP și WorldCover']
    for i, s in enumerate(lines):
        d.text((x + 20, 828 + i * 36), s, font=F(17), fill=TXT)
    return img


def bars(S, year_f):
    w, h = PW - 40, 340
    L = Layer(w, h)
    pl, pr, pt, pb = 40, 8, 50, 30
    per = {y: [0.0, 0.0] for y in YEARS}
    for p in S['parks']:
        per[p['year']][0 if p['prev'] == 'arabil' else 1] += p['ha']
    ymax = 50 * np.ceil(max(sum(v) for v in per.values()) / 50 + 0.2)
    X = lambda i: pl + i * (w - pl - pr) / len(YEARS)
    bw = (w - pl - pr) / len(YEARS)
    Y = lambda v: pt + (1 - v / ymax) * (h - pt - pb)
    for v in np.arange(0, ymax + 1, 50):
        L.line([(pl, Y(v)), (w - pr, Y(v))], GRID + (255,), 1)
        L.text((pl - 8, Y(v) - 8), str(int(v)), 12, MUTED + (255,), anchor='r')
    for i, y in enumerate(YEARS):
        L.text((X(i) + bw / 2, h - pb + 8), f"'{str(y)[2:]}", 12, MUTED + (255,), anchor='m')
        grow = np.clip(year_f - (y - 0.5), 0, 1)
        if grow <= 0:
            continue
        a, pz = per[y]
        x0 = X(i) + 6
        x1 = X(i) + bw - 6
        if a > 0 and Y(0) - Y(a * grow) >= 1:
            L.rect((x0, Y(a * grow), x1, Y(0)), fill=ARABLE_C + (255,), radius=0)
        if pz > 0:
            top, bot = Y((a + pz) * grow), Y(a * grow) - (2 if a > 0 else 0)
            if bot - top >= 1:
                L.rect((x0, top, x1, bot), fill=PAST_C + (255,), radius=0)
    # legend inside chart (top)
    L.rect((pl, 6, pl + 14, 20), fill=ARABLE_C + (255,), radius=3)
    L.text((pl + 22, 4), 'era teren arabil', 13, TXT + (255,))
    L.rect((pl + 170, 6, pl + 184, 20), fill=PAST_C + (255,), radius=3)
    L.text((pl + 192, 4), 'era pajiște', 13, TXT + (255,))
    return L.get()


def render(S, years_rgb, base, year_f, outro=0.0):
    img = base.copy()
    i0 = int(np.clip(np.floor(year_f - 2017), 0, len(YEARS) - 1))
    frac = np.clip(year_f - 2017 - i0, 0, 1)
    blend_t = ease((frac - 0.7) / 0.3) if i0 < len(YEARS) - 1 else 0.0
    rgb = years_rgb[i0] if blend_t <= 0 else years_rgb[i0] * (1 - blend_t) + years_rgb[i0 + 1] * blend_t
    cur_year = YEARS[i0] if blend_t < 0.5 else YEARS[min(i0 + 1, len(YEARS) - 1)]
    rgb = rgb.copy()
    tags = []
    for p in S['parks']:
        if cur_year >= p['year']:
            age = year_f - p['year']
            a = float(np.clip(age / 0.4, 0, 1)) if outro == 0 else 1.0
            ol = outline(p['mask'], 2)
            rgb[ol] = rgb[ol] * (1 - a) + np.array(HOT) * a
            tags.append((p, a))
    paste_map(img, np.clip(rgb, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for p, a in tags:
        tx, ty = MAP[0] + p['cx'], MAP[1] + p['cy']
        s = f"{p['year']} · {int(round(p['ha']))} ha"
        f = F(14, 'SemiBold')
        wbox = int(f.getlength(s)) + 20
        bx, by = int(tx - wbox / 2), int(ty - 14)
        shade_box(img, (bx, by, bx + wbox, by + 28), alpha=int(220 * a), color=(30, 14, 30))
        d.text((bx + 10, by + 5), s, font=f, fill=HOT + (int(255 * a),))
    # furniture
    x, y = MAP[0] + 18, MAP[1] + MAP[3] - 92
    shade_box(img, (x, y, x + 300, y + 74), alpha=205)
    scale_bar(img, PXM, 2, x + 18, y + 22)
    north_arrow(img, x + 262, y + 8, 22)
    d.text((x + 18, y + 50), 'EPSG:3844 · Stereo 70', font=F(12), fill=MUTED)
    lx = MAP[0] + MAP[2] - 336
    shade_box(img, (lx, y + 20, lx + 318, y + 74), alpha=205)
    Lg = Layer(30, 18)
    Lg.rect((2, 2, 27, 15), outline=HOT + (255,), width=2, radius=3)
    img.alpha_composite(Lg.get(), (lx + 14, y + 38))
    d.text((lx + 52, y + 37), 'parc solar detectat de AI', font=F(15, 'Medium'), fill=TXT)
    # year + KPIs
    d.text((PX0 + 20, 210), str(cur_year), font=F(64, 'SemiBold', True), fill=TXT)
    d.text((PX0 + 22, 290), 'compozit Sentinel-2, iunie–august', font=F(15), fill=TXT2)
    done = [p for p in S['parks'] if p['year'] <= cur_year]
    ha = sum(p['ha'] for p in done)
    ha_ar = sum(p['ha'] for p in done if p['prev'] == 'arabil')
    vx = PX0 + PW - 20
    f1 = F(44, 'SemiBold', True)
    s1 = f'{fmt_int(ha_ar)} ha'
    d.text((vx - f1.getlength(s1), 220), s1, font=f1, fill=ARABLE_C)
    s2 = f'teren arabil ocupat · {len(done)} parcuri'
    d.text((vx - F(15).getlength(s2), 280), s2, font=F(15), fill=TXT2)
    img.alpha_composite(bars(S, year_f), (PX0 + 20, 398))
    if outro > 0:
        a = int(255 * outro)
        bx = (MAP[0] + MAP[2] - 490, MAP[1] + 18)
        shade_box(img, (bx[0], bx[1], bx[0] + 472, bx[1] + 84), alpha=int(215 * outro))
        d.text((bx[0] + 18, bx[1] + 12), 'Energie curată, dar pe ce teren?', font=F(19, 'SemiBold'), fill=TXT + (a,))
        d.text((bx[0] + 18, bx[1] + 42), 'Următorul pas: unde se potrivește agrivoltaicul', font=F(15),
               fill=TXT2 + (a,))
    return img


if __name__ == '__main__':
    import os, time
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    S = build()
    print('parks', [(p['year'], round(p['ha'])) for p in S['parks']], round(time.time() - t0, 1), 's')
    years_rgb = [year_rgb(S, i) for i in range(len(YEARS))]
    base = base_chrome()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if mode == 'stills':
        for yf, o, name in ((2023.2, 0, 'm4_a_2023'), (2026.0, 1, 'm4_poster')):
            render(S, years_rgb, base, yf, o).convert('RGB').save(OUT + name + '.png')
        print('ok', round(time.time() - t0, 1))
    else:
        fps = 30
        v = Video(OUT + 'm4_hrana_sau_energie.mp4', fps)
        for i in range(15 * fps):
            t = i / fps
            yf = 2017 + 9.0 * min(1.0, max(0.0, (t - 0.6) / 11.2))
            o = ease((t - 12.4) / 0.9)
            fr = render(S, years_rgb, base, yf, o)
            if t < 0.5:
                fr = Image.blend(Image.new('RGBA', fr.size, BG + (255,)), fr, ease(t / 0.5))
            v.add(fr)
        print('video rc', v.close(), round(time.time() - t0, 1), 's')
