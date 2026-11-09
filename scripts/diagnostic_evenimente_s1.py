"""Diagnosticul evenimentelor radar din august 2024: ce sunt, ce regulă doar radar le separă și ce schimbă (Varianta C).

Nu atinge stratul oficial (Varianta B, D27): îl reproduce la început și se oprește dacă nu iese identic.
NDVI apare doar ca diagnostic, niciodată în regulă (ar fi circular cu TPROD).

Rezultate:
  data/out/s1_events_diagnostic.json                cifrele agregate
  data/out/s1_events_diagnostic.png                 distribuțiile ΔVH și Δ(VH−VV)
  data/interim/q2_s1_events_2024.parquet            evenimentele, cu semnătura radar
  data/interim/irrigation_2024_varianta_c.parquet   clasele B și C pe parcelă (doar diagnostic, nu înlocuiește B)

Rulare, din rădăcina proiectului, după scripts/extract_s1_vh.py:
  .venv/Scripts/python.exe -X utf8 scripts/diagnostic_evenimente_s1.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import geopandas as gpd  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from common import BG, GRID, LINE, MUTED, TXT, TXT2  # noqa: E402
from gisday_config import CRS, INTERIM, OUT  # noqa: E402
from gisday_lib import block_bootstrap_median_diff, geometric_pivots, s1_spring_irrigation_rule  # noqa: E402

EXCLUDED = ('o7_0615_0627',)                 # D27
AUGUST = ('o7_0802_0814', 'o7_0814_0826', 'o29_0803_0815', 'o29_0815_0827')
SAME_INTERVAL = (('o7_0802_0814', 'o29_0803_0815'), ('o7_0814_0826', 'o29_0815_0827'))   # aceeași perioadă, două orbite la ~1 zi
WITH_NEXT = ('o7_0802_0814', 'o29_0803_0815')   # singurele tranziții din august cu o trecere următoare în datele extrase
RAIN_CONTROL = 'o7_0709_0721'                # ploaie regională la trecerea din 21 iulie: umezire cunoscută, independentă de TPROD
MIN_DVV, MAX_RAIN_5D, MAX_RAIN_12D = 1.5, 2.0, 5.0     # pragurile din D26, aceleași ca în s1_spring_irrigation_rule
N_BOOT, SEED = 5000, 2024
LABEL_A, LABEL_B, LABEL_C, LABEL_D = 'A_vh_scade', 'B_ca_martorul_ploaie', 'C_dcr_peste_martor', 'D_dcr_sub_martor'
COLORS = {'primavara': '#D95926', 'martor': '#2A78D6', 'toamna': '#199E70'}   # validate cu validate_palette.js pe fundalul BG


def load():
    P = gpd.read_parquet(OUT / 'parcels.parquet').to_crs(CRS)
    T = pd.read_parquet(OUT / 'parcel_target.parquet')[['parcel_id', 'is_arable', 'tip_cultura_2024', 'loss_rel']]
    F = pd.read_parquet(OUT / 'parcel_features.parquet', columns=['parcel_id', 'ndvi_07', 'ndvi_08'])
    VV = pd.read_parquet(INTERIM / 'q2_s1_vv_arable.parquet')
    VH = pd.read_parquet(INTERIM / 'q2_s1_vh_arable.parquet')
    ERA = pd.read_parquet(INTERIM / 'q2_era5_daily_arable.parquet')
    D = P[['parcel_id', 'geometry']].join(geometric_pivots(P.geometry)).merge(T, on='parcel_id')
    D = D.merge(VV, on='parcel_id', how='left').merge(ERA, on='parcel_id', how='left').merge(VH, on='parcel_id', how='left').merge(F, on='parcel_id', how='left')
    c = D.geometry.centroid
    D['block'] = (c.x // 5000).astype(int).astype(str) + '_' + (c.y // 5000).astype(int).astype(str)
    return D, [x for x in VV.columns if x.startswith('vv_o')]


def reproduce_official(spring):
    """Varianta B trebuie să iasă identic cu stratul oficial; altfel diagnosticul nu e comparabil."""
    tr, res = s1_spring_irrigation_rule(spring, exclude_transitions=EXCLUDED)
    official = pd.read_parquet(OUT / 'irrigation_2024.parquet')[['parcel_id', 'clasa_irigare']]
    check = spring[['parcel_id']].assign(clasa=res.clasa_irigare).merge(official, on='parcel_id')
    assert len(check) == len(spring) and check.clasa.eq(check.clasa_irigare).all(), 'Clasele nu reproduc Varianta B'
    expected = json.loads((OUT / 'irrigation_metrics.json').read_text(encoding='utf-8'))['panou3_radar_varianta_b']
    got = block_bootstrap_median_diff(spring.assign(clasa_irigare=res.clasa_irigare), n_boot=N_BOOT, seed=SEED)
    assert round(got['diff_median_pos_minus_neg'] * 100, 2) == expected['diff_median_pct'], 'Diferența nu reproduce Panoul 3'
    assert [round(v * 100, 2) for v in got['diff_ci95_block_bootstrap']] == expected['diff_ci95_pct'], 'IC nu reproduce Panoul 3'
    return tr, res, got


def long_table(arable, vv_columns):
    """Un rând pentru fiecare parcelă arabilă și fiecare tranziție de 12 zile din iunie–august 2024, aceeași orbită."""
    rows = []
    acq = sorted((int(c.split('_')[1][1:]), pd.to_datetime(c.split('_')[2], format='%Y%m%d'), c) for c in vv_columns)
    acq = pd.DataFrame(acq, columns=['orbit', 'date', 'col'])
    for orbit, g in acq.groupby('orbit'):
        g = g.sort_values('date').reset_index(drop=True)
        for i in range(1, len(g)):
            t0, t1, c0, c1 = g.date[i - 1], g.date[i], g.col[i - 1], g.col[i]
            if (t1 - t0).days != 12 or not pd.Timestamp('2024-06-01') <= t1 <= pd.Timestamp('2024-08-31'):
                continue
            d12 = [f'rain_{d:%Y%m%d}' for d in pd.date_range(t0 + pd.Timedelta(days=1), t1)]
            d5 = [f'rain_{d:%Y%m%d}' for d in pd.date_range(t1 - pd.Timedelta(days=4), t1)]
            frame = pd.DataFrame({'parcel_id': arable.parcel_id, 'key': f'o{orbit}_{t0:%m%d}_{t1:%m%d}', 'orbit': orbit, 't1': t1,
                                  'vv0': arable[c0], 'vv1': arable[c1], 'vh0': arable[c0.replace('vv_', 'vh_')], 'vh1': arable[c1.replace('vv_', 'vh_')],
                                  'r5': arable[d5].sum(axis=1), 'r12': arable[d12].sum(axis=1)})
            next_ok = i + 1 < len(g) and (g.date[i + 1] - t1).days == 12
            frame['vv2'] = arable[g.col[i + 1]] if next_ok else np.nan
            rows.append(frame[frame.vv0.notna() & frame.vv1.notna()])
    L = pd.concat(rows, ignore_index=True)
    L['dvv'], L['dvh'] = L.vv1 - L.vv0, L.vh1 - L.vh0
    L['dcr'] = L.dvh - L.dvv                      # Δ(VH−VV)
    L['cr0'], L['cr1'] = L.vh0 - L.vv0, L.vh1 - L.vv1
    L['dry'] = (L.r5 < MAX_RAIN_5D) & (L.r12 < MAX_RAIN_12D)
    meta = arable[['parcel_id', 'tip_cultura_2024', 'is_pivot', 'area_ha', 'loss_rel', 'ndvi_07', 'ndvi_08', 'block']]
    L = L.merge(meta, on='parcel_id')
    L['spring'] = L.tip_cultura_2024.eq('primavara')
    return L


def signature(df, low, high):
    """Semnătura radar a unui eveniment, cu limitele luate din martorul de ploaie, nu din pierdere sau din NDVI."""
    return np.select([df.dvh < 0, df.dcr > high, df.dcr < low], [LABEL_A, LABEL_C, LABEL_D], LABEL_B)


def r2(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 2)


def quantiles(s):
    return {f'p{p}': r2(v) for p, v in zip((5, 25, 50, 75, 95), np.percentile(s, [5, 25, 50, 75, 95]))}


def loss_stats(s):
    s = s.dropna()
    if not len(s):
        return {'n_cu_tinta': 0}
    return {'n_cu_tinta': int(len(s)), 'mediana_pct': r2(100 * s.median()), 'p25_pct': r2(100 * s.quantile(.25)), 'p75_pct': r2(100 * s.quantile(.75))}


def group_stats(g):
    out = {'n': int(len(g)), 'parcele': int(g.parcel_id.nunique()), 'dvv': quantiles(g.dvv), 'dvh': quantiles(g.dvh), 'dcr': quantiles(g.dcr),
           'pct_dvh_negativ': r2(100 * (g.dvh < 0).mean()), 'pct_dvh_sub_minus1': r2(100 * (g.dvh < -1).mean()), 'pct_dcr_sub_minus2': r2(100 * (g.dcr < -2).mean())}
    out['mediane'] = {c: r2(g[c].median()) for c in ('vv0', 'vv1', 'vh0', 'vh1', 'cr0', 'cr1', 'ndvi_07', 'ndvi_08')}
    return out


def persistence(g):
    """După 12 zile, VV a rămas cu cel puțin 1 dB peste nivelul de dinainte? Umezirea trece, schimbările de suprafață rămân."""
    g = g[g.vv2.notna()]
    return {'n': int(len(g)), 'pct_ramane_peste_t0_cu_1dB': r2(100 * ((g.vv2 - g.vv0) >= 1).mean()), 'revenire_mediana_dB': r2((g.vv2 - g.vv1).median())} if len(g) else {'n': 0}


def rate_gap(pool, hits):
    """Rata pe primăvară față de toamnă pentru fiecare mască din `hits`, cu IC 95% bootstrap pe blocuri de 5 km."""
    blocks = sorted(pool.block.unique())
    idx = pool.block.map({b: i for i, b in enumerate(blocks)}).to_numpy()
    spring = pool.spring.to_numpy()
    draws = np.random.default_rng(SEED).integers(0, len(blocks), size=(N_BOOT, len(blocks)))
    n_sp, n_au = (np.bincount(idx[m], minlength=len(blocks)) for m in (spring, ~spring))
    out = {}
    for name, hit in hits.items():
        e_sp, e_au = (np.bincount(idx[hit & m], minlength=len(blocks)) for m in (spring, ~spring))
        rate_sp, rate_au = e_sp[draws].sum(axis=1) / n_sp[draws].sum(axis=1), e_au[draws].sum(axis=1) / n_au[draws].sum(axis=1)
        diff = rate_sp - rate_au
        out[name] = {'primavara_pct': r2(100 * e_sp.sum() / n_sp.sum()), 'toamna_pct': r2(100 * e_au.sum() / n_au.sum()),
                     'diferenta_pp': r2(100 * (e_sp.sum() / n_sp.sum() - e_au.sum() / n_au.sum())),
                     'ic95_pp': [r2(v) for v in 100 * np.percentile(diff, [2.5, 97.5])],
                     'ic95_primavara_pct': [r2(v) for v in 100 * np.percentile(rate_sp, [2.5, 97.5])],
                     'ic95_toamna_pct': [r2(v) for v in 100 * np.percentile(rate_au, [2.5, 97.5])],
                     'n_observatii': {'primavara': int(n_sp.sum()), 'toamna': int(n_au.sum()), 'blocuri': len(blocks)}}
    return out


def placebo(L, low, high):
    """Rata evenimentelor pe parcelele de primăvară față de cele de toamnă (recoltate, neirigate în august)."""
    pool = L[L.key.isin(AUGUST) & L.dry & L.tip_cultura_2024.isin(['primavara', 'toamna'])].copy()
    ev = (pool.dvv >= MIN_DVV).to_numpy()
    sig = signature(pool, low, high)
    hits = {'toate': ev, **{k: ev & (sig == k) for k in (LABEL_A, LABEL_B, LABEL_C, LABEL_D)}}
    return {'unitate': 'parcelă × tranziție, cele 4 tranziții uscate din august', **rate_gap(pool, hits)}


def placebo_transient(L, low, high):
    """Aceeași comparație pentru evenimentele trecătoare: la trecerea următoare, VV e sub nivelul de dinainte + 1 dB."""
    pool = L[L.key.isin(WITH_NEXT) & L.dry & L.tip_cultura_2024.isin(['primavara', 'toamna']) & L.vv2.notna()].copy()
    ev = (pool.dvv >= MIN_DVV).to_numpy()
    like_rain = signature(pool, low, high) == LABEL_B
    transient = ((pool.vv2 - pool.vv0) < 1).to_numpy()
    return {'unitate': 'parcelă × tranziție, doar tranzițiile din august cu o trecere următoare', 'tranzitii': list(WITH_NEXT),
            **rate_gap(pool, {'toate': ev, 'trecatoare': ev & transient, 'ca_martorul_si_trecatoare': ev & like_rain & transient})}


def classes(spring, base, kept_ids):
    """Clasele pe primăvară: se schimbă doar ce contează ca eveniment. Parcelele scoase ajung la nedeterminat, fiindcă au avut ΔVV ≥ 1,5 dB."""
    irig = spring.is_pivot.to_numpy() | spring.parcel_id.isin(kept_ids).to_numpy()
    return np.where(irig, 'irigat', np.where(base.eq('neirigat').to_numpy(), 'neirigat', 'nedeterminat'))


def compare(spring, cls):
    b = block_bootstrap_median_diff(spring.assign(clasa_irigare=cls), n_boot=N_BOOT, seed=SEED)
    counts = {c: {'n': int((cls == c).sum()), 'ha': r2(spring.area_ha[cls == c].sum())} for c in ('irigat', 'neirigat', 'nedeterminat')}
    return {'clase': counts, 'irigat': {k: (b['irigat'][k] if k == 'n' else r2(100 * b['irigat'][k])) for k in ('n', 'median', 'p25', 'p75')},
            'neirigat': {k: (b['neirigat'][k] if k == 'n' else r2(100 * b['neirigat'][k])) for k in ('n', 'median', 'p25', 'p75')},
            'diferenta_pp': r2(100 * b['diff_median_pos_minus_neg']), 'ic95_pp': [r2(100 * v) for v in b['diff_ci95_block_bootstrap']], 'n_blocuri': b['n_blocks']}


def comma(v, signed=True):
    text = f'{v:+.2f}' if signed else f'{v:.2f}'
    return text.replace('.', ',').replace('-', '−')


def thousands(n):
    return f'{n:,}'.replace(',', '.')


def figure(groups, low, high, path):
    fonts = ROOT / 'render' / 'fonts'
    for name in ('Inter-Regular.otf', 'Inter-Medium.otf', 'Inter-SemiBold.otf'):
        font_manager.fontManager.addfont(str(fonts / name))
    plt.rcParams['font.family'] = 'Inter'
    hexc = lambda rgb: '#%02x%02x%02x' % rgb  # noqa: E731
    fig, axes = plt.subplots(3, 2, figsize=(14, 8), dpi=100, facecolor=hexc(BG), sharex='col')
    columns = (('dvh', 'ΔVH (dB)', -6.0, 10.0), ('dcr', 'Δ(VH − VV) (dB)', -6.0, 6.0))
    for r, (color, title, g) in enumerate(groups):
        for c, (col, xlabel, x0, x1) in enumerate(columns):
            ax = axes[r, c]
            ax.set_facecolor(hexc(BG))
            edges = np.arange(x0, x1 + .25, .5)
            counts, _ = np.histogram(np.clip(g[col], x0, x1), bins=edges)
            ax.bar(edges[:-1] + .25, 100 * counts / len(g), width=.42, color=color, zorder=3)
            if col == 'dcr':
                ax.axvspan(low, high, color=hexc(GRID), alpha=.9, zorder=1, lw=0)
            ax.axvline(0, color=hexc(LINE), lw=1.2, zorder=2)
            med = float(g[col].median())
            ax.axvline(med, color=hexc(TXT), lw=1.6, zorder=4)
            ax.set_ylim(0, 24)
            ax.set_xlim(x0, x1)
            ax.text(med + .18, 21.4, f'mediana {comma(med)}', color=hexc(TXT), fontsize=12, fontweight='medium', zorder=5)
            ax.set_yticks([0, 10, 20])
            ax.set_yticklabels(['0', '10', '20%'], color=hexc(MUTED), fontsize=11)
            ax.tick_params(axis='x', colors=hexc(TXT2), labelsize=11, length=0)
            ax.tick_params(axis='y', length=0)
            ax.grid(axis='y', color=hexc(GRID), lw=.8, zorder=0)
            for side in ('top', 'right', 'left'):
                ax.spines[side].set_visible(False)
            ax.spines['bottom'].set_color(hexc(LINE))
            if c == 0:
                ax.set_title(title, loc='left', color=hexc(TXT), fontsize=14, fontweight='semibold', pad=8)
            if r == 2:
                ax.set_xlabel(xlabel, color=hexc(TXT2), fontsize=13, labelpad=8)
    axes[0, 1].text(high + .15, 16.6, 'zona gri: intervalul\nP5–P95 al martorului', color=hexc(TXT2), fontsize=11, zorder=5, linespacing=1.3)
    fig.suptitle('Ce se schimbă când VV crește cu cel puțin 1,5 dB: Sentinel-1, sudul Olteniei, 2024', x=.045, y=.982, ha='left', color=hexc(TXT), fontsize=19, fontweight='semibold')
    fig.text(.045, .908, 'Procent din evenimente, pe clase de 0,5 dB. Umezirea ridică VH odată cu VV (rândul din mijloc); o tăiere l-ar coborî.', color=hexc(TXT2), fontsize=13)
    fig.text(.045, .022, 'Eveniment = ΔVV ≥ +1,5 dB la 12 zile, aceeași orbită, fără ploaie ERA5-Land. Martorul: ploaia regională de la trecerea din 21 iulie. Contains modified Copernicus Sentinel data 2024.', color=hexc(MUTED), fontsize=11)
    fig.subplots_adjust(left=.045, right=.985, top=.85, bottom=.125, hspace=.34, wspace=.11)
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    D, vv_columns = load()
    arable = D[D.is_arable].copy().reset_index(drop=True)
    spring = D[D.is_arable & D.tip_cultura_2024.eq('primavara')].copy().reset_index(drop=True)
    tr, res, official = reproduce_official(spring)
    base = res.clasa_irigare
    R = {'reproducere_varianta_b': {'clase': base.value_counts().to_dict(), 'diferenta_pp': r2(100 * official['diff_median_pos_minus_neg']),
                                    'ic95_pp': [r2(100 * v) for v in official['diff_ci95_block_bootstrap']]}}
    L = long_table(arable, vv_columns)
    valid = set(tr.loc[~tr.excluded & tr.n_dry.gt(0), 'key'])
    L['event'] = L.spring & L.key.isin(valid) & L.dry & (L.dvv >= MIN_DVV)
    E = L[L.event].copy()

    # aceleași evenimente ca în regula oficială
    per_parcel = E.groupby('parcel_id').size()
    assert per_parcel.reindex(spring.parcel_id).fillna(0).astype(int).to_numpy().tolist() == res.n_events_s1.tolist(), 'Evenimentele diferă de regula oficială'
    assert E.groupby('key').size().to_dict() == tr.loc[~tr.excluded & tr.n_evt_dry.gt(0)].set_index('key').n_evt_dry.to_dict()

    # (a) tranziții și subseturi
    R['evenimente'] = {'total': int(len(E)), 'parcele': int(E.parcel_id.nunique()), 'parcele_dupa_nr_evenimente': {int(k): int(v) for k, v in per_parcel.value_counts().sort_index().items()}}
    R['pe_tranzitii'] = [{'tranzitie': k, 'evenimente': int(len(g)), 'pe_parcele_nepivot': int((~g.is_pivot).sum()), 'pe_pivoti': int(g.is_pivot.sum()),
                          **loss_stats(g.drop_duplicates('parcel_id').loss_rel)} for k, g in E.groupby('key')]
    n_ev = spring.parcel_id.map(per_parcel).fillna(0).astype(int)
    subset = np.select([(n_ev > 0) & ~spring.is_pivot, spring.is_pivot & (n_ev == 0), spring.is_pivot & (n_ev > 0), base.eq('neirigat'), base.eq('nedeterminat')],
                       ['doar_S1', 'doar_pivot', 'ambele', 'neirigat', 'nedeterminat'], '?')
    assert '?' not in set(subset)
    R['pe_subseturi'] = {k: {'n': int((subset == k).sum()), 'ha': r2(spring.area_ha[subset == k].sum()), **loss_stats(spring.loss_rel[subset == k])}
                         for k in ('doar_S1', 'doar_pivot', 'ambele', 'neirigat', 'nedeterminat')}

    # (b) martorul de ploaie dă limitele regulii, fără să se uite la pierdere sau la NDVI
    control = L[L.spring & L.key.eq(RAIN_CONTROL) & (L.dvv >= MIN_DVV)]
    low, high = (float(v) for v in np.percentile(control.dcr, [5, 95]))
    R['regula_propusa'] = {'text': 'Eveniment păstrat ca umezire dacă ΔVH ≥ 0 și Δ(VH−VV) e între P5 și P95 ale martorului de ploaie', 'dcr_p5': r2(low), 'dcr_p95': r2(high), 'martor': RAIN_CONTROL}
    E['semnatura'] = signature(E, low, high)
    spr_dry = L[L.spring & L.key.isin(valid) & L.dry]
    autumn_ev = L[L.tip_cultura_2024.eq('toamna') & L.key.isin(valid) & L.dry & (L.dvv >= MIN_DVV)]
    R['distributii'] = {'evenimente_primavara_aug': group_stats(E), 'ne_evenimente_primavara_aug': group_stats(spr_dry[spr_dry.dvv < MIN_DVV]),
                        'martor_ploaie_21_iul': group_stats(control), 'toamna_miriste_aug': group_stats(autumn_ev)}
    R['semnaturi'] = {k: {'n': int(len(g)), 'pct_din_evenimente': r2(100 * len(g) / len(E)), 'vh0_mediana': r2(g.vh0.median()), 'cr0_mediana': r2(g.cr0.median()),
                          'ndvi_iul_mediana_diagnostic': r2(g.ndvi_07.median()), 'ndvi_aug_mediana_diagnostic': r2(g.ndvi_08.median()),
                          'persistenta': persistence(g), **loss_stats(g.drop_duplicates('parcel_id').loss_rel)} for k, g in E.groupby('semnatura')}
    R['persistenta_martor_ploaie'] = persistence(control)
    R['placebo_toamna'] = placebo(L, low, high)
    R['placebo_toamna_doar_trecatoare'] = placebo_transient(L, low, high)

    # verificări: zgomot, două orbite, concentrare spațială, NDVI ca diagnostic
    A = L[L.spring & L.key.isin(AUGUST) & L.dry].copy()
    A['clasa_ha'] = pd.cut(A.area_ha, [0, 1, 2, 5, 10, 1e9], labels=['<1', '1-2', '2-5', '5-10', '>=10'], right=False)
    R['rata_pe_suprafata_pct'] = {str(k): r2(100 * (g.dvv >= MIN_DVV).mean()) for k, g in A.groupby('clasa_ha', observed=True)}
    n_spring = int(spring.dropna(subset=['vv_o7_20240802']).shape[0])
    R['doua_orbite'] = []
    for a, b in SAME_INTERVAL:
        x, y = set(E[E.key.eq(a)].parcel_id), set(E[E.key.eq(b)].parcel_id)
        R['doua_orbite'].append({'tranzitii': [a, b], 'evenimente': [len(x), len(y)], 'comune': len(x & y), 'la_intamplare': r2(len(x) * len(y) / n_spring)})
    B = L[L.key.isin(AUGUST) & L.dry].copy()
    B['ev'] = B.dvv >= MIN_DVV
    blocks = B.groupby(['key', 'block']).ev.agg(['sum', 'count']).reset_index()
    Em = E[E.key.isin(AUGUST)].merge(blocks, on=['key', 'block'])
    neighbours = (Em['sum'] - 1) / (Em['count'] - 1).clip(lower=1)
    R['concentrare_pe_blocuri'] = {'rata_globala_pct': r2(100 * B.ev.mean()), 'rata_vecinilor_pct_p50_p75_p90': [r2(100 * v) for v in np.percentile(neighbours, [50, 75, 90])],
                                   'pct_evenimente_cu_vecini_peste_15pct': r2(100 * (neighbours >= .15).mean())}
    P_ndvi = L[L.spring].drop_duplicates('parcel_id')
    event_ids = set(E.parcel_id)

    def ndvi_row(g):
        return {'n': int(len(g)), 'pct_iul_peste_05': r2(100 * (g.ndvi_07 >= .5).mean()), 'pct_iul_05_si_aug_04': r2(100 * ((g.ndvi_07 >= .5) & (g.ndvi_08 >= .4)).mean()),
                'pct_aug_sub_025': r2(100 * (g.ndvi_08 < .25).mean())}
    neirigat_ids = set(spring.parcel_id[base.eq('neirigat')])
    R['ndvi_doar_diagnostic'] = {'cu_eveniment': ndvi_row(P_ndvi[P_ndvi.parcel_id.isin(event_ids)]), 'neirigat_B': ndvi_row(P_ndvi[P_ndvi.parcel_id.isin(neirigat_ids)]),
                                 'pivot': ndvi_row(P_ndvi[P_ndvi.is_pivot])}

    # (c) Varianta C, alături de B; B nu se înlocuiește
    all_ids = set(E.parcel_id)
    assert (classes(spring, base, all_ids) == base.to_numpy()).all()
    other = {}
    for a, b in SAME_INTERVAL:
        other[a], other[b] = b, a
    wide = L[L.key.isin(AUGUST) & L.spring].pivot_table(index='parcel_id', columns='key', values='dvv')
    confirmed = E.apply(lambda e: e.key in other and wide.at[e.parcel_id, other[e.key]] >= MIN_DVV, axis=1)
    keep_c = set(E.parcel_id[E.semnatura.eq(LABEL_B)])
    keep_c1 = set(E.parcel_id[E.semnatura.ne(LABEL_A)])
    keep_c2 = set(E.parcel_id[E.semnatura.eq(LABEL_B) & confirmed])
    cls_c = classes(spring, base, keep_c)
    R['varianta_b_oficiala'] = compare(spring, base.to_numpy())
    R['varianta_c_propusa'] = compare(spring, cls_c)
    R['sensibilitate'] = {'C1_doar_dvh_nenegativ': compare(spring, classes(spring, base, keep_c1)),
                          'C2_C_plus_confirmat_pe_a_doua_orbita': compare(spring, classes(spring, base, keep_c2))}

    (OUT / 's1_events_diagnostic.json').write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding='utf-8')
    E[['parcel_id', 'key', 'orbit', 't1', 'dvv', 'dvh', 'dcr', 'vv0', 'vv1', 'vh0', 'vh1', 'cr0', 'cr1', 'semnatura', 'is_pivot']].to_parquet(INTERIM / 'q2_s1_events_2024.parquet')
    pd.DataFrame({'parcel_id': spring.parcel_id, 'clasa_b': base.to_numpy(), 'clasa_c': cls_c}).to_parquet(INTERIM / 'irrigation_2024_varianta_c.parquet')
    figure([(COLORS['primavara'], f"Primăvară, august: {len(E)} de evenimente", E),
            (COLORS['martor'], f'Martor: ploaia din 21 iulie, {thousands(len(control))} de parcele', control),
            (COLORS['toamna'], f'Placebo: toamnă, miriște în august, {thousands(len(autumn_ev))} de evenimente', autumn_ev)], low, high, OUT / 's1_events_diagnostic.png')

    print('reprodus B:', R['reproducere_varianta_b'])
    print('semnaturi:', {k: (v['n'], v['pct_din_evenimente'], v.get('mediana_pct')) for k, v in R['semnaturi'].items()})
    print('persistenta martor:', R['persistenta_martor_ploaie'])
    for k, v in R['semnaturi'].items():
        print(' persistenta', k, v['persistenta'])
    print('placebo:', {k: v for k, v in R['placebo_toamna'].items() if k != 'unitate'})
    print('placebo trecatoare:', {k: v for k, v in R['placebo_toamna_doar_trecatoare'].items() if k not in ('unitate', 'tranzitii')})
    for name in ('varianta_b_oficiala', 'varianta_c_propusa'):
        v = R[name]
        print(name, v['clase'], 'irigat', v['irigat'], 'neirigat', v['neirigat'], 'dif', v['diferenta_pp'], v['ic95_pp'])
    for name, v in R['sensibilitate'].items():
        print(name, v['clase']['irigat'], 'irigat', v['irigat']['median'], 'neirigat', v['neirigat']['median'], 'dif', v['diferenta_pp'], v['ic95_pp'])


if __name__ == '__main__':
    main()
