# Starea proiectului

Verificat pe disc: 08.11.2026. Ultimul commit cu cod și date: `ebe30e8`. „Necomis” înseamnă că fișierul există doar în arborele de lucru.
„Starea curentă” din `AGENT_BRIEF.md` e mai veche decât acest fișier: a fost scrisă înainte de HR-VPP și de 03b.
DEPĂȘIT = rezultatul există, dar a fost calculat pe o țintă care între timp s-a schimbat.

| Etapă | Stare | Dovadă | Pasul următor |
|---|---|---|---|
| S0 Pregătire | GATA | `c24e03e`; `.gitignore`, `.env.example` | Comite `.env.example` (necomis: adaugă `WEKEO_TOKEN`, gol) |
| S1 HR-VPP | GATA, notebook necomis | `data/raw/hrvpp/`: 8 din 8 ani (2017–2024), TPROD s1, tile T34TGP, EPSG:32634; citite integral, fără blocuri corupte, dimensiuni egale cu catalogul WEkEO; acoperă toate parcelele. `notebooks/03a_download_hrvpp.ipynb` | Q3 din `DECIZII.md` |
| S2 SLF 2021 | GATA | `c24e03e`; `data/raw/slf/` (SWF și WVL 2021, 5 m); `notebooks/03a_download_slf.ipynb` | Niciunul |
| S3 Parcele FTW | GATA | `bc87707`; `data/out/parcels.parquet`: 17.466 parcele ≥ 0,5 ha, 826,5 km², EPSG:3844 | Niciunul |
| S4 Trăsături | GATA, necomis | `data/out/parcel_features.parquet` (18:30): 17.466 × 67, cu `tprod_2017`…`tprod_2024` și `tprod_z_2024`. Cele 58 de coloane din `6ef00d6` au rămas identice | Commit |
| S5 Model | DEPĂȘIT | `02e6b06`, vezi rândul 04. Prima rulare, pe ținta de rezervă: R² spațial 0,003 (`3f7c2fb`) | Vezi 04 |
| 03a Descărcări | GATA | Vezi S1 și S2 | Vezi S1 |
| 03b Irigat 2024 | DE REFĂCUT | `notebooks/03b_labels_pack.ipynb` (`6ef00d6`). Necomise: `irrigation_labels.gpkg`, `notebooks/03b_irrigation.ipynb`, `irrigation_2024.parquet`, `irrigation_metrics.json`. Etichete AI: 23 irigate, 243 neirigate, 34 goale. F1 0,619, AUC 0,947, strat `candidate` | D16: etichete slabe automate + 80 de parcele validate de Patrick. Întâi Q2 |
| 03c Vânt | GATA expunerea; scenariul perdelelor NEÎNCEPUT | `02e6b06`; `data/out/parcel_wind.parquet` (17.466), `wind_rose.parquet` | Scenariul doar după harta-erou (D14) |
| 03d Carbon LUCAS | NEÎNCEPUT | Nu există notebook. În `data/private/` e doar cheia CLMS | Arhiva LUCAS până pe 10.11, 18:00 (D14) |
| 03e Ținta | GATA, necomis | `data/out/parcel_target.parquet` (18:30): `loss_source = hrvpp_tprod`, 9.895 parcele arabile cu țintă (4.161 primăvară, 5.734 toamnă). În `6ef00d6`: `ndvi_ja`, 4.161 parcele | Q1 |
| 04 Model | DEPĂȘIT | `02e6b06`; `data/out/model_metrics.json` (17:45): țintă `ndvi_ja`, R² spațial 0,125, RMSE 0,103, 4.160 parcele, 81 de blocuri; primii factori: altitudine, argilă, distanța la canal. `loss` din `vulnerability.parquet` e identic cu ținta NDVI din `ebe30e8`; r = 0,44 cu ținta curentă | Rulare nouă după Q1 |
| 05 Randare | PARȚIAL | `render/r1_hero.py` (`ebe30e8`, modificat local la 18:27). `data/out/harta_erou.png` (18:21, necomis) e desenată pe ținta NDVI: culorile se potrivesc la 171 din 171 de parcele mari eșantionate; cu ținta HR-VPP, la 2,2%. Nu există notebook 05, video sau afișe | După Q1: scară și legendă, apoi randare nouă |
| 06 Valul recoltei | NEÎNCEPUT | Nu există notebook | Doar dacă modelul e validat până pe 12.11 (D14) |

În afara listei: 03f, canalele OSM, e gata (`6ef00d6`; `data/out/parcel_canals.parquet`, 17.466 de rânduri).

## Înainte să rulezi 04 sau harta-erou
`loss_obs` din ținta curentă e în unități TPROD brute (factor de scală 0,1), nu în NDVI. Scara hărții e în NDVI (`render/atlas.py:5-6`), iar textul spune „Pierdere de NDVI” (`render/r1_hero.py:237`). Cu ținta curentă, 64% din parcele depășesc maximul scării, iar culturile de toamnă ar intra pe hartă și în model. Rularea fără Q1 ar amesteca două ținte pe același slide.

## Așteaptă acțiunea lui Patrick
1. Deciziile Q1, Q2 și Q3 din `DECIZII.md`.
2. WEkEO: parola și tokenul au fost lipite în chat pe 08.11, la 18:05–18:06. Nu sunt în repo sau în istoricul git, dar trebuie schimbate, apoi actualizat `.env`.
3. LUCAS: PDF-ul „Temporary Dataset Download” e în `C:\Users\lefpa\Downloads\`, nu în `data/private/`. Cererea de descărcare de la 19:09 nu a fost executată: sesiunea veche se blocase.

## Riscuri și lucruri neverificate
- HR-VPP are două versiuni: 2017–2020 e V101, 2021–2024 e V105. Mediana TPROD pe arabil, în valori brute, 2017–2024: 870, 848, 890, 740, 1.184, 769, 1.026, 728. Efectul versiunii nu e separat de variația dintre ani.
- 03b: F1 arată cât de consecvent reproduce modelul interpretarea AI, nu acuratețea în teren. Sunt doar 23 de exemple pozitive. Scriptul care a completat etichetele a rulat o singură dată și nu e în repo.
- Consumul Earth Engine nu a fost măsurat.
- Testele nu au fost rulate la această verificare. Ultimul rezultat raportat (74 de teste, `ebe30e8`) e dinaintea modificărilor din `gisday_lib.py` și a `tests/test_wekeo.py`.

## Necomise (15 fișiere)
- Date: `data/out/harta_erou.png`, `irrigation_labels.gpkg`, `parcel_features.parquet`, `parcel_target.parquet`, `irrigation_2024.parquet`, `irrigation_metrics.json`.
- Cod: `.env.example`, `gisday_lib.py`, `render/r1_hero.py`, `scripts/label_sheets.py`, `tests/test_wekeo.py`, `notebooks/03_parcel_features.ipynb`, `03a_download_hrvpp.ipynb`, `03b_irrigation.ipynb`, `03e_target.ipynb`.
