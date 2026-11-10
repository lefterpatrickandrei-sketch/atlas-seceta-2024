"""Video 20 s (1920×1080, 30 fps, H.264): productivitatea vegetației (HR-VPP TPROD) pe parcele, an cu an, 2017 → 2024,
cu graficul medianelor desenat în paralel și oprire 6 s pe 2024. Aceeași scară de culori în toți anii. Doar date reale.

Rezultate: data/out/final/atlas_tprod_2017_2024.mp4 și data/out/final/atlas_tprod_2024.png (ultimul cadru).
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 render/atlas_tprod_video.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from rasterio.transform import Affine  # noqa: E402

import atlas  # noqa: E402
from common import (AMBER, BG, GRID, LINE, MUTED, ORANGE, PW, PX0, TXT, TXT2, F, Layer, Video, card, draw_footer, draw_header,  # noqa: E402
                    fmt_int, new_canvas, north_arrow, scale_bar, section_label)
from gisday_config import BASE_YEARS, CRS, INTERIM, OUT, YEAR  # noqa: E402
from r1_hero import MAP_H, MAP_W, MAP_X, MAP_Y, SS, aoi_polygon, basemap, label, paint, to_image, towns  # noqa: E402
from tprod_pe_ani import compute_yearly_stats  # noqa: E402

YEARS = list(BASE_YEARS) + [YEAR]
FPS, SEGMENT, FADE, HOLD = 30, 60, 15, 180          # 2 s pe an, 0,5 s trecere, 2024 rămâne 6 s
N_FRAMES = SEGMENT * (len(YEARS) - 1) + HOLD          # 7 × 60 + 180 = 600 de cadre = 20 s
RAMP = [(0.0, (26, 44, 36)), (0.5, (78, 150, 86)), (1.0, (204, 238, 160))]     # o singură nuanță, de la întunecat la luminos
SPRING_RGB, AUTUMN_RGB = ORANGE, (64, 178, 148)       # aceleași culori ca în tprod_pe_ani.png
CHART = (PX0, 200, PX0 + PW, 690)
YEAR_CARD = (PX0, 706, PX0 + PW, 996)
Y_MIN, Y_MAX = 200.0, 1800.0
MP4 = OUT / 'final' / 'atlas_tprod_2017_2024.mp4'
STILL = OUT / 'final' / 'atlas_tprod_2024.png'


def version(year):
    return 'V101' if year <= 2020 else 'V105'


class Renderer:
    def __init__(self):
        parcels = gpd.read_parquet(OUT / 'parcels.parquet').to_crs(CRS)
        target = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'is_arable']]
        tprod = pd.read_parquet(OUT / 'parcel_features.parquet', columns=['parcel_id'] + [f'tprod_{y}' for y in YEARS])
        self.parcels = parcels.merge(target, on='parcel_id').merge(tprod, on='parcel_id')
        arable = self.parcels.is_arable.to_numpy(bool)
        values = self.parcels.loc[arable, [f'tprod_{y}' for y in YEARS]].to_numpy(float)
        lo, hi = np.nanpercentile(values, [2, 98])
        self.lo, self.hi = float(np.floor(lo / 100) * 100), float(np.ceil(hi / 100) * 100)    # aceeași scară în toți anii
        _, self.stats = compute_yearly_stats()
        self.loss_alt = json.loads((OUT / 'robustete_referinta.json').read_text(encoding='utf-8'))['pe_grupe']
        self.maps = self.render_maps(arable)
        self.static = self.render_static()

    def colors(self, year, arable):
        lut = np.array([np.interp(np.linspace(0, 1, 256), [p for p, _ in RAMP], [c[k] for _, c in RAMP]) for k in range(3)]).T
        rgba = np.zeros((len(self.parcels) + 1, 4), np.uint8)
        body = rgba[1:]
        v = self.parcels[f'tprod_{year}'].to_numpy(float)
        has = arable & ~np.isnan(v)
        pos = np.clip((v[has] - self.lo) / (self.hi - self.lo), 0, 1)
        body[has, :3] = lut[(pos * 255).round().astype(int)]
        body[has, 3] = 255
        body[arable & ~has, :3] = atlas.NO_REF_COLOR
        body[arable & ~has, 3] = 255
        return rgba

    def render_maps(self, arable):
        aoi = aoi_polygon()
        bounds = tuple(np.array(aoi.total_bounds) + np.array([-600, -600, 600, 600]))
        shape = (MAP_H * SS, MAP_W * SS)
        transform, pixel = atlas.fit_frame(bounds, shape[1], shape[0])
        self.map_px_m = pixel * SS
        base = basemap(INTERIM / 's2_august_2024.tif', transform, shape, aoi)
        final = transform * Affine.scale(SS)
        town_points = list(towns().itertuples())
        maps = []
        for year in YEARS:
            out, _ = paint(self.parcels, self.colors(year, arable), transform, shape, base)
            im = to_image(out, (MAP_W, MAP_H))
            d = ImageDraw.Draw(im)
            for town in town_points:
                col, row = ~final @ (town.geometry.x, town.geometry.y)
                d.ellipse((col - 3, row - 3, col + 3, row + 3), fill=TXT, outline=BG, width=1)
                label(d, (col + 8, row - 11), town.name, F(17, 'SemiBold'))
            maps.append(np.asarray(im.convert('RGB'), dtype=np.float32))
        return maps

    def px_x(self, i):
        x0, _, x1, _ = CHART
        return x0 + 70 + i * (x1 - x0 - 110) / (len(YEARS) - 1)

    def px_y(self, value):
        _, y0, _, y1 = CHART
        top, bottom = y0 + 92, y1 - 64
        return bottom - (value - Y_MIN) / (Y_MAX - Y_MIN) * (bottom - top)

    def render_static(self):
        img = new_canvas()
        draw_header(img, 'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei', 'Productivitatea vegetației pe parcele, 2017–2024',
                    'HR-VPP TPROD, sezonul 1, pe parcelele arabile: aceeași scară de culori în toți anii', badge=False)
        d = ImageDraw.Draw(img)
        d.rectangle((MAP_X - 1, MAP_Y - 1, MAP_X + MAP_W, MAP_Y + MAP_H), outline=LINE, width=1)

        card(img, (MAP_X, 874, MAP_X + MAP_W, 982))
        section_label(d, MAP_X + 20, 884, 'TPROD sezonul 1 (unități HR-VPP)')
        ramp_x, ramp_w = MAP_X + 20, 420
        strip = np.zeros((14, ramp_w, 3), np.float32)
        for k in range(3):
            strip[..., k] = np.interp(np.linspace(0, 1, ramp_w), [p for p, _ in RAMP], [c[k] for _, c in RAMP])[None, :]
        img.alpha_composite(Image.fromarray(strip.astype(np.uint8), 'RGB').convert('RGBA'), (ramp_x, 910))
        for pos, value in ((0, self.lo), (0.5, (self.lo + self.hi) / 2), (1, self.hi)):
            text = ('≤ ' if pos == 0 else '≥ ' if pos == 1 else '') + fmt_int(value)
            tx = ramp_x + pos * ramp_w - F(13).getlength(text) * pos
            d.text((tx, 928), text, font=F(13), fill=TXT2)
        d.rounded_rectangle((MAP_X + 470, 911, MAP_X + 492, 923), radius=3, fill=atlas.NO_REF_COLOR)
        d.text((MAP_X + 500, 908), 'Fără valoare', font=F(14), fill=TXT2)
        d.rounded_rectangle((MAP_X + 620, 911, MAP_X + 642, 923), radius=3, fill=BG, outline=atlas.NON_ARABLE_OUTLINE, width=2)
        d.text((MAP_X + 650, 908), 'Non-arabil (contur)', font=F(14), fill=TXT2)
        d.text((MAP_X + 20, 954), 'Productivitatea totală a sezonului, nu recolta; culorile se schimbă și din rotația culturilor.', font=F(14, 'Medium'), fill=TXT)
        scale_bar(img, self.map_px_m, 10, MAP_X + MAP_W - 285, 906)
        north_arrow(img, MAP_X + MAP_W - 44, 892, 22)

        card(img, CHART)
        x0, y0, x1, y1 = CHART
        section_label(d, x0 + 20, y0 + 16, 'Mediana TPROD pe parcelele cu țintă')
        lx = x0 + 20
        for name, color in (('Primăvară', SPRING_RGB), ('Toamnă', AUTUMN_RGB)):
            d.rounded_rectangle((lx, y0 + 52, lx + 22, y0 + 63), radius=3, fill=color)
            d.text((lx + 30, y0 + 48), name, font=F(14, 'Medium'), fill=TXT)
            lx += 30 + F(14, 'Medium').getlength(name) + 28
        for tick in range(400, 1801, 400):
            y = self.px_y(tick)
            d.line((x0 + 56, y, x1 - 24, y), fill=GRID, width=1)
            d.text((x0 + 48 - F(12).getlength(fmt_int(tick)), y - 8), fmt_int(tick), font=F(12), fill=MUTED)
        base_y = self.px_y(Y_MIN)
        d.line((x0 + 56, base_y, x1 - 24, base_y), fill=LINE, width=2)
        for i, year in enumerate(YEARS):
            xx = self.px_x(i)
            text = str(year)[2:] if year != YEAR else str(year)
            font = F(14, 'Bold') if year == YEAR else F(13, 'Medium')
            d.text((xx - font.getlength(text) / 2, base_y + 8), text, font=font, fill=AMBER if year == YEAR else TXT2)
            d.text((xx - F(10).getlength(version(year)) / 2, base_y + 28), version(year), font=F(10), fill=MUTED)

        card(img, YEAR_CARD)
        d.text((64, 1008), 'Limită: 2017–2020 sunt în HR-VPP V101, 2021–2024 în V105; pe vegetația permanentă V105 dă cu ~7% mai mult (D19).', font=F(14), fill=MUTED)
        draw_footer(img, 'Contains modified Copernicus Sentinel data 2017–2024 · CLMS HR-VPP · Fields of The World · © OpenStreetMap · Secetă 2024: AGERPRES (22.12.2024)')
        return img

    def timing(self, frame):
        """Indicele anului afișat, anul de pe care se face trecerea și ponderea trecerii (0 = anul vechi, 1 = anul nou)."""
        last = len(YEARS) - 1
        k = min(frame // SEGMENT, last)
        into = frame - k * SEGMENT
        if k < last and into >= SEGMENT - FADE:
            return k + 1, k, (into - (SEGMENT - FADE) + 1) / FADE
        return k, k, 1.0

    def frame(self, index):
        shown, previous, w = self.timing(index)
        img = self.static.copy()
        blend = self.maps[shown] if shown == previous else self.maps[previous] * (1 - w) + self.maps[shown] * w
        img.alpha_composite(Image.fromarray(blend.astype(np.uint8), 'RGB').convert('RGBA'), (MAP_X, MAP_Y))
        d = ImageDraw.Draw(img)
        is_2024 = YEARS[shown] == YEAR and shown == previous

        # Graficul: liniile până la anul afișat, ultimul segment crește în timpul trecerii
        layer = Layer(1920, 1080)
        x0, y0, x1, y1 = CHART
        if is_2024:
            xx = self.px_x(len(YEARS) - 1)
            d.rounded_rectangle((xx - 26, y0 + 84, xx + 26, self.px_y(Y_MIN) - 2), radius=6, outline=(185, 82, 64), width=2)
        for g, color in (('toamna', AUTUMN_RGB), ('primavara', SPRING_RGB)):
            pts = [(self.px_x(i), self.px_y(r['p50'])) for i, r in enumerate(self.stats[g])]
            drawn = pts[:previous + 1]
            if shown != previous:
                (ax, ay), (bx, by) = pts[previous], pts[shown]
                drawn.append((ax + (bx - ax) * w, ay + (by - ay) * w))
            layer.line(drawn, fill=color + (255,), width=3.5)
            for i, (px, py) in enumerate(pts[:shown + 1] if shown == previous else pts[:previous + 1]):
                layer.circle(px, py, 6 if i == shown else 4, fill=color + (255,), outline=TXT + (255,), width=1.5 if i == shown else 1)
        img.alpha_composite(layer.get())
        if shown == previous:
            for g in ('primavara', 'toamna'):
                r = self.stats[g][shown]
                other = self.stats['toamna' if g == 'primavara' else 'primavara'][shown]
                text = fmt_int(r['p50'])
                dy = -26 if r['p50'] >= other['p50'] else 10
                xx = self.px_x(shown)
                tx = min(xx - F(15, 'Bold').getlength(text) / 2, x1 - 22 - F(15, 'Bold').getlength(text))
                d.text((tx, self.px_y(r['p50']) + dy), text, font=F(15, 'Bold'), fill=TXT)

        # Cardul anului
        cx0, cy0, cx1, _ = YEAR_CARD
        year = YEARS[shown]
        big = F(96, 'Bold', True)
        d.text((cx0 + 20, cy0 + 6), str(year), font=big, fill=AMBER if is_2024 else TXT)
        right = cx0 + 32 + big.getlength(str(year))
        d.text((right, cy0 + 26), f'HR-VPP {version(year)}', font=F(15, 'Medium'), fill=MUTED)
        sp, au = self.stats['primavara'][shown]['p50'], self.stats['toamna'][shown]['p50']
        d.text((right, cy0 + 50), f'mediana: primăvară {fmt_int(sp)} · toamnă {fmt_int(au)}', font=F(16, 'Medium'), fill=TXT2)
        if is_2024:
            tag = 'SECETĂ 2024'
            d.rounded_rectangle((right, cy0 + 82, right + F(15, 'Bold').getlength(tag) + 24, cy0 + 108), radius=6, fill=(76, 36, 28), outline=AMBER, width=1)
            d.text((right + 12, cy0 + 86), tag, font=F(15, 'Bold'), fill=AMBER)
            spring_alt = self.loss_alt['primavara']
            lows = [spring_alt[k]['mediana_pct'] for k in ('a_2020_2023', 'b_2021_2023', 'oficial_2017_2023')]
            autumn = [self.loss_alt['toamna'][k]['mediana_pct'] for k in ('a_2020_2023', 'b_2021_2023', 'oficial_2017_2023')]
            lines = ('Pierderea față de anii comparabili:',
                     f"primăvară {spring_alt['oficial_2017_2023']['mediana_pct']:.0f}% ({min(lows):.0f}–{max(lows):.0f}% după referință),",
                     f"toamnă {max(0, min(autumn)):.0f}–{max(autumn):.0f}% după referință.")
            for i, text in enumerate(lines):
                d.text((cx0 + 20, cy0 + 132 + i * 26), text, font=F(17, 'SemiBold' if i == 0 else 'Regular'), fill=TXT if i == 0 else TXT2)
        else:
            d.text((cx0 + 20, cy0 + 132), 'Fiecare an pe aceeași scară de culori; parcelele', font=F(16), fill=MUTED)
            d.text((cx0 + 20, cy0 + 156), 'își schimbă și cultura de la un an la altul.', font=F(16), fill=MUTED)
        return img


def main():
    renderer = Renderer()
    video = Video(str(MP4), fps=FPS)
    for i in range(N_FRAMES):
        img = renderer.frame(i)
        video.add(img)
        if i == N_FRAMES - 1:
            img.convert('RGB').save(STILL, optimize=True)
    rc = video.close()
    assert rc == 0, f'ffmpeg a ieșit cu {rc}'
    print('scris:', MP4, 'și', STILL, f'| {N_FRAMES} cadre | scara {renderer.lo:.0f}–{renderer.hi:.0f}')


if __name__ == '__main__':
    main()
