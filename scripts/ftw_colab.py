"""Partea GPU din notebooks/02_parcels_ftw.ipynb, de rulat pe Colab. Nu folosește credențiale.

Pași (din rădăcina proiectului):
  colab new -s gisday-ftw --gpu A100
  colab upload -s gisday-ftw gisday_config.py /content/gisday_config.py
  colab upload -s gisday-ftw gisday_lib.py /content/gisday_lib.py
  colab exec -s gisday-ftw -f scripts/ftw_colab.py
  colab download -s gisday-ftw /content/data/interim/ftw_poly_<tile>_<run>.parquet data/interim/ftw_poly_<tile>_<run>.parquet
  colab stop -s gisday-ftw
"""
import os
import subprocess
import sys

sys.path.insert(0, '/content')
os.chdir('/content')
os.environ['MPLBACKEND'] = 'Agg'   # altfel subprocesele ftw moștenesc backend-ul Jupyter și cad

from gisday_config import AOI_BBOX, FTW_PKGS, FTW_RUN, FTW_WIN_A, FTW_WIN_B, INTERIM  # noqa: E402

FTW_ENV = '/content/ftwenv'
FTW = f'{FTW_ENV}/bin/ftw'
CKPT = INTERIM / '3_Class_FULL_FTW_Pretrained.ckpt'

subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'uv', 'pystac-client', 'planetary-computer', 'rasterio', 'pyproj', 'shapely'],
               check=True)
if not os.path.exists(FTW):
    subprocess.run([sys.executable, '-m', 'uv', 'venv', '--clear', '--python', '3.12', FTW_ENV], check=True)
    subprocess.run([sys.executable, '-m', 'uv', 'pip', 'install', '-q', '--python', f'{FTW_ENV}/bin/python', *FTW_PKGS], check=True)
if not CKPT.exists():
    subprocess.run([FTW, 'model', 'download', '--type', 'THREE_CLASS_FULL', '--out', str(CKPT)], check=True)
print(subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], capture_output=True, text=True).stdout)

import planetary_computer  # noqa: E402
import pystac_client  # noqa: E402
from gisday_lib import best_scenes, run_ftw_tile, select_tiles  # noqa: E402

catalog = pystac_client.Client.open('https://planetarycomputer.microsoft.com/api/stac/v1', modifier=planetary_computer.sign_inplace)


def scenes(window):
    items = catalog.search(collections=['sentinel-2-l2a'], bbox=AOI_BBOX, datetime=window, query={'eo:cloud_cover': {'lt': 10}}).item_collection()
    return best_scenes(items, AOI_BBOX)


A, B = scenes(FTW_WIN_A), scenes(FTW_WIN_B)
for tile in select_tiles(A, B, AOI_BBOX):
    base_a, base_b = (s.properties.get('s2:processing_baseline') for s in (A[tile], B[tile]))
    assert base_a == base_b, f'{tile}: versiuni de procesare diferite ({base_a} vs {base_b})'
    print(tile, A[tile].id, base_a, '|', B[tile].id, base_b, flush=True)
    poly = run_ftw_tile(FTW, tile, A[tile], B[tile], CKPT, INTERIM, AOI_BBOX, FTW_RUN)
    print('POLY', poly, f'{poly.stat().st_size / 1024:.0f} KB', flush=True)
