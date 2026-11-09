"""Teste pentru validarea pe blocuri a clasificatorului de irigare."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import f1_score

import gisday_lib as gl


def synthetic(n=240, blocks=24, seed=1):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, n)
    X = pd.DataFrame({'ndvi_07': y * 0.5 + rng.normal(0.25, 0.05, n), 'zgomot': rng.normal(0, 1, n)})
    groups = pd.Series(rng.integers(0, blocks, n).astype(str))
    return X, pd.Series(y), groups


def test_out_of_fold_probabilities_cover_every_parcel():
    X, y, groups = synthetic()
    assert len(gl.out_of_fold_probabilities(X, y, groups)) == len(y)


def test_separable_labels_are_recovered_on_unseen_blocks():
    X, y, groups = synthetic()
    p = gl.out_of_fold_probabilities(X, y, groups)
    assert f1_score(y, p >= 0.5) >= 0.9


def test_a_block_is_never_in_train_and_test_together():
    X, y, groups = synthetic()
    for train, test in gl.block_folds(y, groups):
        assert not set(groups.iloc[train]) & set(groups.iloc[test])


def test_too_few_labels_of_one_class_stop_with_a_clear_message():
    X, y, groups = synthetic(n=40, blocks=10)
    y = pd.Series(np.r_[np.ones(3, dtype=int), np.zeros(37, dtype=int)])
    with pytest.raises(ValueError, match='etichete'):
        gl.out_of_fold_probabilities(X, y, groups)


def test_geometric_pivots_detects_circular_fields_above_five_hectares():
    from shapely.geometry import Point, box
    circle_10ha = Point(0, 0).buffer(np.sqrt(100000.0 / np.pi), quad_segs=64)
    thin_strip = box(0, 0, 2000, 50)
    small_circle = Point(0, 0).buffer(np.sqrt(20000.0 / np.pi), quad_segs=64)
    out = gl.geometric_pivots(pd.Series([circle_10ha, thin_strip, small_circle]))
    assert list(out['is_pivot']) == [True, False, False]


def test_s1_spring_irrigation_rule_classifies_irrigated_unirrigated_and_undetermined():
    dates = pd.date_range('2024-06-01', '2024-08-31', freq='D')
    df = pd.DataFrame({f"rain_{d.strftime('%Y%m%d')}": 0.0 for d in dates}, index=[0, 1, 2])
    df['is_pivot'] = [False, False, False]
    # 3 tranziții consecutive de 12 zile pe orbita 7 (iun–iul 2024)
    df['vv_o7_20240603'] = [-12.0, -12.0, -12.0]
    df['vv_o7_20240615'] = [-10.0, -11.8, -11.0]   # parcela 0: +2.0 dB (eveniment), parcela 1: +0.2 dB, parcela 2: +1.0 dB (>= 0.8 dB)
    df['vv_o7_20240627'] = [-11.5, -11.7, -11.2]
    df['vv_o7_20240709'] = [-11.6, -11.8, -11.3]
    tr, res = gl.s1_spring_irrigation_rule(df)
    assert len(tr) == 3
    assert list(res['clasa_irigare']) == ['irigat', 'neirigat', 'nedeterminat']

