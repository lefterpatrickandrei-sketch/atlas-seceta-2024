"""Sentinel-1 VH pe parcelele arabile, la exact aceleași treceri ca VV (diagnosticul evenimentelor radar).

Rezultat: data/interim/q2_s1_vh_arable.parquet (parcel_id + vh_o<orbită>_<AAAALLZZ>). Rulează pe loturi și se poate relua.
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/extract_s1_vh.py
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import ee  # noqa: E402
import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

from gisday_config import AOI_BBOX, GEE_PROJECT, INTERIM, OUT  # noqa: E402

VV_CACHE = INTERIM / 'q2_s1_vv_arable.parquet'
TARGET = INTERIM / 'q2_s1_vh_arable.parquet'
BATCH_DIR = INTERIM / 'q2_s1_vh_batches'
BATCH = 1500


def acquisitions():
    """Trecerile (orbită, dată) din coloanele cache-ului VV: VH trebuie să acopere exact aceleași."""
    columns = [c for c in pd.read_parquet(VV_CACHE).columns if c.startswith('vv_o')]
    rows = [(int(c.split('_')[1][1:]), c.split('_')[2]) for c in columns]
    return pd.DataFrame(rows, columns=['orbit', 'date']).sort_values(['orbit', 'date']).reset_index(drop=True)


def vh_stack(acq):
    collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                  .filterBounds(ee.Geometry.Rectangle(list(AOI_BBOX)))
                  .filterDate('2024-05-20', '2024-09-01')
                  .filter(ee.Filter.eq('instrumentMode', 'IW'))
                  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')))
    meta = collection.map(lambda i: ee.Feature(None, {'date': i.date().format('YYYYMMdd'), 'orbit': i.get('relativeOrbitNumber_start')}))
    found = {(int(f['properties']['orbit']), f['properties']['date']) for f in meta.getInfo()['features']}
    missing = {(r.orbit, r.date) for r in acq.itertuples()} - found
    assert not missing, f'Treceri VV fără VH: {sorted(missing)}'
    images = []
    for r in acq.itertuples():
        day = pd.to_datetime(r.date, format='%Y%m%d')
        images.append(collection.filter(ee.Filter.eq('relativeOrbitNumber_start', r.orbit))
                      .filterDate(day.strftime('%Y-%m-%d'), (day + pd.Timedelta(days=1)).strftime('%Y-%m-%d'))
                      .select('VH').mean().rename(f'vh_o{r.orbit}_{r.date}'))
    return ee.Image.cat(images)


def main():
    ee.Initialize(project=GEE_PROJECT)
    acq = acquisitions()
    print('treceri:', len(acq), flush=True)
    wanted = set(pd.read_parquet(VV_CACHE, columns=['parcel_id']).parcel_id)
    parcels = gpd.read_parquet(OUT / 'parcels.parquet')
    arable = parcels[parcels.parcel_id.isin(wanted)].sort_values('parcel_id').to_crs(4326).reset_index(drop=True)
    assert len(arable) == len(wanted), f'{len(arable)} parcele pentru {len(wanted)} în cache-ul VV'
    stack = vh_stack(acq)
    bands = stack.bandNames().getInfo()
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    parts = []
    for start in range(0, len(arable), BATCH):
        path = BATCH_DIR / f'batch_{start:05d}_{BATCH}.parquet'
        if path.exists():
            parts.append(pd.read_parquet(path))
            continue
        chunk = arable.iloc[start:start + BATCH]
        features = [ee.Feature(ee.Geometry(g.__geo_interface__), {'parcel_id': int(i)}) for i, g in zip(chunk.parcel_id, chunk.geometry)]
        result = stack.reduceRegions(ee.FeatureCollection(features), ee.Reducer.mean(), scale=10).map(lambda f: f.setGeometry(None)).getInfo()['features']
        frame = pd.DataFrame([f['properties'] for f in result]).reindex(columns=['parcel_id', *bands])
        assert len(frame) == len(chunk), f'Lotul {start}: {len(frame)} rânduri pentru {len(chunk)} parcele'
        frame.to_parquet(path)
        parts.append(frame)
        print(f'{start + len(chunk)}/{len(arable)} în {time.time() - started:.0f} s', flush=True)
    out = pd.concat(parts, ignore_index=True).sort_values('parcel_id').reset_index(drop=True)
    assert out.parcel_id.is_unique and set(out.parcel_id) == wanted
    out.to_parquet(TARGET)
    print('scris:', TARGET.name, out.shape, flush=True)


if __name__ == '__main__':
    main()
