# Fișa tehnică: Atlasul secetei din 2024 — sudul Olteniei

Anexă la prezentarea de la GIS Day 2026. Totul vine din repo (`git log`, `STATUS.md`, `DECIZII.md`, notebook-uri, scripturi) și din mediile Python de pe PC, fără calcule noi. Ce nu se poate dovedi e marcat **necunoscut** sau **nedovedit**. Duratele „măsurate” vin din metadatele de execuție ale notebook-urilor sau din rulările scripturilor din 10.11.2026.

## 1. Etape

| Etapă | Unde a rulat | Durată | Volum | Script |
|---|---|---|---|---|
| Descărcarea HR-VPP (TPROD, EOSD, LENGTH, sezonul 1, 2017–2024, tile T34TGP) | PC local, WEkEO HDA | Ultima rulare: 0,6 min (09.11, EOSD și LENGTH); viteza din output: 7,6 MB/s. Descărcarea inițială a TPROD: **necunoscut** | 24 de GeoTIFF, 3,47 GB | `notebooks/03a_download_hrvpp.ipynb` |
| Scenele Sentinel-2 pentru FTW | Colab: `ftw inference download` din Microsoft Planetary Computer (STAC `sentinel-2-l2a`, nori < 10%) | **necunoscut** | 2 scene L2A pe T34TGP: 12.04.2024 și 11.07.2024, același baseline de procesare 05.10, câte 4 benzi; volum în GB: **necunoscut** | `scripts/ftw_colab.py`; selecția în `gisday_lib.best_scenes` |
| Inferența FTW | Colab; GPU **nedovedit** (vezi secțiunea 2) | **necunoscut** | 1 tile; poligoane `ftw_poly_34TGP_v2.parquet`, 2,8 MB (08.11, 17:31) → 17.466 parcele ≥ 0,5 ha, 826,5 km² | `scripts/ftw_colab.py`; post-procesarea locală în `notebooks/02_parcels_ftw.ipynb` (0,5 min) |
| Statisticile zonale | Earth Engine (`reduceRegions` în loturi de 900: Sentinel-2, Sentinel-1, ERA5-Land, Copernicus DEM, SoilGrids, EUCROPMAP) și PC local pe CPU (TPROD cu `rasterstats`) | Notebook-ul: 2,7 min măsurat (08.11, 16:27–16:30); celula HR-VPP: 155,7 s pentru 8 rastere. Nu se știe dacă loturile EE au venit din cache | 17.466 parcele × 67 de coloane; cache EE 8,3 MB | `notebooks/03_parcel_features.ipynb` |
| Ținta like-for-like | PC local, CPU | Sub 1 min (09.11) | 13.237 parcele arabile, 11.048 cu țintă | `notebooks/03e_target.ipynb`, `gisday_lib.like_for_like_loss` |
| LightGBM + SHAP | PC local, CPU | 0,3 min măsurat (08.11) | 11.965 parcele, 11 factori, 82 de blocuri de 5 km | `notebooks/04_vulnerability_model.ipynb` |
| Regula radar S1 și placebo | Earth Engine (VV, VH și ploaia ERA5-Land pe parcele) și PC local pe CPU (regula, diagnosticul, placebo) | Extragerea VH: 120 s în EE; diagnosticul cu placebo: ~8 s local; extragerea VV și a ploii ERA5: **necunoscut**, scriptul nu e în repo | 13.237 parcele × 34 de treceri Sentinel-1 (VV și VH), ploaie zilnică; 795 de evenimente | `notebooks/03b_irrigation.ipynb`, `scripts/extract_s1_vh.py`, `scripts/diagnostic_evenimente_s1.py` |
| EOSD și LENGTH | PC local, CPU | ~19 s | 16 rastere (EOSD și LENGTH, 2017–2024), 17.466 parcele | `scripts/sfarsit_sezon.py` |
| Figurile | PC local, CPU (Pillow, matplotlib) | Câteva secunde fiecare (harta-erou ~6 s) | 7 PNG 1920×1080 și codul QR (1035×1035) în `data/out/final/` | `render/*.py`, `scripts/qr_harta.py` |
| Video-ul | PC local, CPU, `ffmpeg` cu libx264 | 1 min 52 s | 600 de cadre, 20 s, 3,9 MB (`atlas_tprod_2017_2024.mp4`, în afara git) | `render/atlas_tprod_video.py` |
| Harta web | PC local (pregătirea datelor și testul în Edge prin Playwright); găzduire GitHub Pages | Pregătirea datelor: câteva secunde, nemăsurat exact | 1,31 MB de date; 1,82 MB transferați la încărcare | `scripts/web_date.py`, `scripts/test_web.py`, `web/` |

`__pycache__/4_hrana_sau_energie.mp4` e o machetă cu date simulate din faza de început, nu un rezultat al proiectului.

## 2. A rulat inferența FTW pe A100?

**Nedovedit.** Ce există în repo:

- **Planul de rulare:** `scripts/ftw_colab.py` (rândul 4) cere sesiunea cu `colab new -s gisday-ftw --gpu A100`. Rândul 32 afișează `nvidia-smi`, dar ieșirea acelei rulări nu e salvată nicăieri în repo.
- **Unde au fost făcute poligoanele:** în `notebooks/02_parcels_ftw.ipynb`, output-ul celulei 6 spune că checkpoint-ul lipsește pe PC și că poligoanele vin de pe Colab. Fișierul `ftw_poly_34TGP_v2.parquet` are data 08.11, 17:31, iar commit-ul `bc87707` (08.11, 17:32) adaugă „parcele complete pe toată zona”.
- **Fișierul local `data/PROMPT_OPUS.md`** (neversionat) spune că `00_setup` a rulat pe Colab A100 (40 GB). Asta privește setup-ul, nu inferența.

Concluzie: că inferența a rulat pe Colab e susținut de script și de notebook; **tipul de GPU nu e dovedit** de niciun log.

## 3. Checkpoint-ul `3_Class_FULL_FTW_Pretrained`

| | Ce se poate dovedi |
|---|---|
| Registru | `ftw-tools` 1.4.3 nu are `model_registry`. `ftw_cli/types.py` leagă doar numele `THREE_CLASS_FULL` de fișierul `3_Class_FULL_FTW_Pretrained.ckpt` |
| Encoder | **necunoscut.** Arhitectura e în hiperparametrii checkpoint-ului, încărcat cu `CustomSemanticSegmentationTask.load_from_checkpoint` (`ftw_cli/inference.py`), iar checkpoint-ul nu e pe PC. Clasa din `ftw/trainers.py` acceptă mai multe variante (segmentation-models-pytorch: Unet, DeepLabV3Plus, UPerNet, Segformer, DPT; backbone implicit `resnet50`) |
| Decoder | **necunoscut**, din același motiv |
| Clase | 3 (din numele checkpoint-ului; ieșirea se reduce cu `argmax` pe clase). Semnificația claselor: **necunoscut** din repo |
| Intrare | 8 canale: două scene Sentinel-2 L2A (fereastra A și fereastra B), câte 4 benzi `B04, B03, B02, B08` (`ftw_cli/cfg.py`), stivuite pe (timp, bandă) în `ftw_cli/download_img.py`; inferența merge pe ferestre cu suprapunere (padding) |
| Licență | Checkpoint-urile FULL sunt pentru uz necomercial (CC BY-NC); vezi `web/README.md` |

## 4. Versiunile pachetelor

| Pachet | Versiune | Unde |
|---|---|---|
| ftw-tools | 1.4.3 | Fixat în `gisday_config.FTW_PKGS`; instalat și în `.venv-ftw` pe PC |
| torchgeo | 0.7.2 | Fixat în `gisday_config.FTW_PKGS` |
| torch | 2.15.0 în `.venv-ftw` de pe PC. Pe Colab, unde a rulat inferența: **necunoscut** (instalat de `uv` fără versiune fixată și nelogat) | |
| segmentation-models-pytorch | 0.6.0 | `.venv-ftw` (PC) |
| lightgbm | 4.7.0 | `.venv` (PC) |
| shap | 0.54.1 | `.venv` (PC) |
| rasterio | 1.5.2 | `.venv` și `.venv-ftw` (PC) |
| geopandas | 1.2.0 | `.venv` și `.venv-ftw` (PC) |
| earthengine-api | 1.7.51 | `.venv` (PC) |

`requirements.txt` nu fixează versiunile pentru lightgbm și shap; cele de mai sus sunt cele instalate acum pe PC.

## 5. Consumul de resurse

| Resursă | Valoare |
|---|---|
| Earth Engine (EECU-ore) | **necunoscut.** `STATUS.md` notează că nu a fost măsurat (se vede în Cloud Console → Quotas) |
| Unități Colab | **necunoscut.** Nu există niciun log în repo |
