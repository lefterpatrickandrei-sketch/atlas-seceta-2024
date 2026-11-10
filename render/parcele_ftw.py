"""Hartă 1920×1080 (stilul render/, EPSG:3844): parcelele Fields of The World conturate peste Sentinel-2 din iulie 2024,
pe un detaliu de 5 × 3 km, plus un cadru mic cu toată zona. Doar date reale.

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 render/parcele_ftw.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from PIL import ImageDraw  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.transform import Affine  # noqa: E402
from rasterio.warp import Resampling, reproject  # noqa: E402
from shapely.geometry import box  # noqa: E402

import atlas  # noqa: E402
from common import (AMBER, BG, CYAN, LINE, MUTED, PW, PX0, TXT, TXT2, F, Layer, card, draw_footer, draw_header, fmt_dec,  # noqa: E402
                    fmt_int, new_canvas, north_arrow, scale_bar, section_label)
from gisday_config import CRS, INTERIM, OUT  # noqa: E402
from r1_hero import aoi_polygon, basemap, label, to_image, towns  # noqa: E402

MAP_X, MAP_Y, MAP_W, MAP_H = 64, 200, 1120, 672      # 5:3, ca detaliul de 5 × 3 km
ZOOM_W, ZOOM_H = 5000.0, 3000.0                      # metri
OVERVIEW_W = PW - 40
SS = 2
S2_TIF = INTERIM / 's2_iulie_2024.tif'               # benzile 1–3 = roșu, verde, albastru
OUTLINE_RGB = CYAN


def busiest_block_window(parcels):
    """Fereastra de 5 × 3 km centrată pe parcelele din blocul de 5 km cu cele mai multe parcele (aceeași regulă ca detaliul hărții-erou)."""
    centroids = parcels.geometry.centroid
    blocks = (centroids.x // 5000).astype(int).astype(str) + '_' + (centroids.y // 5000).astype(int).astype(str)
    center = centroids[blocks == blocks.value_counts().idxmax()].union_all().centroid
    return (center.x - ZOOM_W / 2, center.y - ZOOM_H / 2, center.x + ZOOM_W / 2, center.y + ZOOM_H / 2)


def true_color(transform, shape):
    """Sentinel-2 în culori naturale, întins pe P2–P98 din fereastră (comun celor trei benzi), ușor întunecat ca să se vadă contururile."""
    bands = np.zeros((3, *shape), np.float32)
    with rasterio.open(S2_TIF) as src:
        for i in range(3):
            reproject(rasterio.band(src, i + 1), bands[i], dst_transform=transform, dst_crs=CRS, resampling=Resampling.bilinear,
                      src_nodata=0, dst_nodata=0)
    valid = bands.sum(axis=0) > 0
    lo, hi = np.percentile(bands[:, valid], [2, 98])          # aceeași întindere pe toate benzile: culorile își păstrează echilibrul
    out = np.clip((np.moveaxis(bands, 0, -1) - lo) / (hi - lo), 0, 1) ** 0.9
    out = out * 205
    out[~valid] = BG
    return out


def to_px(transform, x, y):
    col, row = ~transform @ (x, y)
    return col, row


def outline_layer(parcels, transform, size):
    """Contururile parcelelor, desenate vectorial și netezite (supraeșantionare 2×), cu un halou închis sub linie."""
    layer = Layer(*size)
    rings = []
    for geom in parcels.geometry:
        for poly in getattr(geom, 'geoms', [geom]):
            rings += [poly.exterior, *poly.interiors]
    paths = [[to_px(transform, x, y) for x, y in ring.coords] for ring in rings]
    for path in paths:
        layer.line(path, fill=BG + (150,), width=3)
    for path in paths:
        layer.line(path, fill=OUTLINE_RGB + (255,), width=1.4)
    return layer.get()


def overview(parcels, aoi, window, town_points):
    """Cadrul mic: toată zona, cu parcelele în umplere discretă și dreptunghiul detaliului."""
    bounds = tuple(np.array(aoi.total_bounds) + np.array([-600, -600, 600, 600]))
    ratio = (bounds[3] - bounds[1]) / (bounds[2] - bounds[0])
    size = (OVERVIEW_W, int(round(OVERVIEW_W * ratio)))
    shape = (size[1] * SS, size[0] * SS)
    transform, pixel = atlas.fit_frame(bounds, shape[1], shape[0])
    base = basemap(S2_TIF, transform, shape, aoi)
    mask = rasterize(parcels.geometry, out_shape=shape, transform=transform, fill=0, default_value=1, dtype='uint8').astype(bool)
    base[mask] = base[mask] * 0.45 + np.array(OUTLINE_RGB, np.float32) * 0.55
    img = to_image(base, size)
    d = ImageDraw.Draw(img)
    final = transform * Affine.scale(SS)
    x0, y0 = to_px(final, window[0], window[3])
    x1, y1 = to_px(final, window[2], window[1])
    d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), outline=AMBER, width=2)
    for town in town_points.itertuples():
        px, py = to_px(final, town.geometry.x, town.geometry.y)
        d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=TXT)
        width = F(13, 'SemiBold').getlength(town.name)
        tx = px + 6 if px + 6 + width < size[0] - 4 else px - 6 - width      # eticheta nu iese din cadru
        label(d, (tx, py - 9), town.name, F(13, 'SemiBold'))
    return img, pixel * SS


def main():
    parcels = gpd.read_parquet(OUT / 'parcels.parquet').to_crs(CRS)
    aoi = aoi_polygon()
    town_points = towns()
    window = busiest_block_window(parcels)
    frame = box(*window)
    inside = parcels[parcels.intersects(frame)]
    whole = inside[inside.within(frame)]

    # Detaliul de 5 × 3 km
    shape = (MAP_H * SS, MAP_W * SS)
    transform, pixel = atlas.fit_frame(window, shape[1], shape[0])
    photo = to_image(true_color(transform, shape), (MAP_W, MAP_H))
    map_transform = transform * Affine.scale(SS)
    photo.alpha_composite(outline_layer(inside, map_transform, (MAP_W, MAP_H)))

    img = new_canvas()
    draw_header(
        img,
        'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei',
        'Unitatea de analiză: parcela, detectată automat',
        'Contururile Fields of The World peste Sentinel-2 din iulie 2024 · detaliu de 5 × 3 km din blocul cu cele mai multe parcele',
        badge=False,
    )
    img.alpha_composite(photo, (MAP_X, MAP_Y))
    d = ImageDraw.Draw(img)
    d.rectangle((MAP_X - 1, MAP_Y - 1, MAP_X + MAP_W, MAP_Y + MAP_H), outline=LINE, width=1)
    for town in town_points.itertuples():
        px, py = to_px(map_transform, town.geometry.x, town.geometry.y)
        if 20 < px < MAP_W - 160 and 20 < py < MAP_H - 30:
            d.ellipse((MAP_X + px - 4, MAP_Y + py - 4, MAP_X + px + 4, MAP_Y + py + 4), fill=TXT, outline=BG, width=1)
            label(d, (MAP_X + px + 10, MAP_Y + py - 12), town.name, F(18, 'SemiBold'))

    # Legenda de sub detaliu
    card(img, (MAP_X, 888, MAP_X + MAP_W, 984))
    d.line((MAP_X + 24, 916, MAP_X + 52, 916), fill=BG, width=4)
    d.line((MAP_X + 24, 916, MAP_X + 52, 916), fill=OUTLINE_RGB, width=2)
    d.text((MAP_X + 62, 906), 'Parcelă Fields of The World (contur automat, ≥ 0,5 ha)', font=F(15, 'Medium'), fill=TXT)
    d.text((MAP_X + 24, 942), 'Fundal: Sentinel-2, iulie 2024, culori naturale', font=F(14), fill=TXT2)
    scale_bar(img, pixel * SS, 1, MAP_X + MAP_W - 300, 906)
    north_arrow(img, MAP_X + MAP_W - 48, 898, 20)
    d.text((MAP_X + MAP_W - 300, 950), 'EPSG:3844 · Stereo 70', font=F(13, 'Medium'), fill=MUTED)

    # Coloana din dreapta: toată zona + cifre
    x = PX0
    over, over_px_m = overview(parcels, aoi, window, town_points)
    card(img, (x, 200, x + PW, 238 + over.size[1] + 64))
    section_label(d, x + 20, 216, 'Toată zona · dreptunghiul = detaliul')
    img.alpha_composite(over, (x + 20, 244))
    d.rectangle((x + 19, 243, x + 20 + over.size[0], 244 + over.size[1]), outline=LINE, width=1)
    scale_bar(img, over_px_m, 10, x + 20, 244 + over.size[1] + 14)
    d.text((x + 200, 244 + over.size[1] + 22), 'parcele FTW în umplere turcoaz', font=F(13), fill=TXT2)

    y_card = 238 + over.size[1] + 80
    card(img, (x, y_card, x + PW, 984))
    section_label(d, x + 20, y_card + 16, 'Cifre')
    total, km2 = len(parcels), parcels.area.sum() / 1e6
    d.text((x + 20, y_card + 46), fmt_int(total), font=F(44, 'Bold', True), fill=TXT)
    big_w = F(44, 'Bold', True).getlength(fmt_int(total))
    d.text((x + 32 + big_w, y_card + 52), 'parcele de cel puțin 0,5 ha', font=F(16, 'Medium'), fill=TXT2)
    d.text((x + 32 + big_w, y_card + 74), f'{fmt_dec(km2, 1)} km² în toată zona', font=F(16, 'Medium'), fill=TXT2)
    lines = (
        (f'În detaliu: {fmt_int(len(inside))} parcele atinse, {fmt_int(len(whole))} întregi', TXT),
        (f'Suprafața mediană: {fmt_dec(parcels.area_ha.median(), 1)} ha în toată zona,', TXT2),
        (f'{fmt_dec(whole.area_ha.median(), 1)} ha pentru parcelele întregi din detaliu', TXT2),
        ('Model: Fields of The World (ftw-tools 1.4.3), pe două', TXT2),
        ('scene Sentinel-2: 12 aprilie și 11 iulie 2024', TXT2),
    )
    for i, (text, color) in enumerate(lines):
        d.text((x + 20, y_card + 118 + i * 26), text, font=F(16, 'Medium' if color == TXT else 'Regular'), fill=color)

    d.text((64, 1008), 'Limită: contururile sunt detectate automat; parcelele sub 0,5 ha sunt eliminate. Pe parcelă se calculează pierderea din 2024 și toți factorii testați.', font=F(14), fill=MUTED)
    draw_footer(img, 'Contains modified Copernicus Sentinel data 2024 · Fields of The World (ftw-tools 1.4.3) · © OpenStreetMap')
    target = OUT / 'parcele_ftw.png'
    img.convert('RGB').save(target, optimize=True)
    print('scris:', target, f'| fereastra {[round(v) for v in window]} | {len(inside)} atinse, {len(whole)} întregi | {pixel * SS:.2f} m/pixel')


if __name__ == '__main__':
    main()
