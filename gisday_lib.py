"""Funcții comune pentru notebook-urile GIS Day 2026. Logica de aici e acoperită de tests/test_gisday_lib.py."""
import hashlib
import subprocess

MARGIN_NORTH_DEG = 0.12     # > un rând de ferestre FTW (896 px = 9 km): ftw pierde ultimul rând din nord (inference.py:158-167)
MARGIN_OTHER_DEG = 0.02     # > marginea de 64 px pe care ftw o aruncă pe laturile de sud și vest
MIN_NORTH_MARGIN_PX = 960   # pasul ferestrelor (896) + marginea (64), pentru rasterele mai mari de 1024 px


# ---- Fields of The World --------------------------------------------------------------------------------------------
def ftw_request_bbox(footprint, aoi_bbox, pad_n=MARGIN_NORTH_DEG, pad=MARGIN_OTHER_DEG):
    """Dreptunghiul (lon/lat) cerut de `ftw inference download`: zona plus marjă, tăiată la amprenta scenelor."""
    from shapely.geometry import box
    west, south, east, north = aoi_bbox
    inter = footprint.intersection(box(west - pad, south - pad, east + pad, north + pad_n))
    if inter.is_empty:
        raise ValueError('Scenele nu acoperă deloc zona cerută')
    return inter.bounds


def best_scenes(items, aoi_bbox):
    """Pentru fiecare tile MGRS: scena care acoperă cel mai mult din zonă, iar la egalitate cea cu mai puțini nori."""
    from shapely.geometry import box, shape
    aoi = box(*aoi_bbox)
    pick = {}
    for it in items:
        tile = it.properties.get('s2:mgrs_tile')
        score = (round(shape(it.geometry).intersection(aoi).area, 4), -it.properties['eo:cloud_cover'])
        if tile not in pick or score > pick[tile][0]:
            pick[tile] = (score, it)
    return {tile: p[1] for tile, p in pick.items()}


def select_tiles(win_a, win_b, aoi_bbox, min_gain=0.01):
    """Tile-urile necesare pentru a acoperi zona, cel mai util primul; sare peste cele care aduc sub `min_gain` din AOI."""
    from shapely.geometry import box, shape
    from shapely.ops import unary_union
    aoi = box(*aoi_bbox)
    left = {t: shape(win_a[t].geometry).intersection(shape(win_b[t].geometry)).intersection(aoi) for t in set(win_a) & set(win_b)}
    chosen, covered = [], None
    while left:
        gain = {t: (g if covered is None else g.difference(covered)).area / aoi.area for t, g in left.items()}
        best = max(sorted(gain), key=gain.get)
        if gain[best] < min_gain:
            break
        geom = left.pop(best)
        covered = geom if covered is None else unary_union([covered, geom])
        chosen.append(best)
    return chosen


def north_margin_px(tif, aoi_bbox):
    """Câți pixeli are rasterul deasupra colțului cel mai nordic al zonei, în proiecția lui."""
    import rasterio
    from pyproj import Transformer
    with rasterio.open(tif) as src:
        to_raster = Transformer.from_crs(4326, src.crs, always_xy=True)
        top_aoi = max(to_raster.transform(x, aoi_bbox[3])[1] for x in (aoi_bbox[0], aoi_bbox[2]))
        return (src.bounds.top - top_aoi) / abs(src.res[1])


def run_ftw_tile(ftw, tile, scene_a, scene_b, ckpt, interim, aoi_bbox, run, gpu='0'):
    """Stiva A+B -> model -> poligoane pentru un tile. Reluabil: întoarce direct poligoanele dacă există deja."""
    from pathlib import Path
    from shapely.geometry import shape
    interim = Path(interim)
    poly = interim / f'ftw_poly_{tile}_{run}.parquet'
    if poly.exists():
        return poly
    tif, pred = interim / f'ftw_in_{tile}_{run}.tif', interim / f'ftw_pred_{tile}_{run}.tif'
    bbox = ftw_request_bbox(shape(scene_a.geometry).intersection(shape(scene_b.geometry)), aoi_bbox)
    if not tif.exists():
        r = subprocess.run([ftw, 'inference', 'download', '--win_a', scene_a.id, '--win_b', scene_b.id, '--out', str(tif),
                            '--bbox', ','.join(f'{c:.5f}' for c in bbox)], capture_output=True, text=True)
        print(r.stdout[-600:], r.stderr[-600:])
        # ftw iese cu cod 0 fără fișier dacă scenele au versiuni de procesare diferite sau nu se intersectează
        assert tif.exists(), f'{tile}: ftw nu a scris {tif.name} (vezi mesajul de mai sus)'
    margin = north_margin_px(tif, aoi_bbox)
    assert margin >= MIN_NORTH_MARGIN_PX, f'{tile}: marja de nord e doar {margin:.0f} px; ftw ar pierde o bandă din zonă'
    if not pred.exists():
        subprocess.run([ftw, 'inference', 'run', str(tif), '--model', str(ckpt), '--out', str(pred), '--gpu', gpu], check=True)
    subprocess.run([ftw, 'inference', 'polygonize', str(pred), '--simplify', '20', '--out', str(poly)], check=True)
    return poly


# ---- Verificarea acoperirii -------------------------------------------------------------------------------------------
def parcel_coverage(parcels, cells):
    """km² de parcele în fiecare celulă (aceeași proiecție metrică); o celulă fără parcele primește 0."""
    import geopandas as gpd
    left = cells[['geometry']].reset_index(names='_cell')
    over = gpd.overlay(left, parcels[['geometry']], how='intersection', keep_geom_type=True)
    return (over.area / 1e6).groupby(over['_cell']).sum().reindex(cells.index, fill_value=0.0)


def coverage_gaps(table, min_arable=8.0, min_ratio=0.2):
    """Celulele cu arabil semnificativ în care parcelele acoperă prea puțin (coloane: arabil_km2, parcele_km2)."""
    big = table['arabil_km2'] >= min_arable
    return table[big & (table['parcele_km2'] / table['arabil_km2'].where(big) < min_ratio)]


# ---- Ținta: pierderea față de anii cu același tip de cultură ------------------------------------------------------------
APR_AUTUMN, APR_SPRING = 0.40, 0.40     # D21: împărțire binară la NDVI aprilie 0,40 (toamnă ≥ 0,40, primăvară < 0,40)
AUTUMN_CROPS = {211, 212, 213, 214, 218, 232}   # EUCROPMAP: grâu comun, grâu durum, orz, secară, triticale, rapiță
SPRING_CROPS = {216, 217, 221, 222, 231, 233}   # EUCROPMAP: porumb, orez, cartof, sfeclă de zahăr, floarea-soarelui, soia


def crop_group(ndvi_apr, autumn=APR_AUTUMN, spring=APR_SPRING):
    """Tipul de cultură dintr-un an, după NDVI din aprilie: 'toamna', 'primavara' sau 'neclasificat' (doar dacă NaN la prag binar)."""
    import numpy as np
    import pandas as pd
    out = np.select([ndvi_apr >= autumn, ndvi_apr < spring], ['toamna', 'primavara'], 'neclasificat')
    return pd.Series(out, index=ndvi_apr.index)


def like_for_like_loss(df, value_fmt, group_fmt, target_year, base_years, min_ref=2, only_groups=None, agg='median'):
    """Pierderea din `target_year` față de mediana (sau media) anilor de referință cu același tip de cultură (D21).

    `value_fmt`/`group_fmt` dau numele coloanelor, de ex. 'tprod_{y}'. Întoarce ref, loss_obs, loss_rel, loss_pct, n_ref_years;
    cu mai puțin de `min_ref` ani de referință, sau pentru un grup neinclus în `only_groups`, pierderea e NaN.
    """
    import warnings
    import numpy as np
    import pandas as pd
    group = df[group_fmt.format(y=target_year)]
    value = df[value_fmt.format(y=target_year)].to_numpy(dtype=float)
    vals = df[[value_fmt.format(y=y) for y in base_years]].to_numpy(dtype=float)
    grps = df[[group_fmt.format(y=y) for y in base_years]].to_numpy(dtype=object)
    usable = group.ne('neclasificat').to_numpy()
    if only_groups is not None:
        usable = usable & group.isin(list(only_groups)).to_numpy()
    same = (grps == group.to_numpy(dtype=object)[:, None]) & ~np.isnan(vals) & usable[:, None]
    n = same.sum(axis=1)
    masked = np.where(same, vals, np.nan)
    with warnings.catch_warnings(), np.errstate(invalid='ignore', divide='ignore'):
        warnings.simplefilter('ignore', RuntimeWarning)
        ref = np.nanmedian(masked, axis=1) if agg == 'median' else np.nanmean(masked, axis=1)
        ref[n < min_ref] = np.nan
        loss = ref - value
        loss_rel = 1.0 - value / ref
        pct = loss_rel * 100
    return pd.DataFrame({'ref': ref, 'loss_obs': loss, 'loss_rel': loss_rel, 'loss_pct': pct, 'n_ref_years': n}, index=df.index)


def crop_group_agreement(groups, crop_codes):
    """Cât de des tipul din NDVI coincide cu sezonul culturii din EUCROPMAP; întoarce (proporție, nr. de parcele comparate)."""
    import numpy as np
    import pandas as pd
    codes = crop_codes.round()
    expected = pd.Series(np.select([codes.isin(AUTUMN_CROPS), codes.isin(SPRING_CROPS)], ['toamna', 'primavara'], ''), index=codes.index)
    known = expected.ne('') & groups.ne('neclasificat')
    return float((groups[known] == expected[known]).mean()), int(known.sum())


# ---- Cache Earth Engine -----------------------------------------------------------------------------------------------
def fingerprint(parcels, bands):
    """Amprentă scurtă a parcelelor și a listei de benzi: cache-ul se invalidează singur dacă oricare se schimbă."""
    h = hashlib.md5()
    h.update(parcels['parcel_id'].to_numpy().tobytes())
    for wkb in parcels.geometry.to_wkb():
        h.update(wkb)
    h.update(','.join(bands).encode())
    return h.hexdigest()[:8]


# ---- Canale OSM -------------------------------------------------------------------------------------------------------
def overpass_ways_to_gdf(elements):
    """Elementele Overpass (`out geom`) ca linii EPSG:4326; le sare pe cele fără cel puțin două puncte."""
    import geopandas as gpd
    from shapely.geometry import LineString
    rows = [{'waterway': e['tags'].get('waterway'), 'usage': e['tags'].get('usage'), 'name': e['tags'].get('name'),
             'geometry': LineString([(p['lon'], p['lat']) for p in e['geometry']])}
            for e in elements if len(e.get('geometry', [])) > 1]
    return gpd.GeoDataFrame(rows, geometry='geometry', crs=4326)


def canal_distances(parcels, ways):
    """Distanța (m) de la fiecare parcelă la canale și la toată rețeaua (canale, șanțuri, drenuri); aceeași proiecție."""
    out = parcels[['parcel_id']].copy()
    out['dist_canal_m'] = parcels.geometry.distance(ways[ways.waterway == 'canal'].union_all())
    out['dist_network_m'] = parcels.geometry.distance(ways.union_all())
    return out


# ---- Expunerea la vânt -------------------------------------------------------------------------------------------------
SHELTER_REACH_M = 300.0     # 20H, cu H = 15 m (AGENT_BRIEF)


def _upwind_edge_points(geom, ux, uy, spacing=20.0, probe=7.5):
    """Punctele de pe marginea parcelei expuse spre amonte: un pas spre amonte iese din parcelă, unul spre aval intră în ea."""
    import shapely
    pts = shapely.get_coordinates(shapely.segmentize(geom.boundary, spacing))
    outside_up = ~shapely.contains_xy(geom, pts[:, 0] + ux * probe, pts[:, 1] + uy * probe)
    inside_down = shapely.contains_xy(geom, pts[:, 0] - ux * probe, pts[:, 1] - uy * probe)
    return pts[outside_up & inside_down]


def wind_exposure(parcels, woody, transform, directions, weights, reach_m=SHELTER_REACH_M, step_m=5.0):
    """Expunerea la vânt a fiecărei parcele, între 0 și 1: partea din marginea din amonte fără element lemnos până la `reach_m`.

    `directions` sunt azimuturile din care bate vântul, iar `weights` ponderile lor (roza vânturilor). `woody` e o mască booleană
    pe grila `transform` (nord-sus), în aceeași proiecție cu parcelele. Ce iese din raster se consideră fără adăpost.
    """
    import numpy as np
    import pandas as pd
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    steps = np.arange(step_m, reach_m + step_m / 2, step_m)
    height, width = woody.shape
    out = np.zeros(len(parcels))
    for i, geom in enumerate(parcels.geometry):
        for azimuth, weight in zip(directions, weights):
            ux, uy = np.sin(np.radians(azimuth)), np.cos(np.radians(azimuth))
            pts = _upwind_edge_points(geom, ux, uy)
            if not len(pts):
                out[i] += weight
                continue
            cols = np.floor((pts[:, 0, None] + ux * steps[None, :] - transform.c) / transform.a).astype(int)
            rows = np.floor((pts[:, 1, None] + uy * steps[None, :] - transform.f) / transform.e).astype(int)
            inside = (rows >= 0) & (rows < height) & (cols >= 0) & (cols < width)
            hit = np.zeros(inside.shape, dtype=bool)
            hit[inside] = woody[rows[inside], cols[inside]]
            out[i] += weight * (1 - hit.any(axis=1).mean())
    return pd.Series(np.clip(out, 0.0, 1.0), index=parcels.index, name='wind_exposure')   # suma ponderilor poate depăși 1 prin rotunjire


def wind_rose(u, v, n_sectors=16):
    """Proporția orelor pe sectoare (azimutul din care bate vântul, indexat după centrul sectorului)."""
    import numpy as np
    import pandas as pd
    width = 360.0 / n_sectors
    azimuth = np.degrees(np.arctan2(-u, -v)) % 360
    sector = np.floor(((azimuth + width / 2) % 360) / width).astype(int)
    counts = np.bincount(sector, minlength=n_sectors)
    return pd.Series(counts / counts.sum(), index=np.arange(n_sectors) * width)


# ---- Etichete pentru irigat ------------------------------------------------------------------------------------------
def select_label_candidates(df, n_high=120, n_low=120, n_mid=60, max_per_block=8, seed=2024):
    """Parcele de etichetat: culturi de primăvară arabile de cel puțin 1 ha, în trei clase după NDVI iulie–august 2024.

    Treimea verde (top 20%) = 'probabil_irigat', jumătatea de jos (sub 40%) = 'probabil_neirigat', restul = 'nesigur'.
    Fiecare bloc de 5 km dă cel mult `max_per_block` parcele, ca eșantionul să acopere toată zona. `irigat` pornește gol.
    """
    import numpy as np
    import pandas as pd
    pool = df[df.is_arable & df.crop_group_2024.eq('primavara') & df.area_ha.ge(1.0)].copy()
    rank = pool.ndvi_ja_2024.rank(pct=True)
    pool['hint'] = np.select([rank > 0.8, rank < 0.4], ['probabil_irigat', 'probabil_neirigat'], 'nesigur')
    pool = pool.sample(frac=1.0, random_state=seed)
    pool = pool[pool.groupby('block').cumcount() < max_per_block]
    wanted = {'probabil_irigat': n_high, 'probabil_neirigat': n_low, 'nesigur': n_mid}
    picked = [pool[pool.hint == h].head(n) for h, n in wanted.items()]
    out = pd.concat(picked).sort_values('parcel_id')[['parcel_id', 'hint']].reset_index(drop=True)
    out['irigat'] = pd.Series([pd.NA] * len(out), dtype='Int8')
    return out


OVERPASS_MIRRORS = ('https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter')


def overpass_elements(query, mirrors=OVERPASS_MIRRORS, tries=3, wait_s=30, post=None):
    """Rulează o interogare Overpass și întoarce elementele; trece la serverul următor când unul e ocupat."""
    import time
    import requests
    post = post or requests.post
    code = None
    for _ in range(tries):
        for url in mirrors:
            try:
                response = post(url, data={'data': query}, headers={'User-Agent': 'gisday2026/1.0'}, timeout=150)
            except requests.exceptions.RequestException as err:     # server lent sau căzut: îl încercăm pe următorul
                code = type(err).__name__
                continue
            code = response.status_code
            if code == 200:
                return response.json()['elements']
        time.sleep(wait_s)
    raise RuntimeError(f'Overpass indisponibil (ultimul cod HTTP: {code})')


# ---- Clasificatorul de irigare și regula Sentinel-1 + pivoți (D26) ---------------------------------------------------
MIN_LABELS_PER_CLASS = 10
LGB_CLASSIFIER = dict(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=5, subsample=0.8,
                      subsample_freq=1, colsample_bytree=0.8, verbose=-1)


def geometric_pivots(geometries, min_cpp=0.75, min_cmbc=0.60, min_area_ha=5.0):
    """Pivoți circulari doar din geometrie (D26 pct. 4): C_PP >= 0,75, C_MBC >= 0,60, A >= 5 ha (fără condiție NDVI)."""
    import numpy as np
    import pandas as pd
    import shapely
    geoms = np.asarray(geometries)
    area_m2 = shapely.area(geoms)
    perim_m = shapely.length(geoms)
    c_pp = 4.0 * np.pi * area_m2 / np.maximum(perim_m ** 2, 1e-9)
    mbc_r = shapely.minimum_bounding_radius(geoms)
    c_mbc = area_m2 / np.maximum(np.pi * (mbc_r ** 2), 1e-9)
    area_ha = area_m2 / 10000.0
    is_piv = (c_pp >= min_cpp) & (c_mbc >= min_cmbc) & (area_ha >= min_area_ha)
    idx = getattr(geometries, 'index', None)
    return pd.DataFrame({'area_ha': area_ha, 'c_pp': c_pp, 'c_mbc': c_mbc, 'is_pivot': is_piv}, index=idx)


def s1_spring_irrigation_rule(df, exclude_transitions=(), min_dvv_event=1.5, max_dvv_dry=0.8,
                              min_dry_transitions=3, max_rain_5d=2.0, max_rain_12d=5.0):
    """Regula radar Sentinel-1 + pivoți pe culturile de primăvară (D26 pct. 1–5).

    Primește un DataFrame `df` (parcele de primăvară) cu coloanele `vv_o{orbit}_{YYYYMMDD}`, `rain_{YYYYMMDD}` și `is_pivot`.
    Întoarce `(transitions_df, result_df)`:
    - `transitions_df`: statisticile pe fiecare trecere consecutivă de 12 zile (aceeași orbită) din iunie–august 2024;
    - `result_df`: pe parcelă (`n_dry_obs`, `n_events_s1`, `max_dvv_dry`, `is_pivot`, `clasa_irigare` în {'irigat', 'neirigat', 'nedeterminat'}).
    """
    import numpy as np
    import pandas as pd
    excl = set(exclude_transitions or ())
    s1_cols = [c for c in df.columns if c.startswith('vv_o')]
    acq = []
    for c in s1_cols:
        parts = c.split('_')
        acq.append((int(parts[1][1:]), pd.to_datetime(parts[2], format='%Y%m%d'), c))
    acq_df = pd.DataFrame(acq, columns=['orbit', 'date', 'col']).sort_values(['orbit', 'date']).reset_index(drop=True)

    tr_rows = []
    dvv_dict, dry_dict = {}, {}
    for orb, g in acq_df.groupby('orbit'):
        g = g.sort_values('date').reset_index(drop=True)
        for i in range(1, len(g)):
            t0, t1 = g.loc[i - 1, 'date'], g.loc[i, 'date']
            c0, c1 = g.loc[i - 1, 'col'], g.loc[i, 'col']
            dt_days = int((t1 - t0).days)
            if dt_days != 12 or t1 < pd.Timestamp('2024-06-01') or t1 > pd.Timestamp('2024-08-31'):
                continue
            key = f"o{orb}_{t0.strftime('%m%d')}_{t1.strftime('%m%d')}"
            d12 = [f"rain_{d.strftime('%Y%m%d')}" for d in pd.date_range(t0 + pd.Timedelta(days=1), t1, freq='D')]
            d5 = [f"rain_{d.strftime('%Y%m%d')}" for d in pd.date_range(t1 - pd.Timedelta(days=4), t1, freq='D')]
            r12 = df[d12].sum(axis=1)
            r5 = df[d5].sum(axis=1)
            dvv = df[c1] - df[c0]
            obs = dvv.notna()
            dry = obs & (r5 < max_rain_5d) & (r12 < max_rain_12d)
            evt_dry = dry & (dvv >= min_dvv_event)
            evt_raw = obs & (dvv >= min_dvv_event)
            n_obs, n_dry = int(obs.sum()), int(dry.sum())
            tr_rows.append({
                'key': key,
                'orbit': int(orb),
                't0': t0.strftime('%Y-%m-%d'),
                't1': t1.strftime('%Y-%m-%d'),
                'dt_days': dt_days,
                'n_obs': n_obs,
                'n_dry': n_dry,
                'pct_dry_obs': float(100.0 * n_dry / max(n_obs, 1)) if n_obs else 0.0,
                'rain5_med': float(r5[obs].median()) if n_obs else np.nan,
                'rain5_p90': float(r5[obs].quantile(0.90)) if n_obs else np.nan,
                'rain12_med': float(r12[obs].median()) if n_obs else np.nan,
                'rain12_p90': float(r12[obs].quantile(0.90)) if n_obs else np.nan,
                'dvv_med_dry': float(dvv[dry].median()) if n_dry else np.nan,
                'dvv_p90_dry': float(dvv[dry].quantile(0.90)) if n_dry else np.nan,
                'n_evt_raw': int(evt_raw.sum()),
                'pct_evt_raw': float(100.0 * evt_raw.sum() / max(n_obs, 1)) if n_obs else 0.0,
                'n_evt_dry': int(evt_dry.sum()),
                'pct_evt_dry': float(100.0 * evt_dry.sum() / max(n_dry, 1)) if n_dry else 0.0,
                'pct_evt_obs': float(100.0 * evt_dry.sum() / max(n_obs, 1)) if n_obs else 0.0,
                'excluded': key in excl,
            })
            if key not in excl:
                dvv_dict[key] = dvv
                dry_dict[key] = dry

    transitions_df = pd.DataFrame(tr_rows)
    if dvv_dict:
        dvv_mat = pd.DataFrame(dvv_dict, index=df.index)
        dry_mat = pd.DataFrame(dry_dict, index=df.index)
        dvv_dry = dvv_mat.where(dry_mat)
        n_dry_obs = dry_mat.sum(axis=1).astype(int)
        n_events = (dvv_dry >= min_dvv_event).sum(axis=1).astype(int)
        max_dvv = dvv_dry.max(axis=1)
    else:
        n_dry_obs = pd.Series(0, index=df.index, dtype=int)
        n_events = pd.Series(0, index=df.index, dtype=int)
        max_dvv = pd.Series(np.nan, index=df.index, dtype=float)

    piv = df['is_pivot'].astype(bool)
    is_irig = (n_events >= 1) | piv
    is_neirig = (~is_irig) & (n_events == 0) & (n_dry_obs >= min_dry_transitions) & (max_dvv < max_dvv_dry)
    clasa = np.where(is_irig, 'irigat', np.where(is_neirig, 'neirigat', 'nedeterminat'))
    result_df = pd.DataFrame({
        'n_dry_obs': n_dry_obs,
        'n_events_s1': n_events,
        'max_dvv_dry': max_dvv,
        'is_pivot': piv,
        'clasa_irigare': clasa,
    }, index=df.index)
    return transitions_df, result_df


def select_validation_80(df, class_col='clasa_irigare', n_per_class=40, min_area_ha=1.0, max_per_block=1, seed=2024):
    """Pachetul de validare Q2 (D26 pct. 8): 40 `irigat` + 40 `neirigat` pe primăvară, răspândite pe blocuri de 5 km."""
    import pandas as pd
    pool = df[df.area_ha.ge(min_area_ha) & df[class_col].isin(['irigat', 'neirigat'])].copy()
    pool = pool.sample(frac=1.0, random_state=seed)
    picked = []
    for cls_name in ('irigat', 'neirigat'):
        sub = pool[pool[class_col] == cls_name]
        cap = max_per_block
        while len(sub[sub.groupby('block').cumcount() < cap]) < n_per_class and cap < len(sub):
            cap += 1
        sel = sub[sub.groupby('block').cumcount() < cap].head(n_per_class)
        if len(sel) < n_per_class:
            raise ValueError(f'Prea puține parcele în clasa {cls_name}: {len(sel)} < {n_per_class}')
        picked.append(sel)
    out = pd.concat(picked).sort_values('parcel_id')[['parcel_id', class_col]].rename(columns={class_col: 'clasa_regula'}).reset_index(drop=True)
    out['irigat'] = pd.Series([pd.NA] * len(out), dtype='Int8')
    return out


def block_folds(y, groups, n_splits=5, seed=2024):
    """Împărțiri antrenare/test în care un bloc de 5 km apare doar într-o parte."""
    from sklearn.model_selection import StratifiedGroupKFold
    return list(StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(y, y, groups))


def out_of_fold_probabilities(X, y, groups, n_splits=5, seed=2024):
    """Probabilitatea de irigare a fiecărei parcele etichetate, prezisă de un model care nu i-a văzut blocul."""
    import lightgbm as lgb
    import numpy as np
    counts = y.value_counts()
    if len(counts) < 2 or counts.min() < MIN_LABELS_PER_CLASS:
        raise ValueError(f'Prea puține etichete pe clasă: {counts.to_dict()} (minimum {MIN_LABELS_PER_CLASS})')
    out = np.zeros(len(y))
    for train, test in block_folds(y, groups, n_splits, seed):
        model = lgb.LGBMClassifier(**LGB_CLASSIFIER, random_state=seed).fit(X.iloc[train], y.iloc[train])
        out[test] = model.predict_proba(X.iloc[test])[:, 1]
    return out


# ---- WEkEO ------------------------------------------------------------------------------------------------------------
def wekeo_client(env):
    """Clientul `hda` din variabilele de mediu: WEKEO_TOKEN (din portal) sau WEKEO_USER + WEKEO_PASSWORD.

    `hda` știe doar utilizator + parolă, așa că tokenul din portal se pune direct în client (api.py:600-618) și e folosit
    până când serverul îl refuză. Valorile nu se afișează niciodată.
    """
    import time
    from hda import Client, Configuration
    kwargs = dict(retry_max=20, sleep_max=60, progress=False)
    token = env.get('WEKEO_TOKEN')
    if token:
        client = Client(config=Configuration(user='token', password='token'), **kwargs)
        client._access_token = token
        client._token_expiration = int(time.time()) + 7 * 24 * 3600
        return client
    if env.get('WEKEO_USER') and env.get('WEKEO_PASSWORD'):
        return Client(config=Configuration(user=env['WEKEO_USER'], password=env['WEKEO_PASSWORD']), **kwargs)
    raise ValueError('Lipsesc credențialele WEkEO: pune în .env WEKEO_TOKEN sau WEKEO_USER și WEKEO_PASSWORD')


def is_complete(folder, product_id, expected_size):
    """Produsul e descărcat complet doar dacă există un fișier cu dimensiunea din catalog (o conexiune ruptă lasă unul mai mic)."""
    from pathlib import Path
    return any(p.stat().st_size == expected_size for p in Path(folder).glob(f'{product_id}*') if p.is_file())
