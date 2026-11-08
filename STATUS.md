# Starea proiectului

Verificat pe disc: 08.11.2026 (după PAS A–C din Q1; oprire obligatorie la C4 înainte de PAS D). Ramura activă: `main` (`bd405e0` local; `2a350f1` pe `origin/main`).
„Starea curentă” din `AGENT_BRIEF.md` e mai veche decât acest fișier: a fost scrisă înainte de HR-VPP și de 03b.
DEPĂȘIT = rezultatul există, dar a fost calculat pe o țintă care între timp s-a schimbat.

| Etapă | Stare | Dovadă | Pasul următor |
|---|---|---|---|
| S0 Pregătire | GATA | `c24e03e`, `2a350f1` pe `main`; `.gitignore`, `.env.example`; copia duplicat `PROMPT_OPUS_1.md` ștearsă | Comite `.env.example` împreună cu S1/S4 |
| S1 HR-VPP + **Q3** | GATA (verificat Q3) | `data/raw/hrvpp/`: 8 din 8 ani (2017–2024), TPROD s1, tile T34TGP, EPSG:32634. **Q3 verificat:** în WEkEO (`search_results.json`, căutare fără filtru de versiune) `V105` există doar pentru 2021–2024, iar 2017–2020 există exclusiv în `V101`. Pe parcele arabile stabile cu același tip de cultură și $\|\Delta\text{NDVI}\| < 0{,}04$, diferența mediană `V105 − V101` este −8,3 unități (−2,5%) la primăvară ($N=102$) și +35,0 (+2,3%) la toamnă ($N=102$); pe non-arabile stabile ($N=474$, $\|\Delta\text{NDVI}\| < 0{,}03$) este +87,0 (+7,0%). Chiar și cu o corecție de +87,0 pe 2017–2020, z-score-ul 2024 rămâne practic neschimbat ($r = 0{,}9901$, Spearman $\rho = 0{,}9960$, deplasare mediană de doar 1,22 puncte pe scara `vuln_score` 0–100). **Diferența de versiune nu contează pentru z-score / percentilă.** | Etapa următoare: **Q1** (`03e` + `04` + harta-erou) |
| S2 SLF 2021 | GATA | `c24e03e`; `data/raw/slf/` (SWF și WVL 2021, 5 m); `notebooks/03a_download_slf.ipynb` | Niciunul |
| S3 Parcele FTW | GATA | `bc87707`; `data/out/parcels.parquet`: 17.466 parcele ≥ 0,5 ha, 826,5 km², EPSG:3844 | Niciunul |
| S4 Trăsături | GATA, necomis | `data/out/parcel_features.parquet` (18:30): 17.466 × 67, cu `tprod_2017`…`tprod_2024` și `tprod_z_2024`. Cele 58 de coloane din `6ef00d6` au rămas identice | Commit după Q1 |
| S5 Model | DEPĂȘIT | `02e6b06`, vezi rândul 04. Prima rulare, pe ținta de rezervă: R² spațial 0,003 (`3f7c2fb`) | Vezi 04 (Q1) |
| 03a Descărcări | GATA | Vezi S1 și S2 | Niciunul |
| 03b Irigat 2024 | DE REFĂCUT | `notebooks/03b_labels_pack.ipynb` (`6ef00d6`). Necomise: `irrigation_labels.gpkg`, `notebooks/03b_irrigation.ipynb`, `irrigation_2024.parquet`, `irrigation_metrics.json`. Etichete AI („AI, neverificate”): 23 irigate, 243 neirigate, 34 goale. F1 0,619, AUC 0,947, strat `candidate` | După Q1: **Q2** (regulă S1 + ERA5 pe 5 parcele + 80 parcele stratificate pentru validarea lui Patrick) |
| 03c Vânt | GATA expunerea; scenariul perdelelor NEÎNCEPUT | `02e6b06`; `data/out/parcel_wind.parquet` (17.466), `wind_rose.parquet` | Scenariul doar după harta-erou (D14) |
| 03d Carbon LUCAS | NEÎNCEPUT | PDF-ul ESDAC `ESDAC - European Commission - Temporary Dataset Download_ LUCAS 2018 TOPSOIL data - 2026-11-06.pdf` a fost copiat în `data/private/` (104.736 B); arhiva de date propriu-zisă încă nu e descărcată | Arhiva LUCAS până pe 10.11, 18:00 (D14), în mesaj separat |
| 03e Ținta | GATA (PAS B1–B4) | `data/out/parcel_target.parquet`: `loss_source = hrvpp_tprod_z`, `z_tprod_2024`, `loss = -z_tprod_2024`, `n_ani_baza`, `tip_cultura_2024`. Toate cele **13.237** parcele arabile au `n_ani_baza == 7 >= 5` (0 excluse pe arabil; 1 parcelă non-arabilă din 17.466 exclusă). Mediana `loss`: `+1,127` pe primăvară ($N=5.388$), `+1,162` pe neclasificat ($N=1.585$), `+0,118` pe toamnă ($N=6.264$) | **Q1-B2:** alegerea pragului pentru `std` / `z` extrem |
| 04 Model | RULAT PE Q1 — **OPRIRE C4** | `notebooks/04_vulnerability_model.ipynb`, `data/out/model_metrics.json`, `vulnerability.parquet`, `vulnerability.gpkg`, `shap_importance.png`. **13.230** parcele arabile (7 fără SoilGrids), 82 blocuri de 5 km. **R² spațial OOF = 0,183** (medie folduri **0,180**), **RMSE = 1,389** (vs model de bază media: $R^2 = -0{,}0004$, $\text{RMSE} = 1{,}537$). Pe grupe: toamnă $R^2 = 0{,}022$, primăvară $R^2 = 0{,}048$. Cu `irrigated_prob` (comparație C2): $R^2$ global $= 0{,}228$ ($0{,}185$ pe primăvară). Primii factori SHAP: `tip_cultura_2024_num` (0,627), `clay_sg_top` (0,116), `tprod_mean_2017_2023` (0,116), `elev` (0,111) | **Q1-C4 (oprire obligatorie, R² < 0,3):** decizia lui Patrick înainte de PAS D (harta-erou) |
| 05 Randare | ÎN AȘTEPTARE (oprire C4) | Nu s-a rulat PAS D conform regulii C4 (`Dacă R² spațial < 0,3: OPREȘTE-TE înainte de hartă`) | După decizia lui Patrick la Q1-B2 și Q1-C4 |
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
