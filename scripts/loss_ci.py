"""T1 (ticket robustețe): IC 95% pe mediana pierderii (loss_rel), primăvară și toamnă, pentru fiecare referință.

Reface ținta exact ca `scripts/robustete_referinta.py` (aceleași funcții `features` și `target`) și folosește
același bootstrap pe blocuri de 5 km ca `scripts/sfarsit_sezon.py` (`block_ci`: 5.000 de extrageri, sămânța 2024).
Blocurile: centroidul parcelei în EPSG:3844, celule de 5 km, ca în `sfarsit_sezon.py` și `diagnostic_evenimente_s1.py`.
Nu schimbă niciun fișier oficial.

Rezultat: data/out/loss_ci.json
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/loss_ci.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from gisday_config import CRS, OUT, YEAR  # noqa: E402
from robustete_referinta import GROUPS, REFERENCES, features, target  # noqa: E402
from sfarsit_sezon import N_BOOT, SEED, block_ci  # noqa: E402

EXPECTED = {'primavara': (30.1, 4973), 'toamna': (-0.2, 6075)}   # STATUS.md, rândul 03e


def main():
    F = features()
    official = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'loss_rel']]
    loss = {name: target(F, years) for name, years in REFERENCES.items()}
    check = F[['parcel_id']].assign(mine=loss['oficial_2017_2023']).merge(official, on='parcel_id')
    assert np.allclose(check.mine, check.loss_rel, equal_nan=True), 'ținta oficială nu se reproduce'

    parcels = gpd.read_parquet(OUT / 'parcels.parquet').to_crs(CRS)
    c = parcels.geometry.centroid
    B = pd.DataFrame({'parcel_id': parcels.parcel_id.to_numpy(),
                      'block': (c.x // 5000).astype(int).astype(str).to_numpy() + '_' + (c.y // 5000).astype(int).astype(str).to_numpy()})
    block = F[['parcel_id']].merge(B, on='parcel_id', how='left')['block']
    block.index = F.index
    assert block.notna().all() and len(block) == len(F)

    group = F[f'grp_{YEAR}']
    R = {'definitie': 'mediana loss_rel × 100 pe parcelele arabile cu țintă, IC 95% bootstrap pe blocuri de 5 km '
                      '(blocurile trase cu întoarcere), aceeași procedură ca robustete_referinta.py și sfarsit_sezon.py',
         'n_boot': N_BOOT, 'samanta': SEED, 'pe_grupe': {}}
    for g in GROUPS:
        R['pe_grupe'][g] = {}
        for name in REFERENCES:
            m = F.is_arable & group.eq(g) & loss[name].notna()
            v = loss[name][m].to_numpy() * 100
            ci, n_blocks = block_ci(v, block[m].to_numpy())
            R['pe_grupe'][g][name] = {'n_parcele': int(len(v)), 'n_blocuri': int(n_blocks),
                                      'mediana_pct': round(float(np.median(v)), 1), 'ic95_pct': ci}
        med, n = EXPECTED[g]
        got = R['pe_grupe'][g]['oficial_2017_2023']
        assert (got['mediana_pct'], got['n_parcele']) == (med, n), f'{g}: {got} ≠ {EXPECTED[g]}'

    (OUT / 'loss_ci.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
    for g in GROUPS:
        for name, e in R['pe_grupe'][g].items():
            print(f"{g:9s} {name:18s} N={e['n_parcele']:5d} blocuri={e['n_blocuri']:3d} mediana={e['mediana_pct']:+.1f}% IC95=[{e['ic95_pct'][0]:+.1f}; {e['ic95_pct'][1]:+.1f}]")


if __name__ == '__main__':
    main()
