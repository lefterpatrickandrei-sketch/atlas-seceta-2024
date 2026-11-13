"""T2 (ticket robustețe): mediana pierderii cu referința 2017–2023 fără câte un an (7 variante).

Aceeași procedură ca `scripts/robustete_referinta.py`: `features` și `target` (like-for-like, minimum 2 ani
comparabili, tăiere P1/P99 pe arabil, calculată pentru fiecare variantă). Nu schimbă niciun fișier oficial.

Rezultat: data/out/loss_leave_one_year.json
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/loss_leave_one_year.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]

import numpy as np  # noqa: E402

from gisday_config import BASE_YEARS, OUT, YEAR  # noqa: E402
from robustete_referinta import GROUPS, features, target  # noqa: E402


def main():
    F = features()
    group = F[f'grp_{YEAR}']
    variants = {'oficial_2017_2023': list(BASE_YEARS)}
    variants.update({f'fara_{y}': [b for b in BASE_YEARS if b != y] for y in BASE_YEARS})
    R = {'definitie': 'mediana loss_rel × 100 pe arabil, referința 2017–2023 fără anul indicat; '
                      'aceeași procedură ca robustete_referinta.py', 'pe_grupe': {g: {} for g in GROUPS}}
    for name, years in variants.items():
        loss = target(F, years)
        for g in GROUPS:
            v = loss[F.is_arable & group.eq(g)].dropna().to_numpy() * 100
            R['pe_grupe'][g][name] = {'n_parcele': int(len(v)), 'mediana_pct': round(float(np.median(v)), 1)}
    for g in GROUPS:
        meds = [e['mediana_pct'] for k, e in R['pe_grupe'][g].items() if k.startswith('fara_')]
        R['pe_grupe'][g]['interval_fara_un_an_pct'] = [min(meds), max(meds)]
    assert R['pe_grupe']['primavara']['oficial_2017_2023'] == {'n_parcele': 4973, 'mediana_pct': 30.1}
    assert R['pe_grupe']['toamna']['oficial_2017_2023'] == {'n_parcele': 6075, 'mediana_pct': -0.2}
    (OUT / 'loss_leave_one_year.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
    for g in GROUPS:
        for k, e in R['pe_grupe'][g].items():
            print(g, k, e)


if __name__ == '__main__':
    main()
