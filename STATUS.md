# Starea proiectului

Verificat pe disc: 09.11.2026 (după `Decizii Q2` pct. 1–8 / `D26`: regula S1 + pivoți fără clasificator optic, excluderea `grup_incert`, refacerea `harta_erou.png` și `tprod_pe_ani.png`, și generarea pachetului de validare cu 80 de parcele în `labels.csv` și `sheet_01..04.png`). Ramura activă: `main` (sincronizată cu `origin/main`).
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
| 03b Irigat 2024 | ÎN AȘTEPTAREA VALIDĂRII LUI PATRICK (`D26` pct. 3 și 8) | `notebooks/03b_irrigation.ipynb`, `notebooks/03b_labels_pack.ipynb`, `scripts/label_sheets.py`, `data/out/pivots_2024.gpkg` (**121** pivoți geometrici, **1.810,1 ha**), `data/out/irrigation_2024.parquet` și `irrigation_2024.gpkg` (pe cele **5.836** parcele arabile de primăvară = **22.315,3 ha**: brut fără excluderi **1.172** `irigat` [4.281,7 ha], **3.301** `neirigat` [13.155,7 ha], **1.363** `nedeterminat` [4.877,9 ha]; fără tranziția regională `o7_0615_0627`: **627** `irigat` [2.943,7 ha], **4.267** `neirigat` [16.838,1 ha], **942** `nedeterminat` [2.533,6 ha]), `data/out/s1_transitions_2024.csv`. Pachetul de validare (80 parcele: 40 `irigat` + 40 `neirigat` din 55 blocuri de 5 km): `data/interim/label_sheets/sheet_01.png` … `sheet_04.png` și `data/out/labels.csv` (`id,irigat`) | Confirmarea excluderii tranziției regionale `o7_0615_0627` (pct. 3) și completarea `labels.csv` de către Patrick (pct. 8) |
| 03c Vânt | GATA expunerea; scenariul perdelelor NEÎNCEPUT | `02e6b06`; `data/out/parcel_wind.parquet` (17.466), `wind_rose.parquet` | Scenariul doar după harta-erou (D14) |
| 03d Carbon LUCAS | AMÂNAT (D24 / `D-03d`) | Amânat conform deciziei `D-03d`; nu se începe | Niciunul |
| 03e Ținta | GATA (D21 + D26 pct. 6: `grup_incert`) | `data/out/parcel_target.parquet`: din **13.237** parcele arabile, **1.036 (7,83% < 15%)** intră în `grup_incert` (`NDVI apr 2024 ∈ [0,38; 0,45]`: 722 parcele; `crop == 250` furaje/lucernă în EUCROPMAP 2022: 325 parcele; reuniune: 1.036). Rămân **5.836** parcele de primăvară și **6.365** de toamnă. Cu țintă like-for-like ($\ge 2$ ani ref): **11.048** parcele (**4.973** primăvară [18.154 ha] și **6.075** toamnă [39.004 ha]), **1.153** fără an comparabil. Mediana `loss_rel × 100`: **+30,1%** (P25–P75: **+1,4% … +52,1%**) pe primăvară și **−0,2%** (P25–P75: **−33,2% … +24,8%**) pe toamnă | Niciunul |
| 04 Model | REZULTAT NEGATIV, NU SE CARTOGRAFIAZĂ (D22 / `D-Q1-final`) | `notebooks/04_vulnerability_model.ipynb`, `data/out/model_metrics.json` (`status: "rezultat negativ, nu se cartografiază"`), `vulnerability.parquet`, `vulnerability.gpkg`, `shap_importance.png` (`a67fb08`). Antrenat pe **11.965** parcele arabile cu țintă (82 blocuri de 5 km). **R² spațial global OOF = 0,0860**, **RMSE = 0,4680**. **În interiorul grupelor:** `primavara` ($N=5.204$) **$R^2\text{ spațial} = +0{,}0033$**, $\text{RMSE} = 0{,}4380$; `toamna` ($N=6.761$) **$R^2\text{ spațial} = +0{,}0058$**, $\text{RMSE} = 0{,}4899$. Nu se randează harta `vuln_score` și nici harta `factor_dominant` | Păstrat în repo și raportat în Panoul 2 al hărții-erou |
| 05 Randare (`PAS D-B` + `D26` pct. 6–7) | GATA | `render/r1_hero.py`, `render/tprod_pe_ani.py`, `data/out/harta_erou.png` (`1920×1080`, cu clasa gri `Grup incert (1.036)` și noile mediane `+30,1%` primăvară / `−0,2%` toamnă), `data/out/tprod_pe_ani.png` (`1920×1080`, fără etichete nesursate, pe cele 11.048 parcele cu țintă), `data/out/loss_2024.gpkg` (`EPSG:3844`, 17.466 parcele) | Completarea Panoului 3 după validarea celor 80 de parcele din Q2 |
| 06 Valul recoltei | NEÎNCEPUT | Nu există notebook | Doar dacă modelul e validat până pe 12.11 (D14) |

În afara listei: 03f, canalele OSM, e gata (`6ef00d6`; `data/out/parcel_canals.parquet`, 17.466 de rânduri).

## Verificări rulate la acest pas (Decizii Q2 pct. 1–8 + Git)
- **Git:** comite și împinge pe `origin/main` toate modificările pentru `D26` (`Decizii Q2` pct. 1–8).
- **Teste automate:** `.venv/Scripts/python.exe -m pytest tests -q` → **83 passed in 3.83s**.
- **Q3 (V101 vs V105):** verificat în catalogul WEkEO și pe parcelele stabile din `parcel_features.parquet`; diferența de versiune nu afectează ținta (`rho = 0,9960`).

## Riscuri și lucruri neverificate
- **WEkEO `.env`:** tokenul din `.env` a expirat (`401 Unauthorized`), iar autentificarea cu user/parolă a returnat `500` la `identity/gettoken` (nu blochează nimic acum, deoarece toate cele 8 rastere HR-VPP 2017–2024 și SLF 2021 sunt deja descărcate și verificate pe disc).
- **LUCAS 2018:** fișierul PDF din `Downloads` nu a putut fi șters din `Downloads` (fiind deschis în alt proces), dar a fost copiat complet în `data/private/`.
- **Consumul Earth Engine** nu a fost măsurat (se verifică în Cloud Console → Quotas).
