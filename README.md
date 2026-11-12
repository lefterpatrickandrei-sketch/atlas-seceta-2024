# GIS Day 2026 — Atlasul secetei din 2024 — sudul Olteniei

Zona: Sadova – Bechet – Dăbuleni – Corabia. Toate livrabilele în EPSG:3844 (Stereo 70).
Prezentarea: 18 noiembrie 2026, FIFIM, Amfiteatrul II 1.

## Structura

```text
gisday2026/
  gisday_config.py        # zona, CRS, ani, ID proiect Earth Engine, repo GitHub
  AGENT_BRIEF.md          # contextul și regulile pentru agentul AI din Antigravity
  notebooks/
    00_setup.ipynb        # runtime, GPU, pachete, Earth Engine
    01_extract_gee.ipynb  # exporturi raster în Drive (QGIS, vizualuri) — opțional
    02_parcels_ftw.ipynb  # parcele Fields of The World pe A100
    03_parcel_features.ipynb  # statistici pe parcelă în Earth Engine + ținta HR-VPP + LUCAS
    04_vulnerability_model.ipynb  # LightGBM + SHAP, scorul 0–100 și factorul dominant
  render/                 # scripturile machetelor (stilul vizual de reutilizat pe date reale)
  data/raw  data/interim  # mari, în afara git
  data/out                # rezultate mici (GeoParquet, GPKG, PNG), în git
  data/private            # LUCAS (licență personală), în afara git
```

## Etapele în Antigravity

**Etapa 0 — proiectul (5 min)**
1. Dezarhivează în `Documents\gisday2026` și deschide folderul în Antigravity (File → Open Folder).
2. Copiază arhiva LUCAS 2018 în `data\private\` (rămâne doar pe PC).
3. În `gisday_config.py` completezi `GEE_PROJECT` și `GITHUB_REPO`.

**Etapa 1 — puntea PC ↔ Colab (10 min)**
Runtime-ul Colab nu vede automat fișierele de pe PC. Puntea e un repo GitHub **privat**:
1. Creezi repo-ul privat `gisday2026` și faci push cu tot folderul (`data/private` e exclus prin `.gitignore`).
2. Creezi un token fine-grained doar pentru acest repo, cu permisiunea *Contents: read and write*.
3. Prima celulă din fiecare notebook clonează repo-ul pe runtime și cere tokenul (nu îl salvează în fișiere). Rulat pe un kernel local, folosește direct folderul de pe PC.

**Etapa 2 — conturi (azi)**
Earth Engine (proiect necomercial, nivel Contributor), WEkEO/CLMS (HR-VPP, Small Landscape Features), Copernicus Data Space (Sentinel-3 LST, SLC pentru SNAP).

**Etapa 3 — `00_setup` pe kernelul Colab A100**
Selectezi kernelul Colab (A100) pentru notebook și rulezi toate celulele. Trebuie să vezi GPU-ul, „Earth Engine OK” și suprafața zonei.

**Etapa 4 — `01_extract_gee` (opțional, rulează singur pe servere)**
Pornește exporturile în Drive pentru QGIS și vizualuri. Le urmărești în pagina Tasks din Earth Engine.

**Etapa 5 — `02_parcels_ftw` pe A100**
Celula de verificare afișează opțiunile reale ale `ftw`; dacă diferă de cele din notebook, corectezi înainte de rulare. Rezultatul: `data/out/parcels.parquet`, trimis automat în repo.

**Etapa 6 — date descărcate manual, în paralel**
- HR-VPP, parametrul de productivitate sezonieră, sezonul 1, anii 2017–2024, tile-urile zonei → `data/raw/hrvpp/`
- Small Landscape Features 2021 → `data/raw/slf/`

**Etapa 7 — `03_parcel_features`**
Statisticile vin direct din Earth Engine. HR-VPP și LUCAS se citesc local: rulează notebook-ul pe kernel local sau urcă fișierele pe runtime. Fără HR-VPP, modelul folosește ținta de rezervă (anomalia NDVI iulie–august).

**Etapa 8 — straturile lucrate cu agentul** (vezi `AGENT_BRIEF.md`, secțiunea „De construit”)
Irigat 2024, expunerea la vânt, carbonul calibrat LUCAS, valul recoltei.

**Etapa 9 — `04_vulnerability_model`**
Scorul 0–100, factorul dominant pe parcelă, `vulnerability.gpkg` pentru QGIS și graficul SHAP.

**Etapa 10 — randarea**
Hărțile, video-ul cu straturile stivuite și slide-urile, în stilul din `render/`.

## Ce e testat și ce nu

- Testat pe date sintetice: unirea parcelelor FTW, zonal stats HR-VPP, filtrul LUCAS, modelul 04 complet.
- Netestat (cere autentificarea ta): celulele Earth Engine și FTW. Dacă o celulă dă eroare, dă mesajul agentului sau mie.
