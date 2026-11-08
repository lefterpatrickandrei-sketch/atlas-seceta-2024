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
| D16 | 08.11.2026 | 03b trece pe etichete slabe automate + 80 de parcele validate de Patrick. Înlocuiește planul cu ~200 de parcele digitizate și etichetele AI din 08.11. Detaliile sunt la Q2. | Mesajul lui Patrick, 08.11.2026 |

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

| Nr. | Întrebare |
|---|---|
| Q1 | Pe ce țintă rulează 04 și harta-erou: NDVI (doar culturi de primăvară, 4.161 parcele) sau HR-VPP (primăvară și toamnă, 9.895)? D03 pune HR-VPP pe primul loc, iar `parcel_target.parquet` e deja pe HR-VPP, dar 04 și harta sunt încă pe NDVI. Legat de asta: culturile de toamnă intră pe hartă și în model? |
| Q2 | Pentru D16: regula etichetelor slabe automate, cum se aleg cele 80 de parcele și dacă intră la antrenare sau doar la validare. |
| Q3 | Seria HR-VPP combină V101 (2017–2020) cu V105 (2021–2024). Se păstrează referința întreagă, cu mențiune pe slide, sau se restrânge? |
