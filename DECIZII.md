# Decizii

O decizie schimbată nu se șterge: se marchează „înlocuită de Dnn”. Orice schimbare de metodologie se face doar cu acordul lui Patrick.

## Stabilite de Patrick

| Nr. | Data | Decizie | Sursă |
|---|---|---|---|
| D01 | 06.11.2026 | *(Titlu înlocuit de D23)* Produsul: hartă-erou „Atlasul vulnerabilității la secetă” pentru sudul Olteniei (Sadova–Bechet–Dăbuleni–Corabia), `AOI_BBOX = (23.85, 43.70, 24.55, 44.00)`, tăiată la granița României. | `data/PROMPT_OPUS.md`, Context |
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
| D21 | 08.11.2026 | **Revizuire Q1 (înlocuiește D17 pe z-score și închide Q1-B2 / Q1-C4):** (1) Nu se aplică plafon pe `std` sau winsorizare pe `z`-ul global, deoarece problema principală este rotația culturilor. (2) Grupele de cultură în 2017–2024 se împart binar la `NDVI aprilie = 0,40` (`toamna >= 0,40`, `primavara < 0,40`, fără clasa „neclasificat”; înlocuiește T1). (3) Ținta nouă este like-for-like relativă: `loss_rel = 1 − TPROD_2024 / mediana TPROD din anii 2017–2023 cu același grup ca în 2024` (minimum 2 ani comparabili, fără împărțire la abaterea standard, cu tăierea extremelor la P1/P99). (4) Antrenarea în `04` se face doar pe parcelele cu țintă like-for-like, iar predicția și `vuln_score` se calculează pentru toate cele 13.230 de parcele arabile (cu coloana `are_tinta = da/nu` în GPKG). (5) Aceiași 11 factori structurali (fără `irrigated_prob`, cu `tip_cultura_2024` factor). (6) `vuln_score` = percentila predicției calculată **în interiorul fiecărei grupe de cultură**, iar `factor_dominant` se alege doar dintre factorii structurali (fără `tip_cultura_2024`). (8) **Poarta nouă (înlocuiește D10 / R² ≥ 0,3):** `R² spațial ≥ 0,10` în interiorul **ambelor** grupe (`toamna` și `primavara`) și mai bun decât modelul de bază; dacă nu trece, oprire înainte de hartă. | Mesajul lui Patrick, 08.11.2026 (Decizii Q1, pct. 1–9) |
| D22 (`D-Q1-final`) | 09.11.2026 | **Modelul structural NU explică pierderea în interiorul grupelor** ($R^2$ spațial 0,003–0,006: $+0{,}0033$ pe `primavara` [$N=5.204$, RMSE $0{,}4380$ vs model de bază $0{,}4398$] și $+0{,}0058$ pe `toamna` [$N=6.761$, RMSE $0{,}4899$ vs model de bază $0{,}4918$]; global $R^2 = 0{,}0860$, RMSE $0{,}4680$ pe $11.965$ parcele și 82 blocuri de 5 km; primii 3 factori SHAP structurali: pe primăvară `clay_sg_top` 0,0482, `elev` 0,0323, `dist_network_m` 0,0298; pe toamnă `tprod_mean_2017_2023` 0,0499, `clay_sg_top` 0,0418, `elev` 0,0380). Rezultat negativ, păstrat și raportat. **NU se randează harta `vuln_score` și nici harta `factor_dominant`.** `model_metrics.json` și `vulnerability.gpkg` rămân în repo, marcate „rezultat negativ, nu se cartografiază”. | Mesajul lui Patrick, 09.11.2026 (`D-Q1-final`) |
| D23 (`D-titlu`) | 09.11.2026 | Produsul devine **„Atlasul secetei din 2024 — sudul Olteniei”** (înlocuiește titlul din D01). Se actualizează titlurile din `render/` și din documentație. | Mesajul lui Patrick, 09.11.2026 (`D-titlu`) |
| D24 (`D-03d`) | 09.11.2026 | **Carbonul LUCAS (03d) este amânat; nu se începe.** | Mesajul lui Patrick, 09.11.2026 (`D-03d`) |
| D25 (`PAS D-B`) | 09.11.2026 | **Harta-erou pe pierderea observată (`data/out/harta_erou.png` și `data/out/loss_2024.gpkg` în EPSG:3844):** (1) Strat principal: `loss_rel` like-for-like pe cele 11.971 parcele cu țintă (6.766 toamnă, 5.205 primăvară; tăiere P1=−1,7634 / P99=+0,7629 pe 240 parcele), afișat ca procent (`loss_rel × 100`) în 6 clase fixe: câștig (`< 0%`), `0–10%`, `10–25%`, `25–40%`, `40–55%`, `> 55%`; cele 1.266 parcele arabile fără an comparabil în gri („fără an comparabil”); non-arabilul cu contur fin, fără umplere. (2) Panou 1: distribuția pierderii pe grupe (primăvară: mediană +30,8%, P25 +2,3% – P75 +52,5%, $N=5.205$; toamnă: mediană +2,4%, P25 −30,8% – P75 +27,6%, $N=6.766$). (3) Panou 2: „Ce am testat și n-a explicat pierderea” (sol SoilGrids 250 m, relief, vânt, distanța la canale; $R^2$ spațial în interiorul grupelor $\approx 0$, validare pe blocuri de 5 km). (4) Panou 3: rezervat (gol, fără cifre provizorii) pentru irigat vs neirigat, de completat după Q2. | Mesajul lui Patrick, 09.11.2026 (`PAS D-B`) |

## Alese de agenți în cod (fără aprobare explicită)

| Nr. | Alegere | Unde |
|---|---|---|
| T1 | *(Înlocuită de D21)* Tipul de cultură: prag binar `NDVI aprilie >= 0,40` = toamnă, `< 0,40` = primăvară. | `gisday_lib.py:102-112` |
| T2 | Pierderea cere cel puțin 2 ani de referință cu același tip de cultură (referința = mediana anilor comparabili din 2017–2023). | `gisday_lib.py:115-138` |
| T3 | 03e trece singur pe HR-VPP când există toți cei 8 ani. | `notebooks/03e_target.ipynb`, celula 4 |
| T4 | Stratul 03b se numește „irigat” la F1 pe blocuri ≥ 0,75; altfel „candidate”. | `notebooks/03b_irrigation.ipynb`, celula 2 |
| T5 | Parcelele sub 0,5 ha se elimină (`P.area_ha >= 0.5`). FTW rulează cu `ftw-tools==1.4.3` și `torchgeo==0.7.2`. | `notebooks/02_parcels_ftw.ipynb`; `gisday_config.py:25-28` |
| T6 | Expunerea la vânt: ore peste 30 °C fără ploaie, direcții cu cel puțin 5% din ore, elemente lemnoase SWF + WVL 2021 până la 20H = 300 m. | `notebooks/03c_wind.ipynb`, celulele 2–4 |
| T7 | Factorii din 04: distanța la canal și la rețea, expunerea la vânt, panta, altitudinea, carbon, nisip, argilă (SoilGrids), suprafața, tipul de cultură 2024, media TPROD 2017–2023. | `notebooks/04_vulnerability_model.ipynb`, celula 4 |

## De decis (Patrick)

- Aprobarea hărții-erou (`PAS D-B`, `data/out/harta_erou.png` și `data/out/loss_2024.gpkg`) înainte de începerea `PAS Q2` (irigat 2024).
