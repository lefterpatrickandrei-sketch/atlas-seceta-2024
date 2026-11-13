"""T4 (ticket robustețe): pierderea din 2024 cu TPROD filtrat după QFLAG HR-VPP, pe toți anii 2017–2024.

Codificarea QFLAG, citită din metadatele fișierelor (tag-urile Flag_value / Flag_meaning, aceleași în V101 și V105):
  0 fără date (seria nu a fost procesată), 1 niciun sezon găsit, 2 completat (filled), 3 nefolosit,
  4 / 5 / 6 calitate scăzută la îngălbenire / vârf / înverzire, 7 / 8 / 9 calitate medie la înverzire / vârf / îngălbenire,
  10 calitate ridicată.
Praguri (alegere declarată, nu valoare din literatură):
  (a) toate pixelii valizi TPROD (ca ținta oficială);
  (b) doar pixelii cu QFLAG ≥ 7 (calitate medie sau ridicată în toate fazele);
  (c) doar pixelii cu QFLAG = 10 (calitate ridicată).
TPROD pe parcelă = media pixelilor cu centrul în parcelă (`rasterio.merge` + `zonal_stats`, ca în 03_parcel_features); un an al unei parcele
se păstrează doar dacă cel puțin jumătate din pixelii ei TPROD valizi trec pragul. Pierderea: aceeași procedură ca
`robustete_referinta.py` (grupe din NDVI aprilie, grup incert scos, like-for-like cu minimum 2 ani, tăiere P1/P99).
Varianta (a) trebuie să refacă ținta oficială. Nu schimbă niciun fișier oficial.

Rezultat: data/out/loss_qflag.json
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/loss_qflag.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import rasterio  # noqa: E402

from gisday_config import BASE_YEARS, OUT, RAW, YEAR  # noqa: E402
from gisday_lib import like_for_like_loss  # noqa: E402
from robustete_referinta import GROUPS, features  # noqa: E402

YEARS = list(BASE_YEARS) + [YEAR]
VARIANTS = {'a_toti_pixelii': None, 'b_qflag_min_7': 7, 'c_qflag_10': 10}
MIN_SHARE = 0.5


def raster_path(year, param):
    found = sorted((RAW / 'hrvpp').glob(f'VPP_{year}_S2_T34TGP-010m_V*_s1_{param}.tif'))
    assert len(found) == 1, f'{param} {year}: {len(found)} fișiere'
    return found[0]


def parcel_tprod(parcels):
    """Media TPROD pe parcelă exact ca în 03_parcel_features (rasterio.merge pe fereastra parcelelor + zonal_stats,
    pixelii cu centrul în parcelă); pentru variantele cu prag, pixelii care nu trec QFLAG devin nodata."""
    from rasterio.merge import merge
    from rasterstats import zonal_stats
    out = {v: {} for v in VARIANTS}
    for year in YEARS:
        srcs = [rasterio.open(raster_path(year, 'TPROD')), rasterio.open(raster_path(year, 'QFLAG'))]
        try:
            geoms = parcels.to_crs(srcs[0].crs).geometry
            tp, tr = merge([srcs[0]], bounds=tuple(geoms.total_bounds))
            qf, tr_q = merge([srcs[1]], bounds=tuple(geoms.total_bounds))
            assert tr == tr_q and tp.shape == qf.shape
            nod = srcs[0].nodata
        finally:
            for s in srcs:
                s.close()
        tp, qf = tp[0], qf[0]
        full = zonal_stats(geoms, tp, affine=tr, nodata=nod, stats=['mean', 'count'])
        n_valid = np.array([x['count'] for x in full], dtype=float)
        for name, thr in VARIANTS.items():
            if thr is None:
                st = full
            else:
                st = zonal_stats(geoms, np.where(qf >= thr, tp, nod), affine=tr, nodata=nod, stats=['mean', 'count'])
            mean = np.array([np.nan if x['mean'] is None else x['mean'] for x in st], dtype=float)
            if thr is not None:
                n = np.array([x['count'] for x in st], dtype=float)
                mean = np.where(n >= MIN_SHARE * n_valid, mean, np.nan)
            out[name][year] = mean
        print('an', year, 'gata', flush=True)
    return out


def loss_from(F, tprod):
    D = F.copy()
    for y in YEARS:
        D[f'tprod_{y}'] = tprod[y]
    rel = like_for_like_loss(D, 'tprod_{y}', 'grp_{y}', YEAR, BASE_YEARS)['loss_rel'].where(D['is_arable'])
    return rel.clip(*rel.quantile([0.01, 0.99])), D


def main():
    F = features()
    parcels = gpd.read_parquet(OUT / 'parcels.parquet')
    parcels = parcels.set_index('parcel_id').loc[F.parcel_id].reset_index()
    T = parcel_tprod(parcels)

    a = T['a_toti_pixelii']
    for y in YEARS:
        diff = np.nanmax(np.abs(a[y] - F[f'tprod_{y}'].to_numpy()))
        assert diff < 1e-6 or np.isnan(diff), f'TPROD {y} nu se reproduce (diferență max {diff})'
    official = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'loss_rel']]
    group = F[f'grp_{YEAR}']
    target_mask = F.is_arable & group.isin(GROUPS)

    R = {'definitie': __doc__.split('\n\n')[0], 'codificare_qflag': __doc__.split('\n\n')[1].split('Praguri')[0].strip(),
         'prag_parcela': f'un an se păstrează dacă ≥ {MIN_SHARE:.0%} din pixelii TPROD valizi trec pragul', 'variante': {}}
    base_loss = None
    for name, tprod in T.items():
        loss, D = loss_from(F, tprod)
        if name == 'a_toti_pixelii':
            chk = F[['parcel_id']].assign(mine=loss).merge(official, on='parcel_id')
            assert np.allclose(chk.mine, chk.loss_rel, equal_nan=True), 'ținta oficială nu se reproduce'
            base_loss = loss
        e = {}
        for g in GROUPS:
            m = F.is_arable & group.eq(g)
            v = loss[m].dropna().to_numpy() * 100
            e[g] = {'n_parcele': int(len(v)), 'mediana_pct': round(float(np.median(v)), 1)}
            both = m & loss.notna() & base_loss.notna()
            e[g]['aceleasi_parcele_ca_a'] = {'n': int(both.sum()),
                                             'mediana_a_pct': round(float(np.median(base_loss[both]) * 100), 1),
                                             'mediana_varianta_pct': round(float(np.median(loss[both]) * 100), 1)}
        e['parcele_cu_valoare_pe_an_pct'] = {str(y): round(float(np.isfinite(tprod[y][target_mask.to_numpy()]).mean() * 100), 1) for y in YEARS}
        R['variante'][name] = e
    assert R['variante']['a_toti_pixelii']['primavara']['mediana_pct'] == 30.1
    assert R['variante']['a_toti_pixelii']['toamna']['mediana_pct'] == -0.2
    (OUT / 'loss_qflag.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
    for name, e in R['variante'].items():
        print(name, json.dumps(e, ensure_ascii=False))


if __name__ == '__main__':
    main()
