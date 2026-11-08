"""Teste pentru ținta care compară fiecare parcelă doar cu anii în care a avut același tip de cultură."""
import numpy as np
import pandas as pd
import pytest

import gisday_lib as gl

YEARS = [2020, 2021, 2022, 2023]


def table(values, groups):
    """values / groups: câte o listă pentru anii 2020–2024, pentru o singură parcelă."""
    row = {}
    for y, v, g in zip(YEARS + [2024], values, groups):
        row[f'v_{y}'] = v
        row[f'g_{y}'] = g
    return pd.DataFrame([row])


def loss(values, groups, **kw):
    return gl.like_for_like_loss(table(values, groups), 'v_{y}', 'g_{y}', 2024, YEARS, **kw).iloc[0]


P, T, N = 'primavara', 'toamna', 'neclasificat'


# ---- tipul de cultură din NDVI-ul din aprilie ----------------------------------------------------------------------------
@pytest.mark.parametrize('ndvi, expected', [(0.6, T), (0.5, T), (0.2, P), (0.349, P), (0.35, N), (0.45, N), (np.nan, N)])
def test_crop_group_uses_april_ndvi_thresholds(ndvi, expected):
    assert gl.crop_group(pd.Series([ndvi])).iloc[0] == expected


# ---- pierderea comparată cu ani de același tip -----------------------------------------------------------------------------
def test_loss_uses_only_years_with_the_same_crop_group():
    r = loss([0.65, 0.20, 0.55, 0.20, 0.35], [P, T, P, T, P])
    assert r.ref == pytest.approx(0.60)
    assert r.loss_obs == pytest.approx(0.25)
    assert r.n_ref_years == 2


def test_loss_is_expressed_also_as_percent_of_the_reference():
    assert loss([0.60, 0.20, 0.60, 0.20, 0.30], [P, T, P, T, P]).loss_pct == pytest.approx(50.0)


def test_loss_needs_at_least_two_reference_years():
    r = loss([0.65, 0.20, 0.20, 0.20, 0.35], [P, T, T, T, P])
    assert np.isnan(r.loss_obs) and r.n_ref_years == 1


def test_reference_year_without_data_is_not_counted():
    r = loss([0.60, np.nan, 0.70, 0.20, 0.35], [P, P, P, T, P])
    assert r.ref == pytest.approx(0.65)
    assert r.n_ref_years == 2


def test_loss_is_nan_when_the_target_year_is_unclassified():
    assert np.isnan(loss([0.6, 0.6, 0.6, 0.6, 0.3], [N, N, N, N, N]).loss_obs)


def test_loss_is_nan_when_the_target_value_is_missing():
    assert np.isnan(loss([0.6, 0.6, 0.6, 0.6, np.nan], [P, P, P, P, P]).loss_obs)


def test_only_groups_leaves_other_groups_without_a_loss():
    r = loss([0.6, 0.6, 0.6, 0.6, 0.3], [T, T, T, T, T], only_groups={P})
    assert np.isnan(r.loss_obs)


# ---- controlul pe EUCROPMAP ---------------------------------------------------------------------------------------------
def test_agreement_counts_only_parcels_with_a_known_season():
    groups = pd.Series([T, P, T, P, N])
    codes = pd.Series([211, 216, 216, 500, 211])     # grâu=toamnă, porumb=primăvară, porumb greșit, pajiște ignorată, neclasificat ignorat
    share, n = gl.crop_group_agreement(groups, codes)
    assert n == 3
    assert share == pytest.approx(2 / 3)
