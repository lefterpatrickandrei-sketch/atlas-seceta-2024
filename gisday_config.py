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

# Repo privat folosit ca punte între PC și runtime-ul Colab
GITHUB_REPO = 'https://github.com/lefterpatrickandrei-sketch/gisday2026.git'
