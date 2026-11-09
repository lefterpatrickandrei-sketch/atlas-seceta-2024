# Starea proiectului

Verificat pe disc: 09.11.2026 (după `D-Q1-final`, `D-titlu`, `D-03d` și `PAS D-B` — harta-erou pe pierderea observată `loss_rel` și `loss_2024.gpkg`). Ramura activă: `main` (sincronizată cu `origin/main`).
Produsul (D23): **„Atlasul secetei din 2024 — sudul Olteniei”**.
„Starea curentă” din `AGENT_BRIEF.md` e mai veche decât acest fișier: a fost scrisă înainte de HR-VPP și de 03b.
DEPĂȘIT = rezultatul există, dar a fost calculat pe o țintă care între timp s-a schimbat.

| Etapă | Stare | Dovadă | Pasul următor |
|---|---|---|---|
| S0 Pregătire | GATA | `c24e03e`, `2a350f1` pe `main`; `.gitignore`, `.env.example`; copia duplicat `PROMPT_OPUS_1.md` ștearsă | Niciunul |
| S1 HR-VPP + **Q3** | GATA (verificat Q3) | `data/raw/hrvpp/`: 8 din 8 ani (2017–2024), TPROD s1, tile T34TGP, EPSG:32634. **Q3 verificat:** în WEkEO (`search_results.json`, căutare fără filtru de versiune) `V105` există doar pentru 2017–2020 în `V101` și 2021–2024 în `V105`. Testul aditiv (+87 pe 2017–2020) dă Spearman $\rho = 0{,}9960$, deplasare mediană 1,22 / P90 4,04 pe `vuln_score`; testul multiplicativ ($\times 1{,}07$ pe 2017–2020) dă Spearman $\rho = 0{,}9989$, deplasare mediană 0,50 / P90 1,50 puncte pe `vuln_score`. **Seria HR-VPP se păstrează (D20).** | Niciunul |
| S2 SLF 2021 | GATA | `c24e03e`; `data/raw/slf/` (SWF și WVL 2021, 5 m); `notebooks/03a_download_slf.ipynb` | Niciunul |
| S3 Parcele FTW | GATA | `bc87707`; `data/out/parcels.parquet`: 17.466 parcele ≥ 0,5 ha, 826,5 km², EPSG:3844 | Niciunul |
| S4 Trăsături | GATA | `90d5016`; `data/out/parcel_features.parquet`: 17.466 × 67, cu `tprod_2017`…`tprod_2024` și `tprod_z_2024`. Cele 58 de coloane din `6ef00d6` au rămas identice | Niciunul |
| S5 Model | REZULTAT NEGATIV (păstrat, D22) | Vezi rândul 04 (`a67fb08`) | Niciunul |
| 03a Descărcări | GATA | Vezi S1 și S2 | Niciunul |
| 03b Irigat 2024 | ÎN AȘTEPTARE (`PAS Q2`, după aprobarea hărții) | `notebooks/03b_labels_pack.ipynb` (`6ef00d6`). Necomise: `irrigation_labels.gpkg`, `notebooks/03b_irrigation.ipynb`, `irrigation_2024.parquet`, `irrigation_metrics.json`. Etichete AI („AI, neverificate”): 23 irigate, 243 neirigate, 34 goale | **PAS Q2** (după ce Patrick aprobă harta-erou): pct. 1 praguri S1 + ERA5 + pivoți pe 5 parcele |
| 03c Vânt | GATA expunerea; scenariul perdelelor NEÎNCEPUT | `02e6b06`; `data/out/parcel_wind.parquet` (17.466), `wind_rose.parquet` | Scenariul doar după harta-erou (D14) |
| 03d Carbon LUCAS | AMÂNAT (D24 / `D-03d`) | Amânat conform deciziei `D-03d`; nu se începe | Niciunul |
| 03e Ținta | GATA (D21: like-for-like relativă) | `data/out/parcel_target.parquet` (`a67fb08`): `loss_source = hrvpp_tprod_lfl_rel`, împărțire binară la `NDVI aprilie = 0,40` (`toamna` $\ge 0{,}40$: **7.098** parcele; `primavara` $< 0{,}40$: **6.139** parcele; `0` neclasificate; acord cu EUCROPMAP 2022: **93,7%** pe 12.809 parcele). Ținta `loss_rel = 1 - TPROD_2024 / mediana(TPROD 2017–2023 cu același grup)`, min. 2 ani comparabili: **11.971** parcele arabile cu țintă (**6.766** toamnă, **5.205** primăvară) și **1.266** fără țintă (`< 2` ani ref). Tăierea la `P1 = -1,7634` / `P99 = +0,7629` afectează **240** de parcele (120 sub P1, 120 peste P99). Mediana `loss_rel`: **+0,3079** (−30,8%) la primăvară și **+0,0237** (−2,4%) la toamnă | Niciunul |
| 04 Model | REZULTAT NEGATIV, NU SE CARTOGRAFIAZĂ (D22 / `D-Q1-final`) | `notebooks/04_vulnerability_model.ipynb`, `data/out/model_metrics.json` (`status: "rezultat negativ, nu se cartografiază"`), `vulnerability.parquet`, `vulnerability.gpkg`, `shap_importance.png` (`a67fb08`). Antrenat pe **11.965** parcele arabile cu țintă (82 blocuri de 5 km). **R² spațial global OOF = 0,0860**, **RMSE = 0,4680**. **În interiorul grupelor:** `primavara` ($N=5.204$) **$R^2\text{ spațial} = +0{,}0033$**, $\text{RMSE} = 0{,}4380$; `toamna` ($N=6.761$) **$R^2\text{ spațial} = +0{,}0058$**, $\text{RMSE} = 0{,}4899$. Nu se randează harta `vuln_score` și nici harta `factor_dominant` | Păstrat în repo și raportat în Panoul 2 al hărții-erou |
| 05 Randare (`PAS D-B`) | GATA (`PAS D-B`) — **ÎN AȘTEPTAREA APROBĂRII LUI PATRICK** | `render/r1_hero.py`, `render/atlas.py`, `data/out/harta_erou.png` (`1920×1080`), `data/out/loss_2024.gpkg` (`EPSG:3844`, 17.466 parcele). Strat principal: `loss_rel × 100` în 6 clase fixe (`< 0%`: 4.451, `0–10%`: 1.013, `10–25%`: 1.702, `25–40%`: 1.818, `40–55%`: 1.558, `> 55%`: 1.429), gri pentru `fără an comparabil` (1.266), contur fin fără umplere pentru `non-arabil` (4.229). Panou 1: distribuția pe grupe (primăvară vs toamnă); Panou 2: modelul structural ($R^2 \approx 0$ în grupe); Panou 3: rezervat pentru Q2. Verificat pe 5 parcele aleatorii: culoarea din PNG corespunde exact clasei din `loss_2024.gpkg` | Aprobarea hărții de către Patrick, apoi **PAS Q2** (irigat 2024, cu completarea Panoului 3) |
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
