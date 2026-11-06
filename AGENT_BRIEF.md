# Brief pentru agentul AI — GIS Day 2026, Atlasul vulnerabilității la secetă

Citește acest fișier integral înainte de orice modificare. Proiectul NU are legătură cu StratumRO.

## Obiectiv
O hartă-erou pentru GIS Day 2026 (18 nov., FIFIM; organizatori AgroCliN și UGR Comisia 3): vulnerabilitatea la secetă a fiecărei parcele agricole din sudul Olteniei în 2024, prezisă de un model LightGBM din factori structurali și explicată cu SHAP. În jurul ei: straturile irigat 2024, valul recoltei, perdele forestiere (scenariu), carbon în sol.

## Reguli obligatorii
1. Nu ghici API-uri, nume de benzi, coloane sau flag-uri CLI. Verifică întâi: `--help`, `bandNames().getInfo()`, `df.columns`, fișierele reale de pe disc.
2. Toate livrabilele în EPSG:3844. Configurarea comună e în `gisday_config.py`; nu o duplica.
3. Indicii din vara 2024 (NDVI/NDMI/VV/VH lunar) NU intră ca factori în modelul 04: sunt ținta sau servesc la detecția irigării și a recoltei. Altfel modelul e circular.
4. LUCAS 2018: licență personală, netransferabilă. `data/private` nu intră în git, iar punctele individuale cu valori nu apar pe hărți sau slide-uri; publici doar hărți derivate și statistici agregate (R², RMSE). Sursa se menționează: ESDAC / European Commission, JRC.
5. Fiecare etapă scrie pe disc (GeoParquet/COG) și poate fi reluată independent. Rezultatele mici merg în `data/out` și în repo.
6. Machetele din `render/` folosesc date simulate; sunt doar referință de stil (paletă, tipografie Inter, layout 1920×1080). Pe hărțile finale nu rămâne niciun număr simulat.

## Zona și date
- Zona: `AOI_BBOX` din config, tăiată la granița României (FAO/GAUL/2015/level0).
- Earth Engine: `COPERNICUS/S2_SR_HARMONIZED`, `COPERNICUS/S1_GRD`, `ECMWF/ERA5_LAND/HOURLY` și `DAILY_AGGR`, `COPERNICUS/DEM/GLO30`, `JRC/D5/EUCROPMAP/V1` (2018, 2022), `projects/soilgrids-isric/{soc,sand,clay}_mean`.
- Descărcate manual: CLMS HR-VPP (actualizarea 2024 publicată pe 13.10.2025) în `data/raw/hrvpp/`; CLMS Small Landscape Features 2021 în `data/raw/slf/`; LUCAS 2018 Topsoil în `data/private/`.
- Parcele: Fields of The World (`ftw-tools`, MIT; checkpoint `3_Class_FULL_FTW_Pretrained.ckpt`, uz necomercial), scene Sentinel-2 L2A de pe Planetary Computer.

## Starea curentă
- 00–04 scrise. 04 și părțile locale din 02/03 testate pe date sintetice; celulele Earth Engine și FTW netestate.

## De construit (în ordine)
1. **03b · Irigat 2024 (Ideea 1).** Etichete: ~200 de parcele digitizate în QGIS (`data/out/irrigation_labels.gpkg`, coloana `irigat` 0/1; pivoții circulari sunt exemple sigure). Factori: indicii lunari 2024 din `parcel_gee_stats.parquet` + ploaia ERA5-Land. Clasificator Random Forest/LightGBM, validare pe blocuri spațiale → coloana `irrigated_prob` în `parcel_features.parquet`. Metodă de referință: Pageot et al. 2020, doi:10.3390/rs12183044.
2. **03c · Expunerea la vânt (Ideea 5).** Din ERA5-Land orar: direcția dominantă în orele cu temperatura peste 30 °C și fără ploaie. Pentru fiecare parcelă: există un element lemnos (SLF 2021) în amonte, la cel mult 20H (H = 15 m)? → `wind_exposure` 0–1. Apoi optimizarea perdelelor noi (greedy, buget în km) ca scenariu, cum arată macheta `render/m5_perdele.py`.
3. **03d · Carbonul calibrat (Ideea 3).** Compozit de sol gol Sentinel-2 2017–2025 (primăvara, praguri NDVI/NBR2), LightGBM pe punctele LUCAS din zonă + covariabile DEM → `soc_lucas_model`; validare spațială. Rulează local dacă LUCAS nu e pe runtime.
4. **06 · Valul recoltei (Ideea 2).** Serii la 10 zile S1 VH/VV + S2 NDVI/NBR2 pe parcelă, sezonul 2024 → ziua recoltării prin punct de ruptură (referință: Kavats et al. 2019, Remote Sensing 11(21):2496). Opțional coerență din SNAP.
5. **05 · Randare.** Harta scorului (0–100) și a factorului dominant; video 1920×1080 la 30 fps cu straturile stivuite care se prăbușesc în scor; afișe PNG. Reutilizează `render/common.py`.

## Limite de spus pe slide
Modelul arată asocieri, nu cauze dovedite. Ținta HR-VPP măsoară productivitatea vegetației, nu recolta în t/ha.
