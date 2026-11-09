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


def test_read_validation_labels_csv_accepts_comma_and_semicolon(tmp_path):
    p_comma = tmp_path / 'comma.csv'
    p_semi = tmp_path / 'semi.csv'
    p_comma.write_text('id,irigat\n101,1\n102,0\n103,\n', encoding='utf-8')
    p_semi.write_text('id;irigat\n101;1\n102;0\n103;\n', encoding='utf-8')
    df_c = gl.read_validation_labels_csv(p_comma)
    df_s = gl.read_validation_labels_csv(p_semi)
    assert df_c.equals(df_s)
    assert list(df_c['parcel_id']) == [101, 102, 103]
    assert int(df_c.loc[0, 'irigat']) == 1 and int(df_c.loc[1, 'irigat']) == 0 and pd.isna(df_c.loc[2, 'irigat'])


def test_olofsson_evaluation_weights_overall_and_producer_accuracy():
    y_map = ['irigat'] * 40 + ['neirigat'] * 40
    # 32/40 = 80% pe irigat, 38/40 = 95% pe neirigat
    y_ref = [1] * 32 + [0] * 8 + [0] * 38 + [1] * 2
    res = gl.olofsson_evaluation(y_map, y_ref, {'irigat': 600, 'neirigat': 4400})
    assert res['user_accuracy']['irigat']['est'] == pytest.approx(0.80)
    assert res['user_accuracy']['neirigat']['est'] == pytest.approx(0.95)
    # W_irigat = 0.12, W_neirigat = 0.88 -> OA = 0.12*0.80 + 0.88*0.95 = 0.932
    assert res['overall_accuracy']['est'] == pytest.approx(0.12 * 0.80 + 0.88 * 0.95)
    # p_11 = 0.12*0.80 = 0.096, p_21 = 0.88*(2/40) = 0.044 -> Recall irigat = 0.096 / (0.096 + 0.044)
    assert res['producer_accuracy']['irigat']['est'] == pytest.approx(0.096 / 0.140)


def test_block_bootstrap_median_diff_returns_medians_and_ci():
    df = pd.DataFrame({
        'clasa_irigare': ['irigat'] * 20 + ['neirigat'] * 20,
        'loss_rel': [0.20] * 20 + [0.35] * 20,
        'block': [f'b_{i % 5}' for i in range(40)],
    })
    out = gl.block_bootstrap_median_diff(df, n_boot=200, seed=1)
    assert out['irigat']['median'] == pytest.approx(0.20)
    assert out['neirigat']['median'] == pytest.approx(0.35)
    assert out['diff_median_pos_minus_neg'] == pytest.approx(-0.15)


