"""Sarcina 5: sfârșitul sezonului de vegetație (HR-VPP EOSD și LENGTH, sezonul 1, 2017–2024) pe parcele, 2024 față de anii comparabili.

Codificarea, după HR-VPP Product User Manual, Seasonal Trajectories and VPP parameters, Issue 2.5 (31.08.2025),
tabelul 4 (§4.4) și §5.3.8 (vezi D32):
  EOSD   = data în format YYDOY (18030 = ziua 30 din 2018), întreg cu semn pe 16 biți, fără valoare = 0, interval 16001–65365.
  LENGTH = numărul de zile dintre începutul și sfârșitul sezonului, 1–1096, fără valoare = 0.
  Sezonul aparține anului în care are vârful; începutul poate fi în anul anterior, sfârșitul în anul următor (YY mai mare).
  Sezonul 1 = primul în ordine cronologică dintre cele cel mult două sezoane ale anului.

Ce face:
  1. Decodează EOSD pe pixel în „ziua anului” față de 1 ianuarie al anului produsului, cu aceeași numerotare pentru aceeași
     dată calendaristică în anii bisecți (29 februarie nu decalează restul anului); sfârșitul din anul următor depășește 365.
  2. Mediana pe parcelă (pixelii cu centrul în parcelă, ca la TPROD) pentru fiecare an, EOSD și LENGTH.
  3. Diferența 2024 față de mediana anilor comparabili, cu aceleași grupe like-for-like ca la pierdere (`like_for_like_loss`, D21),
     pe aceleași parcele cu țintă (fără grupul incert).
  4. Pe grupe: mediana, P25–P75 și IC 95% bootstrap pe blocuri de 5 km; apoi efectul versiunilor V101/V105.

Rezultate: data/out/parcel_eos.parquet (pe parcelă) și data/out/eos_metrics.json (agregat).
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/sfarsit_sezon.py
"""
import calendar
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT)]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402
from rasterio.features import rasterize  # noqa: E402
from rasterio.windows import from_bounds  # noqa: E402

from gisday_config import BASE_YEARS, CRS, OUT, RAW, YEAR  # noqa: E402
from gisday_lib import crop_group, like_for_like_loss  # noqa: E402

YEARS = list(BASE_YEARS) + [YEAR]
V105_YEARS = [y for y in BASE_YEARS if y >= 2021]
NO_VALUE = 0
DATE_RANGE = (16001, 65365)
LENGTH_RANGE = (1, 1096)
N_BOOT, SEED = 5000, 2024
GROUPS = ('primavara', 'toamna')


def raster_path(year, param):
    found = sorted((RAW / 'hrvpp').glob(f'VPP_{year}_S2_T34TGP-010m_V*_s1_{param}.tif'))
    assert len(found) == 1, f'{param} {year}: {len(found)} fișiere'
    return found[0]


def decode_eosd(raw, year):
    """YYDOY → ziua față de 1 ianuarie al anului produsului (1 = 1 ianuarie), aliniată calendaristic în anii bisecți."""
    raw = raw.astype(np.int32)
    yy, doy = raw // 1000, raw % 1000
    ok = (raw >= DATE_RANGE[0]) & (raw <= DATE_RANGE[1]) & (doy >= 1) & (doy <= 366)
    jan1 = np.array([(dt.date(2000 + k, 1, 1) - dt.date(year, 1, 1)).days if 1 <= 2000 + k <= 9999 else 0 for k in range(100)])
    rel = jan1[np.clip(yy, 0, 99)] + doy
    if calendar.isleap(year):
        rel = rel - (rel >= 61)          # 1 martie al unui an bisect devine ziua 60, ca în ceilalți ani
    return np.where(ok, rel, np.nan)


def decode_length(raw):
    raw = raw.astype(np.float64)
    return np.where((raw >= LENGTH_RANGE[0]) & (raw <= LENGTH_RANGE[1]), raw, np.nan)


def parcel_medians(parcels):
    """Mediana pe parcelă, pe fiecare an, pentru EOSD (decodat) și LENGTH. Toate rasterele au aceeași grilă T34TGP."""
    first = raster_path(YEAR, 'EOSD')
    with rasterio.open(first) as src:
        crs, grid = src.crs, (src.transform, src.shape)
        geoms = parcels.to_crs(crs).geometry
        window = from_bounds(*(np.array(geoms.total_bounds) + [-100, -100, 100, 100]), transform=src.transform).round_offsets().round_lengths()
        transform = src.window_transform(window)
    index = rasterize(((g, i) for i, g in enumerate(geoms, 1)), out_shape=(int(window.height), int(window.width)), transform=transform, fill=0, dtype='int32')
    inside = index > 0
    ids = index[inside] - 1
    pixels = np.bincount(ids, minlength=len(parcels))
    out, versions = {}, {}
    for year in YEARS:
        for param in ('EOSD', 'LENGTH'):
            path = raster_path(year, param)
            versions[year] = re.search(r'_(V\d+)_', path.name).group(1)
            with rasterio.open(path) as src:
                assert (src.crs, (src.transform, src.shape)) == (crs, grid), f'grilă diferită: {path.name}'
                assert src.nodata == NO_VALUE, f'nodata neașteptat în {path.name}'
                raw = src.read(1, window=window)
            values = decode_eosd(raw, year) if param == 'EOSD' else decode_length(raw)
            v = values[inside]
            ok = ~np.isnan(v)
            med = pd.Series(v[ok]).groupby(ids[ok]).median().reindex(range(len(parcels)))
            name = param.lower()
            out[f'{name}_{year}'] = med.to_numpy()
            out[f'{name}_valid_{year}'] = np.bincount(ids[ok], minlength=len(parcels)) / np.maximum(pixels, 1)
    frame = pd.DataFrame(out, index=parcels.index)
    frame['pixels'] = pixels
    return frame, versions


def block_ci(values, blocks):
    """IC 95% al medianei, bootstrap pe blocuri de 5 km (blocurile se trag cu întoarcere)."""
    codes, uniques = pd.factorize(blocks)
    order = np.argsort(codes, kind='stable')
    parts = np.split(values[order], np.searchsorted(codes[order], np.arange(1, len(uniques))))
    draws = np.random.default_rng(SEED).integers(0, len(parts), size=(N_BOOT, len(parts)))
    medians = np.array([np.median(np.concatenate([parts[i] for i in d])) for d in draws])
    return [round(float(x), 1) for x in np.percentile(medians, [2.5, 97.5])], len(uniques)


def summary(values, blocks):
    values = np.asarray(values, float)
    keep = ~np.isnan(values)
    values, blocks = values[keep], np.asarray(blocks)[keep]
    ci, n_blocks = block_ci(values, blocks)
    p25, p50, p75 = np.percentile(values, [25, 50, 75])
    return {'n': int(len(values)), 'mediana_zile': round(float(p50), 1), 'p25_zile': round(float(p25), 1), 'p75_zile': round(float(p75), 1),
            'ic95_zile': ci, 'n_blocuri': n_blocks}


def day_label(day):
    """Ziua (aliniată la un an nebisect) ca dată scurtă; peste 365 trece în anul următor."""
    if np.isnan(day):
        return None
    date = dt.date(2023, 1, 1) + dt.timedelta(days=int(round(day)) - 1)
    return f'{date.day}.{date.month:02d}' + (' (anul următor)' if date.year > 2023 else '')


def main():
    parcels = gpd.read_parquet(OUT / 'parcels.parquet').to_crs(CRS)
    target = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'is_arable', 'tip_cultura_2024', 'loss_rel']]
    features = pd.read_parquet(OUT / 'parcel_features.parquet', columns=['parcel_id', 'ndvi_04'] + [f'ndvi_apr_{y}' for y in BASE_YEARS])
    D = parcels[['parcel_id', 'geometry']].merge(target, on='parcel_id').merge(features, on='parcel_id').reset_index(drop=True)
    assert len(D) == len(parcels)
    medians, versions = parcel_medians(D)
    D = pd.concat([D, medians], axis=1)
    for y in BASE_YEARS:
        D[f'grp_{y}'] = crop_group(D[f'ndvi_apr_{y}'])
    D[f'grp_{YEAR}'] = crop_group(D['ndvi_04'])          # aceleași grupe ca în 03e
    c = D.geometry.centroid
    D['block'] = (c.x // 5000).astype(int).astype(str) + '_' + (c.y // 5000).astype(int).astype(str)

    # Aceleași parcele ca ținta de pierdere: arabile, cu țintă like-for-like, fără grupul incert
    sample = D.is_arable & D.loss_rel.notna() & D.tip_cultura_2024.isin(GROUPS)
    assert (D.loss_rel.notna() & D.is_arable).sum() == sample.sum() == 11048, 'setul diferă de ținta de pierdere'
    for name in ('eosd', 'length'):
        full = like_for_like_loss(D, name + '_{y}', 'grp_{y}', YEAR, BASE_YEARS)
        v105 = like_for_like_loss(D, name + '_{y}', 'grp_{y}', YEAR, V105_YEARS)
        D[f'{name}_ref'], D[f'{name}_n_ref'] = full.ref, full.n_ref_years
        D[f'{name}_dif_2024'] = -full.loss_obs                   # 2024 minus referința: negativ = mai devreme / mai scurt
        D[f'{name}_dif_2024_ref_v105'] = -v105.loss_obs
        D.loc[~sample, [f'{name}_ref', f'{name}_dif_2024', f'{name}_dif_2024_ref_v105']] = np.nan

    R = {'sursa_codificare': 'HR-VPP Product User Manual, Seasonal Trajectories and VPP parameters, Issue 2.5 (31.08.2025), tabelul 4 și §5.3.8',
         'versiuni': versions, 'parcele_in_set': int(sample.sum()), 'pe_grupe': {}, 'versiuni_v101_v105': {}}
    for g in GROUPS:
        sub = D[sample & D.tip_cultura_2024.eq(g)]
        entry = {}
        for name in ('eosd', 'length'):
            entry[name] = summary(sub[f'{name}_dif_2024'], sub.block)
            ok = sub[f'{name}_dif_2024'].notna()
            entry[name]['mediana_2024'] = round(float(sub.loc[ok, f'{name}_{YEAR}'].median()), 1)
            entry[name]['mediana_referinta'] = round(float(sub.loc[ok, f'{name}_ref'].median()), 1)
            if name == 'eosd':
                entry[name]['data_2024'], entry[name]['data_referinta'] = day_label(entry[name]['mediana_2024']), day_label(entry[name]['mediana_referinta'])
            both = sub[[f'{name}_dif_2024', f'{name}_dif_2024_ref_v105']].dropna()
            R['versiuni_v101_v105'].setdefault(g, {})[name] = {
                'n_parcele_comune': int(len(both)),
                'mediana_ref_2017_2023': round(float(both[f'{name}_dif_2024'].median()), 1),
                'mediana_ref_doar_v105_2021_2023': round(float(both[f'{name}_dif_2024_ref_v105'].median()), 1),
                'ic95_ref_doar_v105': summary(both[f'{name}_dif_2024_ref_v105'], sub.loc[both.index, 'block'])['ic95_zile']}
        entry['pixeli_valizi_2024_sub_50pct'] = int((sub[f'eosd_valid_{YEAR}'] < .5).sum())
        R['pe_grupe'][g] = entry

    # Pe an: mediana EOSD și LENGTH pe parcelele din set care au avut grupul g în acel an, plus parcele fără sezon valid
    per_year = {}
    for g in GROUPS:
        rows = {}
        for y in YEARS:
            m = sample & D[f'grp_{y}'].eq(g)
            rows[y] = {'n': int(m.sum()), 'eosd_mediana': round(float(D.loc[m, f'eosd_{y}'].median()), 1),
                       'eosd_data': day_label(D.loc[m, f'eosd_{y}'].median()), 'length_mediana': round(float(D.loc[m, f'length_{y}'].median()), 1),
                       'pct_fara_eosd': round(float(100 * D.loc[m, f'eosd_{y}'].isna().mean()), 1),
                       'pct_eosd_inainte_de_1_iunie': round(float(100 * (D.loc[m, f'eosd_{y}'] < 152).mean()), 1), 'versiune': versions[y]}
        per_year[g] = rows
    R['pe_an'] = per_year

    # Saltul de versiune pe parcele non-arabile, ca la TPROD: mediana 2021–2023 (V105) minus mediana 2017–2020 (V101)
    non = D[~D.is_arable]
    shift = {}
    for name in ('eosd', 'length'):
        v101 = non[[f'{name}_{y}' for y in BASE_YEARS if y <= 2020]].median(axis=1)
        v105 = non[[f'{name}_{y}' for y in V105_YEARS]].median(axis=1)
        d = (v105 - v101).dropna()
        shift[name] = {'n': int(len(d)), 'mediana_zile': round(float(d.median()), 1), 'p25_zile': round(float(d.quantile(.25)), 1), 'p75_zile': round(float(d.quantile(.75)), 1)}
    R['versiuni_v101_v105']['non_arabil_v105_minus_v101'] = shift

    cols = ['parcel_id', 'tip_cultura_2024'] + [f'{p}_{y}' for p in ('eosd', 'length') for y in YEARS] + \
           [f'{p}_{s}' for p in ('eosd', 'length') for s in ('ref', 'n_ref', 'dif_2024', 'dif_2024_ref_v105')] + [f'eosd_valid_{YEAR}', 'pixels']
    D[cols].to_parquet(OUT / 'parcel_eos.parquet')
    (OUT / 'eos_metrics.json').write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str), encoding='utf-8')
    for g in GROUPS:
        e = R['pe_grupe'][g]
        print(g, 'EOSD', e['eosd'], '| LENGTH', e['length'])
        print('  versiuni', R['versiuni_v101_v105'][g])
    print('non-arabil V105−V101:', shift)
    for g in GROUPS:
        print(g, 'pe an:', {y: (r['eosd_data'], r['length_mediana'], r['pct_fara_eosd'], r['pct_eosd_inainte_de_1_iunie']) for y, r in per_year[g].items()})


if __name__ == '__main__':
    main()
