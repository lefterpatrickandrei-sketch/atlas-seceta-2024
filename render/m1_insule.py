"""Mockup 1 — Insulele verzi (synthetic data). Poster + 15 s video."""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from common import *

MW, MH, PXM = MAP[2], MAP[3], 20.0
OUT = str(__import__('pathlib').Path(__file__).resolve().parent / 'out') + '/'

CROPS = ['grau', 'orz', 'rapita', 'porumb', 'floarea', 'soia', 'pajiste']
P_CROP = [0.30, 0.08, 0.10, 0.25, 0.19, 0.05, 0.03]
SUMMER = {'porumb', 'floarea', 'soia'}

CURVES = {
    ('grau', 0): [(100, .80), (140, .82), (158, .70), (172, .42), (182, .30), (215, .28)],
    ('orz', 0): [(100, .78), (132, .80), (150, .64), (164, .38), (174, .30), (215, .28)],
    ('rapita', 0): [(100, .70), (130, .72), (150, .62), (165, .40), (178, .28), (215, .26)],
    ('porumb', 0): [(100, .12), (130, .16), (150, .32), (170, .52), (190, .60), (205, .48), (220, .34), (240, .28), (280, .24)],
    ('porumb', 1): [(100, .12), (130, .17), (150, .38), (170, .66), (190, .84), (215, .86), (235, .80), (255, .62), (280, .45)],
    ('floarea', 0): [(100, .12), (128, .20), (150, .42), (170, .58), (185, .56), (205, .38), (225, .28), (280, .25)],
    ('floarea', 1): [(100, .12), (128, .20), (150, .45), (170, .70), (190, .76), (210, .66), (230, .48), (280, .38)],
    ('soia', 0): [(100, .12), (140, .18), (160, .36), (185, .52), (205, .46), (225, .32), (280, .26)],
    ('soia', 1): [(100, .12), (140, .18), (160, .42), (185, .76), (210, .85), (235, .74), (280, .50)],
    ('pajiste', 0): [(100, .52), (150, .48), (180, .34), (210, .24), (240, .22), (280, .26)],
}

VEG_LUT = lut_from([(0.0, (92, 76, 58)), (0.15, (122, 100, 74)), (0.25, (150, 128, 90)), (0.35, (152, 142, 96)),
                    (0.5, (108, 128, 72)), (0.65, (70, 118, 56)), (0.8, (40, 102, 47)), (1.0, (26, 84, 40))])
STUBBLE = np.array((190, 170, 124), np.float32)
PLOWED = np.array((88, 69, 52), np.float32)
BLOOM = np.array((222, 196, 52), np.float32)
WATER = np.array((26, 50, 68), np.float32)
FOREST = np.array((33, 60, 38), np.float32)
VILLAGE = np.array((122, 118, 112), np.float32)
ROAD = np.array((150, 146, 138), np.float32)
CANAL = np.array((44, 92, 116), np.float32)

D0, D1 = 121, 258   # 1 May .. 14 Sep 2024


def build(seed=11):
    rng = np.random.default_rng(seed)
    fd = make_fields(MH, MW, PXM, theta=-11, seed=seed, strip=(170, 560))
    f = fd['field']
    # Danube arms: main arm west, a branch separating the polder from the eastern terrace
    rw_m, rw_d, _ = river(MH, MW, seed + 1, x0=46, amp=26, wl=520, width=30)
    rb_m, rb_d, rb_pts = river(MH, MW, seed + 2, x0=712, amp=38, wl=460, width=15)
    water = rw_m | rb_m
    n1 = fbm(MH, MW, seed + 3, cells=(16, 32, 64))
    forest = ((rw_d < 16 + 18 * n1) | (rb_d < 9 + 16 * n1)) & ~water
    forest |= blobs(MH, MW, [(1040, 120), (930, 700)], [34, 26], seed + 4)
    village = blobs(MH, MW, [(880, 300), (1010, 560), (330, 640)], [26, 32, 18], seed + 5, rough=0.5)
    # irrigation canals inside the polder (x < river branch)
    polder_x = np.array([np.interp(y, [p[1] for p in rb_pts], [p[0] for p in rb_pts]) for y in range(MH)])
    xx = np.tile(np.arange(MW), (MH, 1))
    in_polder = (xx > 70) & (xx < polder_x[:, None] - 12)
    canal = np.zeros((MH, MW), bool)
    ub, vb = fd['ub'], fd['vb']
    for u0 in ub[2::3]:
        canal |= np.abs(fd['U'] - u0) < 16
    for v0 in vb[1::3]:
        canal |= np.abs(fd['V'] - v0) < 14
    canal &= in_polder & ~water & ~forest & ~village
    nonag = water | forest | village
    nf = fd['nf']
    ag_frac = np.bincount(f.ravel(), weights=(~nonag).ravel(), minlength=nf) / np.maximum(fd['area_px'], 1)
    is_ag = ag_frac > 0.6
    polder_f = np.zeros(nf, bool)
    cyi = np.clip(fd['cy'].astype(int), 0, MH - 1)
    polder_f[:] = (fd['cx'] > 75) & (fd['cx'] < polder_x[cyi] - 12)
    crop = rng.choice(len(CROPS), nf, p=P_CROP)
    # pivots: largest compact polder fields + two on the terrace
    field = f.copy()
    pivots = []
    cand = np.argsort(-fd['area_px'])
    want_p, want_e = 11, 2
    for fid in cand:
        if want_p == 0 and want_e == 0:
            break
        if not is_ag[fid] or ag_frac[fid] < 0.97:
            continue
        if polder_f[fid] and want_p == 0:
            continue
        if (not polder_f[fid]) and want_e == 0:
            continue
        ys, xs = np.nonzero(f == fid)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        sub = (f[y0:y1, x0:x1] == fid)
        dist = ndimage.distance_transform_edt(np.pad(sub, 1))[1:-1, 1:-1]
        r = dist.max()
        if r < 14:
            continue
        cy_, cx_ = np.unravel_index(np.argmax(dist), dist.shape)
        rr = min(r - 1.5, 27)
        yy, xg = np.mgrid[y0:y1, x0:x1]
        circ = sub & (np.hypot(yy - (y0 + cy_), xg - (x0 + cx_)) <= rr)
        pivots.append((len(pivots), y0 + cy_, x0 + cx_, rr, circ, (y0, x0)))
        if polder_f[fid]:
            want_p -= 1
        else:
            want_e -= 1
    n_piv = len(pivots)
    piv_ids = []
    for i, cy_, cx_, rr, circ, (y0, x0) in pivots:
        nid = nf + i
        sl = field[y0:y0 + circ.shape[0], x0:x0 + circ.shape[1]]
        sl[circ] = nid
        piv_ids.append(nid)
    NF = nf + n_piv
    crop = np.r_[crop, np.full(n_piv, CROPS.index('porumb'))]
    polder_f = np.r_[polder_f, np.ones(n_piv, bool)]
    is_ag = np.r_[is_ag, np.ones(n_piv, bool)]
    irr = np.zeros(NF, bool)
    pr = np.where(polder_f, 1.0, 0.0)
    for fid in range(nf):
        c = CROPS[crop[fid]]
        if c in ('porumb', 'soia'):
            irr[fid] = rng.random() < (0.62 if polder_f[fid] else 0.05)
        elif c == 'floarea':
            irr[fid] = rng.random() < (0.15 if polder_f[fid] else 0.02)
    irr[nf:] = True
    # pivot corners stay rainfed: parent fields of pivots become dry stubble/soil
    phase = rng.normal(0, 4, NF)
    amp = rng.uniform(0.92, 1.04, NF)
    east = (np.r_[fd['cx'], [p[2] for p in pivots]] / MW)
    amp = amp - np.where(irr, 0, 0.10 * east)  # eastern terrace drier
    harvest = np.full(NF, 999.0)
    hmap = {'grau': (186, 5), 'orz': (176, 4), 'rapita': (181, 4), 'floarea': (238, 7), 'soia': (255, 6),
            'porumb': (258, 9)}
    for fid in range(NF):
        c = CROPS[crop[fid]]
        if c in hmap:
            m, s = hmap[c]
            if irr[fid]:
                m += 14
            harvest[fid] = m + rng.normal(0, s)
    plow = np.where(rng.random(NF) < 0.55, harvest + rng.uniform(14, 45, NF), 999.0)
    bright = rng.normal(1.0, 0.035, NF)
    # static texture
    tex = 0.94 + 0.12 * fbm(MH, MW, seed + 9, cells=(48, 96, 192))
    tex2 = 0.9 + 0.2 * fbm(MH, MW, seed + 10, cells=(64, 128, 256))
    edges = np.zeros((MH, MW), bool)
    edges[:, 1:] |= field[:, 1:] != field[:, :-1]
    edges[1:, :] |= field[1:, :] != field[:-1, :]
    rng2 = np.random.default_rng(seed + 12)
    rr = rng2.random((MH, MW))
    gard = fbm(MH, MW, seed + 13, cells=(96, 192, 384)) > 0.5
    vcls = np.where(gard, 0, np.where(rr < 0.45, 1, np.where(rr < 0.8, 2, 3)))
    vcls[(rr > 0.93)] = 1
    roofs = village & (vcls == 1)
    area_px = np.bincount(field.ravel(), minlength=NF).astype(float)
    return dict(vcls=vcls, field=field, NF=NF, crop=crop, irr=irr, is_ag=is_ag, polder=polder_f, phase=phase, amp=amp,
                harvest=harvest, plow=plow, bright=bright, tex=tex, tex2=tex2, edges=edges, water=water,
                forest=forest, village=village, roofs=roofs, road=fd['road'], canal=canal, nonag=nonag,
                pivots=pivots, piv_ids=np.array(piv_ids), area_px=area_px, nf_base=nf)


def ndvi_at(S, doy):
    NF = S['NF']
    out = np.zeros(NF, np.float32)
    for (c, ir), pts in CURVES.items():
        ci = CROPS.index(c)
        sel = (S['crop'] == ci) & (S['irr'] == bool(ir)) if c in SUMMER else (S['crop'] == ci)
        if not sel.any():
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        out[sel] = np.interp(doy - S['phase'][sel], xs, ys) * S['amp'][sel]
    return np.clip(out, 0, 1)


def field_colors(S, doy):
    v = ndvi_at(S, doy)
    col = VEG_LUT[np.clip((v * 255).astype(int), 0, 255)].copy()
    harvested = doy >= S['harvest']
    plowed = doy >= S['plow']
    col[harvested] = STUBBLE * (0.95 + 0.1 * (S['bright'][harvested, None] - 1))
    col[plowed] = PLOWED
    rap = S['crop'] == CROPS.index('rapita')
    bloom = np.clip((136 - (doy - S['phase'][rap])) / 18.0, 0, 1) * 0.75
    col[rap] = col[rap] * (1 - bloom[:, None]) + BLOOM * bloom[:, None]
    col *= S['bright'][:, None]
    return col, v


def map_rgb(S, doy):
    col, _ = field_colors(S, doy)
    fld = S['field']
    rgb = col[fld] * S['tex'][..., None]
    rgb[S['forest']] = FOREST * S['tex2'][S['forest']][:, None]
    vm = S['village']
    vpal = np.array([(58, 84, 50), (150, 98, 80), (168, 164, 156), (112, 108, 100)], np.float32)
    rgb[vm] = vpal[S['vcls'][vm]] * S['tex'][vm][:, None]
    rgb[S['water']] = WATER * (0.95 + 0.1 * S['tex2'][S['water']][:, None])
    rgb[S['canal']] = CANAL
    ag = ~S['nonag']
    e = S['edges'] & ag
    rgb[e] *= 0.80
    rgb[S['road'] & ag] = ROAD
    return np.clip(rgb, 0, 255)


def season_stats(S):
    days = np.arange(D0, D1 + 1)
    summer_ids = np.isin(S['crop'], [CROPS.index(c) for c in SUMMER]) & S['is_ag']
    res = {k: [] for k in ('irr', 'dry')}
    for d in days:
        v = ndvi_at(S, d)
        h = S['harvest']
        for k, m in (('irr', summer_ids & S['irr']), ('dry', summer_ids & ~S['irr'])):
            mm = m & (h > d)
            vv = v[mm] if mm.any() else v[m]
            res[k].append(np.percentile(vv, [25, 50, 75]))
    return days, {k: np.array(v) for k, v in res.items()}


# ---------------------------------------------------------------- rendering ----
def base_chrome():
    img = new_canvas()
    draw_header(img, 'GIS Day 2026 · Ideea 1 · reziliență prin irigații',
                'Insulele verzi: cine a rezistat secetei din 2024',
                'Parcelele irigate efectiv, detectate automat din Sentinel-1/2, și răcirea lor măsurată din Sentinel-3')
    draw_footer(img, 'Date simulate pentru design · versiunea finală: Sentinel-2 L2A, Sentinel-1 GRD, '
                     'Sentinel-3 SLSTR LST, ERA5-Land, parcele FTW · EPSG:3844')
    x = PX0
    card(img, (x, 200, x + 296, 322))
    card(img, (x + 320, 200, x + PW, 322))
    card(img, (x, 342, x + PW, 700))
    card(img, (x, 720, x + PW, 996))
    d = ImageDraw.Draw(img)
    section_label(d, x + 20, 216, 'Irigat detectat (AI)')
    section_label(d, x + 340, 216, 'Răcire măsurată')
    section_label(d, x + 20, 358, 'NDVI median · culturi de vară')
    section_label(d, x + 20, 736, 'Temperatura suprafeței · 1 aug 2024')
    return img


def kpi(d, x, y, value, sub, alpha=255):
    d.text((x, y), value, font=F(44, 'SemiBold', True), fill=TXT + (alpha,))
    d.text((x + 1, y + 54), sub, font=F(16), fill=TXT2 + (alpha,))


def chart(S, stats, doy, cur_visible=True):
    days, st = stats
    w, h = PW - 40, 296
    L = Layer(w, h)
    pl, pr, pt, pb = 40, 64, 14, 34
    X = lambda dd: pl + (dd - D0) / (D1 - D0) * (w - pl - pr)
    Y = lambda v: pt + (1 - v / 1.0) * (h - pt - pb)
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        L.line([(pl, Y(v)), (w - pr, Y(v))], fill=GRID + (255,), width=1)
        L.text((pl - 8, Y(v) - 8), fmt_dec(v, 2) if v not in (0, 1) else str(int(v)), 12, MUTED + (255,), anchor='r')
    for m, dd in ((5, 122), (6, 153), (7, 183), (8, 214), (9, 245)):
        L.text((X(dd), h - pb + 10), RO_MON3[m - 1].capitalize(), 12, MUTED + (255,), anchor='m')
    k = int(np.clip(doy - D0, 0, len(days) - 1)) + 1
    for key, color in (('dry', ORANGE), ('irr', CYAN)):
        q = st[key][:k]
        band = [(X(days[i]), Y(q[i, 2])) for i in range(k)] + [(X(days[i]), Y(q[i, 0])) for i in range(k - 1, -1, -1)]
        L.poly(band, color + (52,))
        L.line([(X(days[i]), Y(q[i, 1])) for i in range(k)], color + (255,), 2.4)
        L.circle(X(days[k - 1]), Y(q[k - 1, 1]), 4.5, fill=color + (255,))
    # direct labels at the line ends
    qi, qd = st['irr'][k - 1, 1], st['dry'][k - 1, 1]
    xe = X(days[k - 1]) + 10
    yi, yd = Y(qi) - 8, Y(qd) - 8
    if abs(yi - yd) < 18:
        yi, yd = (yi - 9, yd + 9) if yi < yd else (yi + 9, yd - 9)
    if k > 30:
        L.text((xe, yi), 'irigat', 13, CYAN + (255,), 'SemiBold')
        L.text((xe, yd), 'neirigat', 13, ORANGE + (255,), 'SemiBold')
    if cur_visible:
        L.line([(X(days[k - 1]), pt), (X(days[k - 1]), h - pb)], TXT2 + (110,), 1)
    return L.get()


def lst_panel(S, doy, alpha=1.0):
    v = ndvi_at(S, 214)
    summer = np.isin(S['crop'], [CROPS.index(c) for c in SUMMER]) & S['is_ag']
    li = float(np.mean(47.0 - 18.0 * v[summer & S['irr']]))
    ld = float(np.mean(47.0 - 18.0 * v[summer & ~S['irr']]))
    w, h = PW - 40, 200
    L = Layer(w, h)
    a = int(255 * alpha)
    x0, x1 = 150, w - 40
    lo, hi = 28, 46
    X = lambda t: x0 + (t - lo) / (hi - lo) * (x1 - x0)
    for t in range(28, 47, 3):
        L.line([(X(t), 18), (X(t), 128)], GRID + (a,), 1)
        L.text((X(t), 138), f'{t}°', 12, MUTED + (a,), anchor='m')
    rows = (('Parcele irigate', li, CYAN, 46), ('Parcele neirigate', ld, ORANGE, 100))
    for name, val, c, y in rows:
        L.text((0, y - 9), name, 14, TXT + (a,), 'Medium')
        L.line([(X(lo), y), (X(val), y)], c + (int(a * 0.35),), 2)
        L.circle(X(val), y, 7, fill=c + (a,), outline=CARD + (a,), width=2)
        L.text((X(val), y - 30), fmt_dec(val, 1) + ' °C', 14, TXT + (a,), 'SemiBold', anchor='m')
    L.text((0, 166), 'Sentinel-3 SLSTR (1 km), medie pe sistemele de irigații', 13, MUTED + (a,))
    return L.get(), li - ld, li, ld


def legend(img, reveal):
    x, y = MAP[0] + 18, MAP[1] + 18
    shade_box(img, (x, y, x + 316, y + 128), alpha=200)
    d = ImageDraw.Draw(img)
    section_label(d, x + 16, y + 14, 'NDVI · Sentinel-2')
    ramp_bar(img, x + 16, y + 40, 284, 10, [(0, (92, 76, 58)), (0.3, (150, 132, 92)), (0.55, (100, 128, 70)),
                                            (1, (30, 90, 42))],
             labels=[(0.0, 'sol gol'), (0.42, 'uscat'), (1.0, 'verde')])
    a = int(255 * (0.35 + 0.65 * reveal))
    L = Layer(30, 18)
    L.rect((2, 2, 27, 15), outline=CYAN + (a,), width=2, radius=3)
    img.alpha_composite(L.get(), (x + 16, y + 92))
    d.text((x + 54, y + 92), 'parcelă irigată, detectată de AI', font=F(14, 'Medium'), fill=TXT + (a,))


def timeline(img, doy):
    x0, y0 = MAP[0] + MAP[2] - 520, MAP[1] + MAP[3] - 92
    shade_box(img, (x0, y0, x0 + 502, y0 + 74), alpha=205)
    d = ImageDraw.Draw(img)
    day, mon = doy_to_date(doy)
    d.text((x0 + 18, y0 + 10), f'{day} {RO_MONTHS[mon - 1]}', font=F(26, 'SemiBold', True), fill=TXT)
    d.text((x0 + 18, y0 + 44), '2024', font=F(14, 'Medium'), fill=TXT2)
    tx0, tx1, ty = x0 + 180, x0 + 480, y0 + 30
    L = Layer(502, 74)
    L.line([(tx0 - x0, ty - y0), (tx1 - x0, ty - y0)], LINE + (255,), 4)
    p = (doy - D0) / (D1 - D0)
    L.line([(tx0 - x0, ty - y0), (tx0 - x0 + p * (tx1 - tx0), ty - y0)], CYAN + (255,), 4)
    L.circle(tx0 - x0 + p * (tx1 - tx0), ty - y0, 6, fill=TXT + (255,))
    img.alpha_composite(L.get(), (x0, y0))
    for m, dd in ((5, 122), (6, 153), (7, 183), (8, 214), (9, 245)):
        xx = tx0 + (dd - D0) / (D1 - D0) * (tx1 - tx0)
        s = RO_MON3[m - 1].capitalize()
        d.text((xx - F(13).getlength(s) / 2, ty + 12), s, font=F(13), fill=TXT2)


def map_furniture(img):
    x, y = MAP[0] + 18, MAP[1] + MAP[3] - 92
    shade_box(img, (x, y, x + 300, y + 74), alpha=205)
    scale_bar(img, PXM, 4, x + 18, y + 22)
    north_arrow(img, x + 262, y + 8, 22)
    ImageDraw.Draw(img).text((x + 18, y + 50), 'EPSG:3844 · Stereo 70', font=F(12), fill=MUTED)


def callout(img, S, alpha):
    if alpha <= 0 or not len(S['pivots']):
        return
    piv = min(S['pivots'], key=lambda p: (p[2] - MW * 0.52) ** 2 + (p[1] - MH * 0.18) ** 2)
    px, py = MAP[0] + piv[2], MAP[1] + piv[1]
    tx, ty = px + 64, py + 64
    if tx + 210 > MAP[0] + MW - 10:
        tx = px - 270
    a = int(255 * alpha)
    L = Layer(MW, MH)
    L.line([(px - MAP[0] + piv[3] * 0.7, py - MAP[1] + piv[3] * 0.7), (tx - MAP[0], ty - MAP[1] + 18)],
           TXT + (a,), 1.5)
    img.alpha_composite(L.get(), (MAP[0], MAP[1]))
    shade_box(img, (tx - 6, ty - 4, tx + 196, ty + 50), alpha=int(200 * alpha))
    d = ImageDraw.Draw(img)
    d.text((tx + 6, ty + 2), 'pivoți de irigare', font=F(16, 'SemiBold'), fill=TXT + (a,))
    d.text((tx + 6, ty + 24), 'rămân verzi în august', font=F(14), fill=TXT2 + (a,))


def render(S, stats, base, doy, reveal=0.0, kpi_t=0.0, lst_a=0.0):
    img = base.copy()
    rgb = map_rgb(S, doy)
    if reveal > 0:
        m = np.isin(S['field'], np.flatnonzero(S['irr'] & S['is_ag']))
        ol = outline(m, 2)
        g = glow(ol, CYAN, radius=3, strength=0.55 * reveal)
        rgb = np.clip(rgb + g, 0, 255)
        rgb[ol] = rgb[ol] * (1 - reveal) + np.array(CYAN) * reveal
    paste_map(img, rgb.astype(np.uint8))
    legend(img, reveal)
    map_furniture(img)
    timeline(img, doy)
    callout(img, S, reveal)
    d = ImageDraw.Draw(img)
    irr_ha = S['area_px'][S['irr'] & S['is_ag']].sum() * PXM * PXM / 1e4
    ag_ha = S['area_px'][S['is_ag']].sum() * PXM * PXM / 1e4
    lst_img, delta, li, ld = lst_panel(S, doy, lst_a)
    if kpi_t > 0:
        a = int(255 * min(1, kpi_t * 2))
        kpi(d, PX0 + 20, 238, f'{fmt_int(irr_ha * ease(kpi_t))} ha',
            f'{int(round(100 * irr_ha / ag_ha))}% din teren agricol', a)
        kpi(d, PX0 + 340, 238, f'−{fmt_dec(-delta * ease(kpi_t), 1)} °C', 'irigat vs. neirigat, 1 aug', a)
    else:
        for xx in (PX0 + 20, PX0 + 340):
            d.text((xx, 238), '…', font=F(44, 'SemiBold', True), fill=MUTED)
    img.alpha_composite(chart(S, stats, doy), (PX0 + 20, 388))
    if lst_a > 0:
        img.alpha_composite(lst_img, (PX0 + 20, 776))
    if lst_a < 1:
        a = int(255 * (1 - lst_a))
        d.text((PX0 + 20, 776), 'Se completează după detecția AI', font=F(16), fill=MUTED + (a,))
    return img


if __name__ == '__main__':
    import os, time
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    S = build()
    stats = season_stats(S)
    base = base_chrome()
    print('built', round(time.time() - t0, 1), 's; fields', S['NF'], 'pivots', len(S['pivots']))
    mode = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if mode == 'stills':
        for doy, rv, k, la, name in ((135, 0, 0, 0, 'm1_a_may'), (222, 1, 1, 1, 'm1_poster')):
            t1 = time.time()
            im = render(S, stats, base, doy, rv, k, la)
            im.convert('RGB').save(OUT + name + '.png')
            print(name, round(time.time() - t1, 2), 's')
    else:
        fps = 30
        v = Video(OUT + 'm1_insulele_verzi.mp4', fps)
        n = 15 * fps
        for i in range(n):
            t = i / fps
            if t < 10.0:
                doy = D0 + (222 - D0) * ease(t / 10.0) if t > 0.6 else D0
                rv = kp = la = 0.0
            else:
                doy = 222
                rv = ease((t - 10.0) / 1.2)
                kp = ease((t - 10.6) / 1.6)
                la = ease((t - 11.6) / 1.0)
            fr = render(S, stats, base, doy, rv, kp, la)
            if t < 0.5:
                fr = Image.blend(Image.new('RGBA', fr.size, BG + (255,)), fr, ease(t / 0.5))
            v.add(fr)
        print('video rc', v.close(), round(time.time() - t0, 1), 's')
