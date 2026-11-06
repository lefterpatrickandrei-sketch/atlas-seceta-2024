"""Mockup 5 — Perdele forestiere proiectate de AI (synthetic data). Poster."""
import heapq
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from common import *

MW, MH, PXM = MAP[2], MAP[3], 20.0
OUT = str(__import__('pathlib').Path(__file__).resolve().parent / 'out') + '/'
LIME = (156, 230, 92)
OLD = (40, 112, 58)
STRESS = lut_from([(0.0, (30, 32, 34)), (0.35, (88, 60, 40)), (0.7, (190, 104, 46)), (1.0, (255, 156, 72))])
REACH = 15            # protected distance downwind, px (15 px = 300 m = 20H for H = 15 m)
BUDGET_KM = 45
HI_STRESS = 0.35


def build(seed=51):
    rng = np.random.default_rng(seed)
    fd = make_fields(MH, MW, PXM, theta=-6, seed=seed, strip=(180, 600), big_p=0.3)
    f = fd['field']
    village = blobs(MH, MW, [(250, 520), (820, 240), (980, 640)], [26, 30, 20], seed + 1, rough=0.5)
    nonag = village
    nf = fd['nf']
    n = fbm(MH, MW, seed + 2, cells=(3, 6, 12, 24))
    xx = np.tile(np.arange(MW), (MH, 1))
    stress_px = np.clip(0.55 * n + 0.45 * (xx / MW) ** 0.8, 0, 1)      # drier to the east
    fs = np.bincount(f.ravel(), weights=stress_px.ravel(), minlength=nf) / np.maximum(fd['area_px'], 1)
    fs = np.clip(fs + rng.normal(0, 0.06, nf), 0, 1) ** 2.2
    stress = fs[f]
    stress[nonag] = 0
    # candidate segments: boundaries between horizontally adjacent fields (N-S running edges)
    L, R = f[:, :-1], f[:, 1:]
    ys, xs = np.nonzero((L != R) & ~nonag[:, :-1] & ~nonag[:, 1:])
    keys = L[ys, xs].astype(np.int64) * 100000 + R[ys, xs]
    order = np.argsort(keys, kind='stable')
    ks = keys[order]
    cut = np.flatnonzero(np.diff(ks)) + 1
    segs = []
    for s, e in zip(np.r_[0, cut], np.r_[cut, len(ks)]):
        idx = order[s:e]
        if len(idx) < 12:
            continue
        sy, sx = ys[idx], xs[idx] + 1        # belt drawn on the east field's first column
        span_y = sy.max() - sy.min() + 1
        if span_y < 0.7 * len(idx) or (sx.max() - sx.min()) > 0.3 * span_y + 6:
            continue                          # keep only N-S running edges
        prot = []
        wts = []
        for k in range(1, REACH + 1):
            px_ = sx - k
            ok = px_ >= 0
            prot.append(sy[ok] * MW + px_[ok])
            wts.append(np.full(ok.sum(), 1.0 if k <= 8 else 1.0 - 0.6 * (k - 8) / (REACH - 8)))
        segs.append(dict(y=sy, x=sx, prot=np.concatenate(prot), w=np.concatenate(wts), km=len(idx) * PXM / 1000))
    # existing belts (Small Landscape Features analogue)
    existing = rng.random(len(segs)) < 0.10
    flat_ag = (~nonag).ravel()
    stress_flat = stress.ravel()
    covered = np.zeros(MH * MW, np.float32)
    for i in np.flatnonzero(existing):
        np.maximum.at(covered, segs[i]['prot'], segs[i]['w'])
    def gain(i):
        sg = segs[i]
        add = np.clip(sg['w'] - covered[sg['prot']], 0, None)
        return float(np.sum(add * stress_flat[sg['prot']] * flat_ag[sg['prot']]))
    heap = [(-gain(i) / segs[i]['km'], i) for i in range(len(segs)) if not existing[i]]
    heapq.heapify(heap)
    chosen, curve = [], [(0.0, 0.0, 0.0)]
    km_tot, ha_tot, hi_tot = 0.0, 0.0, 0.0
    while heap:
        g, i = heapq.heappop(heap)
        g_now = gain(i) / segs[i]['km']
        if heap and g_now < -heap[0][0] - 1e-9:
            heapq.heappush(heap, (-g_now, i))
            continue
        if g_now <= 0:
            break
        sg = segs[i]
        before = covered[sg['prot']].copy()
        np.maximum.at(covered, sg['prot'], sg['w'])
        dcov = (covered[sg['prot']] - before) * flat_ag[sg['prot']]
        ha_tot += float(np.sum(dcov)) * PXM * PXM / 1e4
        hi_tot += float(np.sum(dcov * (stress_flat[sg['prot']] >= HI_STRESS))) * PXM * PXM / 1e4
        km_tot += sg['km']
        chosen.append((i, km_tot))
        curve.append((km_tot, hi_tot, ha_tot))
    sel = [i for i, k in chosen if k <= BUDGET_KM]
    tex = 0.94 + 0.12 * fbm(MH, MW, seed + 3, cells=(64, 128))
    return dict(fd=fd, f=f, nonag=nonag, village=village, stress=stress, segs=segs, existing=existing, sel=sel,
                curve=np.array(curve), tex=tex, edges=fd['edge'], road=fd['road'])


def render():
    S = build()
    img = new_canvas()
    draw_header(img, 'GIS Day 2026 · Ideea 5 · adaptare prin îmbunătățiri funciare',
                'Perdele forestiere proiectate de AI',
                'Unde protejează o perdea nouă cele mai multe culturi stresate de secetă, la cel mai mic cost în km',
                accent=LIME)
    draw_footer(img, 'Date simulate pentru design · versiunea finală: ERA5-Land orar, anomalie NDMI Sentinel-2, '
                     'CLMS HR-VPP, CLMS Small Landscape Features 2021, parcele FTW · EPSG:3844')
    f = S['f']
    rgb = STRESS[np.clip((S['stress'] * 255).astype(int), 0, 255)] * S['tex'][..., None]
    rgb[S['edges']] *= 0.7
    rgb[S['road']] = (64, 66, 70)
    vm = S['village']
    rng = np.random.default_rng(3)
    pal = np.array([(52, 62, 50), (96, 80, 72), (110, 110, 108)], np.float32)
    rgb[vm] = pal[rng.integers(0, 3, vm.sum())]
    # protected zones of the chosen belts
    prot = np.zeros(MH * MW, np.float32)
    for i in S['sel']:
        np.maximum.at(prot, S['segs'][i]['prot'], S['segs'][i]['w'])
    prot = prot.reshape(MH, MW) * (~S['nonag'])
    rgb = rgb * (1 - 0.42 * prot[..., None]) + np.array(LIME) * 0.42 * prot[..., None]
    belt_old = np.zeros((MH, MW), bool)
    for i in np.flatnonzero(S['existing']):
        belt_old[S['segs'][i]['y'], S['segs'][i]['x']] = True
    belt_old = ndimage.binary_dilation(belt_old, iterations=1)
    belt_new = np.zeros((MH, MW), bool)
    for i in S['sel']:
        belt_new[S['segs'][i]['y'], S['segs'][i]['x']] = True
    belt_new = ndimage.binary_dilation(belt_new, iterations=1)
    rgb += glow(belt_new, LIME, radius=3, strength=0.5)
    rgb[belt_old] = OLD
    rgb[belt_new] = LIME
    paste_map(img, np.clip(rgb, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # wind rose overlay (top-right of map)
    cx, cy, R = MAP[0] + 140, MAP[1] + 140, 84
    shade_box(img, (cx - 116, cy - 122, cx + 116, cy + 128), alpha=215)
    rose = np.array([2, 2, 3, 9, 16, 10, 5, 3, 2, 2, 2, 2, 3, 3, 3, 2], float)   # from N, clockwise
    Lr = Layer(232, 250)
    ox, oy = 116, 122
    for r in (0.33, 0.66, 1.0):
        Lr.circle(ox, oy, R * r, outline=LINE + (255,), width=1)
    for k, v in enumerate(rose):
        a0 = np.deg2rad(k * 22.5 - 9 - 90)
        a1 = np.deg2rad(k * 22.5 + 9 - 90)
        rr = R * v / rose.max()
        Lr.poly([(ox, oy), (ox + rr * np.cos(a0), oy + rr * np.sin(a0)), (ox + rr * np.cos(a1), oy + rr * np.sin(a1))],
                (LIME if v == rose.max() else (170, 180, 190)) + (235,))
    img.alpha_composite(Lr.get(), (cx - 116, cy - 122))
    d.text((cx - F(13, 'SemiBold').getlength('N') / 2, cy - R - 26), 'N', font=F(13, 'SemiBold'), fill=TXT2)
    s = 'vântul în zilele > 30 °C, fără ploaie'
    d.text((cx - F(12).getlength(s) / 2, cy + R + 16), s, font=F(12), fill=TXT2)
    # furniture + legend
    x, y = MAP[0] + 18, MAP[1] + MH - 92
    shade_box(img, (x, y, x + 300, y + 74), alpha=205)
    scale_bar(img, PXM, 4, x + 18, y + 22)
    north_arrow(img, x + 262, y + 8, 22)
    d.text((x + 18, y + 50), 'EPSG:3844 · Stereo 70', font=F(12), fill=MUTED)
    # ---- panel
    X0 = PX0
    card(img, (X0, 200, X0 + 296, 322))
    card(img, (X0 + 320, 200, X0 + PW, 322))
    card(img, (X0, 342, X0 + PW, 700))
    card(img, (X0, 720, X0 + PW, 996))
    d = ImageDraw.Draw(img)
    curve = S['curve']
    ha_at = float(np.interp(BUDGET_KM, curve[:, 0], curve[:, 1]))
    ha_all_at = float(np.interp(BUDGET_KM, curve[:, 0], curve[:, 2]))
    section_label(d, X0 + 20, 216, 'Perdele propuse')
    section_label(d, X0 + 340, 216, 'Culturi protejate')
    d.text((X0 + 20, 238), f'{BUDGET_KM} km', font=F(44, 'SemiBold', True), fill=LIME)
    d.text((X0 + 21, 292), f'{len(S["sel"])} segmente noi', font=F(16), fill=TXT2)
    d.text((X0 + 340, 238), f'{fmt_int(ha_all_at)} ha', font=F(44, 'SemiBold', True), fill=TXT)
    d.text((X0 + 341, 292), 'în zona de până la 20H în aval', font=F(16), fill=TXT2)
    section_label(d, X0 + 20, 358, 'Culturi cu stres ridicat protejate vs. km plantați')
    w, h = PW - 40, 300
    Lc = Layer(w, h)
    pl, pr, pt, pb = 48, 16, 30, 34
    xmax = int(50 * np.ceil(curve[-1, 0] / 50))
    ymax = 500 * np.ceil(curve[:, 1].max() * 1.08 / 500)
    Xc = lambda v: pl + v / xmax * (w - pl - pr)
    Yc = lambda v: pt + (1 - v / ymax) * (h - pt - pb)
    step_y = 1000 if ymax > 4000 else 500
    for v in np.arange(0, ymax + 1, step_y):
        Lc.line([(pl, Yc(v)), (w - pr, Yc(v))], GRID + (255,), 1)
        Lc.text((pl - 8, Yc(v) - 8), fmt_int(v), 12, MUTED + (255,), anchor='r')
    for v in range(0, xmax + 1, 100 if xmax > 400 else 50):
        Lc.text((Xc(v), h - pb + 8), str(v), 12, MUTED + (255,), anchor='m')
    pts = [(Xc(a), Yc(b)) for a, b, _ in curve if a <= xmax]
    Lc.line(pts, TXT2 + (255,), 2)
    sel_pts = [(Xc(a), Yc(b)) for a, b, _ in curve if a <= BUDGET_KM]
    Lc.poly(sel_pts + [(Xc(BUDGET_KM), Yc(0)), (Xc(0), Yc(0))], LIME + (46,))
    Lc.line(sel_pts, LIME + (255,), 2.6)
    Lc.line([(Xc(BUDGET_KM), Yc(ha_at)), (Xc(BUDGET_KM), Yc(0))], LIME + (160,), 1)
    Lc.circle(Xc(BUDGET_KM), Yc(ha_at), 6, fill=LIME + (255,), outline=CARD + (255,), width=2)
    ha_max = float(curve[curve[:, 0] <= xmax, 1].max())
    pct = 100 * ha_at / ha_max
    Lc.text((Xc(BUDGET_KM) + 12, Yc(ha_at) + 10), f'{int(round(pct))}% din beneficiu', 13, TXT + (255,), 'SemiBold')
    Lc.text((Xc(BUDGET_KM) + 12, Yc(ha_at) + 28), f'cu {int(round(100 * BUDGET_KM / xmax))}% din lungime', 12,
            TXT2 + (255,))
    Lc.text((w - pr, h - pb + 22 - 2), '', 12, MUTED + (255,))
    img.alpha_composite(Lc.get(), (X0 + 20, 384))
    d.text((X0 + 20 + w - 140, 384 + h - 6), 'km plantați', font=F(12), fill=MUTED)
    d.text((X0 + 20 + 4, 384 + 4), 'ha cu stres ridicat', font=F(12), fill=MUTED)
    section_label(d, X0 + 20, 736, 'Legendă')
    rows = [('line', OLD, 'perdele existente (Small Landscape Features)'),
            ('line', LIME, 'perdele propuse de AI'),
            ('zone', LIME, 'zona protejată în aval, până la 20H')]
    for i, (k, c, s) in enumerate(rows):
        yy = 772 + i * 34
        Lg = Layer(36, 20)
        if k == 'line':
            Lg.line([(2, 10), (34, 10)], c + (255,), 4)
        else:
            Lg.rect((2, 2, 34, 18), fill=c + (110,), radius=3)
        img.alpha_composite(Lg.get(), (X0 + 20, yy))
        d.text((X0 + 68, yy), s, font=F(16), fill=TXT)
    d.text((X0 + 20, 884), 'Stresul hidric al culturii (anomalie NDMI 2024)', font=F(15), fill=TXT2)
    ramp_bar(img, X0 + 20, 914, PW - 40, 12, [(0, (30, 32, 34)), (0.35, (88, 60, 40)), (0.7, (190, 104, 46)),
                                             (1, (255, 156, 72))],
             labels=[(0, 'scăzut'), (1, 'ridicat')])
    return img


if __name__ == '__main__':
    import os, time
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    render().convert('RGB').save(OUT + 'm5_poster.png')
    print('ok', round(time.time() - t0, 1))
