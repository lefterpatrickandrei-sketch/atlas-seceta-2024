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

## Starea curentă (06.11.2026, verificată independent, commit `3f7c2fb`)
- Secrete: doar în `.env` (vezi `.env.example`) și `data/private/` (cheia CLMS `clms_service_key.json`), ambele în afara git. Fișierele ajutătoare locale sunt excluse prin `.git/info/exclude`.
- S2 gata: Small Landscape Features 2021 (SWF + WVL, raster 5 m, EPSG:3035) în `data/raw/slf/` (`03a_download_slf.ipynb`).
- S1 în așteptare: `03a_download_hrvpp.ipynb` e scris; descărcarea HR-VPP cere `WEKEO_USER`/`WEKEO_PASSWORD` în `.env`. LUCAS 2018 lipsește din `data/private/`.
- S3 gata (Colab A100, oprit după rulare): 13.455 parcele FTW ≥ 0,5 ha (664 km², 39% din AOI), fără dubluri și fără gol la 24° E → `data/out/parcels.parquet`. Ferestre S2: 1 apr–31 mai și 1–18 iul 2024 (aceeași procesare 05.10); ftw-tools 1.4.3 + torchgeo 0.7.2, `MPLBACKEND=Agg`. Notă: o parcelă mare de 383,7 ha merită verificată vizual în QGIS.
- S4 gata fără HR-VPP și LUCAS: `data/out/parcel_features.parquet` (15 loturi grupate pe blocuri de 5 km, 215 s), ținta de rezervă `ndvi_ja_z_2024`. Consumul EECU nu a fost măsurat (se verifică în Cloud Console → Quotas pentru `earthengine.googleapis.com` pe proiectul `gisday2026`). Cache-ul `data/interim/gee_batches/` este indexat doar după numărul lotului și TREBUIE șters dacă se regenerează parcelele. Notă: `COPERNICUS/DEM/GLO30` este marcat depreciat (înlocuit de `COPERNICUS/DEM/GLO30_2024_1`), dar încă funcționează.
- S5: 7 factori (relief, SoilGrids, cultură, suprafață) → R² spațial 0,003, RMSE 1,450 (și −0,001 cu cozile tăiate; sub pragul 0,3): decizie metodologică în așteptare. Lipsesc factorii irigat, canal, vânt; `dist_canal_m` nu are încă sursă de date (de ex. canalele din OSM). Notebook-urile 02–04 nu au output-uri salvate în celule (au rulat prin scripturi echivalente).

## Plan aprobat de Patrick (08.11.2026)
Harta-erou și video-ul se îngheață pe 14.11, prezentarea e gata pe 17.11. Decizii aprobate:
- **Harta-erou** arată pierderea observată în 2024 și insulele irigate; scorul modelat și SHAP sunt panou secundar, cu R² scris pe slide.
- **Ținta** compară fiecare parcelă doar cu anii în care a avut același tip de cultură (verde în aprilie = toamnă, gol în aprilie = primăvară). Parcelele non-arabile ies din model și din colorare.
- **`irrigated_prob` e strat de hartă, nu factor** (ar fi circular). Nici `crop` 2022 nu mai e factor.
- **Tăieri:** Carbon LUCAS doar dacă arhiva ajunge până marți 10.11, 18:00; Valul recoltei doar dacă modelul e validat până joi 12.11; scenariul perdelelor doar după ce harta-erou e gata.

| Zi | Agent | Patrick |
|---|---|---|
| Dum 08 | E0 pregătire, E1 parcele complete, E2 trăsături EE | |
| Lun 09 | E3 ținta, E5 canale OSM, pachet etichetare | `.env`, consum Earth Engine |
| Mar 10 | E4 HR-VPP, E6 irigat | etichetare în QGIS |
| Mie 11 | E7 vânt, E8 model | |
| Joi 12 | E8 încheiat, E9 randare | decizie Valul recoltei |
| Vin 13 | E9 | verificare hartă în QGIS |
| Sâm 14 | hartă și video înghețate | acord final |
| Dum 15 – Lun 16 | E10 prezentare | logo-uri |
| Mar 17 | corecturi | repetiție |

## De construit (în ordine)
1. **03b · Irigat 2024 (Ideea 1).** Etichete: ~200 de parcele digitizate în QGIS (`data/out/irrigation_labels.gpkg`, coloana `irigat` 0/1; pivoții circulari sunt exemple sigure). Factori: indicii lunari 2024 din `parcel_gee_stats.parquet` + ploaia ERA5-Land. Clasificator Random Forest/LightGBM, validare pe blocuri spațiale → coloana `irrigated_prob` în `parcel_features.parquet`. Metodă de referință: Pageot et al. 2020, doi:10.3390/rs12183044.
2. **03c · Expunerea la vânt (Ideea 5).** Din ERA5-Land orar: direcția dominantă în orele cu temperatura peste 30 °C și fără ploaie. Pentru fiecare parcelă: există un element lemnos (SLF 2021) în amonte, la cel mult 20H (H = 15 m)? → `wind_exposure` 0–1. Apoi optimizarea perdelelor noi (greedy, buget în km) ca scenariu, cum arată macheta `render/m5_perdele.py`.
3. **03d · Carbonul calibrat (Ideea 3).** Compozit de sol gol Sentinel-2 2017–2025 (primăvara, praguri NDVI/NBR2), LightGBM pe punctele LUCAS din zonă + covariabile DEM → `soc_lucas_model`; validare spațială. Rulează local dacă LUCAS nu e pe runtime.
4. **06 · Valul recoltei (Ideea 2).** Serii la 10 zile S1 VH/VV + S2 NDVI/NBR2 pe parcelă, sezonul 2024 → ziua recoltării prin punct de ruptură (referință: Kavats et al. 2019, Remote Sensing 11(21):2496). Opțional coerență din SNAP.
5. **05 · Randare.** Harta scorului (0–100) și a factorului dominant; video 1920×1080 la 30 fps cu straturile stivuite care se prăbușesc în scor; afișe PNG. Reutilizează `render/common.py`.

## Limite de spus pe slide
Modelul arată asocieri, nu cauze dovedite. Ținta HR-VPP măsoară productivitatea vegetației, nu recolta în t/ha.
