"""Verificare de robustețe pentru ținta oficială (D21): loss_rel like-for-like pe TPROD cu referința restrânsă la 2020–2023
și la 2021–2023, plus saltul TPROD și EOSD între 2017–2019 și 2020+ pe non-arabilul stabil. Nu schimbă ținta oficială.

Procedura e aceeași ca în notebooks/03e_target.ipynb (celulele 2 și 4): grupele din NDVI aprilie, grupul incert scos,
`like_for_like_loss` cu cel puțin 2 ani comparabili, tăiere la P1/P99 pe arabil. Scriptul reface întâi ținta oficială
și se oprește dacă nu iese identic.

Non-arabil stabil (definiția de aici; cea din D19, N = 474, nu are cod în repo): parcele non-arabile cu NDVI aprilie ≥ 0,40
în toți cei 8 ani (vegetație permanentă) și TPROD valid în toți cei 8 ani.

Rezultat: data/out/robustete_referinta.json
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/robustete_referinta.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT)]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from gisday_config import BASE_YEARS, OUT, YEAR  # noqa: E402
from gisday_lib import crop_group, like_for_like_loss  # noqa: E402

YEARS = list(BASE_YEARS) + [YEAR]
REFERENCES = {'oficial_2017_2023': list(BASE_YEARS), 'a_2020_2023': [2020, 2021, 2022, 2023], 'b_2021_2023': [2021, 2022, 2023]}
GROUPS = ('primavara', 'toamna')


def features():
    F = pd.read_parquet(OUT / 'parcel_features.parquet')
    codes = F['crop'].round()
    F['is_arable'] = codes.between(211, 290)
    for y in BASE_YEARS:
        F[f'grp_{y}'] = crop_group(F[f'ndvi_apr_{y}'])
    F[f'grp_{YEAR}'] = crop_group(F['ndvi_04'])
    F.loc[F['ndvi_04'].between(0.38, 0.45) | (codes == 250), f'grp_{YEAR}'] = 'grup_incert'
    return F


def target(F, base_years):
    L = like_for_like_loss(F, 'tprod_{y}', 'grp_{y}', YEAR, base_years)
    rel = L['loss_rel'].where(F['is_arable'])
    p01, p99 = rel.quantile([0.01, 0.99])
    return rel.clip(p01, p99)


def stats(values):
    v = values.dropna().to_numpy() * 100
    p25, p50, p75 = np.percentile(v, [25, 50, 75])
    return {'n': int(len(v)), 'mediana_pct': round(float(p50), 1), 'p25_pct': round(float(p25), 1), 'p75_pct': round(float(p75), 1)}


def main():
    F = features()
    official = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'loss_rel']]
    loss = {name: target(F, years) for name, years in REFERENCES.items()}
    check = F[['parcel_id']].assign(mine=loss['oficial_2017_2023']).merge(official, on='parcel_id')
    assert np.allclose(check.mine, check.loss_rel, equal_nan=True), 'ținta oficială nu se reproduce'
    group = F[f'grp_{YEAR}']

    R = {'definitie': 'loss_rel like-for-like (D21), aceeași procedură ca 03e; fiecare referință are propria tăiere P1/P99', 'pe_grupe': {}}
    for g in GROUPS:
        m = F.is_arable & group.eq(g)
        entry = {name: stats(loss[name][m]) for name in REFERENCES}
        for name in ('a_2020_2023', 'b_2021_2023'):
            same = m & loss[name].notna()
            entry[f'oficial_pe_parcelele_{name}'] = stats(loss['oficial_2017_2023'][same])
        R['pe_grupe'][g] = entry

    stable = ~F.is_arable & np.all([F[f'grp_{y}'].eq('toamna') | (y == YEAR) & (F['ndvi_04'] >= 0.40) for y in YEARS], axis=0) & F[[f'tprod_{y}' for y in YEARS]].notna().all(axis=1)
    S = F[stable]
    eos = pd.read_parquet(OUT / 'parcel_eos.parquet').set_index('parcel_id')
    E = eos.loc[S.parcel_id]
    R['non_arabil_stabil'] = {'definitie': 'non-arabil, NDVI aprilie ≥ 0,40 în toți cei 8 ani, TPROD valid în toți cei 8 ani', 'n': int(len(S)),
                              'tprod_mediana_pe_an': {y: round(float(S[f'tprod_{y}'].median()), 1) for y in YEARS},
                              'eosd_mediana_pe_an': {y: round(float(E[f'eosd_{y}'].median()), 1) for y in YEARS}}
    for label, early, late in (('2017_2019_vs_2020_2023', [2017, 2018, 2019], [2020, 2021, 2022, 2023]),
                               ('v101_2017_2020_vs_v105_2021_2023', [2017, 2018, 2019, 2020], [2021, 2022, 2023])):
        a = S[[f'tprod_{y}' for y in early]].median(axis=1)
        b = S[[f'tprod_{y}' for y in late]].median(axis=1)
        rel = (b / a - 1) * 100
        days = E[[f'eosd_{y}' for y in late]].median(axis=1).to_numpy() - E[[f'eosd_{y}' for y in early]].median(axis=1).to_numpy()
        R['non_arabil_stabil'][label] = {
            'tprod_dif_rel_pct': {'mediana': round(float(rel.median()), 1), 'p25': round(float(rel.quantile(.25)), 1), 'p75': round(float(rel.quantile(.75)), 1)},
            'eosd_dif_zile': {'mediana': round(float(np.nanmedian(days)), 1), 'p25': round(float(np.nanpercentile(days, 25)), 1), 'p75': round(float(np.nanpercentile(days, 75)), 1)}}

    (OUT / 'robustete_referinta.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
    for g in GROUPS:
        print(g, json.dumps(R['pe_grupe'][g], ensure_ascii=False))
    ns = R['non_arabil_stabil']
    print('stabil n', ns['n'], '| TPROD pe an', ns['tprod_mediana_pe_an'], '| EOSD pe an', ns['eosd_mediana_pe_an'])
    print('salturi', {k: v for k, v in ns.items() if k.startswith(('2017', 'v101'))})


if __name__ == '__main__':
    main()
