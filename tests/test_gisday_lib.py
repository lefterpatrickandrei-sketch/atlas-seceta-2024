"""Teste pentru logica din gisday_lib.py. Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -m pytest tests -q"""
from types import SimpleNamespace

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

import gisday_lib as gl

AOI = (23.85, 43.70, 24.55, 44.00)


def item(tile, geom, cloud=1.0):
    return SimpleNamespace(geometry=mapping(geom), properties={'s2:mgrs_tile': tile, 'eo:cloud_cover': cloud})


# ---- FTW: cererea rasterului și alegerea scenelor -------------------------------------------------------------------
def test_ftw_bbox_leaves_margin_larger_than_the_lost_top_row():
    west, south, east, north = gl.ftw_request_bbox(box(20, 40, 28, 48), AOI)
    assert north == pytest.approx(44.12)
    assert (west, south, east) == pytest.approx((23.83, 43.68, 24.57))


def test_ftw_bbox_is_clipped_to_the_scene_footprint():
    assert gl.ftw_request_bbox(box(24.0, 43.75, 24.3, 44.05), AOI) == pytest.approx((24.0, 43.75, 24.3, 44.05))


def test_ftw_bbox_rejects_a_scene_outside_the_area():
    with pytest.raises(ValueError):
        gl.ftw_request_bbox(box(10, 10, 11, 11), AOI)


def test_best_scenes_prefers_coverage_then_low_cloud():
    full_cloudy = item('34TGP', box(*AOI), cloud=9)
    full_clear = item('34TGP', box(*AOI), cloud=2)
    sliver_clear = item('34TGP', box(24.5, 43.7, 24.55, 44.0), cloud=0)
    assert gl.best_scenes([sliver_clear, full_cloudy, full_clear], AOI)['34TGP'] is full_clear


def test_select_tiles_drops_a_tile_that_adds_no_new_area():
    a = {'34TGP': item('34TGP', box(*AOI)), '35TLJ': item('35TLJ', box(24.5, 43.7, 24.55, 44.0))}
    assert gl.select_tiles(a, a, AOI) == ['34TGP']


def test_select_tiles_keeps_both_halves_when_each_adds_area():
    west = box(23.85, 43.7, 24.25, 44.0)
    east = box(24.15, 43.7, 24.55, 44.0)
    a = {'W': item('W', west), 'E': item('E', east)}
    assert sorted(gl.select_tiles(a, a, AOI)) == ['E', 'W']


def test_select_tiles_uses_the_overlap_of_both_windows():
    a = {'34TGP': item('34TGP', box(*AOI))}
    b = {'34TGP': item('34TGP', box(23.85, 43.7, 23.86, 43.71))}
    assert gl.select_tiles(a, b, AOI) == []


def write_stack(path, margin_px, res=10.0):
    """Raster UTM 34 a cărui margine de nord e cu `margin_px` pixeli peste colțul cel mai nordic al zonei."""
    fwd = Transformer.from_crs(4326, 32634, always_xy=True)
    top_aoi = max(fwd.transform(x, AOI[3])[1] for x in (AOI[0], AOI[2]))
    x0, _ = fwd.transform(AOI[0], AOI[3])
    profile = dict(driver='GTiff', width=4, height=4, count=1, dtype='uint8', crs='EPSG:32634',
                   transform=from_origin(x0, top_aoi + margin_px * res, res, res))
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(np.zeros((1, 4, 4), dtype='uint8'))


def test_north_margin_measures_pixels_above_the_area(tmp_path):
    write_stack(tmp_path / 'stack.tif', margin_px=1000)
    assert gl.north_margin_px(tmp_path / 'stack.tif', AOI) == pytest.approx(1000, abs=1)


def scene(geom):
    return SimpleNamespace(id='X', geometry=mapping(geom))


def test_run_ftw_tile_reuses_existing_polygons(tmp_path, monkeypatch):
    poly = tmp_path / 'ftw_poly_34TGP_v2.parquet'
    poly.write_bytes(b'x')
    monkeypatch.setattr(gl.subprocess, 'run', lambda *a, **k: pytest.fail('nu trebuie rulat ftw'))
    assert gl.run_ftw_tile('ftw', '34TGP', scene(box(*AOI)), scene(box(*AOI)), 'ck', tmp_path, AOI, 'v2') == poly


def test_run_ftw_tile_stops_before_inference_without_north_margin(tmp_path, monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        write_stack(tmp_path / 'ftw_in_34TGP_v2.tif', margin_px=100)
        return SimpleNamespace(stdout='', stderr='', returncode=0)

    monkeypatch.setattr(gl.subprocess, 'run', fake_run)
    with pytest.raises(AssertionError, match='marj'):
        gl.run_ftw_tile('ftw', '34TGP', scene(box(*AOI)), scene(box(*AOI)), 'ck', tmp_path, AOI, 'v2')
    assert [c[1:3] for c in calls] == [['inference', 'download']]


# ---- Verificarea acoperirii ------------------------------------------------------------------------------------------
def cells_and_parcels():
    cells = gpd.GeoDataFrame({'x': [0, 1]}, geometry=[box(0, 0, 1000, 1000), box(1000, 0, 2000, 1000)], crs='EPSG:3844')
    parcels = gpd.GeoDataFrame(geometry=[box(500, 0, 1500, 1000)], crs='EPSG:3844')
    return cells, parcels


def test_parcel_coverage_splits_a_parcel_between_cells():
    cells, parcels = cells_and_parcels()
    assert gl.parcel_coverage(parcels, cells).tolist() == pytest.approx([0.5, 0.5])


def test_parcel_coverage_is_zero_for_an_empty_cell():
    cells, _ = cells_and_parcels()
    parcels = gpd.GeoDataFrame(geometry=[box(0, 0, 100, 100)], crs='EPSG:3844')
    assert gl.parcel_coverage(parcels, cells).tolist() == pytest.approx([0.01, 0.0])


def test_coverage_gaps_flags_only_big_arable_cells_with_low_coverage():
    t = pd.DataFrame({'arabil_km2': [10, 10, 2], 'parcele_km2': [1, 5, 0]})
    assert gl.coverage_gaps(t).index.tolist() == [0]


# ---- Amprenta pentru cache-ul Earth Engine -----------------------------------------------------------------------------
def fingerprint_parcels(x1=100):
    return gpd.GeoDataFrame({'parcel_id': [1, 2]}, geometry=[box(0, 0, x1, 100), box(200, 0, 300, 100)], crs='EPSG:3844')


def test_fingerprint_is_stable_for_the_same_input():
    assert gl.fingerprint(fingerprint_parcels(), ['a', 'b']) == gl.fingerprint(fingerprint_parcels(), ['a', 'b'])


def test_fingerprint_changes_when_a_parcel_changes():
    assert gl.fingerprint(fingerprint_parcels(), ['a']) != gl.fingerprint(fingerprint_parcels(x1=101), ['a'])


def test_fingerprint_changes_when_the_band_list_changes():
    assert gl.fingerprint(fingerprint_parcels(), ['a']) != gl.fingerprint(fingerprint_parcels(), ['a', 'b'])


# ---- Canale OSM ------------------------------------------------------------------------------------------------------
def test_overpass_ways_become_lines_and_skip_elements_without_geometry():
    elements = [
        {'tags': {'waterway': 'canal', 'usage': 'irrigation'}, 'geometry': [{'lon': 24.0, 'lat': 43.8}, {'lon': 24.1, 'lat': 43.8}]},
        {'tags': {'waterway': 'ditch'}, 'geometry': [{'lon': 24.0, 'lat': 43.9}]},
        {'tags': {'waterway': 'drain'}},
    ]
    w = gl.overpass_ways_to_gdf(elements)
    assert w.crs.to_epsg() == 4326
    assert w.waterway.tolist() == ['canal']
    assert w.usage.tolist() == ['irrigation']


def test_canal_distances_separate_canals_from_the_whole_network():
    from shapely.geometry import LineString
    parcels = gpd.GeoDataFrame({'parcel_id': [7]}, geometry=[box(0, 0, 100, 100)], crs='EPSG:3844')
    ways = gpd.GeoDataFrame({'waterway': ['canal', 'ditch']}, geometry=[LineString([(1100, 0), (1100, 100)]), LineString([(300, 0), (300, 100)])], crs='EPSG:3844')
    out = gl.canal_distances(parcels, ways)
    assert out.parcel_id.tolist() == [7]
    assert out.dist_canal_m.iloc[0] == pytest.approx(1000)
    assert out.dist_network_m.iloc[0] == pytest.approx(200)


def test_canal_distance_is_zero_for_a_parcel_crossed_by_a_canal():
    from shapely.geometry import LineString
    parcels = gpd.GeoDataFrame({'parcel_id': [1]}, geometry=[box(0, 0, 100, 100)], crs='EPSG:3844')
    ways = gpd.GeoDataFrame({'waterway': ['canal']}, geometry=[LineString([(50, -10), (50, 110)])], crs='EPSG:3844')
    assert gl.canal_distances(parcels, ways).dist_canal_m.iloc[0] == 0


def _fake_post(codes):
    calls = iter(codes)

    def post(url, **kwargs):
        code = next(calls)
        return SimpleNamespace(status_code=code, json=lambda: {'elements': [{'id': 1}]})
    return post


def test_overpass_moves_to_the_next_server_when_one_is_busy():
    assert gl.overpass_elements('q', mirrors=['a', 'b'], wait_s=0, post=_fake_post([502, 200])) == [{'id': 1}]


def test_overpass_raises_after_all_attempts_fail():
    with pytest.raises(RuntimeError, match='502'):
        gl.overpass_elements('q', mirrors=['a'], tries=2, wait_s=0, post=_fake_post([502, 502]))


def test_overpass_treats_a_timeout_as_a_busy_server():
    import requests
    calls = iter([requests.exceptions.ReadTimeout('lent'), SimpleNamespace(status_code=200, json=lambda: {'elements': [{'id': 2}]})])

    def post(url, **kwargs):
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    assert gl.overpass_elements('q', mirrors=['a', 'b'], wait_s=0, post=post) == [{'id': 2}]
