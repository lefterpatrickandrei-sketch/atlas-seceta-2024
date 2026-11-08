"""Teste pentru expunerea la vânt: raster sintetic de 1 km la 5 m, o parcelă pătrată de 200 m în mijloc."""
import geopandas as gpd
import numpy as np
import pytest
from rasterio.transform import from_origin
from shapely.geometry import box

import gisday_lib as gl

RES = 5.0
SIZE = 200          # pixeli
WEST_WIND = 270     # vântul bate dinspre vest: amonte = spre x mai mic
EAST_WIND = 90
TRANSFORM = from_origin(0, 1000, RES, RES)
PARCEL = gpd.GeoDataFrame({'parcel_id': [1]}, geometry=[box(400, 400, 600, 600)], crs='EPSG:3844')


def woody():
    return np.zeros((SIZE, SIZE), dtype=bool)


def wall(mask, x_m, y0_m=0, y1_m=1000):
    """Perdea verticală (lată de 10 m) la x_m, între y0_m și y1_m."""
    col0, col1 = int(x_m / RES), int((x_m + 10) / RES)
    row0, row1 = int((1000 - y1_m) / RES), int((1000 - y0_m) / RES)
    mask[row0:row1, col0:col1] = True
    return mask


def exposure(mask, dirs=(WEST_WIND,), weights=(1.0,)):
    return gl.wind_exposure(PARCEL, mask, TRANSFORM, dirs, weights).iloc[0]


def test_parcel_without_woody_elements_is_fully_exposed():
    assert exposure(woody()) == pytest.approx(1.0)


def test_wall_just_upwind_shelters_the_parcel():
    assert exposure(wall(woody(), 380)) == pytest.approx(0.0)


def test_wall_downwind_gives_no_shelter():
    assert exposure(wall(woody(), 620)) == pytest.approx(1.0)


def test_wall_beyond_the_reach_gives_no_shelter():
    assert exposure(wall(woody(), 60)) == pytest.approx(1.0)


def test_wall_along_half_of_the_upwind_edge_shelters_half():
    assert exposure(wall(woody(), 380, y0_m=500, y1_m=1000)) == pytest.approx(0.5, abs=0.08)


def test_directions_are_weighted_by_the_wind_rose():
    assert exposure(wall(woody(), 380), dirs=(WEST_WIND, EAST_WIND), weights=(0.75, 0.25)) == pytest.approx(0.25)


def test_weights_are_normalised():
    assert exposure(wall(woody(), 380), dirs=(WEST_WIND, EAST_WIND), weights=(3, 1)) == pytest.approx(0.25)


def test_points_outside_the_raster_count_as_unsheltered():
    parcel = gpd.GeoDataFrame({'parcel_id': [1]}, geometry=[box(0, 400, 200, 600)], crs='EPSG:3844')
    assert gl.wind_exposure(parcel, woody(), TRANSFORM, (WEST_WIND,), (1.0,)).iloc[0] == pytest.approx(1.0)


def test_result_keeps_the_parcel_index():
    parcels = PARCEL.copy()
    parcels.index = [42]
    assert gl.wind_exposure(parcels, woody(), TRANSFORM, (WEST_WIND,), (1.0,)).index.tolist() == [42]


# ---- Roza vânturilor --------------------------------------------------------------------------------------------------
def test_wind_rose_puts_a_west_wind_in_the_270_sector():
    rose = gl.wind_rose(np.array([5.0]), np.array([0.0]))     # u > 0 = aerul se mișcă spre est, deci bate dinspre vest
    assert rose[270.0] == pytest.approx(1.0)


def test_wind_rose_returns_shares_of_hours():
    rose = gl.wind_rose(np.array([5.0, 5.0, 5.0, 0.0]), np.array([0.0, 0.0, 0.0, -3.0]))    # v < 0 = dinspre nord
    assert rose[270.0] == pytest.approx(0.75)
    assert rose[0.0] == pytest.approx(0.25)


def test_wind_rose_wraps_northerly_directions_into_the_zero_sector():
    az = np.radians(355.0)
    rose = gl.wind_rose(np.array([-np.sin(az)]), np.array([-np.cos(az)]))
    assert rose[0.0] == pytest.approx(1.0)


def test_exposure_stays_within_bounds_with_rounded_weights():
    dirs = (67.5, 90.0, 112.5, 135.0, 292.5, 45.0, 22.5)
    weights = (0.084, 0.238, 0.253, 0.093, 0.075, 0.035, 0.027)
    assert gl.wind_exposure(PARCEL, woody(), TRANSFORM, dirs, weights).iloc[0] <= 1.0
