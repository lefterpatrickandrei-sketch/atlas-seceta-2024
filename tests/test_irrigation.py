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
