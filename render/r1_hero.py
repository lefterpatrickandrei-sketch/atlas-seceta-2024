"""Harta-erou (1920×1080, EPSG:3844): pierderea observată în 2024, parcelă cu parcelă. Doar date reale.

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 render/r1_hero.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.transform import Affine  # noqa: E402
from rasterio.warp import Resampling, reproject  # noqa: E402

import atlas  # noqa: E402
from common import (BG, CYAN, GRID, LINE, MUTED, PW, PX0, TXT, TXT2, F, card, draw_footer, draw_header, fmt_dec, fmt_int,  # noqa: E402
                    new_canvas, north_arrow, ramp_bar, scale_bar, section_label)
from gisday_config import AOI_BBOX, CRS, GEE_PROJECT, INTERIM, OUT, RAW  # noqa: E402
from gisday_lib import overpass_elements  # noqa: E402

MAP_X, MAP_Y, MAP_W, MAP_H = 64, 200, 1120, 664
SS = 2                                  # supraeșantionare pentru margini curate
INSET = (76, 628, 340, 224)             # x, y, w, h pe pânză: colțul de sud-vest, fără culturi (Dunărea și malul bulgăresc)
INSET_PX_M = 10.0
CANAL_RGB = (96, 176, 226)
TOWNS = ['Sadova', 'Bechet', 'Dăbuleni', 'Corabia']
FACTOR_NAMES = {'elev': 'Altitudine', 'clay_sg_top': 'Argilă în sol', 'sand_sg_top': 'Nisip în sol', 'soc_sg_top': 'Carbon organic în sol',
                'slope': 'Pantă', 'dist_canal_m': 'Distanța la canal', 'dist_network_m': 'Distanța la rețeaua de apă',
                'wind_exposure': 'Expunerea la vânt', 'area_ha': 'Suprafața parcelei', 'soc_lucas_model': 'Carbon organic (LUCAS)'}


def aoi_polygon():
    cached = INTERIM / 'aoi_3844.gpkg'
    if not cached.exists():
        import ee
        from shapely.geometry import shape
        ee.Initialize(project=GEE_PROJECT)
        ro = ee.FeatureCollection('FAO/GAUL/2015/level0').filter(ee.Filter.eq('ADM0_NAME', 'Romania'))
        geom = ee.Geometry.Rectangle(list(AOI_BBOX)).intersection(ro.geometry(), ee.ErrorMargin(10))
        gpd.GeoDataFrame(geometry=[shape(geom.getInfo())], crs=4326).to_crs(CRS).to_file(cached, driver='GPKG')
    return gpd.read_file(cached)


def towns():
    cached = RAW / 'osm' / 'places.json'
    if not cached.exists():
        west, south, east, north = AOI_BBOX
        names = '|'.join(TOWNS)
        query = f'[out:json][timeout:60];(node["place"~"^(town|village)$"]["name"~"^({names})$"]({south},{west},{north},{east}););out;'
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(overpass_elements(query)), encoding='utf-8')
    rows = [(e['tags']['name'], e['lon'], e['lat']) for e in json.loads(cached.read_text(encoding='utf-8'))]
    frame = pd.DataFrame(rows, columns=['name', 'lon', 'lat']).drop_duplicates('name')
    return gpd.GeoDataFrame(frame, geometry=gpd.points_from_xy(frame.lon, frame.lat), crs=4326).to_crs(CRS)


def basemap(tif, transform, shape, aoi):
    """Imaginea Sentinel-2 ca fundal: desaturată și întunecată, cu zona din afara României și mai stinsă."""
    bands = np.zeros((3, *shape), np.float32)
    with rasterio.open(tif) as src:
        for i in range(3):
            reproject(rasterio.band(src, i + 1), bands[i], dst_transform=transform, dst_crs=CRS, resampling=Resampling.average,
                      src_nodata=0, dst_nodata=0)
    rgb = np.moveaxis(bands, 0, -1)
    valid = rgb.sum(axis=2) > 0
    tone = np.clip(np.clip((rgb - 1000) / 10000, 0, 1) * 3.1, 0, 1) ** 0.85
    gray = tone.mean(axis=2, keepdims=True)
    out = (0.32 * tone + 0.68 * gray) * 150 + np.array(BG, np.float32) * 0.5
    inside = rasterize(aoi.geometry, out_shape=shape, transform=transform, fill=0, default_value=1, dtype='uint8').astype(bool)
    out[~inside] *= 0.42
    out[~valid] = BG
    return out


def parcel_colors(parcels):
    """Tabel RGBA pe parcele (indexul 0 = fără parcelă): culori doar pe parcelele arabile."""
    rgba = np.zeros((len(parcels) + 1, 4), np.uint8)
    body = rgba[1:]
    arable = parcels.is_arable.to_numpy()
    has = arable & parcels.loss_obs.notna().to_numpy()
    autumn = arable & ~has & parcels.crop_group_2024.eq('toamna').to_numpy()
    other = arable & ~has & ~autumn
    body[has, :3] = atlas.loss_rgb(parcels.loss_obs.to_numpy()[has])
    body[has, 3] = 245
    body[autumn] = (96, 106, 120, 150)
    body[other] = (72, 78, 88, 120)
    return rgba


def paint(parcels, colors, transform, shape, base, edges=False):
    index = rasterize(((g, i) for i, g in enumerate(parcels.geometry, 1)), out_shape=shape, transform=transform, fill=0, dtype='int32')
    layer = colors[index].astype(np.float32)
    alpha = layer[..., 3:] / 255
    out = base * (1 - alpha) + layer[..., :3] * alpha
    if edges:
        line = (index != np.roll(index, 1, axis=0)) | (index != np.roll(index, 1, axis=1))
        out[line & (colors[index, 3] > 0)] *= 0.35
    return out, index


def burn_lines(out, ways, transform, color, alpha=0.8):
    mask = rasterize(ways.geometry, out_shape=out.shape[:2], transform=transform, fill=0, default_value=1, all_touched=True, dtype='uint8').astype(bool)
    out[mask] = out[mask] * (1 - alpha) + np.array(color, np.float32) * alpha


def burn_outline(out, index, ids, color):
    """Conturul parcelelor din `ids` (indexi de rasterizare), peste imagine."""
    from scipy import ndimage
    mask = np.isin(index, ids)
    edge = ndimage.binary_dilation(mask, iterations=2) & ~mask
    out[edge] = color


def to_image(array, size):
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), 'RGB').resize(size, Image.LANCZOS).convert('RGBA')


def label(draw, xy, text, font, fill=TXT):
    draw.text(xy, text, font=font, fill=fill, stroke_width=3, stroke_fill=BG)


def legend_swatch(draw, x, y, color, text, width=26):
    draw.rounded_rectangle((x, y + 3, x + width, y + 15), radius=3, fill=color)
    draw.text((x + width + 10, y), text, font=F(15), fill=TXT2)


def draw_histogram(img, frame, values, median):
    x0, y0, x1, y1 = frame
    edges, counts = atlas.loss_histogram(values)
    d = ImageDraw.Draw(img)
    bar_w = (x1 - x0) / len(counts)
    top = counts.max()
    colors = atlas.loss_rgb((edges[:-1] + edges[1:]) / 2)
    for fraction in (0.5, 1.0):
        y = y1 - (y1 - y0) * fraction
        d.line((x0, y, x1, y), fill=GRID, width=1)
    d.line((x0, y1, x1, y1), fill=LINE, width=1)
    for i, count in enumerate(counts):
        h = (y1 - y0) * count / top
        if h >= 1:
            d.rounded_rectangle((x0 + i * bar_w + 1, y1 - h, x0 + (i + 1) * bar_w - 2, y1), radius=3, fill=tuple(int(v) for v in colors[i]))
    span = edges[-1] - edges[0]
    for value in (-0.2, 0.0, 0.2):
        x = x0 + (value - edges[0]) / span * (x1 - x0)
        d.line((x, y1, x, y1 + 5), fill=LINE, width=1)
        text = fmt_dec(value, 1).replace('-', '−')
        d.text((x - F(14).getlength(text) / 2, y1 + 8), text, font=F(14), fill=TXT2)
    d.text((x1 - F(14).getlength('0,35'), y1 + 8), '0,35', font=F(14), fill=TXT2)
    x_median = x0 + (median - edges[0]) / span * (x1 - x0)
    d.line((x_median, y0 - 4, x_median, y1), fill=TXT, width=2)
    d.text((x_median + 8, y0 - 8), f'mediana {fmt_dec(median, 2)}', font=F(15, 'Medium'), fill=TXT)
    d.text((x0, y0 - 8), f'{fmt_int(top)} parcele', font=F(13), fill=MUTED)


def draw_factors(img, x0, y0, width, shap_means):
    d = ImageDraw.Draw(img)
    name_w, row = 210, 30
    top = shap_means.iloc[0]
    for i, (name, value) in enumerate(shap_means.items()):
        y = y0 + i * row
        d.text((x0, y), FACTOR_NAMES.get(name, name), font=F(16), fill=TXT2)
        d.rounded_rectangle((x0 + name_w, y + 4, x0 + name_w + (width - name_w) * value / top, y + 16), radius=3, fill=(120, 142, 170))


def main():
    parcels = gpd.read_parquet(OUT / 'parcels.parquet').merge(pd.read_parquet(OUT / 'parcel_target.parquet'), on='parcel_id')
    irrigation = OUT / 'irrigation_2024.parquet'
    if irrigation.exists():
        parcels = parcels.merge(pd.read_parquet(irrigation), on='parcel_id', how='left')
    aoi = aoi_polygon()
    canals = gpd.read_file(OUT / 'canals_osm.gpkg')
    main_canals = canals[canals.waterway == 'canal']
    base_tif = INTERIM / 's2_august_2024.tif'
    bounds = tuple(np.array(aoi.total_bounds) + np.array([-600, -600, 600, 600]))
    colors = parcel_colors(parcels)
    modeled = parcels[parcels.is_arable & parcels.loss_obs.notna()]
    k = atlas.hero_kpis(modeled)

    # harta
    shape = (MAP_H * SS, MAP_W * SS)
    transform, pixel = atlas.fit_frame(bounds, shape[1], shape[0])
    map_px_m = pixel * SS
    out, index = paint(parcels, colors, transform, shape, basemap(base_tif, transform, shape, aoi))
    burn_lines(out, main_canals, transform, CANAL_RGB, alpha=0.75)
    irrigated_ids = None
    if 'irrigated' in parcels:
        irrigated_ids = np.flatnonzero(parcels.irrigated.fillna(False).to_numpy(dtype=bool)) + 1
        burn_outline(out, index, irrigated_ids, CYAN)

    # pânza
    img = new_canvas()
    draw_header(img, 'GIS Day 2026 · Atlasul vulnerabilității la secetă · sudul Olteniei', 'Seceta din 2024, parcelă cu parcelă',
                'Cât a pierdut vegetația culturilor de primăvară față de anii în care parcela a avut același tip de cultură', badge=False)
    img.alpha_composite(to_image(out, (MAP_W, MAP_H)), (MAP_X, MAP_Y))
    d = ImageDraw.Draw(img)
    d.rectangle((MAP_X - 1, MAP_Y - 1, MAP_X + MAP_W, MAP_Y + MAP_H), outline=LINE, width=1)

    # localități
    final_transform = transform * Affine.scale(SS)
    for town in towns().itertuples():
        col, row = ~final_transform @ (town.geometry.x, town.geometry.y)
        px, py = MAP_X + col, MAP_Y + row
        d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=TXT, outline=BG, width=1)
        label(d, (px + 8, py - 11), town.name, F(17, 'SemiBold'))

    # detaliu
    ix, iy, iw, ih = INSET
    centroids = modeled.geometry.centroid
    blocks = (centroids.x // 5000).astype(int).astype(str) + '_' + (centroids.y // 5000).astype(int).astype(str)
    busiest = blocks.value_counts().idxmax()
    center = centroids[blocks == busiest].union_all().centroid
    half_w, half_h = iw * INSET_PX_M / 2, ih * INSET_PX_M / 2
    inset_bounds = (center.x - half_w, center.y - half_h, center.x + half_w, center.y + half_h)
    inset_shape = (ih * SS, iw * SS)
    inset_transform, _ = atlas.fit_frame(inset_bounds, inset_shape[1], inset_shape[0])
    inset_out, inset_index = paint(parcels, colors, inset_transform, inset_shape, basemap(base_tif, inset_transform, inset_shape, aoi), edges=True)
    burn_lines(inset_out, main_canals, inset_transform, CANAL_RGB, alpha=0.9)
    if irrigated_ids is not None:
        burn_outline(inset_out, inset_index, irrigated_ids, CYAN)
    img.alpha_composite(to_image(inset_out, (iw, ih)), (ix, iy))
    d.rectangle((ix - 1, iy - 1, ix + iw, iy + ih), outline=TXT2, width=1)
    label(d, (ix + 10, iy + 8), 'Detaliu · parcelele detectate de AI', F(14, 'SemiBold'))
    col, row = ~final_transform @ (inset_bounds[0], inset_bounds[3])
    d.rectangle((MAP_X + col, MAP_Y + row, MAP_X + col + iw * INSET_PX_M / map_px_m, MAP_Y + row + ih * INSET_PX_M / map_px_m), outline=TXT, width=2)

    # legendă
    card(img, (MAP_X, 880, MAP_X + MAP_W, 996))
    section_label(d, MAP_X + 20, 896, 'Pierdere de NDVI în iulie–august 2024')
    span = atlas.LOSS_MAX - atlas.LOSS_MIN
    stops = [((v - atlas.LOSS_MIN) / span, tuple(int(x) for x in atlas.loss_rgb(np.array([v]))[0])) for v in np.linspace(atlas.LOSS_MIN, atlas.LOSS_MAX, 23)]
    ramp_bar(img, MAP_X + 20, 922, 330, 12, stops,
             labels=[(0.0, 'câștig'), (-atlas.LOSS_MIN / span, '0'), ((0.15 - atlas.LOSS_MIN) / span, '0,15'), (1.0, '0,35')], label_font=F(14))
    swatch_x = MAP_X + 390
    legend_swatch(d, swatch_x, 900, (96, 106, 120), 'Culturi de toamnă, recoltate înainte de vârful secetei')
    legend_swatch(d, swatch_x, 926, (72, 78, 88), 'Arabil neclasificat sau fără ani de referință')
    d.line((swatch_x, 963, swatch_x + 26, 963), fill=CANAL_RGB, width=2)
    d.text((swatch_x + 36, 954), 'Canale (OpenStreetMap)', font=F(15), fill=TXT2)
    if irrigated_ids is not None:
        d.rounded_rectangle((swatch_x + 240, 957, swatch_x + 266, 969), radius=3, outline=CYAN, width=2)
        d.text((swatch_x + 276, 954), 'Parcele irigate detectate', font=F(15), fill=TXT2)
    scale_bar(img, map_px_m, 10, MAP_X + MAP_W - 290, 912)
    north_arrow(img, MAP_X + MAP_W - 44, 898, 22)
    d.text((MAP_X + MAP_W - 290, 962), 'Stereo 70 · EPSG:3844', font=F(13), fill=MUTED)

    # panou: indicatori
    x = PX0
    card(img, (x, 200, x + 296, 322))
    card(img, (x + 320, 200, x + PW, 322))
    section_label(d, x + 20, 216, 'Culturi de primăvară')
    d.text((x + 20, 240), f"{fmt_int(k['ha'])} ha", font=F(44, 'Bold', True), fill=TXT)
    d.text((x + 20, 294), f"{fmt_int(k['n'])} parcele analizate", font=F(16), fill=TXT2)
    section_label(d, x + 340, 216, 'Pierdere peste 0,2 NDVI')
    d.text((x + 340, 240), f"{fmt_int(k['ha_high'])} ha", font=F(44, 'Bold', True), fill=TXT)
    d.text((x + 340, 294), f"{k['share_high'] * 100:.0f}% din suprafața analizată", font=F(16), fill=TXT2)

    # panou: distribuția
    card(img, (x, 342, x + PW, 672))
    section_label(d, x + 20, 358, 'Câte parcele au pierdut cât')
    draw_histogram(img, (x + 24, 410, x + PW - 24, 630), modeled.loss_obs.to_numpy(), k['median_loss'])

    # panou: model
    metrics = json.loads((OUT / 'model_metrics.json').read_text(encoding='utf-8'))
    shap = pd.read_parquet(OUT / 'vulnerability.parquet')
    means = shap[[c for c in shap.columns if c.startswith('shap_')]].abs().mean().sort_values(ascending=False).head(5)
    means.index = means.index.str.replace('shap_', '', regex=False)
    card(img, (x, 692, x + PW, 996))
    section_label(d, x + 20, 708, 'Ce a mers împreună cu pierderea')
    draw_factors(img, x + 20, 736, PW - 40, means)
    d.line((x + 20, 896, x + PW - 20, 896), fill=LINE, width=1)
    d.text((x + 20, 908), f"Factorii structurali explică ~{fmt_dec(metrics['r2_spatial'] * 100, 1)}% din variație", font=F(19, 'SemiBold'), fill=TXT)
    d.text((x + 20, 938), f"R² spațial {fmt_dec(metrics['r2_spatial'], 3)} · validare pe blocuri de 5 km · {fmt_int(metrics['n_parcels'])} parcele", font=F(15), fill=TXT2)
    d.text((x + 20, 962), 'Asocieri, nu cauze dovedite.', font=F(15), fill=TXT2)

    draw_footer(img, 'Contains modified Copernicus Sentinel data 2024 · parcele Fields of The World · JRC EUCROPMAP · SoilGrids · ERA5-Land · © OpenStreetMap contributors')
    target = OUT / 'harta_erou.png'
    img.convert('RGB').save(target, optimize=True)
    print('scris:', target, f"| {k['n']} parcele, {k['ha']:.0f} ha, mediana {k['median_loss']:.3f}, {map_px_m:.1f} m/pixel, bloc detaliu {busiest}")


if __name__ == '__main__':
    main()
