"""Calcule pentru harta-erou: încadrare, indicatori și culori (fără desen). Testate în tests/test_render.py."""
import numpy as np
from rasterio.transform import Affine

LOSS_MIN, LOSS_MAX = -0.2, 0.35     # scara hărții, în unități NDVI (pierdere > 0, câștig < 0)
HIGH_LOSS = 0.2                     # peste acest prag, pierdere mare
_STOPS = [(LOSS_MIN, (34, 158, 132)), (-0.06, (86, 136, 128)), (0.0, (126, 130, 136)), (0.1, (194, 142, 86)),
          (0.2, (232, 124, 44)), (LOSS_MAX, (246, 84, 36))]


def fit_frame(bounds, width, height):
    """Transformare nord-sus care încape `bounds` într-un cadru de `width`×`height` pixeli, centrat, cu o singură scară."""
    west, south, east, north = bounds
    pixel = max((east - west) / width, (north - south) / height)
    x0 = (west + east) / 2 - pixel * width / 2
    y0 = (south + north) / 2 + pixel * height / 2
    return Affine(pixel, 0, x0, 0, -pixel, y0), pixel


def hero_kpis(df):
    """Indicatorii din panou, din coloanele area_ha și loss_obs."""
    high = df.loss_obs >= HIGH_LOSS
    return dict(n=len(df), ha=float(df.area_ha.sum()), median_loss=float(df.loss_obs.median()),
                ha_high=float(df.area_ha[high].sum()), share_high=float(df.area_ha[high].sum() / df.area_ha.sum()))


def loss_rgb(values):
    """Culoarea fiecărei valori de pierdere (uint8, N×3): gri la zero, portocaliu pentru pierdere, verde-albăstrui pentru câștig."""
    xs = [p for p, _ in _STOPS]
    v = np.clip(np.asarray(values, dtype=float), LOSS_MIN, LOSS_MAX)
    return np.stack([np.interp(v, xs, [c[i] for _, c in _STOPS]) for i in range(3)], axis=1).round().astype(np.uint8)


def loss_histogram(values, step=0.05):
    """Histogramă pe scara hărții; valorile din afara scării intră în clasele de la margine."""
    edges = np.arange(LOSS_MIN, LOSS_MAX + step / 2, step)
    counts, _ = np.histogram(np.clip(values, edges[0], edges[-1]), bins=edges)
    return edges, counts
