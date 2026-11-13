"""T5 (ticket robustețe): producția și suprafața INS pe Dolj, Olt și total național, 2017–2024.

Sursa: INS, TEMPO Online, tabelele AGR109A (producția, tone) și AGR108A (suprafața cultivată, ha), forma de
proprietate Total. Culturi: porumb boabe, floarea-soarelui, grâu (total). Randament = producție / suprafață (t/ha).
Variații: 2024 față de 2023 și față de media 2017–2023. Datele se citesc prin API-ul public TEMPO; nu se completează
nimic din alte surse.

Rezultat: data/out/ins_judete.csv și data/out/ins_judete.json
Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/ins_judete.py
"""
import datetime as dt
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT)]

import pandas as pd  # noqa: E402
import requests  # noqa: E402

from gisday_config import OUT  # noqa: E402

API = 'http://statistici.insse.ro:8077/tempo-ins'
YEARS = {2017: 4760, 2018: 4779, 2019: 4798, 2020: 4817, 2021: 4836, 2022: 4855, 2023: 4874, 2024: 4893}
AREAS = {'Dolj': 3079, 'Olt': 3091, 'Total national': 112}
TABLES = {  # cod tabel: (coduri culturi, cod UM, coloana)
    'AGR109A': ({'porumb boabe': 5863, 'floarea-soarelui': 5872, 'grau': 17237}, 9729, 'productie_t'),
    'AGR108A': ({'porumb boabe': 5817, 'floarea-soarelui': 5828, 'grau': 17175}, 9427, 'suprafata_ha'),
}
PROPRIETATE_TOTAL = 5789


def fetch(code, crops, um):
    meta = requests.get(f'{API}/matrix/{code}', timeout=60).json()
    q = ':'.join([','.join(map(str, crops.values())), str(PROPRIETATE_TOTAL), ','.join(map(str, AREAS.values())),
                  ','.join(map(str, YEARS.values())), str(um)])
    body = {'language': 'ro', 'encQuery': q, 'matCode': code, 'matMaxDim': meta['details']['matMaxDim'],
            'matUMSpec': meta['details']['matUMSpec'], 'matRegJ': meta['details']['matRegJ']}
    r = requests.post(f'{API}/pivot', json=body, timeout=120)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    return df, meta.get('ultimaActualizare'), meta.get('matrixName')


def main():
    frames, sources = [], {}
    for code, (crops, um, col) in TABLES.items():
        df, updated, name = fetch(code, crops, um)
        df.columns = ['cultura', 'proprietate', 'zona', 'an', 'um', col]
        df['cultura'] = df['cultura'].str.strip().map({'Porumb boabe': 'porumb boabe', 'Floarea soarelui': 'floarea-soarelui',
                                                       'Grau - total': 'grau'})
        df['zona'] = df['zona'].str.strip().replace({'TOTAL': 'Total national'})
        df['an'] = df['an'].str.extract(r'(\d{4})', expand=False).astype(int)
        df[col] = pd.to_numeric(df[col], errors='coerce')
        assert df['cultura'].notna().all(), df['cultura'].unique()
        print(code, df.shape, df['an'].min(), df['an'].max())
        frames.append(df[['cultura', 'zona', 'an', col]])
        sources[code] = {'tabel': name, 'ultima_actualizare_INS': updated, 'adresa': f'{API}/matrix/{code}'}
    D = frames[0].merge(frames[1], on=['cultura', 'zona', 'an'], how='outer')
    D['randament_t_ha'] = D['productie_t'] / D['suprafata_ha']
    D = D.sort_values(['zona', 'cultura', 'an']).reset_index(drop=True)
    D.to_csv(OUT / 'ins_judete.csv', index=False, encoding='utf-8')

    res = {}
    for (zona, cult), g in D.groupby(['zona', 'cultura']):
        g = g.set_index('an')
        if 2024 not in g.index or g.loc[2024, 'randament_t_ha'] != g.loc[2024, 'randament_t_ha']:
            res.setdefault(zona, {})[cult] = 'lipsă 2024'
            continue
        r24, r23 = g.loc[2024, 'randament_t_ha'], g.loc[2023, 'randament_t_ha']
        base = g.loc[2017:2023, 'randament_t_ha'].mean()
        p24, p23 = g.loc[2024, 'productie_t'], g.loc[2023, 'productie_t']
        res.setdefault(zona, {})[cult] = {
            'randament_2024_t_ha': round(float(r24), 2), 'randament_2023_t_ha': round(float(r23), 2),
            'randament_medie_2017_2023_t_ha': round(float(base), 2),
            'randament_2024_vs_2023_pct': round(float((r24 / r23 - 1) * 100), 1),
            'randament_2024_vs_medie_2017_2023_pct': round(float((r24 / base - 1) * 100), 1),
            'productie_2024_vs_2023_pct': round(float((p24 / p23 - 1) * 100), 1)}
    out = {'sursa': sources, 'accesat': dt.date.today().isoformat(),
           'nota': 'randament = producție / suprafață cultivată, calculat; forma de proprietate Total', 'rezultate': res}
    (OUT / 'ins_judete.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
