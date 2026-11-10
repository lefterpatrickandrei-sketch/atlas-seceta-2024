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
from common import (BG, GRID, LINE, MUTED, PW, PX0, TXT, TXT2, F, Layer, card, draw_footer, draw_header, fmt_dec, fmt_int,  # noqa: E402
                    new_canvas, north_arrow, scale_bar, section_label)
from gisday_config import AOI_BBOX, CRS, GEE_PROJECT, INTERIM, OUT, RAW  # noqa: E402
from gisday_lib import overpass_elements  # noqa: E402

MAP_X, MAP_Y, MAP_W, MAP_H = 64, 200, 1120, 664
SS = 2                                  # supraeșantionare pentru margini curate
INSET = (76, 628, 340, 224)             # x, y, w, h pe pânză: colțul de sud-vest, fără culturi (Dunărea și malul bulgăresc)
INSET_PX_M = 10.0
CANAL_RGB = (96, 176, 226)
PIVOT_RGB = (237, 240, 243)     # contur fin, distinct de canale și de non-arabil
TOWNS = ['Sadova', 'Bechet', 'Dăbuleni', 'Corabia']
ROUND_MAX_FILL = 0.85                   # D31: un cerc umple 0,785 din dreptunghiul minim, un dreptunghi 1


def round_pivots(pivots):
    """D31: din pivoții geometrici (D26 pct. 4) rămân pe hartă doar parcelele rotunde, după cât umplu dreptunghiul minim."""
    fill = pivots.area / pivots.geometry.minimum_rotated_rectangle().area
    return pivots[fill <= ROUND_MAX_FILL]


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
    """Tabel RGBA pe parcele (indexul 0 = fără parcelă):
    - arabil cu țintă: cele 6 clase fixe din `atlas.loss_class_rgb` (opac, alpha=255)
    - arabil grup incert: gri deschis `atlas.INCERT_COLOR` (opac, alpha=255)
    - arabil fără an comparabil: gri închis `atlas.NO_REF_COLOR` (opac, alpha=255)
    - non-arabil: fără umplere (alpha=0); conturul fin se desenează separat în `paint`.
    """
    rgba = np.zeros((len(parcels) + 1, 4), np.uint8)
    body = rgba[1:]
    arable = parcels.is_arable.to_numpy(dtype=bool)
    incert = arable & parcels.tip_cultura_2024.eq('grup_incert').to_numpy()
    has = arable & ~incert & parcels.loss_rel.notna().to_numpy()
    no_ref = arable & ~incert & ~has
    body[has, :3] = atlas.loss_class_rgb(parcels.loss_rel.to_numpy()[has])
    body[has, 3] = 255
    body[incert, :3] = atlas.INCERT_COLOR
    body[incert, 3] = 255
    body[no_ref, :3] = atlas.NO_REF_COLOR
    body[no_ref, 3] = 255
    return rgba


def paint(parcels, colors, transform, shape, base, edges=False):
    index = rasterize(((g, i) for i, g in enumerate(parcels.geometry, 1)), out_shape=shape, transform=transform, fill=0, dtype='int32')
    layer = colors[index].astype(np.float32)
    alpha = layer[..., 3:] / 255.0
    out = base * (1.0 - alpha) + layer[..., :3] * alpha

    # Contur fin pe parcelele non-arabile (fără umplere)
    non_arable_ids = np.flatnonzero(~parcels.is_arable.to_numpy(dtype=bool)) + 1
    non_arable_mask = np.isin(index, non_arable_ids)
    line_any = (index != np.roll(index, 1, axis=0)) | (index != np.roll(index, 1, axis=1))
    non_arable_edge = line_any & non_arable_mask
    out[non_arable_edge] = out[non_arable_edge] * 0.35 + np.array(atlas.NON_ARABLE_OUTLINE, np.float32) * 0.65

    if edges:
        arable_edge = line_any & (colors[index, 3] > 0)
        out[arable_edge] *= 0.38
    return out, index


def burn_lines(out, ways, transform, color, alpha=0.8):
    mask = rasterize(ways.geometry, out_shape=out.shape[:2], transform=transform, fill=0, default_value=1, all_touched=True, dtype='uint8').astype(bool)
    out[mask] = out[mask] * (1 - alpha) + np.array(color, np.float32) * alpha


def to_image(array, size):
    return Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), 'RGB').resize(size, Image.LANCZOS).convert('RGBA')


def label(draw, xy, text, font, fill=TXT):
    draw.text(xy, text, font=font, fill=fill, stroke_width=3, stroke_fill=BG)


def legend_swatch(draw, x, y, color, text, width=22, outline_only=False):
    if outline_only:
        draw.rounded_rectangle((x, y + 3, x + width, y + 15), radius=3, fill=BG, outline=color, width=2)
    else:
        draw.rounded_rectangle((x, y + 3, x + width, y + 15), radius=3, fill=color)
    draw.text((x + width + 8, y), text, font=F(14), fill=TXT2)


def fmt_signed_pct(val_pct, nd=1):
    s = fmt_dec(abs(val_pct), nd)
    if val_pct > 0:
        return f'+{s}%'
    if val_pct < 0:
        return f'−{s}%'
    return f'{s}%'


def draw_group_distribution(img, x0, y0, width, modeled):
    """Panou 1: distribuția pierderii pe grupe (primăvară vs toamnă), mediana, P25–P75 și N pe fiecare grupă."""
    d = ImageDraw.Draw(img)
    groups = [
        ('primavara', 'Culturi de primăvară', 'porumb, floarea-soarelui, soia (NDVI apr. < 0,38, fără furaje)'),
        ('toamna', 'Culturi de toamnă', 'grâu, orz, rapiță (NDVI apr. > 0,45, fără furaje)'),
    ]
    scale_min, scale_max = -60.0, 80.0
    bar_x0 = x0
    bar_w = width

    for idx, (g_key, g_title, g_sub) in enumerate(groups):
        top_y = y0 + idx * 156
        sub = modeled[modeled.tip_cultura_2024 == g_key]
        pct = sub.loss_rel.to_numpy() * 100.0
        n_grp = len(sub)
        ha_grp = float(sub.area_ha.sum())
        p25, med, p75 = np.percentile(pct, [25, 50, 75])

        # Titlu grup + N + suprafață
        d.text((bar_x0, top_y), g_title, font=F(19, 'SemiBold'), fill=TXT)
        n_txt = f'N = {fmt_int(n_grp)} parcele ({fmt_int(ha_grp)} ha)'
        d.text((bar_x0 + bar_w - F(14, 'Medium').getlength(n_txt), top_y + 3), n_txt, font=F(14, 'Medium'), fill=TXT2)
        d.text((bar_x0, top_y + 23), g_sub, font=F(13), fill=MUTED)

        # Cifre cheie: Mediana și P25–P75
        med_str = f'Mediană: {fmt_signed_pct(med, 1)}'
        iqr_str = f'P25–P75: {fmt_signed_pct(p25, 1)} … {fmt_signed_pct(p75, 1)}'
        d.text((bar_x0, top_y + 45), med_str, font=F(20, 'Bold', True), fill=TXT)
        d.text((bar_x0 + 210, top_y + 48), iqr_str, font=F(15, 'Medium'), fill=TXT2)

        # Bară stivuită pe cele 6 clase fixe
        cls_idx = atlas.loss_class_index(sub.loss_rel.to_numpy())
        counts = np.bincount(cls_idx, minlength=6)
        shares = counts / max(n_grp, 1)
        by0, by1 = top_y + 76, top_y + 96
        cur_x = float(bar_x0)
        for c_i in range(6):
            seg_w = bar_w * shares[c_i]
            if seg_w >= 1.0:
                col = tuple(int(v) for v in atlas.LOSS_CLASS_COLORS[c_i])
                d.rectangle((cur_x, by0, cur_x + seg_w, by1), fill=col)
                if seg_w >= 44:
                    pct_lbl = f'{shares[c_i] * 100:.0f}%'
                    tw_lbl = F(12, 'SemiBold').getlength(pct_lbl)
                    d.text((cur_x + (seg_w - tw_lbl) / 2, by0 + 3), pct_lbl, font=F(12, 'SemiBold'), fill=BG if c_i in (1, 2, 3) else TXT)
            cur_x += seg_w
        d.rectangle((bar_x0, by0, bar_x0 + bar_w, by1), outline=LINE, width=1)

        # Axă + boxplot P25–Mediană–P75 pe scara [-60%, +80%]
        ax_y = top_y + 116
        d.line((bar_x0, ax_y, bar_x0 + bar_w, ax_y), fill=GRID, width=2)

        def to_px(val):
            v_clip = min(max(val, scale_min), scale_max)
            return bar_x0 + (v_clip - scale_min) / (scale_max - scale_min) * bar_w

        x_zero = to_px(0.0)
        d.line((x_zero, ax_y - 8, x_zero, ax_y + 8), fill=MUTED, width=1)
        x_p25, x_med, x_p75 = to_px(p25), to_px(med), to_px(p75)
        box_col = (232, 128, 48) if g_key == 'primavara' else (138, 148, 152)
        d.rounded_rectangle((x_p25, ax_y - 6, x_p75, ax_y + 6), radius=3, fill=box_col, outline=TXT2, width=1)
        d.line((x_med, ax_y - 9, x_med, ax_y + 9), fill=TXT, width=3)

        if idx == 1:
            for tick in (-50, -25, 0, 25, 50, 75):
                tx = to_px(tick)
                d.line((tx, ax_y + 6, tx, ax_y + 11), fill=LINE, width=1)
                t_str = f'{tick:+d}%'.replace('-', '−').replace('+0%', '0%')
                d.text((tx - F(12).getlength(t_str) / 2, ax_y + 13), t_str, font=F(12), fill=MUTED)


def draw_radar_panel(img, x0, y0, width, placebo):
    """Panou 3 (D30): regula radar, testul placebo pe miriștile de toamnă și concluzia. Cifrele vin din diagnosticul S1."""
    d = ImageDraw.Draw(img)
    events = placebo['toate']
    d.text((x0, y0), 'Regula: VV crește cu cel puțin 1,5 dB în 12 zile, fără ploaie.', font=F(15, 'Medium'), fill=TXT2)
    big = F(32, 'Bold', True)
    for offset, value, line1, line2 in ((0, events['primavara_pct'], 'evenimente pe culturile', 'de primăvară'),
                                        (292, events['toamna_pct'], 'evenimente pe miriști', 'de toamnă (placebo)')):
        number = f'{fmt_dec(value, 2)}%'
        d.text((x0 + offset, y0 + 26), number, font=big, fill=TXT)
        text_x = x0 + offset + big.getlength(number) + 12
        d.text((text_x, y0 + 30), line1, font=F(14), fill=TXT2)
        d.text((text_x, y0 + 49), line2, font=F(14), fill=TXT2)
    signed = lambda v: fmt_signed_pct(v, 2).rstrip('%')  # noqa: E731
    low, high = events['ic95_pp']
    d.text((x0, y0 + 76), f"Diferență: {signed(events['diferenta_pp'])} pp (IC 95%: {signed(low)}…{signed(high)} pp), bootstrap pe blocuri de 5 km.", font=F(13), fill=MUTED)
    d.line((x0, y0 + 100, x0 + width, y0 + 100), fill=LINE, width=1)
    d.text((x0, y0 + 110), 'Semnalul radar din august nu separă irigarea.', font=F(21, 'SemiBold'), fill=TXT)


def build_loss_gpkg(parcels):
    """Construiește și salvează `data/out/loss_2024.gpkg` (EPSG:3844) cu clasa de pierdere pe fiecare parcelă."""
    out_gdf = parcels[['parcel_id', 'area_ha', 'is_arable', 'tip_cultura_2024', 'n_ref_years', 'ref', 'loss_rel', 'geometry']].copy()
    out_gdf['loss_pct_lfl'] = (out_gdf['loss_rel'] * 100.0).round(2)
    clasa = np.full(len(out_gdf), 'non-arabil', dtype=object)
    arable = out_gdf['is_arable'].to_numpy(dtype=bool)
    incert = arable & out_gdf['tip_cultura_2024'].eq('grup_incert').to_numpy()
    has = arable & ~incert & out_gdf['loss_rel'].notna().to_numpy()
    no_ref = arable & ~incert & ~has
    clasa[incert] = 'grup incert'
    clasa[no_ref] = 'fără an comparabil'
    clasa[has] = atlas.loss_class_label(out_gdf.loc[has, 'loss_rel'].to_numpy())
    out_gdf['clasa_pierdere'] = clasa
    out_gdf = gpd.GeoDataFrame(out_gdf, geometry='geometry', crs=CRS)
    gpkg_path = OUT / 'loss_2024.gpkg'
    out_gdf.to_file(gpkg_path, layer='loss_2024', driver='GPKG')
    return out_gdf


def main():
    parcels = gpd.read_parquet(OUT / 'parcels.parquet').merge(pd.read_parquet(OUT / 'parcel_target.parquet'), on='parcel_id')
    parcels = parcels.to_crs(CRS)
    build_loss_gpkg(parcels)

    aoi = aoi_polygon()
    canals = gpd.read_file(OUT / 'canals_osm.gpkg')
    main_canals = canals[canals.waterway == 'canal']
    pivot_outlines = round_pivots(gpd.read_file(OUT / 'pivots_2024.gpkg').to_crs(CRS)).boundary
    print('pivoți desenați (rotunzi):', len(pivot_outlines))
    base_tif = INTERIM / 's2_august_2024.tif'
    bounds = tuple(np.array(aoi.total_bounds) + np.array([-600, -600, 600, 600]))
    colors = parcel_colors(parcels)
    modeled = parcels[parcels.is_arable & parcels.loss_rel.notna()].copy()
    incert_cnt = int((parcels.is_arable & parcels.tip_cultura_2024.eq('grup_incert')).sum())
    no_ref_cnt = int((parcels.is_arable & ~parcels.tip_cultura_2024.eq('grup_incert') & parcels.loss_rel.isna()).sum())
    non_arable_cnt = int((~parcels.is_arable).sum())

    # Harta principală
    shape = (MAP_H * SS, MAP_W * SS)
    transform, pixel = atlas.fit_frame(bounds, shape[1], shape[0])
    map_px_m = pixel * SS
    out, index = paint(parcels, colors, transform, shape, basemap(base_tif, transform, shape, aoi))
    burn_lines(out, main_canals, transform, CANAL_RGB, alpha=0.75)
    burn_lines(out, pivot_outlines, transform, PIVOT_RGB, alpha=0.9)

    # Pânza 1920×1080
    img = new_canvas()
    draw_header(
        img,
        'GIS Day 2026 · Atlasul secetei din 2024 — sudul Olteniei',
        'Seceta din 2024, parcelă cu parcelă',
        'Pierderea de productivitate (HR-VPP TPROD) față de mediana anilor 2017–2023 cu același tip de cultură',
        badge=False,
    )
    img.alpha_composite(to_image(out, (MAP_W, MAP_H)), (MAP_X, MAP_Y))
    d = ImageDraw.Draw(img)
    d.rectangle((MAP_X - 1, MAP_Y - 1, MAP_X + MAP_W, MAP_Y + MAP_H), outline=LINE, width=1)

    # Localități
    final_transform = transform * Affine.scale(SS)
    for town in towns().itertuples():
        col, row = ~final_transform @ (town.geometry.x, town.geometry.y)
        px, py = MAP_X + col, MAP_Y + row
        d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=TXT, outline=BG, width=1)
        label(d, (px + 8, py - 11), town.name, F(17, 'SemiBold'))

    # Fereastră de detaliu (blocul de 5 km cu cele mai multe parcele)
    ix, iy, iw, ih = INSET
    centroids = modeled.geometry.centroid
    blocks = (centroids.x // 5000).astype(int).astype(str) + '_' + (centroids.y // 5000).astype(int).astype(str)
    busiest = blocks.value_counts().idxmax()
    center = centroids[blocks == busiest].union_all().centroid
    half_w, half_h = iw * INSET_PX_M / 2, ih * INSET_PX_M / 2
    inset_bounds = (center.x - half_w, center.y - half_h, center.x + half_w, center.y + half_h)
    inset_shape = (ih * SS, iw * SS)
    inset_transform, _ = atlas.fit_frame(inset_bounds, inset_shape[1], inset_shape[0])
    inset_out, _ = paint(parcels, colors, inset_transform, inset_shape, basemap(base_tif, inset_transform, inset_shape, aoi), edges=True)
    burn_lines(inset_out, main_canals, inset_transform, CANAL_RGB, alpha=0.9)
    burn_lines(inset_out, pivot_outlines, inset_transform, PIVOT_RGB, alpha=0.9)
    img.alpha_composite(to_image(inset_out, (iw, ih)), (ix, iy))
    d.rectangle((ix - 1, iy - 1, ix + iw, iy + ih), outline=TXT2, width=1)
    label(d, (ix + 10, iy + 8), 'Detaliu · mozaicul pierderii pe parcelă', F(14, 'SemiBold'))
    col, row = ~final_transform @ (inset_bounds[0], inset_bounds[3])
    d.rectangle((MAP_X + col, MAP_Y + row, MAP_X + col + iw * INSET_PX_M / map_px_m, MAP_Y + row + ih * INSET_PX_M / map_px_m), outline=TXT, width=2)

    # Legendă (6 clase fixe + grup incert + fără an comparabil + non-arabil + canale + scară + nord + CRS)
    card(img, (MAP_X, 874, MAP_X + MAP_W, 982))
    section_label(d, MAP_X + 20, 884, f'Pierderea observată în 2024 (loss_rel × 100 · {fmt_int(len(modeled))} parcele cu referință)')
    col_x = [MAP_X + 20, MAP_X + 165, MAP_X + 275, MAP_X + 385, MAP_X + 495, MAP_X + 605]
    for c_i, (lbl_cls, rgb_cls) in enumerate(zip(atlas.LOSS_CLASS_LABELS, atlas.LOSS_CLASS_COLORS)):
        legend_swatch(d, col_x[c_i], 906, tuple(int(v) for v in rgb_cls), lbl_cls)

    legend_swatch(d, MAP_X + 20, 932, atlas.INCERT_COLOR, f'Grup incert ({fmt_int(incert_cnt)})')
    legend_swatch(d, MAP_X + 210, 932, atlas.NO_REF_COLOR, f'Fără an comparabil ({fmt_int(no_ref_cnt)})')
    legend_swatch(d, MAP_X + 445, 932, atlas.NON_ARABLE_OUTLINE, f'Non-arabil ({fmt_int(non_arable_cnt)})', outline_only=True)
    d.line((MAP_X + 645, 940, MAP_X + 669, 940), fill=CANAL_RGB, width=3)
    d.text((MAP_X + 677, 932), 'Canale (OSM)', font=F(14), fill=TXT2)
    ring = Layer(22, 22)
    ring.circle(11, 11, 8, outline=PIVOT_RGB + (255,), width=1)
    img.alpha_composite(ring.get(), (MAP_X + 20, 956))
    d.text((MAP_X + 50, 958), 'Parcele circulare (posibili pivoți)', font=F(14), fill=TXT2)

    scale_bar(img, map_px_m, 10, MAP_X + MAP_W - 285, 906)
    north_arrow(img, MAP_X + MAP_W - 44, 892, 22)
    d.text((MAP_X + MAP_W - 285, 954), 'EPSG:3844 · Stereo 70', font=F(13, 'Medium'), fill=MUTED)

    # Frază explicativă imediat sub legendă
    d.text(
        (MAP_X, 988),
        'Fiecare parcelă e comparată cu anii 2017–2023 în care a avut același tip de cultură; „câștig” = 2024 peste mediana acelor ani.',
        font=F(15, 'Medium'),
        fill=TXT2,
    )

    # ---- Coloana din dreapta: 3 panouri (PAS D-B pct. 2, 3, 4) ----
    x = PX0

    # Panou 1: distribuția pierderii pe grupe (primăvară vs toamnă)
    card(img, (x, 200, x + PW, 578))
    section_label(d, x + 20, 216, 'Panou 1 · Distribuția pierderii pe grupe de cultură')
    draw_group_distribution(img, x + 20, 248, PW - 40, modeled)

    # Panou 2: Ce am testat și n-a explicat pierderea
    card(img, (x, 594, x + PW, 774))
    section_label(d, x + 20, 610, 'Panou 2 · Ce am testat și n-a explicat pierderea')
    d.text((x + 20, 640), 'Solul (SoilGrids 250 m), relieful, expunerea la vânt și distanța', font=F(18, 'SemiBold'), fill=TXT)
    d.text((x + 20, 666), 'la canale nu explică diferențele de pierdere în interiorul grupelor.', font=F(18, 'SemiBold'), fill=TXT)
    d.line((x + 20, 702, x + PW - 20, 702), fill=LINE, width=1)
    d.text((x + 20, 714), 'R² spațial în interiorul grupelor ≈ 0 (primăvară 0,003 · toamnă 0,006)', font=F(15, 'Medium'), fill=TXT2)
    d.text((x + 20, 738), 'Validare pe blocuri spațiale de 5 km (82 blocuri · 11.965 parcele · LightGBM).', font=F(14), fill=MUTED)

    # Panou 3: încercarea de a vedea irigarea din radar (D30)
    card(img, (x, 790, x + PW, 996))
    section_label(d, x + 20, 806, 'Panou 3 · Am încercat să vedem irigarea din radar')
    diagnostic = json.loads((OUT / 's1_events_diagnostic.json').read_text(encoding='utf-8'))
    draw_radar_panel(img, x + 20, 836, PW - 40, diagnostic['placebo_toamna'])

    # Limită metodologică scrisă mic + Subsol (PAS D-B pct. 5 + D27 pct. 2)
    d.text((64, 1012), 'Limite: TPROD măsoară productivitatea vegetației, nu recolta în t/ha (V101 2017–2020, V105 2021–2024). S1 valid aproape doar în aug. 2024; pivoții geometrici pot fi inactivi.', font=F(13), fill=MUTED)
    draw_footer(img, 'Contains modified Copernicus Sentinel data 2024 · CLMS HR-VPP · ERA5-Land · Fields of The World · SoilGrids · © OpenStreetMap')

    target = OUT / 'harta_erou.png'
    img.convert('RGB').save(target, optimize=True)
    print('scris:', target, 'și', OUT / 'loss_2024.gpkg', f'| {len(modeled)} parcele cu țintă, {incert_cnt} grup incert, {no_ref_cnt} fără an comparabil, {non_arable_cnt} non-arabile, {map_px_m:.1f} m/pixel')


if __name__ == '__main__':
    main()
