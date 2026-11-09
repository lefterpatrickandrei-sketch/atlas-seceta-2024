"""Teste pentru selecția parcelelor de etichetat (irigat 2024): doar culturi de primăvară, strat pe NDVI, răspândite în spațiu."""
import numpy as np
import pandas as pd

import gisday_lib as gl


def table(n=2000, blocks=100, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        'parcel_id': np.arange(1, n + 1),
        'is_arable': True,
        'crop_group_2024': 'primavara',
        'area_ha': 5.0,
        'ndvi_ja_2024': rng.uniform(0.1, 0.8, n),
        'block': rng.integers(0, blocks, n).astype(str),
    })


def test_selects_the_requested_number_per_class():
    out = gl.select_label_candidates(table(), n_high=120, n_low=120, n_mid=60)
    assert out.hint.value_counts().to_dict() == {'probabil_irigat': 120, 'probabil_neirigat': 120, 'nesigur': 60}


def test_keeps_only_arable_spring_crops_of_at_least_one_hectare():
    t = table(30, blocks=3)
    t.loc[0, 'is_arable'] = False
    t.loc[1, 'crop_group_2024'] = 'toamna'
    t.loc[2, 'area_ha'] = 0.7
    out = gl.select_label_candidates(t, n_high=30, n_low=30, n_mid=30, max_per_block=30)
    assert not set(out.parcel_id) & {1, 2, 3}


def test_likely_irrigated_are_greener_than_likely_not():
    t = table()
    out = t.merge(gl.select_label_candidates(t), on='parcel_id')
    assert out[out.hint == 'probabil_irigat'].ndvi_ja_2024.min() > out[out.hint == 'probabil_neirigat'].ndvi_ja_2024.max()


def test_limits_parcels_per_block():
    t = table()
    out = t.merge(gl.select_label_candidates(t, max_per_block=4), on='parcel_id')
    assert out.groupby('block').size().max() <= 4


def test_a_parcel_is_selected_once_and_the_label_starts_empty():
    out = gl.select_label_candidates(table())
    assert out.parcel_id.is_unique
    assert out.irigat.isna().all()


def test_selection_is_repeatable():
    t = table()
    assert gl.select_label_candidates(t).equals(gl.select_label_candidates(t))


def test_select_validation_80_balances_classes_across_blocks():
    df = pd.DataFrame({
        'parcel_id': np.arange(1, 201),
        'area_ha': 3.0,
        'clasa_irigare': np.where(np.arange(200) < 100, 'irigat', 'neirigat'),
        'block': [f'b_{i % 50}' for i in range(200)],
    })
    out = gl.select_validation_80(df, n_per_class=40, max_per_block=1)
    assert len(out) == 80
    assert out.clasa_regula.value_counts().to_dict() == {'irigat': 40, 'neirigat': 40}
    assert out.irigat.isna().all()

