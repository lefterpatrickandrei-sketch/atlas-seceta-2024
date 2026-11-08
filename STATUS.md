# Starea proiectului

Verificat pe disc: 08.11.2026 (după revizuirea Q1 cu ținta like-for-like relativă `loss_rel` și poarta de R² spațial pe grupe; oprire înainte de PAS D). Ramura activă: `main` (sincronizată cu `origin/main`).
„Starea curentă” din `AGENT_BRIEF.md` e mai veche decât acest fișier: a fost scrisă înainte de HR-VPP și de 03b.
DEPĂȘIT = rezultatul există, dar a fost calculat pe o țintă care între timp s-a schimbat.

| Etapă | Stare | Dovadă | Pasul următor |
|---|---|---|---|
| S0 Pregătire | GATA | `c24e03e`, `2a350f1` pe `main`; `.gitignore`, `.env.example`; copia duplicat `PROMPT_OPUS_1.md` ștearsă | Niciunul |
| S1 HR-VPP + **Q3** | GATA (verificat Q3) | `data/raw/hrvpp/`: 8 din 8 ani (2017–2024), TPROD s1, tile T34TGP, EPSG:32634. **Q3 verificat:** în WEkEO (`search_results.json`, căutare fără filtru de versiune) `V105` există doar pentru 2017–2020 în `V101` și 2021–2024 în `V105`. Testul aditiv (+87 pe 2017–2020) dă Spearman $\rho = 0{,}9960$, deplasare mediană 1,22 / P90 4,04 pe `vuln_score`; testul multiplicativ ($\times 1{,}07$ pe 2017–2020) dă Spearman $\rho = 0{,}9989$, deplasare mediană 0,50 / P90 1,50 puncte pe `vuln_score`. **Seria HR-VPP se păstrează (D20).** | Niciunul |
| S2 SLF 2021 | GATA | `c24e03e`; `data/raw/slf/` (SWF și WVL 2021, 5 m); `notebooks/03a_download_slf.ipynb` | Niciunul |
| S3 Parcele FTW | GATA | `bc87707`; `data/out/parcels.parquet`: 17.466 parcele ≥ 0,5 ha, 826,5 km², EPSG:3844 | Niciunul |
| S4 Trăsături | GATA | `90d5016`; `data/out/parcel_features.parquet`: 17.466 × 67, cu `tprod_2017`…`tprod_2024` și `tprod_z_2024`. Cele 58 de coloane din `6ef00d6` au rămas identice | Niciunul |
| S5 Model | DEPĂȘIT | `02e6b06`, vezi rândul 04. Prima rulare, pe ținta de rezervă: R² spațial 0,003 (`3f7c2fb`); a doua rulare, pe z-score brut: R² spațial global 0,183, dar în grupe 0,022–0,048 (`90d5016`) | Vezi 04 (Q1 revizuit, D21) |
| 03a Descărcări | GATA | Vezi S1 și S2 | Niciunul |
| 03b Irigat 2024 | DE REFĂCUT | `notebooks/03b_labels_pack.ipynb` (`6ef00d6`). Necomise: `irrigation_labels.gpkg`, `notebooks/03b_irrigation.ipynb`, `irrigation_2024.parquet`, `irrigation_metrics.json`. Etichete AI („AI, neverificate”): 23 irigate, 243 neirigate, 34 goale. F1 0,619, AUC 0,947, strat `candidate` | După decizia la poarta Q1: **Q2** (regulă S1 + ERA5 + 80 parcele stratificate pentru validarea lui Patrick) |
| 03c Vânt | GATA expunerea; scenariul perdelelor NEÎNCEPUT | `02e6b06`; `data/out/parcel_wind.parquet` (17.466), `wind_rose.parquet` | Scenariul doar după harta-erou (D14) |
| 03d Carbon LUCAS | NEÎNCEPUT | PDF-ul ESDAC `ESDAC - European Commission - Temporary Dataset Download_ LUCAS 2018 TOPSOIL data - 2026-11-06.pdf` a fost copiat în `data/private/` (104.736 B); arhiva de date propriu-zisă încă nu e descărcată | Arhiva LUCAS până pe 10.11, 18:00 (D14), în mesaj separat |
| 03e Ținta | GATA (D21: like-for-like relativă) | `data/out/parcel_target.parquet`: `loss_source = hrvpp_tprod_lfl_rel`, împărțire binară la `NDVI aprilie = 0,40` (`toamna` $\ge 0{,}40$: **7.098** parcele; `primavara` $< 0{,}40$: **6.139** parcele; `0` neclasificate; acord cu EUCROPMAP 2022: **93,7%** pe 12.809 parcele). Ținta `loss_rel = 1 - TPROD_2024 / mediana(TPROD 2017–2023 cu același grup)`, min. 2 ani comparabili: **11.971** parcele arabile cu țintă (**6.766** toamnă, **5.205** primăvară) și **1.266** fără țintă (`< 2` ani ref). Tăierea la `P1 = -1,7634` / `P99 = +0,7629` afectează **240** de parcele (120 sub P1, 120 peste P99). Mediana `loss_rel`: **+0,3079** (−30,8%) la primăvară și **+0,0237** (−2,4%) la toamnă | Niciunul |
| 04 Model | RULAT PE Q1 REVIZUIT (D21) — **OPRIRE LA POARTĂ** | `notebooks/04_vulnerability_model.ipynb`, `data/out/model_metrics.json`, `vulnerability.parquet`, `vulnerability.gpkg` (cu `are_tinta = 'da' / 'nu'`), `shap_importance.png`. Antrenat pe **11.965** parcele arabile cu țintă (82 blocuri de 5 km), predicții și `vuln_score` (percentilă în interiorul fiecărui grup de cultură) pe toate cele **13.230** de parcele arabile. **R² spațial global OOF = 0,0860** (medie folduri **0,0856**), **RMSE = 0,4680** (vs model de bază global: $R^2 = -0{,}0005$, $\text{RMSE} = 0{,}4897$). **În interiorul grupelor:** `primavara` ($N=5.204$) **$R^2\text{ spațial} = +0{,}0033$**, $\text{RMSE} = 0{,}4380$ (vs model de bază pe grup: $R^2 = -0{,}0049$, $\text{RMSE} = 0{,}4398$); `toamna` ($N=6.761$) **$R^2\text{ spațial} = +0{,}0058$**, $\text{RMSE} = 0{,}4899$ (vs model de bază pe grup: $R^2 = -0{,}0021$, $\text{RMSE} = 0{,}4918$). Primii 3 factori SHAP structurali: pe **primăvară** `clay_sg_top` (0,0477), `elev` (0,0331), `dist_network_m` (0,0302); pe **toamnă** `tprod_mean_2017_2023` (0,0502), `clay_sg_top` (0,0418), `elev` (0,0375) | **OPRIRE LA POARTĂ (D21, R² în grupe < 0,10):** decizia lui Patrick (de ex. harta-erou cu pierderea observată + Q2 irigatul validat) |
| 05 Randare | ÎN AȘTEPTARE (oprire la poarta D21) | Nu s-a rulat PAS D deoarece $R^2$ spațial în interiorul grupelor (`+0,0033` pe primăvară și `+0,0058` pe toamnă) este sub pragul de `0,10` | După decizia lui Patrick la poarta D21 |
| 06 Valul recoltei | NEÎNCEPUT | Nu există notebook | Doar dacă modelul e validat până pe 12.11 (D14) |

În afara listei: 03f, canalele OSM, e gata (`6ef00d6`; `data/out/parcel_canals.parquet`, 17.466 de rânduri).

## Verificări rulate la acest pas (Q3 + Git)
- **Git:** comutat pe `main`, `git merge --ff-only docs/stare-proiect` (`ebe30e8..2a350f1`), `git push origin main` reușit. Copia duplicat `PROMPT_OPUS_1.md` a fost ștearsă.
- **Teste automate:** `pytest tests -q` → **80 passed in 13.21s** (inclusiv `tests/test_wekeo.py`).
- **Q3 (V101 vs V105):** verificat în catalogul WEkEO și pe parcelele stabile din `parcel_features.parquet`; diferența de versiune nu afectează ținta z-score / percentilă (`r = 0,9901`, `rho = 0,9960`).

## Riscuri și lucruri neverificate
- **WEkEO `.env`:** tokenul din `.env` a expirat (`401 Unauthorized`), iar autentificarea cu user/parolă a returnat `500` la `identity/gettoken` (nu blochează nimic acum, deoarece toate cele 8 rastere HR-VPP 2017–2024 și SLF 2021 sunt deja descărcate și verificate pe disc).
- **LUCAS 2018:** fișierul PDF din `Downloads` nu a putut fi șters din `Downloads` (fiind deschis în alt proces), dar a fost copiat complet în `data/private/`.
- **Consumul Earth Engine** nu a fost măsurat (se verifică în Cloud Console → Quotas).

## Necomise (7 fișiere — aferente 03b și randării vechi, în așteptarea deciziei C4 și a etapei Q2)
- Date: `data/out/harta_erou.png` (veche, pe NDVI), `irrigation_labels.gpkg`, `irrigation_2024.parquet`, `irrigation_metrics.json`.
- Cod: `render/r1_hero.py`, `scripts/label_sheets.py`, `notebooks/03b_irrigation.ipynb`.
