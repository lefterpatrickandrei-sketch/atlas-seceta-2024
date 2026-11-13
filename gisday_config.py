"""Configurare comună pentru toate notebook-urile GIS Day 2026 — Atlasul vulnerabilității la secetă."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
RAW = DATA / 'raw'            # descărcări mari (HR-VPP, SLF, Sentinel) — nu intră în git
INTERIM = DATA / 'interim'    # rezultate intermediare — nu intră în git
OUT = DATA / 'out'            # rezultate finale mici (GeoParquet, CSV) — intră în git
PRIVATE = DATA / 'private'    # LUCAS 2018 Topsoil — licență personală, doar în repo privat
for _p in (RAW, INTERIM, OUT, PRIVATE):
    _p.mkdir(parents=True, exist_ok=True)

# Earth Engine: ID-ul proiectului Cloud înregistrat necomercial (nivel Community)
GEE_PROJECT = 'gisday2026'

# Zona: Sadova – Bechet – Dăbuleni – Corabia (sudul Olteniei), dreptunghi aproximativ, WGS84.
# Se taie la granița României în notebook-uri (malul bulgăresc al Dunării iese din calcul).
AOI_BBOX = (23.85, 43.70, 24.55, 44.00)   # lon_min, lat_min, lon_max, lat_max

CRS = 'EPSG:3844'             # Stereo 70 pentru toate livrabilele
YEAR = 2024                   # sezonul secetei
BASE_YEARS = list(range(2017, 2024))   # referința pentru anomalii

# Fields of The World: ferestrele Sentinel-2 și versiunile testate împreună (02_parcels_ftw, scripts/ftw_colab.py)
FTW_WIN_A = f'{YEAR}-04-01/{YEAR}-05-31'
FTW_WIN_B = f'{YEAR}-07-01/{YEAR}-07-18'   # din ~23.07.2024 procesarea e 05.11, iar ftw-tools 1.4.3 nu combină versiuni diferite
FTW_PKGS = ['ftw-tools==1.4.3', 'torchgeo==0.7.2']   # torchgeo >= 0.8 nu mai are clasa importată de ftw-tools 1.4.3
FTW_RUN = 'v2'                             # eticheta rulării: INTERIM/ftw_poly_<tile>_<run>.parquet

# Repo-ul unic al proiectului (D39), folosit și ca punte între PC și runtime-ul Colab
GITHUB_REPO = 'https://github.com/lefterpatrickandrei-sketch/atlas-seceta-2024.git'
