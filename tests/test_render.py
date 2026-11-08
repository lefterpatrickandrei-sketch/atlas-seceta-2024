"""Teste pentru utilitarele de randare."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'render'))
import common  # noqa: E402


@pytest.mark.parametrize('weight, display', [('Regular', False), ('Medium', False), ('SemiBold', False), ('Bold', False),
                                             ('Regular', True), ('Medium', True), ('SemiBold', True), ('Bold', True)])
def test_inter_fonts_load_on_this_machine(weight, display):
    assert common.F(24, weight, display=display).getname()[0].startswith('Inter')


# ---- Calculele hărții-erou ------------------------------------------------------------------------------------------
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import atlas  # noqa: E402


def test_fit_frame_uses_one_scale_and_centres_the_area():
    transform, pixel = atlas.fit_frame((0, 0, 1000, 500), 200, 200)
    assert pixel == pytest.approx(5.0)
    assert (transform.a, transform.e) == pytest.approx((5.0, -5.0))
    assert ~transform @ (0, 500) == pytest.approx((0.0, 50.0))


def test_fit_frame_is_limited_by_the_tighter_side():
    _, pixel = atlas.fit_frame((0, 0, 100, 1000), 200, 200)
    assert pixel == pytest.approx(5.0)


def test_hero_kpis_summarise_area_and_high_loss():
    df = pd.DataFrame({'area_ha': [10.0, 10.0, 20.0], 'loss_obs': [0.1, 0.3, 0.25]})
    k = atlas.hero_kpis(df)
    assert (k['n'], k['ha'], k['ha_high']) == (3, 40.0, 30.0)
    assert k['median_loss'] == pytest.approx(0.25)
    assert k['share_high'] == pytest.approx(0.75)


def test_loss_colors_are_neutral_at_zero_warm_for_loss_and_cool_for_gain():
    neutral, loss, gain = atlas.loss_rgb(np.array([0.0, 0.3, -0.2]))
    assert max(neutral) - min(neutral) < 16
    assert loss[0] > loss[2] + 100
    assert gain[1] > gain[0] + 60


def test_loss_colors_clamp_outside_the_scale():
    low, high, top = atlas.loss_rgb(np.array([-9.0, 9.0, atlas.LOSS_MAX]))
    assert tuple(high) == tuple(top)
    assert tuple(low) == tuple(atlas.loss_rgb(np.array([atlas.LOSS_MIN]))[0])


def test_histogram_counts_values_beyond_the_scale_in_the_edge_bins():
    edges, counts = atlas.loss_histogram(np.array([-1.0, 0.0, 0.01, 2.0]), step=0.1)
    assert counts.sum() == 4
    assert counts[0] == 1 and counts[-1] == 1
    assert len(edges) == len(counts) + 1
