"""Mockup 3 — Radiografia solului (synthetic data). Poster."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from common import *

MW, MH, PXM = MAP[2], MAP[3], 20.0
OUT = str(__import__('pathlib').Path(__file__).resolve().parent / 'out') + '/'
PAPER = (241, 237, 229)
INK = (34, 30, 26)
INK2 = (96, 90, 82)
SOIL = lut_from([(0.0, (206, 172, 124)), (0.3, (170, 132, 92)), (0.6, (118, 88, 62)), (0.85, (76, 58, 44)),
                 (1.0, (54, 42, 34))])
SOC_PAPER = [(0.0, (244, 228, 196)), (0.35, (222, 176, 118)), (0.7, (168, 104, 56)), (1.0, (92, 52, 28))]
SOC_LUT = lut_from(SOC_PAPER)
VEG = lut_from([(0.0, (92, 76, 58)), (0.15, (122, 100, 74)), (0.25, (150, 128, 90)), (0.35, (152, 142, 96)),
                (0.5, (108, 128, 72)), (0.65, (70, 118, 56)), (0.8, (40, 102, 47)), (1.0, (26, 84, 40))])
LO, HI = 8.0, 28.0


def build(seed=31):
    rng = np.random.default_rng(seed)
    fd = make_fields(MH, MW, PXM, theta=-10, seed=seed, strip=(170, 560))
    f = fd['field']
    rv_m, rv_d, _ = river(MH, MW, seed + 1, x0=470, amp=55, wl=600, width=9, vertical=False, extra=0.5)
    tr_m, tr_d, _ = river(MH, MW, seed + 2, x0=830, amp=30, wl=380, width=4, vertical=True)
    tr_m[:420] = False
    tr_d = np.where(np.arange(MH)[:, None] < 420, 1e3, tr_d)
    water = rv_m | tr_m
    n = fbm(MH, MW, seed + 3, cells=(4, 8, 16, 32))
    dem = 80 + 18 * n - 34 * np.exp(-(rv_d / 75.0) ** 2) - 16 * np.exp(-(tr_d / 40.0) ** 2)
    gy, gx = np.gradient(dem, PXM)
    slope = np.hypot(gx, gy)
    sl = np.clip(slope / np.percentile(slope, 98), 0, 1)
    az, alt = np.deg2rad(315), np.deg2rad(40)
    hs = (np.sin(alt) + np.cos(alt) * (gx * np.sin(az) - gy * np.cos(az)) / np.sqrt(1 + gx ** 2 + gy ** 2))
    hs = np.clip(hs / max(hs.max(), 1e-6), 0, 1)
    n1 = fbm(MH, MW, seed + 4, cells=(16, 32, 64))
    forest = ((rv_d < 6 + 14 * n1) | (tr_d < 3 + 6 * n1)) & ~water
    forest |= blobs(MH, MW, [(140, 120), (1000, 690)], [30, 24], seed + 5)
    village = blobs(MH, MW, [(300, 300), (760, 600), (980, 180)], [22, 26, 16], seed + 6, rough=0.5)
    nonag = water | forest | village
    valley = np.exp(-(rv_d / 60.0) ** 2)
    soc = (17.5 + 22.0 * (n - 0.5) - 11.0 * (sl - 0.2) + 3.0 * valley + 5.0 * (fbm(MH, MW, seed + 7, cells=(24, 48)) - 0.5))
    nf = fd['nf']
    mgmt = rng.normal(0, 1.6, nf)
    soc = soc + mgmt[f]
    soc = np.clip(soc, 6, 30)
    socn = np.clip((soc - LO) / (HI - LO), 0, 1)
    ag_frac = np.bincount(f.ravel(), weights=(~nonag).ravel(), minlength=nf) / np.maximum(fd['area_px'], 1)
    is_ag = ag_frac > 0.6
    # summer appearance per field
    kind = rng.choice(4, nf, p=[0.42, 0.33, 0.17, 0.08])     # green crop, stubble, plowed, rapeseed stubble
    ndv = np.where(kind == 0, rng.uniform(0.55, 0.78, nf), rng.uniform(0.18, 0.3, nf))
    bright = rng.normal(1, 0.04, nf)
    tex = 0.94 + 0.12 * fbm(MH, MW, seed + 8, cells=(48, 96, 192))
    bare_winter = rng.random(nf) < 0.42
    return dict(fd=fd, f=f, nf=nf, soc=soc, socn=socn, sl=sl, hs=hs, nonag=nonag, water=water, forest=forest,
                village=village, kind=kind, ndv=ndv, bright=bright, tex=tex, is_ag=is_ag, bare_winter=bare_winter,
                edges=fd['edge'], road=fd['road'])


def natural_rgb(S):
    f = S['f']
    col = VEG[np.clip((S['ndv'] * 255).astype(int), 0, 255)].copy()
    col[S['kind'] == 1] = (190, 170, 124)
    col[S['kind'] == 2] = (92, 72, 54)
    col[S['kind'] == 3] = (168, 150, 112)
    col *= S['bright'][:, None]
    rgb = col[f] * S['tex'][..., None]
    rgb = paint_nonag(S, rgb)
    rgb[S['edges'] & ~S['nonag']] *= 0.8
    rgb[S['road'] & ~S['nonag']] = (150, 146, 138)
    return rgb


def paint_nonag(S, rgb):
    rgb[S['forest']] = np.array((33, 60, 38)) * (0.9 + 0.2 * S['tex'][S['forest']][:, None] - 0.1)
    rng = np.random.default_rng(5)
    vm = S['village']
    pal = np.array([(58, 84, 50), (150, 98, 80), (168, 164, 156), (112, 108, 100)], np.float32)
    rgb[vm] = pal[rng.integers(0, 4, vm.sum())]
    rgb[S['water']] = (26, 50, 68)
    return rgb


def bare_rgb(S):
    s = np.clip(S['socn'] ** 0.85 * 0.92 + 0.06 * (1 - S['sl']), 0, 1)
    rgb = SOIL[np.clip((s * 255).astype(int), 0, 255)] * (0.8 + 0.34 * S['hs'])[..., None] * S['tex'][..., None]
    hatch = ((np.add.outer(np.arange(MH), np.arange(MW)) // 4) % 3 == 0)
    na = S['nonag']
    rgb[na] = np.where(hatch[na][:, None], (52, 58, 66), (34, 39, 46))
    rgb[S['water']] = (24, 40, 54)
    rgb[S['edges'] & ~na] *= 0.9
    return rgb


def lucas_points(S, n=44, seed=7):
    rng = np.random.default_rng(seed)
    pts = []
    ys, xs = np.nonzero(~S['nonag'] & S['is_ag'][S['f']])
    while len(pts) < n:
        i = rng.integers(len(ys))
        y, x = ys[i], xs[i]
        if all((x - a) ** 2 + (y - b) ** 2 > 60 ** 2 for a, b, *_ in pts):
            obs = S["soc"][y, x] + rng.normal(0, 2.4)
            pred = S["soc"][y, x] + rng.normal(0, 2.2)
            pts.append((x, y, obs, pred))
    return pts


def render():
    S = build()
    img = new_canvas()
    draw_header(img, 'GIS Day 2026 · Ideea 3 · neutralitate climatică prin sol',
                'Radiografia solului: carbonul văzut prin câmpul gol',
                'Compozit Sentinel-2 din pixelii fără vegetație, calibrat pe punctele LUCAS cu un model CNN',
                accent=(222, 176, 118))
    draw_footer(img, 'Date simulate pentru design · versiunea finală: compozit Sentinel-2 L2A 2017–2025, '
                     'Copernicus DEM GLO-30, ERA5-Land, LUCAS 2018 Topsoil · EPSG:3844')
    nat = natural_rgb(S)
    bare = bare_rgb(S)
    yy, xx = np.mgrid[0:MH, 0:MW]
    xt, xb = 0.62 * MW, 0.40 * MW
    xl = xt + (xb - xt) * yy / MH
    right = xx > xl
    rgb = np.where(right[..., None], bare, nat)
    paste_map(img, np.clip(rgb, 0, 255).astype(np.uint8))
    # divider + handle
    L = Layer(MW, MH)
    L.line([(xt, 0), (xb, MH)], (255, 255, 255, 235), 2.5)
    mx, my = (xt + xb) / 2, MH / 2
    L.circle(mx, my, 20, fill=(255, 255, 255, 240))
    L.poly([(mx - 12, my), (mx - 4, my - 7), (mx - 4, my + 7)], BG + (255,))
    L.poly([(mx + 12, my), (mx + 4, my - 7), (mx + 4, my + 7)], BG + (255,))
    pts = lucas_points(S)
    for x, y, *_ in pts:
        L.circle(x, y, 5.5, fill=(255, 255, 255, 255), outline=BG + (255,), width=2)
    img.alpha_composite(L.get(), (MAP[0], MAP[1]))
    d = ImageDraw.Draw(img)
    # side labels
    for (x, y, k, t) in ((MAP[0] + 18, MAP[1] + 18, 'Cu plante', 'Sentinel-2, iulie 2024'),
                         (MAP[0] + MW - 368, MAP[1] + 18, 'Fără plante', 'compozit de sol gol, 2017–2025')):
        shade_box(img, (x, y, x + 350, y + 70), alpha=205)
        section_label(d, x + 16, y + 14, k, color=TXT)
        d.text((x + 16, y + 38), t, font=F(15), fill=TXT2)
    # callout on one LUCAS point on the bare side
    cand = [p for p in pts if xt + 110 < p[0] < MW - 270 and 150 < p[1] < 470]
    p = cand[0] if cand else pts[0]
    px, py = MAP[0] + p[0], MAP[1] + p[1]
    tx, ty = px + 26, py - 70
    shade_box(img, (tx, ty, tx + 214, ty + 54), alpha=215)
    d.text((tx + 12, ty + 7), f'LUCAS · {fmt_dec(p[2], 1)} g C/kg', font=F(16, 'SemiBold'), fill=TXT)
    d.text((tx + 12, ty + 30), f'modelul prezice {fmt_dec(p[3], 1)}', font=F(14), fill=TXT2)
    # map furniture
    x, y = MAP[0] + 18, MAP[1] + MH - 92
    shade_box(img, (x, y, x + 300, y + 74), alpha=205)
    scale_bar(img, PXM, 4, x + 18, y + 22)
    north_arrow(img, x + 262, y + 8, 22)
    d.text((x + 18, y + 50), 'EPSG:3844 · Stereo 70', font=F(12), fill=MUTED)
    x2 = MAP[0] + MW - 318
    shade_box(img, (x2, y + 20, x2 + 300, y + 74), alpha=205)
    L2 = Layer(24, 24)
    L2.circle(12, 12, 6, fill=(255, 255, 255, 255), outline=BG + (255,), width=2)
    img.alpha_composite(L2.get(), (x2 + 14, y + 35))
    d.text((x2 + 46, y + 37), 'punct LUCAS 2018, carbon măsurat', font=F(14, 'Medium'), fill=TXT)

    # ---- right panel
    X0 = PX0
    card(img, (X0, 200, X0 + PW, 604), fill=PAPER)
    d = ImageDraw.Draw(img)
    section_label(d, X0 + 20, 216, 'Carbon organic prezis · g C/kg', color=INK2)
    th = Image.fromarray(np.uint8(SOC_LUT[(S['socn'] * 255).astype(int)]), 'RGB')
    th_arr = np.array(th)
    th_arr[S['nonag']] = (226, 222, 214)
    th = Image.fromarray(th_arr).resize((440, 314), Image.LANCZOS).convert('RGBA')
    img.alpha_composite(th, (X0 + 20, 250))
    # vertical ramp
    rx, ry, rh = X0 + 488, 250, 314
    arr = np.zeros((rh, 14, 3), np.float32)
    tvals = np.linspace(1, 0, rh)
    for ch in range(3):
        arr[:, :, ch] = np.interp(tvals, [p_ for p_, _ in SOC_PAPER], [c[ch] for _, c in SOC_PAPER])[:, None]
    img.alpha_composite(Image.fromarray(arr.astype(np.uint8)).convert('RGBA'), (rx, ry))
    for v in (8, 13, 18, 23, 28):
        yv = ry + (1 - (v - LO) / (HI - LO)) * (rh - 1)
        d.line((rx + 14, yv, rx + 20, yv), fill=INK2)
        d.text((rx + 26, yv - 9), str(v), font=F(14), fill=INK)
    d.text((X0 + 20, 574), 'gri = pădure, ape, localități (fără predicție)', font=F(13), fill=INK2)
    # scatter card
    card(img, (X0, 624, X0 + PW, 878))
    section_label(d, X0 + 20, 640, 'Validare pe punctele LUCAS')
    obs = np.array([p_[2] for p_ in pts])
    pred = np.array([p_[3] for p_ in pts])
    r2 = 1 - np.sum((obs - pred) ** 2) / np.sum((obs - obs.mean()) ** 2)
    rmse = np.sqrt(np.mean((obs - pred) ** 2))
    w, h = 360, 184
    L3 = Layer(w, h)
    pl, pb, pt, pr = 40, 30, 8, 10
    Xs = lambda v: pl + (v - 5) / 25 * (w - pl - pr)
    Ys = lambda v: pt + (1 - (v - 5) / 25) * (h - pt - pb)
    for v in (5, 10, 15, 20, 25, 30):
        L3.line([(pl, Ys(v)), (w - pr, Ys(v))], GRID + (255,), 1)
        L3.text((pl - 8, Ys(v) - 8), str(v), 12, MUTED + (255,), anchor='r')
        L3.text((Xs(v), h - pb + 8), str(v), 12, MUTED + (255,), anchor='m')
    L3.line([(Xs(5), Ys(5)), (Xs(30), Ys(30))], TXT2 + (160,), 1.5)
    for o, pr_ in zip(obs, pred):
        L3.circle(Xs(o), Ys(pr_), 4.5, fill=(222, 176, 118, 235), outline=CARD + (255,), width=1.5)
    img.alpha_composite(L3.get(), (X0 + 20, 668))
    d.text((X0 + 20 + pl, 668 + h + 2), 'măsurat în laborator (LUCAS), g C/kg', font=F(13), fill=MUTED)
    d.text((X0 + 20 + pl - 34, 668 - 22 + 4), '', font=F(13), fill=MUTED)
    tx = X0 + 404
    d.text((tx, 676), 'R²', font=F(15, 'Medium'), fill=TXT2)
    d.text((tx, 698), fmt_dec(r2, 2), font=F(44, 'SemiBold', True), fill=TXT)
    d.text((tx, 760), 'RMSE', font=F(15, 'Medium'), fill=TXT2)
    d.text((tx, 782), f'{fmt_dec(rmse, 1)} g/kg', font=F(28, 'SemiBold', True), fill=TXT)
    d.text((tx, 830), 'axa verticală: prezis', font=F(13), fill=MUTED)
    # priority card
    card(img, (X0, 898, X0 + PW, 996))
    fsoc = np.bincount(S['f'].ravel(), weights=S['soc'].ravel(), minlength=S['nf']) / np.maximum(
        np.bincount(S['f'].ravel(), minlength=S['nf']), 1)
    agf = S['is_ag']
    prio = agf & (fsoc < 15) & S['bare_winter']
    pct = 100 * prio.sum() / agf.sum()
    d.text((X0 + 20, 914), f'{int(round(pct))}%', font=F(52, 'SemiBold', True), fill=(222, 176, 118))
    d.text((X0 + 150, 920), 'din parcele: prioritate pentru culturi de acoperire', font=F(17, 'SemiBold'), fill=TXT)
    d.text((X0 + 150, 948), 'sol sub 15 g C/kg și descoperit în noiembrie–martie', font=F(15), fill=TXT2)
    return img


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    render().convert('RGB').save(OUT + 'm3_poster.png')
    print('ok')
