"""T3 (ticket robustețe): sensibilitatea pierderii la pragul NDVI din aprilie (0,35 / 0,40 / 0,45).

Doar test de sensibilitate; clasificarea oficială (D21, D26 pct. 6) nu se schimbă.
Pentru fiecare prag t: grupa din fiecare an (2017–2024) = toamnă dacă NDVI aprilie ≥ t, altfel primăvară
(`crop_group` cu ambele praguri = t). Grupul incert din 2024 se mută odată cu pragul: banda [t − 0,02; t + 0,05]
(la t = 0,40 e banda oficială 0,38–0,45), plus codul EUCROPMAP 250. Pierderea: `like_for_like_loss`, minimum 2 ani
comparabili, tăiere P1/P99 pe arabil, ca în `robustete_referinta.py`. La t = 0,40 trebuie să iasă ținta oficială.

Rezultat: data/out/loss_prag_ndvi.json
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/loss_prag_ndvi.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from gisday_config import BASE_YEARS, OUT, YEAR  # noqa: E402
from gisday_lib import crop_group, like_for_like_loss  # noqa: E402
from robustete_referinta import GROUPS  # noqa: E402

THRESHOLDS = (0.35, 0.40, 0.45)


def groups(F, t):
    codes = F['crop'].round()
    G = pd.DataFrame(index=F.index)
    for y in BASE_YEARS:
        G[f'grp_{y}'] = crop_group(F[f'ndvi_apr_{y}'], t, t)
    G[f'grp_{YEAR}'] = crop_group(F['ndvi_04'], t, t)
    G.loc[F['ndvi_04'].between(round(t - 0.02, 2), round(t + 0.05, 2)) | (codes == 250), f'grp_{YEAR}'] = 'grup_incert'
    return G


def main():
    F = pd.read_parquet(OUT / 'parcel_features.parquet')
    F['is_arable'] = F['crop'].round().between(211, 290)
    official = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'loss_rel']]
    base = None
    R = {'definitie': __doc__.split('\n\n')[1].replace('\n', ' '), 'pe_praguri': {}}
    for t in THRESHOLDS:
        G = groups(F, t)
        D = pd.concat([F[['parcel_id', 'is_arable'] + [f'tprod_{y}' for y in list(BASE_YEARS) + [YEAR]]], G], axis=1)
        rel = like_for_like_loss(D, 'tprod_{y}', 'grp_{y}', YEAR, BASE_YEARS)['loss_rel'].where(D['is_arable'])
        rel = rel.clip(*rel.quantile([0.01, 0.99]))
        if t == 0.40:
            check = D[['parcel_id']].assign(mine=rel).merge(official, on='parcel_id')
            assert np.allclose(check.mine, check.loss_rel, equal_nan=True), 'ținta oficială nu se reproduce la 0,40'
        g24 = G[f'grp_{YEAR}'].where(D['is_arable'])
        entry = {}
        for g in GROUPS:
            v = rel[D.is_arable & g24.eq(g)].dropna().to_numpy() * 100
            entry[g] = {'n_parcele': int(len(v)), 'mediana_pct': round(float(np.median(v)), 1)}
        entry['grup_incert_n'] = int((D.is_arable & g24.eq('grup_incert')).sum())
        R['pe_praguri'][f'{t:.2f}'] = entry
        R['pe_praguri'][f'{t:.2f}']['_g24'] = g24
    ref = R['pe_praguri']['0.40'].pop('_g24')
    for k, e in R['pe_praguri'].items():
        if '_g24' not in e:
            continue
        g24 = e.pop('_g24')
        m = ref.notna() & g24.notna() & ref.ne(g24)
        e['grupa_2024_schimbata_fata_de_0_40'] = {f'{a}->{b}': int(n) for (a, b), n in
                                                 pd.crosstab(ref[m], g24[m]).stack().items() if n}
    assert R['pe_praguri']['0.40']['primavara'] == {'n_parcele': 4973, 'mediana_pct': 30.1}
    assert R['pe_praguri']['0.40']['toamna'] == {'n_parcele': 6075, 'mediana_pct': -0.2}
    (OUT / 'loss_prag_ndvi.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
    for k, e in R['pe_praguri'].items():
        print(k, json.dumps(e, ensure_ascii=False))


if __name__ == '__main__':
    main()
