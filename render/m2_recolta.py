"""Mockup 2 — Valul recoltei (synthetic data). 20 s video + poster."""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from common import *

MW, MH, PXM = MAP[2], MAP[3], 50.0
OUT = str(__import__('pathlib').Path(__file__).resolve().parent / 'out') + '/'
D0, D1 = 165, 312
CROPS = ['orz', 'rapita', 'grau', 'floarea', 'soia', 'porumb']
P_CROP = [0.08, 0.09, 0.32, 0.22, 0.05, 0.24]
BASE = {'orz': (175, 4), 'rapita': (181, 4), 'grau': (191, 5), 'floarea': (241, 7), 'soia': (263, 6),
        'porumb': (279, 10)}
WINTER = {'orz', 'rapita', 'grau'}
RAMP = [(0.0, (252, 224, 96)), (0.22, (248, 166, 62)), (0.48, (228, 92, 76)), (0.74, (178, 64, 132)),
        (1.0, (104, 66, 168))]
RLUT = lut_from(RAMP)
BGMAP = np.array((17, 22, 28), np.float32)


def rampc(doy):
    t = np.clip((np.asarray(doy) - 170) / (305 - 170), 0, 1)
    return RLUT[(t * 255).astype(int)]


def build(seed=21):
    rng = np.random.default_rng(seed)
    fd = make_fields(MH, MW, PXM, theta=-9, seed=seed, bu=(1500, 3200), bv=(1300, 2800), strip=(220, 720),
                     big_p=0.3, road_p=0.5)
    f = fd['field']
    rv_m, rv_d, _ = river(MH, MW, seed + 1, x0=520, amp=70, wl=700, width=7, vertical=False)
    rv2_m, rv2_d, _ = river(MH, MW, seed + 2, x0=180, amp=40, wl=520, width=4, vertical=True)
    water = rv_m | rv2_m
    n1 = fbm(MH, MW, seed + 3, cells=(24, 48, 96))
    forest = ((rv_d < 4 + 10 * n1) | (rv2_d < 3 + 6 * n1)) & ~water
    forest |= blobs(MH, MW, [(950, 120), (300, 300), (780, 700)], [26, 18, 22], seed + 4)
    towns = blobs(MH, MW, [(640, 470), (230, 610), (930, 330), (420, 160), (1040, 690), (90, 140)],
                  [22, 12, 11, 9, 10, 8], seed + 5, rough=0.5)
    nonag = water | forest | towns
    nf = fd['nf']
    ag_frac = np.bincount(f.ravel(), weights=(~nonag).ravel(), minlength=nf) / np.maximum(fd['area_px'], 1)
    is_ag = ag_frac > 0.5
    crop = rng.choice(len(CROPS), nf, p=P_CROP)
    smooth = fbm(MH, MW, seed + 6, cells=(4, 8, 16))
    sm_f = np.bincount(f.ravel(), weights=smooth.ravel(), minlength=nf) / np.maximum(fd['area_px'], 1)
    south = fd['cy'] / MH          # 0 north .. 1 south
    west = 1 - fd['cx'] / MW
    harvest = np.zeros(nf)
    for i, c in enumerate(CROPS):
        sel = crop == i
        m, s = BASE[c]
        harvest[sel] = (m - 9.0 * south[sel] - 3.0 * west[sel] + 10.0 * (sm_f[sel] - 0.5)
                        + rng.normal(0, s * 0.55, sel.sum()))
    edges = fd['edge']
    tex = 0.93 + 0.14 * fbm(MH, MW, seed + 7, cells=(64, 128, 256))
    area_ha = fd['area_px'] * PXM * PXM / 1e4
    return dict(field=f, nf=nf, crop=crop, harvest=harvest, is_ag=is_ag, edges=edges, road=fd['road'],
                water=water, forest=forest, towns=towns, nonag=nonag, tex=tex, area_ha=area_ha)


STAND_W = np.array((98, 90, 58), np.float32)    # standing winter cereal / rapeseed (ripe, golden-dim)
STAND_S = np.array((50, 70, 46), np.float32)    # standing summer crop


def map_rgb(S, doy, glow_days=3.5):
    nf = S['nf']
    winter = np.isin(S['crop'], [CROPS.index(c) for c in WINTER])
    col = np.where(winter[:, None], STAND_W, STAND_S).astype(np.float32)
    h = S['harvest']
    done = h <= doy
    col[done] = rampc(h[done]) * 0.74
    recent = done & (doy - h < glow_days)
    k = np.clip(1 - (doy - h[recent]) / glow_days, 0, 1)[:, None]
    col[recent] = col[recent] * (1 - 0.33 * k) + np.array((255, 236, 200)) * 0.33 * k
    col[~S['is_ag']] = BGMAP
    rgb = col[S['field']] * S['tex'][..., None]
    rgb[S['forest']] = (26, 40, 31)
    rgb[S['water']] = (30, 58, 82)
    tm = S['towns']
    rgb[tm] = np.array((74, 78, 86), np.float32) * (0.8 + 0.4 * S['tex'][tm][:, None] - 0.2)
    rgb[S['edges'] & ~S['nonag']] *= 0.62
    rgb[S['road'] & ~S['nonag']] = (34, 40, 48)
    # glow halo around fields harvested in the last days
    rmask = recent_mask = np.isin(S['field'], np.flatnonzero(recent)) & ~S['nonag']
    if rmask.any():
        g = ndimage.gaussian_filter(rmask.astype(np.float32), 5)
        rgb += g[..., None] * np.array((255, 196, 110), np.float32) * 0.5
    return np.clip(rgb, 0, 255).astype(np.uint8)


def weekly(S):
    edges = np.arange(D0, D1 + 7, 7)
    ag = S['is_ag']
    hist = np.histogram(S['harvest'][ag], bins=edges, weights=S['area_ha'][ag])[0] / 1000.0
    return edges, hist


def base_chrome():
    img = new_canvas()
    draw_header(img, 'GIS Day 2026 · Ideea 2 · agricultură și climă',
                'Valul recoltei: recolta ca un front meteo',
                'Ziua recoltării pe fiecare parcelă, detectată automat din serii Sentinel-1 și Sentinel-2', accent=AMBER)
    draw_footer(img, 'Date simulate pentru design · versiunea finală: Sentinel-1 GRD, Sentinel-2 L2A, parcele FTW, '
                     'tipul culturii din JRC EUCROPMAP + Galileo · EPSG:3844')
    x = PX0
    card(img, (x, 200, x + PW, 330))
    card(img, (x, 350, x + PW, 742))
    card(img, (x, 762, x + PW, 996))
    d = ImageDraw.Draw(img)
    section_label(d, x + 20, 366, 'Suprafață recoltată pe săptămână · mii ha')
    section_label(d, x + 20, 778, 'Legendă')
    # legend content (static)
    ramp_bar(img, x + 20, 812, PW - 40, 12, RAMP,
             labels=[(0.0, 'iun'), (0.096, '1 iul'), (0.326, '1 aug'), (0.556, '1 sep'), (0.778, '1 oct'), (1.0, 'nov')])
    d.text((x + 20, 852), 'Culoarea = ziua recoltării', font=F(14), fill=TXT2)
    for i, (c, s) in enumerate(((STAND_W, 'grâu, orz, rapiță în picioare'), (STAND_S, 'porumb, floarea-soarelui în picioare'))):
        yy = 892 + i * 30
        d.rounded_rectangle((x + 20, yy, x + 44, yy + 16), radius=3, fill=tuple(int(v) for v in c))
        d.text((x + 56, yy - 1), s, font=F(15), fill=TXT)
    g = Layer(26, 20)
    g.rect((1, 2, 25, 18), fill=(255, 214, 140, 255), radius=3)
    img.alpha_composite(g.get(), (x + 330, 892))
    d.text((x + 366, 891), 'recoltat în ultimele 3 zile', font=F(15), fill=TXT)
    return img


def hist_chart(S, wk, doy):
    edges, hist = wk
    w, h = PW - 40, 330
    L = Layer(w, h)
    pl, pr, pt, pb = 36, 8, 46, 30
    ymax = max(5, np.ceil(hist.max() / 5) * 5)
    X = lambda dd: pl + (dd - D0) / (D1 + 7 - D0) * (w - pl - pr)
    Y = lambda v: pt + (1 - v / ymax) * (h - pt - pb)
    step = 5 if ymax <= 30 else 10
    for v in np.arange(0, ymax + 0.1, step):
        L.line([(pl, Y(v)), (w - pr, Y(v))], GRID + (255,), 1)
        L.text((pl - 8, Y(v) - 8), str(int(v)), 12, MUTED + (255,), anchor='r')
    for m, dd in ((6, 153), (7, 183), (8, 214), (9, 245), (10, 275), (11, 306)):
        if D0 <= dd <= D1:
            L.text((X(dd), h - pb + 8), RO_MON3[m - 1].capitalize(), 12, MUTED + (255,), anchor='m')
    bw = (X(edges[1]) - X(edges[0]))
    for i in range(len(hist)):
        e0, e1 = edges[i], edges[i + 1]
        if e0 > doy:
            continue
        frac = 1.0 if doy >= e1 else (doy - e0) / 7.0
        v = hist[i] * frac
        c = tuple(int(t) for t in rampc((e0 + e1) / 2))
        x0 = X(e0) + 1
        L.rect((x0, Y(v), x0 + bw - 2, Y(0)), fill=c + (255,), radius=3 if v > 0.6 else 0)
    # wave annotations once each wave is past its peak
    peaks = ((0, 205, 'valul de vară', 'grâu · orz · rapiță'), (1, 300, 'valul de toamnă', 'floarea-soarelui · porumb'))
    for j, show_after, a, b in peaks:
        if doy < show_after:
            continue
        lo, hi = (D0, 225) if j == 0 else (225, D1)
        sel = [(i, hist[i]) for i in range(len(hist)) if lo <= edges[i] < hi]
        i_max = max(sel, key=lambda t: t[1])[0]
        cx = X(edges[i_max]) + bw + 8
        ty = Y(hist[i_max]) + 2
        L.text((cx, ty), a, 13, TXT + (255,), 'SemiBold')
        L.text((cx, ty + 17), b, 12, TXT2 + (255,))
    return L.get()


def render(S, wk, base, doy, outro=0.0):
    img = base.copy()
    paste_map(img, map_rgb(S, doy))
    # map furniture
    x, y = MAP[0] + 18, MAP[1] + MAP[3] - 92
    shade_box(img, (x, y, x + 300, y + 74), alpha=205)
    scale_bar(img, PXM, 10, x + 18, y + 22)
    north_arrow(img, x + 262, y + 8, 22)
    d = ImageDraw.Draw(img)
    d.text((x + 18, y + 50), 'EPSG:3844 · Stereo 70', font=F(12), fill=MUTED)
    # date card
    day, mon = doy_to_date(doy)
    d.text((PX0 + 20, 214), f'{day} {RO_MONTHS[mon - 1]}', font=F(58, 'SemiBold', True), fill=TXT)
    d.text((PX0 + 22, 288), f'2024 · ziua {int(doy)} din an', font=F(16), fill=TXT2)
    ag = S['is_ag']
    done = (S['harvest'] <= doy) & ag
    pct = 100 * S['area_ha'][done].sum() / S['area_ha'][ag].sum()
    vx = PX0 + PW - 20
    f1, f2 = F(44, 'SemiBold', True), F(15)
    s = f'{int(round(pct))}%'
    d.text((vx - f1.getlength(s), 222), s, font=f1, fill=AMBER)
    s2 = f'{fmt_int(done.sum())} parcele recoltate'
    d.text((vx - f2.getlength(s2), 280), s2, font=f2, fill=TXT2)
    img.alpha_composite(hist_chart(S, wk, doy), (PX0 + 20, 392))
    if outro > 0:
        a = int(255 * outro)
        bx = (MAP[0] + MAP[2] - 520, MAP[1] + 18)
        shade_box(img, (bx[0], bx[1], bx[0] + 502, bx[1] + 84), alpha=int(215 * outro))
        d.text((bx[0] + 18, bx[1] + 12), 'Două fronturi, același câmp de date', font=F(19, 'SemiBold'), fill=TXT + (a,))
        d.text((bx[0] + 18, bx[1] + 42), 'Recolta urcă dinspre sud spre nord, de două ori pe an', font=F(15),
               fill=TXT2 + (a,))
    return img


if __name__ == '__main__':
    import os, time
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    S = build()
    wk = weekly(S)
    base = base_chrome()
    print('built', round(time.time() - t0, 1), 's; fields', S['nf'], 'max week kha', wk[1].max().round(1))
    mode = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if mode == 'stills':
        for doy, o, name in ((192, 0, 'm2_a_july'), (268, 0, 'm2_b_sept'), (D1, 1, 'm2_poster')):
            t1 = time.time()
            render(S, wk, base, doy, o).convert('RGB').save(OUT + name + '.png')
            print(name, round(time.time() - t1, 2), 's')
    else:
        fps = 30
        v = Video(OUT + 'm2_valul_recoltei.mp4', fps)
        n = 20 * fps
        for i in range(n):
            t = i / fps
            doy = D0 + (D1 - D0) * min(1.0, max(0.0, (t - 0.8) / 16.7))
            o = ease((t - 17.8) / 1.0)
            fr = render(S, wk, base, doy, o)
            if t < 0.5:
                fr = Image.blend(Image.new('RGBA', fr.size, BG + (255,)), fr, ease(t / 0.5))
            v.add(fr)
        print('video rc', v.close(), round(time.time() - t0, 1), 's')
