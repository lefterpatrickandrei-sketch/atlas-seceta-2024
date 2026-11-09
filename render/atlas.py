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


# ---- Scară fixă în 6 clase procentuale pentru loss_rel × 100 (PAS D-B) ----
LOSS_CLASS_BINS = (0.0, 10.0, 25.0, 40.0, 55.0)
LOSS_CLASS_LABELS = ('câștig (< 0%)', '0–10%', '10–25%', '25–40%', '40–55%', '> 55%')
LOSS_CLASS_COLORS = np.array([
    (36, 162, 134),   # < 0% (câștig): verde-turcoaz
    (138, 148, 152),  # 0–10%: gri-neutru cald
    (204, 162, 84),   # 10–25%: ocru-galben
    (232, 128, 48),   # 25–40%: portocaliu
    (228, 78, 38),    # 40–55%: roșu-portocaliu
    (178, 34, 38),    # > 55%: roșu intens
], dtype=np.uint8)
NO_REF_COLOR = (82, 90, 102)
NON_ARABLE_OUTLINE = (92, 100, 110)


def loss_class_index(loss_rel):
    """Returnează indexul clasei (0..5) pentru vectorul `loss_rel` (fracție, ex. 0.30 = 30%)."""
    v = np.asarray(loss_rel, dtype=float)
    # < 0 -> 0; [0, 0.10) -> 1; [0.10, 0.25) -> 2; [0.25, 0.40) -> 3; [0.40, 0.55] -> 4; > 0.55 -> 5
    idx = np.zeros(v.shape, dtype=np.int32)
    idx[v >= 0.0] = 1
    idx[v >= 0.10] = 2
    idx[v >= 0.25] = 3
    idx[v >= 0.40] = 4
    idx[v > 0.55] = 5
    return idx


def loss_class_label(loss_rel):
    """Returnează eticheta clasei pentru fiecare valoare din `loss_rel`."""
    idx = loss_class_index(loss_rel)
    return np.asarray(LOSS_CLASS_LABELS, dtype=object)[idx]


def loss_class_rgb(loss_rel):
    """Returnează culoarea RGB (uint8, N×3) a clasei fixe pentru fiecare valoare din `loss_rel`."""
    idx = loss_class_index(loss_rel)
    return LOSS_CLASS_COLORS[idx]
