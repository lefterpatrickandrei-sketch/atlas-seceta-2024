"""Sarcina 2: rulează celula 4 din notebooks/03b_irrigation.ipynb (evaluarea Olofsson pe labels.csv și poarta de 70%)
fără să atingă stratul oficial.

Celula 4 folosește variabile din celulele 1–3, iar celulele 2–3 rescriu pivots_2024.*, irrigation_2024.* și
s1_transitions_2024.csv. Scriptul execută codul celulelor 1–4 exact cum e în notebook, dar redirecționează scrierile acestor
fișiere în data/interim/sarcina2_verificare/ și verifică apoi că ies identice cu cele oficiale; hash-urile oficiale se
compară înainte și după. În data/out se scriu doar irrigation_metrics.json (rezultatul celulei 4) și lista parcelelor
în care eticheta contrazice clasa radar (D27 pct. 6).

Evaluarea produsă în commit-ul efc72ae e invalidă (D36): etichetele din labels.csv nu respectă criteriul foilor. Cât timp
irrigation_metrics.json o marchează invalidă, scriptul refuză să ruleze; --forteaza e doar pentru etichete noi, conforme.

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/sarcina2_evaluare.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT)]

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

from gisday_config import INTERIM, OUT  # noqa: E402

NOTEBOOK = ROOT / 'notebooks' / '03b_irrigation.ipynb'
OFFICIAL = ('pivots_2024.gpkg', 'pivots_2024.parquet', 'irrigation_2024.parquet', 'irrigation_2024.gpkg', 's1_transitions_2024.csv')
CHECK = INTERIM / 'sarcina2_verificare'
WRONG = OUT / 'validare_parcele_gresite.csv'
NEW_KEYS = ('validation_olofsson_by_parcels', 'validation_olofsson_by_ha', 'panou3_gate_passed',
            'validation_status', 'validation_note', 'irigat_layer_status', 'panou3_gate_status')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def redirect_official_writes():
    """Scrierile celulelor 2–3 în fișierele oficiale ajung în CHECK; restul scrierilor nu se schimbă."""
    def target(path):
        p = Path(path)
        return CHECK / p.name if p.name in OFFICIAL and p.parent.resolve() == OUT.resolve() else path

    def wrap(cls, name):
        original = getattr(cls, name)

        def inner(self, path, *args, **kwargs):
            return original(self, target(path), *args, **kwargs)
        setattr(cls, name, inner)

    for cls, name in ((pd.DataFrame, 'to_parquet'), (pd.DataFrame, 'to_csv'), (gpd.GeoDataFrame, 'to_file'), (gpd.GeoDataFrame, 'to_parquet')):
        wrap(cls, name)


def same_as_official(name):
    a, b = OUT / name, CHECK / name
    if name.endswith('.parquet'):
        return pd.read_parquet(a).equals(pd.read_parquet(b))
    if name.endswith('.csv'):
        return a.read_text(encoding='utf-8') == b.read_text(encoding='utf-8')
    ga, gb = gpd.read_file(a), gpd.read_file(b)
    return ga.drop(columns='geometry').equals(gb.drop(columns='geometry')) and bool(ga.geometry.geom_equals_exact(gb.geometry, tolerance=1e-9).all())


def pct(v):
    return f'{100 * v:.1f}%'


def main():
    current = json.loads((OUT / 'irrigation_metrics.json').read_text(encoding='utf-8'))
    if str(current.get('validation_status', '')).startswith('invalidă') and '--forteaza' not in sys.argv:
        sys.exit('Evaluarea e marcată invalidă (D36): etichetele din labels.csv nu respectă criteriul. '
                 'O rulare ar suprascrie marcajul; folosește --forteaza doar cu etichete noi.')
    before = {name: sha(OUT / name) for name in OFFICIAL + ('labels.csv',)}
    CHECK.mkdir(parents=True, exist_ok=True)
    redirect_official_writes()

    cells = [''.join(c['source']) for c in json.loads(NOTEBOOK.read_text(encoding='utf-8'))['cells']]
    assert cells[4].startswith('# 3. Evaluarea pe labels.csv'), 'celula 4 nu e evaluarea'
    ns = {'__name__': '03b'}
    for i in (1, 2, 3, 4):
        print(f'--- celula {i} din 03b')
        exec(compile(cells[i], f'03b_irrigation.ipynb, celula {i}', 'exec'), ns)

    after = {name: sha(OUT / name) for name in before}
    assert after == before, 'un fișier oficial s-a schimbat'
    for name in OFFICIAL:
        assert same_as_official(name), f'{name} recalculat diferă de cel oficial'

    new = json.loads((OUT / 'irrigation_metrics.json').read_text(encoding='utf-8'))
    old = json.loads(subprocess.run(['git', 'show', 'HEAD:data/out/irrigation_metrics.json'], capture_output=True, cwd=ROOT).stdout.decode('utf-8'))
    assert {k: v for k, v in new.items() if k not in NEW_KEYS} == {k: v for k, v in old.items() if k not in NEW_KEYS}, 'metricile vechi s-au schimbat'

    ev = ns['eval_df']
    blanks = ev.groupby('clasa_regula').irigat.apply(lambda s: int(s.isna().sum())).to_dict()
    wrong = ev[ev.irigat.notna() & ((ev.clasa_regula.eq('irigat') & (ev.irigat == 0)) | (ev.clasa_regula.eq('neirigat') & (ev.irigat == 1)))]
    wrong[['numar', 'foaie', 'parcel_id', 'clasa_regula', 'irigat', 'is_pivot', 'n_events_s1_fara_0627', 'max_dvv_dry', 'area_ha']].sort_values(['clasa_regula', 'numar']).to_csv(WRONG, index=False)

    print('\n=== REZUMAT')
    print('stratul oficial: identic la recalculare, hash neschimbat:', list(OFFICIAL))
    print('goale pe clasa radar:', blanks, '| completate:', int(ev.irigat.notna().sum()))
    for label, key in (('pe parcele', 'validation_olofsson_by_parcels'), ('pe hectare', 'validation_olofsson_by_ha')):
        m = new[key]
        ua, pa, oa = m['user_accuracy'], m['producer_accuracy'], m['overall_accuracy']
        print(f"{label}: n pe strat {m['n_per_stratum']} | matrice {m['confusion_counts']} | ponderi {({k: round(v, 3) for k, v in m['weights'].items()})}")
        for c in ('irigat', 'neirigat'):
            print(f"  UA {c}: {pct(ua[c]['est'])} (IC 95% {pct(ua[c]['ci95'][0])}…{pct(ua[c]['ci95'][1])}) | PA {c}: {pct(pa[c]['est'])} (IC 95% {pct(pa[c]['ci95'][0])}…{pct(pa[c]['ci95'][1])})")
        print(f"  OA ponderată: {pct(oa['est'])} (IC 95% {pct(oa['ci95'][0])}…{pct(oa['ci95'][1])})")
    print('poarta de 70% pe irigat trecută:', new['panou3_gate_passed'])
    irig = ev[ev.clasa_regula.eq('irigat') & ev.irigat.notna()]
    for name, part in (('pivoți', irig[irig.is_pivot]), ('evenimente S1', irig[~irig.is_pivot])):
        print(f'  irigat radar, {name}: {int((part.irigat == 1).sum())} confirmate din {len(part)}')
    print('parcele unde eticheta contrazice clasa radar:', len(wrong), '->', WRONG.relative_to(ROOT).as_posix())


if __name__ == '__main__':
    main()
