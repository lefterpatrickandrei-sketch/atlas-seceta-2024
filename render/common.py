"""Shared drawing toolkit for the GIS Day 2026 mockups (synthetic data only)."""
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

W, H = 1920, 1080
FD = str(__import__('pathlib').Path(__file__).resolve().parent / 'fonts') + '/'   # Inter (licență OFL, render/fonts/LICENSE.txt)
_fc = {}


def F(size, weight='Regular', display=False):
    key = (size, weight, display)
    if key not in _fc:
        name = ('InterDisplay-' if display else 'Inter-') + weight + '.otf'
        _fc[key] = ImageFont.truetype(FD + name, size)
    return _fc[key]


# ---- palette (dark theme) -------------------------------------------------
BG = (12, 16, 21)
PANEL = (19, 25, 32)
CARD = (23, 30, 38)
LINE = (48, 58, 70)
GRID = (36, 44, 54)
TXT = (237, 240, 243)
TXT2 = (165, 175, 186)
MUTED = (114, 126, 139)
AMBER = (250, 178, 25)
# dataviz reference palette, dark-mode steps
BLUE = (57, 135, 229)
ORANGE = (217, 89, 38)
AQUA = (25, 158, 112)
YELLOW = (201, 133, 0)
MAGENTA = (213, 81, 129)
VIOLET = (144, 133, 233)
CYAN = (64, 222, 206)      # map highlight for AI detections

MAP = (64, 200, 1120, 800)          # x, y, w, h  (map frame)
PX0, PW = 1240, 616                 # right panel x and width (ends at 1856)


# ---- text helpers -----------------------------------------------------------
def tw(text, font, tracking=0.0):
    if not tracking:
        return font.getlength(text)
    return sum(font.getlength(c) for c in text) + tracking * (len(text) - 1)


def tracked(d, xy, text, font, fill, tracking=0.0, right=False):
    x, y = xy
    if right:
        x -= tw(text, font, tracking)
    for c in text:
        d.text((x, y), c, font=font, fill=fill)
        x += font.getlength(c) + tracking
    return x


def fmt_int(n):
    return f"{int(round(n)):,}".replace(',', '.')


def fmt_dec(x, nd=1):
    return f"{x:.{nd}f}".replace('.', ',')


RO_MONTHS = ['ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie', 'iulie',
             'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie']
RO_MON3 = ['ian', 'feb', 'mar', 'apr', 'mai', 'iun', 'iul', 'aug', 'sep', 'oct', 'nov', 'dec']


def doy_to_date(doy, year=2024):
    import datetime as dt
    d = dt.date(year, 1, 1) + dt.timedelta(days=int(doy) - 1)
    return d.day, d.month


def doy_label(doy, year=2024, short=False):
    day, mon = doy_to_date(doy, year)
    return f"{day} {(RO_MON3 if short else RO_MONTHS)[mon - 1]}"


# ---- chrome ----------------------------------------------------------------
def new_canvas():
    return Image.new('RGBA', (W, H), BG + (255,))


def draw_badge(img, text='MACHETĂ · DATE SIMULATE', right=1856, y=46):
    f = F(30, 'SemiBold')
    t = tw(text, f, 2.2)
    pw, ph = int(t + 52), 58
    b = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    bd = ImageDraw.Draw(b)
    bd.rounded_rectangle((2, 2, pw - 3, ph - 3), radius=27, fill=AMBER + (34,), outline=AMBER + (255,), width=3)
    tracked(bd, (26, 12), text, f, AMBER + (255,), 2.2)
    b = b.resize((pw // 2, ph // 2), Image.LANCZOS)
    img.alpha_composite(b, (right - pw // 2, y))


def draw_header(img, kicker, title, subtitle, accent=CYAN, badge=True):
    d = ImageDraw.Draw(img)
    tracked(d, (64, 44), kicker.upper(), F(17, 'SemiBold'), accent, 2.2)
    d.text((61, 70), title, font=F(54, 'Bold', True), fill=TXT)
    d.text((64, 144), subtitle, font=F(23), fill=TXT2)
    if badge:      # hărțile cu date reale nu poartă ștampila de machetă
        draw_badge(img)


def draw_footer(img, left, right='GIS Day 2026 · 18 noiembrie · FIFIM, Amfiteatrul II 1'):
    d = ImageDraw.Draw(img)
    d.text((64, 1036), left, font=F(16), fill=MUTED)
    f = F(16, 'Medium')
    d.text((1856 - f.getlength(right), 1036), right, font=f, fill=MUTED)


def section_label(d, x, y, text, color=TXT2):
    tracked(d, (x, y), text.upper(), F(14, 'SemiBold'), color, 1.6)


def paste_map(img, rgb, frame=True):
    x, y, w, h = MAP
    im = Image.fromarray(np.ascontiguousarray(rgb), 'RGB').convert('RGBA')
    img.alpha_composite(im, (x, y))
    if frame:
        d = ImageDraw.Draw(img)
        d.rectangle((x - 1, y - 1, x + w, y + h), outline=LINE, width=1)


def shade_box(img, box, alpha=170, radius=10, color=BG):
    """Semi-transparent rounded backing for overlays drawn on the map."""
    x0, y0, x1, y1 = box
    s = 2
    layer = Image.new('RGBA', ((x1 - x0) * s, (y1 - y0) * s), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((0, 0, (x1 - x0) * s - 1, (y1 - y0) * s - 1),
                                            radius=radius * s, fill=color + (alpha,))
    layer = layer.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    img.alpha_composite(layer, (x0, y0))


def scale_bar(img, px_m, km, x, y, label_unit='km'):
    """Two-segment scale bar starting at (x, y) in canvas pixels."""
    d = ImageDraw.Draw(img)
    L = int(round(km * 1000 / px_m))
    half = L // 2
    d.rectangle((x, y, x + half, y + 6), fill=TXT)
    d.rectangle((x + half, y, x + L, y + 6), fill=(90, 100, 112))
    d.rectangle((x, y, x + L, y + 6), outline=TXT, width=1)
    f = F(14, 'Medium')
    for v, xx in ((0, x), (km / 2, x + half), (km, x + L)):
        s = fmt_dec(v, 1).replace(',0', '') if v else '0'
        if xx == x + L:
            s += f' {label_unit}'
        d.text((xx - f.getlength(s) / 2 if xx != x else xx, y + 11), s, font=f, fill=TXT)
    return L


def north_arrow(img, x, y, size=26):
    s = 3
    layer = Image.new('RGBA', (size * s, int(size * 1.5) * s), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx = size * s / 2
    ld.polygon([(cx, 0), (size * s * 0.92, size * 1.15 * s), (cx, size * 0.85 * s)], fill=TXT + (255,))
    ld.polygon([(cx, 0), (size * s * 0.08, size * 1.15 * s), (cx, size * 0.85 * s)], fill=(120, 130, 142, 255))
    layer = layer.resize((size, int(size * 1.5)), Image.LANCZOS)
    img.alpha_composite(layer, (x, y + 18))
    d = ImageDraw.Draw(img)
    f = F(15, 'SemiBold')
    d.text((x + size / 2 - f.getlength('N') / 2, y), 'N', font=f, fill=TXT)


def ramp_bar(img, x, y, w, h, colors, labels=None, label_font=None, ticks=None):
    """Horizontal colour ramp; colors = list of (pos 0..1, rgb)."""
    xs = np.linspace(0, 1, w)
    arr = np.zeros((h, w, 3), np.float32)
    pos = [p for p, _ in colors]
    for ch in range(3):
        arr[:, :, ch] = np.interp(xs, pos, [c[ch] for _, c in colors])[None, :]
    im = Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA')
    img.alpha_composite(im, (x, y))
    d = ImageDraw.Draw(img)
    if labels:
        f = label_font or F(14)
        for p, s in labels:
            xx = x + p * w
            anchor = xx - f.getlength(s) / 2
            anchor = min(max(anchor, x), x + w - f.getlength(s))
            d.text((anchor, y + h + 7), s, font=f, fill=TXT2)


# ---- supersampled overlay layer --------------------------------------------
class Layer:
    """Draw anti-aliased shapes at 2x then downsample (s=2)."""

    def __init__(self, w, h, s=2):
        self.w, self.h, self.s = w, h, s
        self.img = Image.new('RGBA', (w * s, h * s), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def P(self, pts):
        return [(x * self.s, y * self.s) for x, y in pts]

    def line(self, pts, fill, width=2):
        if len(pts) >= 2:
            self.d.line(self.P(pts), fill=fill, width=int(width * self.s), joint='curve')

    def poly(self, pts, fill):
        if len(pts) >= 3:
            self.d.polygon(self.P(pts), fill=fill)

    def circle(self, x, y, r, fill=None, outline=None, width=1):
        s = self.s
        self.d.ellipse((x * s - r * s, y * s - r * s, x * s + r * s, y * s + r * s), fill=fill, outline=outline,
                       width=int(width * s))

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        s = self.s
        b = tuple(v * s for v in box)
        if radius:
            self.d.rounded_rectangle(b, radius=radius * s, fill=fill, outline=outline, width=int(width * s))
        else:
            self.d.rectangle(b, fill=fill, outline=outline, width=int(width * s))

    def text(self, xy, text, size, fill, weight='Regular', anchor=None):
        x, y = xy
        f = F(int(size * self.s), weight)
        if anchor == 'r':
            x = x - f.getlength(text) / self.s
        elif anchor == 'm':
            x = x - f.getlength(text) / self.s / 2
        self.d.text((x * self.s, y * self.s), text, font=f, fill=fill)

    def get(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)


# ---- noise and landscape ----------------------------------------------------
def _up(g, h, w, order=3):
    z = ndimage.zoom(g, (h / g.shape[0] * 1.02, w / g.shape[1] * 1.02), order=order, mode='nearest')
    return z[:h, :w]


def fbm(h, w, seed, cells=(6, 12, 24, 48, 96), gain=0.55):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    m = max(h, w)
    for c in cells:
        gh = max(3, int(round(c * h / m)) + 2)
        gw = max(3, int(round(c * w / m)) + 2)
        out += amp * _up(rng.random((gh, gw)).astype(np.float32), h, w)
        tot += amp
        amp *= gain
    out /= tot
    out -= out.min()
    out /= max(out.max(), 1e-6)
    return out


def make_fields(h, w, px, theta=-12.0, seed=1, bu=(1300, 2600), bv=(1000, 2300), strip=(160, 520),
                subsplit_p=0.45, big_p=0.25, road_p=0.55):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    Xm = (xx + 0.5) * px
    Ym = (yy + 0.5) * px
    t = np.deg2rad(theta)
    U = Xm * np.cos(t) + Ym * np.sin(t)
    V = -Xm * np.sin(t) + Ym * np.cos(t)
    ub = [U.min() - rng.uniform(0, 900)]
    while ub[-1] < U.max():
        ub.append(ub[-1] + rng.uniform(*bu))
    vb = [V.min() - rng.uniform(0, 900)]
    while vb[-1] < V.max():
        vb.append(vb[-1] + rng.uniform(*bv))
    ub, vb = np.array(ub), np.array(vb)
    iu = np.clip(np.searchsorted(ub, U, side='right') - 1, 0, len(ub) - 2)
    iv = np.clip(np.searchsorted(vb, V, side='right') - 1, 0, len(vb) - 2)
    nbv = len(vb) - 1
    block = (iu * nbv + iv).astype(np.int64)
    lu = U - ub[iu]
    lv = V - vb[iv]
    flat_b = block.ravel()
    order = np.argsort(flat_b, kind='stable')
    sb = flat_b[order]
    cut = np.flatnonzero(np.diff(sb)) + 1
    starts, ends = np.r_[0, cut], np.r_[cut, len(sb)]
    field = np.full(h * w, -1, np.int64)
    lu_f, lv_f = lu.ravel(), lv.ravel()
    orient_of, block_of = [], []
    fid = 0
    for s, e in zip(starts, ends):
        idx = order[s:e]
        b = int(sb[s])
        bu_i, bv_i = divmod(b, nbv)
        Lub, Lvb = ub[bu_i + 1] - ub[bu_i], vb[bv_i + 1] - vb[bv_i]
        orient = int(rng.integers(0, 2))
        a, c = lu_f[idx], lv_f[idx]
        main, Lmain = (a, Lub) if orient == 0 else (c, Lvb)
        other, Lother = (c, Lvb) if orient == 0 else (a, Lub)
        if rng.random() < subsplit_p:
            k = int(rng.integers(2, 4))
            cuts = np.sort(rng.uniform(0.25, 0.75, k - 1)) * Lother
        else:
            cuts = np.array([])
        sub = np.searchsorted(cuts, other, side='right')
        for si in range(len(cuts) + 1):
            m = sub == si
            if not m.any():
                continue
            lo, hi = (strip[1], strip[1] * 2.3) if rng.random() < big_p else strip
            br = [0.0]
            while br[-1] < Lmain:
                br.append(br[-1] + rng.uniform(lo, hi))
            br = np.array(br[1:-1])
            k = np.searchsorted(br, main[m], side='right')
            field[idx[m]] = fid + k
            nk = len(br) + 1
            orient_of += [orient] * nk
            block_of += [b] * nk
            fid += nk
    uniq, inv = np.unique(field, return_inverse=True)
    field = inv.reshape(h, w).astype(np.int32)
    orient_of = np.array(orient_of)[uniq]
    block_of = np.array(block_of)[uniq]
    edge = np.zeros((h, w), bool)
    edge[:, 1:] |= field[:, 1:] != field[:, :-1]
    edge[1:, :] |= field[1:, :] != field[:-1, :]
    road_u = rng.random(len(ub)) < road_p
    road_v = rng.random(len(vb)) < road_p
    rw = px * 0.8
    Lu = ub[iu + 1] - ub[iu]
    Lv = vb[iv + 1] - vb[iv]
    road = (((lu < rw) & road_u[iu]) | ((Lu - lu < rw) & road_u[iu + 1]) |
            ((lv < rw) & road_v[iv]) | ((Lv - lv < rw) & road_v[iv + 1]))
    nf = int(field.max()) + 1
    cnt = np.bincount(field.ravel(), minlength=nf).astype(np.float64)
    cy = np.bincount(field.ravel(), weights=np.repeat(np.arange(h), w), minlength=nf) / np.maximum(cnt, 1)
    cx = np.bincount(field.ravel(), weights=np.tile(np.arange(w), h), minlength=nf) / np.maximum(cnt, 1)
    return dict(field=field, edge=edge, road=road, block=block, U=U, V=V, nf=nf, orient=orient_of,
                blockof=block_of, area_px=cnt, cx=cx, cy=cy, px=px, theta=theta, h=h, w=w, ub=ub, vb=vb)


def card(img, box, radius=12, fill=CARD, outline=None):
    x0, y0, x1, y1 = box
    L = Layer(x1 - x0, y1 - y0)
    L.rect((0, 0, x1 - x0 - 0.5, y1 - y0 - 0.5), fill=fill + (255,), outline=(outline + (255,)) if outline else None,
           width=1, radius=radius)
    img.alpha_composite(L.get(), (x0, y0))


def relabel_after_mask(fields, keep):
    """Return field raster where pixels outside `keep` are -1."""
    f = fields['field'].copy()
    f[~keep] = -1
    return f


def river(h, w, seed, x0, amp=60, wl=420, width=18, vertical=True, extra=0.35):
    rng = np.random.default_rng(seed)
    pts = []
    ph1, ph2 = rng.uniform(0, 6.28, 2)
    n = (h if vertical else w) + 80
    for t in range(-40, n, 3):
        o = amp * math.sin(t / wl * 6.283 + ph1) + amp * extra * math.sin(t / (wl * 0.37) * 6.283 + ph2)
        pts.append((x0 + o, t) if vertical else (t, x0 + o))
    im = Image.new('L', (w, h), 0)
    ImageDraw.Draw(im).line(pts, fill=255, width=width, joint='curve')
    m = np.array(im) > 127
    dist = ndimage.distance_transform_edt(~m)
    return m, dist, pts


def blobs(h, w, centers, radii, seed, rough=0.35):
    yy, xx = np.mgrid[0:h, 0:w]
    n = fbm(h, w, seed, cells=(24, 48, 96))
    m = np.zeros((h, w), bool)
    for (cx, cy), r in zip(centers, radii):
        dd = np.hypot(xx - cx, yy - cy) / r
        m |= dd + (n - 0.5) * rough * 2 < 1.0
    return m


def lut_from(stops, n=256):
    pos = [p for p, _ in stops]
    xs = np.linspace(0, 1, n)
    return np.stack([np.interp(xs, pos, [c[k] for _, c in stops]) for k in range(3)], 1).astype(np.float32)


def outline(mask, width=2):
    er = ndimage.binary_erosion(mask, iterations=width)
    return mask & ~er


def glow(mask, color, radius=4, strength=0.9):
    g = ndimage.gaussian_filter(mask.astype(np.float32), radius)
    g = np.clip(g / max(g.max(), 1e-6) * strength, 0, 1)
    return g[..., None] * np.array(color, np.float32)[None, None, :]


# ---- video pipe ------------------------------------------------------------
class Video:
    def __init__(self, path, fps=30, w=W, h=H):
        self.tmp = path[:-4] + '.part.mp4'
        self.path = path
        self.p = subprocess.Popen(
            ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
             '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
             '-pix_fmt', 'yuv420p', '-movflags', '+faststart', self.tmp], stdin=subprocess.PIPE)

    def add(self, img):
        self.p.stdin.write(np.asarray(img.convert('RGB'), dtype=np.uint8).tobytes())

    def close(self):
        self.p.stdin.close()
        rc = self.p.wait()
        if rc == 0:
            import os
            os.replace(self.tmp, self.path)
        return rc


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)
