# Decizii

O decizie schimbată nu se șterge: se marchează „înlocuită de Dnn”. Orice schimbare de metodologie se face doar cu acordul lui Patrick.

## Stabilite de Patrick

| Nr. | Data | Decizie | Sursă |
|---|---|---|---|
| D01 | 06.11.2026 | Produsul: hartă-erou „Atlasul vulnerabilității la secetă” pentru sudul Olteniei (Sadova–Bechet–Dăbuleni–Corabia), `AOI_BBOX = (23.85, 43.70, 24.55, 44.00)`, tăiată la granița României. | `data/PROMPT_OPUS.md`, Context |
| D02 | 06.11.2026 | Unitatea de analiză: parcele Fields of The World. | idem |
| D03 | 06.11.2026 | Ținta: pierderea de productivitate din 2024 față de 2017–2023. Principal HR-VPP TPROD, rezervă NDVI iulie–august din Sentinel-2. | idem |
| D04 | 06.11.2026 | Model LightGBM + SHAP, validare spațială pe blocuri de 5 km. | idem |
| D05 | 06.11.2026 | Indicii din vara 2024 nu sunt factori în modelul 04 (circularitate). | idem; `AGENT_BRIEF.md`, regula 3 |
| D06 | 06.11.2026 | Toate livrabilele în EPSG:3844; configurarea comună doar în `gisday_config.py`. | `data/PROMPT_OPUS.md`, regula 5 |
| D07 | 06.11.2026 | Secretele stau doar în `.env` și `data/private/`, în afara git. Fișierele de credențiale nu urcă pe Colab. | idem, regula 2 |
| D08 | 06.11.2026 | Descărcările cu chei Copernicus rulează local; Colab e doar pentru calcul GPU. | idem, regula 4 |
| D09 | 06.11.2026 | LUCAS 2018 are licență personală: rămâne în `data/private/`, punctele individuale nu apar pe hărți sau slide-uri, iar sursa se menționează (ESDAC / European Commission, JRC). | `AGENT_BRIEF.md`, regula 4 |
| D10 | 06.11.2026 | Dacă R² spațial e sub 0,3, modelul nu se „repară”: se raportează distribuția țintei și se întreabă. | `data/PROMPT_OPUS.md`, S5 |
| D11 | 08.11.2026 | Harta-erou arată pierderea observată în 2024 și insulele irigate. Scorul modelat și SHAP sunt panou secundar, cu R² scris pe slide. | `AGENT_BRIEF.md`, Plan aprobat |
| D12 | 08.11.2026 | Ținta compară parcela doar cu anii în care a avut același tip de cultură (verde în aprilie = toamnă, gol în aprilie = primăvară). Parcelele non-arabile ies din model și din colorare. | idem |
| D13 | 08.11.2026 | `irrigated_prob` e strat de hartă, nu factor. Nici `crop` 2022 nu mai e factor. | idem |
| D14 | 08.11.2026 | Tăieri: Carbon LUCAS doar dacă arhiva ajunge până pe 10.11, 18:00; Valul recoltei doar dacă modelul e validat până pe 12.11; scenariul perdelelor doar după ce harta-erou e gata. | idem |
| D15 | 08.11.2026 | Harta-erou și video-ul se îngheață pe 14.11; prezentarea e gata pe 17.11. | idem |
| D16 | 08.11.2026 | 03b trece pe etichete slabe automate + 80 de parcele validate de Patrick. Înlocuiește planul cu ~200 de parcele digitizate și etichetele AI din 08.11. Detaliile sunt la D18. | Mesajul lui Patrick, 08.11.2026 |
| D17 | 08.11.2026 | Ținta = z-score HR-VPP TPROD 2024 față de 2017–2023, pe parcelă. Harta-erou afișează `vuln_score` 0–100 (percentilă), nu unități TPROD. Se rerulează 04 pe această țintă, apoi harta; dacă R² spațial < 0,3, oprire și raportare la Patrick. | Mesajul lui Patrick, 08.11.2026 (Q1) |
| D18 | 08.11.2026 | Etichetele AI rămân doar pentru antrenare, marcate „AI, neverificate”. Se propune regula Sentinel-1 (umezire fără ploaie, ERA5-Land) pentru pozitive suplimentare, cu pragurile arătate pe 5 parcele. Se pregătesc 80 de parcele pentru validarea lui Patrick: 40 prezise irigate + 40 neirigate, răspândite în toată zona, cu foi și `labels.csv` doar pentru ele. Acuratețea se raportează doar pe acestea. | Mesajul lui Patrick, 08.11.2026 (Q2) |
| D19 | 08.11.2026 | **Limita versiunilor HR-VPP (`V101` în 2017–2020 vs `V105` în 2021–2024):** în catalogul WEkEO (`data/raw/hrvpp/search_results.json`), `V105` există doar pentru 2021–2024, iar 2017–2020 există exclusiv în `V101`. Pe parcele stabile non-arabile ($N=474$), diferența mediană `V105 − V101` e +87,0 unități (+7,0%), iar pe monocultură arabilă ($N=102$) e −2,5% (primăvară) și +2,3% (toamnă). Test de sensibilitate pe cele 13.237 parcele arabile: (1) cu offset aditiv +87,0 pe V101: Spearman $\rho = 0{,}9960$, deplasare pe `vuln_score` (0–100) mediană **1,22 puncte**, P90 **4,04 puncte**; (2) cu factor multiplicativ $\times 1{,}07$ pe V101: Spearman $\rho = 0{,}9982$, deplasare mediană **0,88 puncte**, P90 **2,80 puncte**. Se păstrează seria 2017–2023 completă, cu mențiunea limitei pe slide. | Mesajul lui Patrick, 08.11.2026 (Q3 + PAS A1–A2) |
| D20 | 08.11.2026 | Ordinea de execuție: Q3, apoi Q1 (04 + hartă), apoi Q2, cu actualizarea `STATUS.md` și oprire după fiecare. | Mesajul lui Patrick, 08.11.2026 |

## Alese de agenți în cod (fără aprobare explicită)

| Nr. | Alegere | Unde |
|---|---|---|
| T1 | Tipul de cultură: NDVI aprilie ≥ 0,5 = toamnă, < 0,35 = primăvară. | `gisday_lib.py:102` |
| T2 | Pierderea cere cel puțin 2 ani de referință cu același tip de cultură. | `gisday_lib.py:115-137` |
| T3 | 03e trece singur pe HR-VPP când există toți cei 8 ani. | `notebooks/03e_target.ipynb`, celula 4 |
| T4 | Stratul 03b se numește „irigat” la F1 pe blocuri ≥ 0,75; altfel „candidate”. | `notebooks/03b_irrigation.ipynb`, celula 2 |
| T5 | Parcelele sub 0,5 ha se elimină (`P.area_ha >= 0.5`). FTW rulează cu `ftw-tools==1.4.3` și `torchgeo==0.7.2`. | `notebooks/02_parcels_ftw.ipynb`; `gisday_config.py:25-28` |
| T6 | Expunerea la vânt: ore peste 30 °C fără ploaie, direcții cu cel puțin 5% din ore, elemente lemnoase SWF + WVL 2021 până la 20H = 300 m. | `notebooks/03c_wind.ipynb`, celulele 2–4 |
| T7 | Factorii din 04: distanța la canal și la rețea, expunerea la vânt, panta, altitudinea, carbon, nisip, argilă (SoilGrids), suprafața. | `notebooks/04_vulnerability_model.ipynb`, celula 4 |

## De decis (Patrick)

| Nr. | Întrebare | Opțiuni / Propunere |
|---|---|---|
| **Q1-B2** | **Pragul pentru `z` extrem / abatere standard mică în `03e`:** pe parcelele cu `std_2017_2023 < 142,8` (P5), o variație normală dă `\|z\|` până la `19,9`. | **Propunere dublă:** (1) plafon inferior `std_min = 142,8` (P5 pe arabil, ~15% din mediana `TPROD`) la numitorul lui `z`, sau (2) winsorizare `loss ∈ [−3,5, +3,5]` (P1..P99), care ridică $R^2$ spațial de la `0,183` la `0,214` și reduce RMSE de la `1,389` la `1,213`. |
| **Q1-C4** | **Oprire obligatorie la `R² spațial = 0,183 < 0,3` în `04`:** aproape toată explicația globală ($R^2 = 0{,}183$) vine din contrastul `tip_cultura_2024` (primăvară `loss` median `+1,127` vs toamnă `+0,118`), iar în interiorul grupelor $R^2$ este `0,022` (toamnă) și `0,048` (primăvară). Cum continuăm spre PAS D (harta-erou)? | **(a)** Mergem la PAS D conform D11 (harta-erou afișează vulnerabilitatea observată / percentila `0–100`, iar modelul + SHAP rămân în panoul secundar cu `R² = 0,183` scris explicit pe slide).<br>**(b)** Calculăm `z` doar față de anii cu același tip de cultură sau doar pe culturile de primăvară.<br>**(c)** Aplicăm pragul B2 ales mai sus și apoi randăm PAS D. |
