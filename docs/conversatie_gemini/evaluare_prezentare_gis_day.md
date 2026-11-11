# Evaluare și optimizare prezentare GIS Day — conversație Gemini

> Transcriere a exportului `scrip gemini.pdf` (12 pagini, imagini fără text selectabil; copia originală e lângă acest fișier).
> Sursa conversației: https://gemini.google.com/app/3fbe09993d8743eb
> Exportul a fost citit pagină cu pagină și transcris. Cifrele sunt cele din export. **Nu toate au fost reverificate față de `DECIZII.md` / `data/out/` (vezi „Observații de verificat").**

## Cuprins
1. [Feedback pe prezentare: 4 retușuri](#1-feedback-pe-prezentare-4-retușuri)
2. [Cele două slide-uri cu video și exportul din Claude](#2-cele-două-slide-uri-cu-video-și-exportul-din-claude)
3. [Comparația între ani vs. între primăvară și toamnă](#3-comparația-între-ani-vs-între-primăvară-și-toamnă)
4. [Anual (efect) → lunar (cauză)](#4-anual-efect--lunar-cauză)
5. [Întrebări probabile din sală + răspunsuri](#5-întrebări-probabile-din-sală--răspunsuri)
6. [Rezumat detaliat al proiectului](#6-rezumat-detaliat-al-proiectului)
7. [Întrebări tehnice (cod, GIS, validare)](#7-întrebări-tehnice-cod-gis-validare)
8. [Terminologie: „agenți AI de programare" și ce a rulat unde](#8-terminologie-agenți-ai-de-programare-și-ce-a-rulat-unde)
9. [Discursul pe slide-uri (cu timpi)](#9-discursul-pe-slide-uri-cu-timpi)
10. [LLM multimodal vs. agent + glosar](#10-llm-multimodal-vs-agent--glosar)
11. [Diagrama fluxului de lucru](#11-diagrama-fluxului-de-lucru)
12. [Observații de verificat](#12-observații-de-verificat)

---

## 1. Feedback pe prezentare: 4 retușuri

Prezentarea e solidă metodologic (în special testul placebo pe miriști pentru Sentinel-1 și exemplul parcelei 10.771). Cele 4 detalii de corectat înainte de 18 noiembrie:

1. **Pragul NDVI între Planșa 4 și Planșa 7** (întrebare sigură din sală)
   - Planșa 4 explică zona tampon: `NDVI apr. sub 0,38` pentru primăvară și `NDVI apr. peste 0,45` pentru toamnă → de aici 1.036 parcele din „Grup incert" (între 0,38 și 0,45).
   - Planșa 7 (Pasul 4) simplifică la `NDVI aprilie, prag 0,40`, dar două rânduri mai jos spune „excluse: 1.036 incerte". Dacă pragul ar fi unic (0,40), n-ar exista parcele incerte. **De scris pe Planșa 7 ambele praguri, 0,38 / 0,45.**
2. **Diferența de 1% din rotunjire între Planșa 4 și Planșa 5**
   - Graficul de distribuție de pe Planșa 4: clasa `10–25%` la primăvară = **13%**, iar clasa `25–40%` la toamnă = tot **13%**.
   - Pe Planșa 5 (același grafic, mare), ambele valori apar ca **14%** (primăvară: 24% | 7% | 14% | 17% | 18% | 21%; toamnă: 50% | 10% | 15% | 14% | 8%). **De aliniat la aceleași procente.**
3. **Formularea „unde a pierdut seceta"** (Planșa 1 și 2)
   - În subtitlul de pe Planșa 1 și titlul de pe Planșa 2: „unde a pierdut seceta și ce a decis pierderea". Gramatical, „a pierdut seceta" sună ca și cum seceta ar fi fost învinsă.
   - Propunere: „unde a lovit seceta" sau „cât s-a pierdut în seceta din 2024", legat de titlul de pe Planșa 5 („Seceta a ales după calendar").
4. **Rezoluția siglelor** (Planșa 1 și 10)
   - Siglele USAMV, FIFIM și UGR din colțul dreapta-jos sunt pixelate și comprimate. De înlocuit cu PNG/SVG curate.

Întrebare rămasă deschisă de la Gemini: care e al doilea video, pe lângă animația 2017–2024 de pe Planșa 8 (e Planșa 4, cu zoom pe mozaicul parcelelor?).

## 2. Cele două slide-uri cu video și exportul din Claude

- Când încarci un `.pptx`, sistemul îl convertește într-un PDF static, deci videourile devin capturi de ecran.
- **Planșa 4** („Seceta din 2024, parcelă cu parcelă") și **Planșa 8** („Productivitatea vegetației pe parcele, 2017–2024") sunt singurele pe fundal închis, fără text nativ. Pe Planșa 8 se vede cadrul înghețat la finalul seriei 2017–2024 (chenar portocaliu pe 2024, evoluția medianei HR-VPP TPROD). În Anexa B apare `Video: deck.gl`.
- Fluxul: Planșa 4 → Planșa 5 și Planșa 8 → Planșa 9. Mai întâi rulezi vizualizarea pe fundal închis (contrast maxim pe proiectorul din Amfiteatrul II 1), apoi slide-ul static luminos cu cifrele-cheie (`30%`, `R² ≈ 0`, `3,40% vs. 3,91%`) și codul QR.

**Exportul direct ca PowerPoint din `claude.ai/artifact` aplatizează animațiile și videourile în imagini statice (PNG)**, de aceea Planșa 4 și 8 apar fără mișcare. Poziționarea Planșei 6 („Cum am lucrat") la finalul Părții 1 (5 minute) e corectă.

Ce descarci din meniul `claude.ai` (pentru videouri + backup):
- **Web page (.html)**: prezentarea exact ca în browser, permite legarea fișierelor `.mp4`.
- **PowerPoint, current fonts (.pptx)**: dacă prezinți de pe laptopul tău, cu fonturile instalate.
- **PowerPoint, basic fonts (.pptx)**: backup pe stick USB pentru PC-ul sălii din FIFIM, Amfiteatrul II 1, ca textul să nu se decaleze (*Basic fonts work on any computer*).

Ce i se cere lui Claude Code (local, în Antigravity IDE), după ce `.html` și `.pptx` sunt în folderul proiectului:
- **`.html` (și GitHub Pages):** să înlocuiască imaginile statice de pe Planșa 4 și 8 cu `<video autoplay loop muted playsinline>` care încarcă `.mp4` generate cu `deck.gl`, apoi `git commit` + `git push` pe GitHub Pages (lângă harta web MapLibre GL). În sală se rulează `.html`-ul în browser, cu `F11` (Fullscreen).
- **`.pptx`:** fie se adaugă manual `.mp4` pe slide-urile 4 și 8 (*Insert → Video → This Device*, cu *Start: Automatically*), fie se inserează automat cu `python-pptx` și se salvează în `git`.

## 3. Comparația între ani vs. între primăvară și toamnă

Metodologia e corectă: se fac **ambele comparații**, în două etape care răspund la întrebări diferite.

1. **ÎNTRE ANI (pe fiecare parcelă, doar în interiorul aceluiași sezon):** `pierdere = 1 − TPROD 2024 / mediana TPROD 2017–2023` doar cu anii în care parcela a avut **același tip de cultură** (primăvară cu primăvară, toamnă cu toamnă).
2. **ÎNTRE PRIMĂVARĂ ȘI TOAMNĂ (pentru cauză):** după calculul pierderii pe parcelă, cele 11.048 de parcele sunt împărțite în două grupe: primăvara are pierdere mediană de **30%**, toamna ≈ **0%** (−0,2%).

Dacă întreabă cineva de ce nu s-au comparat direct anii fără separare pe cultură:
- **Comparația brută între ani (fără separare)** e bună doar pentru biomasă regională sau rotație, nu pentru secetă. Culturile de toamnă (grâu, rapiță) au un `TPROD` de bază mult mai mare decât cele de primăvară. Exemplu pe Planșa 7: **parcela 10.771** a avut în 2024 cultură de primăvară (`TPROD = 491`); media tuturor anilor (cu grâu) e `1.062` → pierdere falsă de **54%**; comparată doar cu anii de primăvară (`493`) → pierdere reală **0%**.
- **Seria an cu an (Planșa 8):** în 2024 curba de primăvară cade la **534**, iar toamna rămâne la **917**.
- **Comparația primăvară vs. toamnă (Planșele 4, 5, 9) — necesară pentru cauzalitate:** fără separarea sezoanelor, arșița din iunie–august (Planșa 2) s-ar fi diluat într-o medie generală; modelul LightGBM ar fi părut că explică ceva (`R² global = 0,086`), dar acea putere vine exclusiv din diferența de calendar (toamnă `EOSD 9 iunie` vs. primăvară `EOSD 26 iulie`); în interiorul fiecărui sezon solul și terenul au `R² ≈ 0` (`0,003` și `0,006`).

Nu mai trebuie schimbat nimic la logică. La întrebare, se arată spre **Parcela 10.771 (Planșa 7)** și spre **graficul multianual (Planșa 8)**.

## 4. Anual (efect) → lunar (cauză)

- **Pierderea pe parcelă este ANUALĂ (2024 vs. 2017–2023):** `HR-VPP TPROD` măsoară productivitatea totală pe tot sezonul. Harta pierderii (Planșele 1, 4 și seria de pe 8) arată bilanțul anual față de mediana anilor 2017–2023 cu aceeași grupă de cultură.
- **Explicația diferenței dintre culturi este LUNARĂ (aprilie–septembrie 2024):** rezoluție lunară pe Planșa 2 (Contextul) și în graficul de jos de pe Planșa 5: seceta (32%, 47% și 21% din ploaia normală) și arșița (+3,4 °C … +4,3 °C peste normală) s-au concentrat în **iunie–august**. Culturile de toamnă își încheiaseră vegetația pe **9 iunie**; cele de primăvară au fost prinse în mijlocul sezonului (**26 iulie**).

Firul verbal:
1. **Planșa 1 (anual, 2024):** anunți rezultatul: `30%` pierdere la primăvară, `≈ 0` la toamnă.
2. **Planșa 2 (lunar, apr–sep):** arăți desfășurarea pe luni a verii 2024: de ce a lipsit apa (iunie–august) și de ce data de 9 iunie a salvat culturile de toamnă.
3. **Planșele 3–9 (anual 2017–2024 + sezoane):** la nivel de parcelă, cum ai calculat pierderea față de anii anteriori, cum evoluează harta an cu an (Planșa 8) și cum testele pe sol și radar (Planșa 9) confirmă că calendarul a făcut diferența.

## 5. Întrebări probabile din sală + răspunsuri

Direcții: îmbunătățiri funciare și agricultură, geodezie și teledetecție, metodologia cu agenți AI. Răspunsurile detaliate sunt în Anexele A, B, C.

1. **Irigațiile și radarul Sentinel-1** (întrebare sigură la FIFIM)
   - *De ce nu s-a văzut irigarea pe radar în zona Sadova–Dăbuleni–Corabia și ce s-a întâmplat cu pivoții circulari?*
   - **Răspuns (Planșa 4, 9, Anexa B):** în august, regula `VV ≥ 1,5 dB` dă `3,40%` evenimente pe culturi și `3,91%` pe miriști → pică testul placebo. Pivoții sunt identificați doar geometric și pot fi inactivi fără date din teren.
2. **Nisipurile de la Dăbuleni și `R² ≈ 0` la sol**
   - *Cum se explică faptul că solul nisipos și distanța la canale nu influențează pierderea (`R² = 0,003` primăvară, `0,006` toamnă)?*
   - **Răspuns (Planșa 3, 4, Anexa B):** fiecare parcelă e comparată cu propriul istoric (2017–2023), deci efectul permanent al solului e deja absorbit în referință. În plus, SoilGrids la 250 m e prea grosier pentru variații locale.
3. **Delimitarea automată vs. cadastru / APIA** (Geodezie, UGR)
   - *De ce 17.466 de parcele automat din Sentinel-2 (10 m) cu FTW, nu blocurile fizice APIA sau cadastrul?*
   - **Răspuns (Planșa 6 și 7):** doar date deschise, economie de **290–580 de ore** de digitizare manuală. Scenele din aprilie și iulie 2024 surprind limitele lucrate efectiv în acel sezon.
4. **Schimbarea versiunii HR-VPP (V101 vs. V105) și recolta în t/ha**
   - *TPROD nu măsoară recolta în t/ha; trecerea V101→V105 în 2021 nu distorsionează pierderea de 30%?*
   - **Răspuns (Planșa 10, Anexa A):** V105 dă cu 7,4% mai mult pe vegetația stabilă, dar pierderea la primăvară rămâne **28,8%** chiar și doar cu anii V105 (2021–2023). Tiparul e confirmat de INS (în acest export: porumb −29,0%, grâu −1,3%).
5. **Clasificarea culturilor doar în două grupe și rotația**
   - *De ce nu fiecare specie și cum ai evitat falsificarea prin rotație?*
   - **Răspuns (Planșa 4, 7, Anexa C):** NDVI-ul din aprilie (93,7% acord cu EUCROPMAP, 1.036 incerte excluse) separă exact calendarul verii. Compararea doar cu anii din aceeași grupă (ex. parcela 10.771) elimină eroarea rotației.
6. **Contribuția proprie vs. agenții AI (Claude Code și Gemini)**
   - *Dacă agenții au scris codul, care a fost contribuția ta și cum ai garantat că n-au inventat rezultate?*
   - **Răspuns (Planșa 6, Anexa B):** agenții au scris codul, dar verificarea umană și validarea pe 82 de blocuri de 5 km au oprit 3 erori critice: ținta pe NDVI, capcana rotației și irigația falsă pe miriști.

## 6. Rezumat detaliat al proiectului

**„Atlasul secetei din 2024 — Sudul Olteniei"**

**Obiectiv și zonă.** Analiză la nivel de parcelă a impactului secetei din vara 2024 pe **1.690 km²** (între Sadova, Bechet, Dăbuleni și Corabia, până la Dunăre), în **EPSG:3844 (Stereo 70)**. Scop: pierderea relativă de productivitate a vegetației în 2024 față de istoricul fiecărei parcele (2017–2023) pe aceeași grupă de cultură, și factorii care au decis pierderea (teren, apă din irigații, calendarul culturii).

**Contextul climatic (vara 2024).** ERA5-Land (C3S), față de normala 1991–2020: în aprilie–septembrie doar **72%** din precipitațiile normale (266 mm vs. 370 mm). Deficitul sever: iunie **32%**, iulie **47%**, august **21%**. Tmax medie peste normală cu **+2,5 °C** pe tot sezonul (+4,3 °C iunie, +3,9 °C iulie, +3,4 °C august; în export, ordinea lunilor e cea scrisă acolo). **23 de zile** cu `Tmax ≥ 35 °C` (3 în iunie, 13 în iulie, 7 în august) față de o medie multianuală de 5,8 zile. Național: **2,2 milioane ha** de culturi de primăvară afectate, doar **~2,7%** din arabil irigat.

**Metodologia în 5 pași (doar date deschise).**
1. Două scene **Sentinel-2** (10 m; B04, B03, B02, B08): 12 aprilie și 11 iulie 2024.
2. Rețeaua **Fields of The World** (`ftw-tools 1.4.3`, model cu 3 clase, rulat pe Google Colab) → **17.466** parcele; **13.237** arabile după JRC EUCROPMAP 2022.
3. Productivitatea sezonieră din **Copernicus CLMS HR-VPP TPROD** (10 m, sezonul 1, 24 de fișiere, 3,47 GB, tile T34TGP), 2017–2024.
4. Clasificare cultură: NDVI aprilie (prag general 0,40, cu intervale stricte `< 0,38` primăvară și `> 0,45` toamnă) → **93,7%** acord cu EUCROPMAP.
5. Ținta: `pierdere = 1 − TPROD_2024 / mediana TPROD_2017–2023`, doar cu minim 2 ani de referință în aceeași grupă → **11.048** parcele valide (**4.973** primăvară pe **18.154 ha**; **6.075** toamnă pe **39.004 ha**); excluse **1.036** incerte și **1.153** fără 2 ani comparabili.

**Capcana rotației.** Parcela 10.771: `TPROD_2024 = 491`; media tuturor anilor `1.062` (cu grâu) → pierdere falsă 54%; față de anii cu aceeași grupă (`493`) → nu a pierdut nimic.

**Cele trei ipoteze.**
1. **Calendarul culturii — CONFIRMATĂ.** Primăvară: pierdere mediană **+30,1%** (P25–P75: +1,4%…+52,1%). Toamnă: mediană **−0,2%** (P25–P75: −33,2%…+24,8%), jumătate din parcele câștig față de mediană. **HR-VPP EOSD:** 2024 = cel mai devreme sfârșit de sezon din seria 2017–2024: toamna pe **9 iunie** (față de 28 iunie în referință, cu 19 zile mai devreme); primăvara pe **26 iulie** (față de 16 august, cu 17,5 zile mai devreme).
2. **Terenul și solul — INFIRMATĂ.** `LightGBM 4.7.0` + `SHAP 0.54.1`, 11 variabile (altitudine/pantă din Copernicus DEM GLO-30; carbon, nisip, argilă din ISRIC SoilGrids 250 m; expunere la vânt; 2 distanțe la canale OSM; suprafață; grupă de cultură; TPROD mediu istoric), validat cu `GroupKFold` pe **82 de blocuri de 5 km** (11.965 parcele, 5 pliuri). În interiorul fiecărui sezon `R² = 0,003` (primăvară) și `0,006` (toamnă), sub pragul util de 0,10. `R² global = 0,086` (RMSE 0,468 vs. 0,490 la modelul de bază) vine doar din contrastul dintre sezoane.
3. **Apa / irigarea din radar — RESPINSĂ la placebo.** 34 de treceri Sentinel-1; regula: `VV` crește cu `≥ 1,5 dB` în 12 zile fără ploaie (`< 2 mm` în 5 zile, `< 5 mm` în interval, ERA5-Land), ferestre fără ploaie aproape exclusiv în august. Regula găsește **627** parcele de primăvară „irigate" (2.943,7 ha), pierdere mediană 31,95% vs. 29,96% pe cele 4.267 neirigate (diferență nesemnificativă: +1,99 pp, IC 95% −4,33…+7,15). Placebo pe miriști deja recoltate: „udări" în **3,91%** din cazuri vs. **3,40%** la primăvară (−0,52 pp, IC 95% −1,46…+0,43) → semnalul radar din august nu separă irigarea fără date din teren.

**Robustețea, validarea INS, agenții AI.** Pierderea la primăvară rămâne între **24% și 30%** indiferent de anii de referință: 30,1% (2017–2023), 23,5% (2020–2023), 28,8% (2021–2023, doar HR-VPP V105, care dă valori cu 7,4% mai mari pe 1.267 de parcele non-arabile stabile față de V101 din 2017–2020). Tiparul concordă cu **INS** (comunicat nr. 77 din 31.03.2025, randament 2024 vs. 2023, date provizorii): porumb −29,0%, floarea-soarelui −36,8%, grâu −1,3%. Cod: `rasterio 1.5.2`, `geopandas 1.2.0`, `earthengine-api 1.7.51`; animațiile `deck.gl` și harta web `MapLibre GL` (GitHub Pages). Scrise cu agenți AI (**Claude Code cu Claude Opus 5.5 și Gemini în Antigravity IDE**), cost suplimentar **0 €**, verificare umană la fiecare pas prin `STATUS.md`, `DECIZII.md` și `git`; economie de **290–580 de ore** de digitizare manuală.

## 7. Întrebări tehnice (cod, GIS, validare)

- **De ce `GroupKFold` pe blocuri de 5 km și nu `KFold` standard?** Autocorelație spațială: un split aleatoriu pune parcele vecine în train și test și umflă artificial `R²`; cele 82 de blocuri testează generalizarea reală.
- **De ce mediana (nu media) pentru referința 2017–2023?** Seriile sunt scurte (2–7 ani cu aceeași grupă); mediana e robustă la extreme anterioare (seceta din 2020, vârful din 2021 vizibile pe Planșa 8).
- **Cum s-a evitat ca saltul de +7,4% V101→V105 să strice rezultatul?** S-a măsurat eroarea sistematică pe 1.267 de parcele non-arabile stabile și s-a recalculat pierderea strict pe anii V105 (2021–2023): primăvara pierde tot 28,8% (~29%).
- **De ce s-a renunțat la CNN pentru sol și la Galileo?** `R² = 0,003` pe sol la 250 m: un CNN nu poate extrage semnal suplimentar din aceleași date grosiere; iar acordul de 93,7% pe NDVI aprilie a făcut inutilă clasificarea Galileo.

## 8. Terminologie: „agenți AI de programare" și ce a rulat unde

Pentru discursul vorbit: **„agenți AI de programare"** (nu „LLM multimodal" și nici „inteligența numerelor comerciale"). Numele exacte (Claude Code, Claude Opus 5.5, Gemini) rămân scrise pe Planșa 6 pentru transparență.

Împărțirea calculului (Planșa 6 și Anexa C):
- **Google Earth Engine:** strict extragerile de date satelitare și climatice.
- **Google Colab (GPU):** doar rularea rețelei neuronale **Fields of The World** (`ftw-tools 1.4.3`), care a delimitat cele 17.466 de parcele din scenele Sentinel-2. Celelalte modele mari planificate inițial pe GPU (Galileo și rețeaua CNN pentru sol) au fost abandonate.
- **PC local (CPU):** toate celelalte calcule și modele: LightGBM cu SHAP, testul radar și agregările statistice.

## 9. Discursul pe slide-uri (cu timpi)

*(Cu opțiunea de a sări de la Planșa 6 direct la Planșa 10 dacă sunt doar 5 minute, sau de a parcurge toate cele 10 planșe dacă sunt 8–10 minute.)*

**Planșa 1 · Titlul și miza (0:00 – 0:45).** Bună ziua. Fiecare hartă are o poveste, iar aceasta este a mea: o analiză parcelă cu parcelă a secetei din 2024 în sudul Olteniei. Am pornit de la două întrebări simple: unde a lovit seceta și ce anume a decis când două parcele vecine au avut rezultate complet diferite. Pe baza imaginilor Sentinel-2, am delimitat automat 17.466 de parcele și am ajuns la o concluzie clară: culturile de primăvară au suferit o pierdere medie de 30%, în timp ce culturile de toamnă au avut pierdere aproape zero.

**Planșa 2 · Contextul climatic (0:45 – 1:30).** Ca să înțelegem de ce, trebuie să ne uităm întâi la desfășurarea lunară a verii 2024. Între aprilie și septembrie a plouat doar 72% din normala climatologică — 266 mm față de 370 mm — însă lipsa apei și canicula s-au concentrat sever în iunie, iulie și august. În aceste trei luni, precipitațiile au scăzut la 32%, 47% și respectiv 21% din normală, iar temperaturile maxime au sărit cu peste 3,4 până la 4,3 grade peste medie, adunând 23 de zile cu cel puțin 35 °C față de nici 6 zile într-un an normal. Momentul decisiv se vede pe axa timpului: culturile de toamnă și-au încheiat sezonul de vegetație pe 9 iunie, exact înainte de arșiță, pe când cele de primăvară au rămas în câmp până pe 26 iulie.

**Planșa 3 · Zona și ipotezele (1:30 – 2:15).** Zona studiată acoperă 1.690 km² de-a lungul Dunării, între Sadova, Bechet, Dăbuleni și Corabia, în proiecție Stereo 70. Din cele 17.466 de parcele extrase automat cu rețeaua Fields of The World, 13.237 sunt terenuri arabile. Pentru a explica mozaicul pierderilor, am testat trei ipoteze: terenul (sol, relief, vânt, distanța la canale), apa (irigarea detectată din radar) și calendarul culturii (toamnă sau primăvară). Important de precizat: harta măsoară scăderea productivității vegetației în 2024 față de istoricul fiecărei parcele pe aceeași cultură, nu recolta în tone la hectar și nici evaluarea financiară a daunelor.

**Planșa 4 · Video 1: Harta pierderii, parcelă cu parcelă (2:15 – 3:15).** *(Lași videoul să ruleze pe ecran.)* Pe hartă vedem cele 11.048 de parcele cu istoric comparabil între 2017 și 2023. Contrastul dintre verde și roșu nu urmează nici lunca Dunării, nici rețeaua de canale. În dreapta sus se vede ruptura dintre sezoane: pe 4.973 de parcele de primăvară pierderea mediană este +30,1%, pe când pe cele 6.075 de parcele de toamnă mediana este −0,2%, jumătate din ele având chiar un an mai bun decât media lor istorică. Panourile 2 și 3 rezumă testele negative: în interiorul fiecărui sezon, solul și relieful au putere explicativă zero, iar semnalul radar din august nu reușește să separe irigarea.

**Planșa 5 · Sinteza rezultatului și harta web (3:15 – 4:00).** Așadar, seceta din 2024 a ales după calendar. Pierderea de 30% la culturile de primăvară rămâne stabilă — între 24% și 30% — indiferent ce ani alegem ca referință. Terenul nu a explicat diferențele, apa nu se vede din satelit fără date din teren, iar calendarul culturii a decis totul: toamna încheiase vegetația pe 9 iunie, primăvara a prins toată arșița din iulie–august. Dacă scanați codul QR de pe ecran, puteți deschide pe telefon harta interactivă și puteți căuta orice parcelă din zonă.

**Planșa 6 · Cum am lucrat cu agenții AI (4:00 – 4:50).** Am construit acest proiect folosind agenți AI de programare într-o buclă strictă de patru pași: agenții au scris codul, calculele au rulat în Earth Engine pentru extrageri, pe Colab pentru rețeaua neurală FTW și pe PC pentru restul analizelor, dar la pasul 3 agentul s-a oprit obligatoriu și a arătat cifrele înainte de orice decizie. Această verificare umană a oprit trei erori majore ale agenților: folosirea NDVI în loc de productivitatea vegetației TPROD, capcana rotației culturilor care făcea ca porumbul pus după grâu să pară calamitat și o falsă detecție a irigației pe radar. Totul a fost realizat cu 0 euro cost suplimentar, doar din date deschise, economisind între 290 și 580 de ore de digitizare manuală. *(Notă: dacă ai limită strictă de 5 minute, aici apeși pe „sari la concluzii" și treci direct la Planșa 10. Dacă ai timp complet, continui cu Planșele 7–9.)*

**Planșa 7 · Metoda în 5 pași și capcana rotației (4:50 – 5:45).** Metoda transformă pixelii în pierdere în cinci pași reproductibili. Plecăm de la două imagini Sentinel-2 din aprilie și iulie 2024 la 10 metri rezoluție, extragem contururile cu Fields of The World și filtrăm arabilul cu EUCROPMAP. Adăugăm seria de productivitate Copernicus HR-VPP TPROD din 2017 până în 2024 și separăm culturile de toamnă de cele de primăvară după NDVI-ul din aprilie, care are un acord de 93,7% cu clasificarea europeană. Pasul critic este al cincilea: comparăm 2024 doar cu anii în care parcela a avut aceeași grupă de cultură. Jos vedeți de ce: pe parcela 10.771, dacă raportăm anul 2024 la media tuturor anilor, pare că a pierdut 54% fiindcă în alți ani a avut grâu; comparată corect cu anii ei de primăvară, nu a pierdut nimic.

**Planșa 8 · Video 2: Seria multianuală 2017–2024 (5:45 – 6:30).** *(Lași al doilea video să ruleze.)* În această animație urmărim productivitatea vegetației an cu an, din 2017 până în 2024, pe aceeași scară de culori. Pe graficul din dreapta sus se vede cum, timp de șapte ani, curba portocalie a culturilor de primăvară și cea verde a culturilor de toamnă au evoluat apropiat. În 2024 apare ruptura: toamna rămâne sus, la o mediană de 917 unități TPROD, în timp ce primăvara se prăbușește la 534.

**Planșa 9 · Cele trei teste statistice (6:30 – 7:30).** Aici sunt cifrele din spatele celor trei teste. Primul: am antrenat un model LightGBM pe 11 factori de sol, relief, vânt și distanță la canale, validat spațial pe 82 de blocuri de 5 km; în interiorul sezonelor, R² este 0,003 la primăvară și 0,006 la toamnă — practic zero. Al doilea: regula radar pe Sentinel-1 (creștere VV de minimum 1,5 dB în 12 zile fără ploaie) dă 3,40% „udări" pe culturile de primăvară, dar când am rulat-o ca test placebo pe miriștile deja recoltate, unde nu udă nimeni, a dat 3,91%. De aceea am refuzat să livrăm un strat fals de irigații. Al treilea test confirmă cauza: indicatorul EOSD arată în 2024 cel mai timpuriu sfârșit de sezon din toată seria, cu aproape trei săptămâni mai devreme decât media 2017–2023.

**Planșa 10 · Concluzii (7:30 – 8:15).** În concluzie, rămânem cu trei idei principale. Unu: seceta din 2024 a lovit după calendar — primăvara a pierdut 30%, iar toamna a scăpat pentru că și-a încheiat sezonul pe 9 iunie. Doi: o hartă onestă arată și ceea ce nu poate măsura — solul la rezoluția globală nu explică diferențele locale, iar irigarea din august nu poate fi separată din radar fără date din teren. Trei: deși măsurăm vegetația din satelit, tiparul nostru se suprapune peste statistica națională INS, care indică scăderi de randament de 29% la porumb și 37% la floarea-soarelui, față de doar 1% la grâu. Vă mulțumesc și aștept întrebările dumneavoastră.

## 10. LLM multimodal vs. agent + glosar

La bază sunt **modele LLM multimodale cu capabilități de interacțiune externă** (*tool use / function calling*); „agent AI" descrie arhitectura prin care modelele sunt conectate la terminal, fișiere și `git` în `Antigravity IDE` și `Claude Code`.
- **Creierul (LLM multimodal):** `Claude Opus 5.5` și `Gemini` înțeleg simultan text, cod și imagini (hărți, histograme) și pot inspecta vizual planșele și diagnosticele.
- **Sistemul de execuție (agent):** rulează scripturi externe (Earth Engine, Colab, PC), citește ieșirile `.json` și se oprește la pragul de verificare umană înainte de a salva starea în `STATUS.md`, `DECIZII.md` și `git`.

### Glosar

**1. Teledetecție, sateliți, proiecții**
- **GIS** — Geographic Information System.
- **EPSG:3844 (Stereo 70)** — proiecția stereografică națională 1970 a României.
- **T34TGP** — caroiajul MGRS (100 × 100 km) pentru scena Sentinel-2 care acoperă sudul Olteniei.
- **B02, B03, B04, B08** — benzile Sentinel-2 (Albastru, Verde, Roșu, Infraroșu apropiat), 10 m.
- **NDVI** — Normalized Difference Vegetation Index; în aprilie (prag 0,40) separă culturile de toamnă de cele de primăvară.
- **CLMS** — Copernicus Land Monitoring Service.
- **HR-VPP** — High Resolution Vegetation Phenology and Productivity (Copernicus, 10 m).
- **TPROD** — Total Productivity: productivitatea totală a vegetației pe sezon.
- **EOSD** — End of Season Date: ziua în care se încheie ciclul de vegetație.
- **V101 / V105** — versiunile HR-VPP (V101: 2017–2020; V105: 2021–2024).
- **VV și dB (Sentinel-1)** — polarizarea Vertical-Vertical a radarului SAR și unitatea de măsură (decibeli).

**2. Baze de date spațiale și climatice**
- **ERA5-Land (C3S)** — reanaliza climatică (celule de ~10 km) pentru precipitații și temperaturi.
- **Tmax** — temperatura maximă zilnică (prag de caniculă ≥ 35 °C).
- **FTW (`ftw-tools 1.4.3`)** — Fields of The World: rețea de segmentare cu 3 clase (interior, limită, fundal) pentru delimitarea parcelelor.
- **JRC EUCROPMAP 2022** — harta europeană a culturilor (filtrarea arabilului).
- **ISRIC SoilGrids (250 m)** — proprietățile solului (carbon organic, nisip, argilă).
- **Copernicus DEM GLO-30** — modelul digital al altitudinii (30 m).
- **OSM (ODbL)** — OpenStreetMap, sursa canalelor de irigații.

**3. Modele, statistică, calcul**
- **LOSS_REL** — pierderea relativă 2024: `1 − TPROD_2024 / mediana TPROD_2017–2023`.
- **P25–P75** — intervalul intercuartilic.
- **LightGBM** — Light Gradient Boosting Machine (arbori de decizie), testează dacă cei 11 factori explică pierderea.
- **SHAP** — SHapley Additive exPlanations.
- **GroupKFold** — validare încrucișată pe grupuri spațiale (82 de blocuri 5 × 5 km, 5 pliuri).
- **R²** — coeficientul de determinație (0 = lipsă de relație).
- **RMSE / RMSD** — eroarea / abaterea pătratică medie.
- **pp** — puncte procentuale (ex. 3,40% − 3,91% = −0,52 pp).
- **IC 95%** — interval de încredere, prin bootstrap pe blocurile de 5 km.
- **CNN** — rețea neuronală convoluțională (eliminată după ce terenul a dat R² ≈ 0).
- **GPU A100 / EECU-ore** — placa NVIDIA A100 (40 GB) din Colab și Earth Engine Compute Units. *(Atenție: în repo, `fisa_tehnica` spune că tipul GPU nu e dovedit; vezi secțiunea 12.)*
- **INS** — Institutul Național de Statistică.
- **FIFIM / USAMV / UGR** — Facultatea de Îmbunătățiri Funciare și Ingineria Mediului, Universitatea de Științe Agronomice și Medicină Veterinară, Uniunea Geodezilor din România.

## 11. Diagrama fluxului de lucru

```
╔══════════════════════════════════════════════════════════════════╗
║ NIVELUL 1: BUCLA AGENTICĂ (LLM MULTIMODAL + EXECUȚIE EXTERNĂ)     ║
║                                                                   ║
║  1. SCRIE CODUL            2. CALCULEAZĂ (EXTERN)                 ║
║  Claude Opus 5.5/Gemini →  • GEE: extrageri date                  ║
║  în Antigravity IDE        • Colab: FTW                           ║
║        ▲                   • PC (CPU): LightGBM                   ║
║        │                          │                               ║
║  4. NOTEAZĂ STAREA   ←     3. VERIFICARE UMANĂ                    ║
║  STATUS.md, DECIZII.md     Agentul arată cifrele;                 ║
║  și commit în git          TU decizi (3 erori critice oprite aici)║
╚══════════════════════════════════════════════════════════════════╝
                               ▼
╔══════════════════════════════════════════════════════════════════╗
║ NIVELUL 2: PIPELINE-UL GEOSPAȚIAL ÎN 5 PAȘI (EPSG:3844)           ║
║                                                                   ║
║ [1] Sentinel-2 (10 m, T34TGP): 12.04.2024 & 11.07.2024 (B04,B03,  ║
║     B02,B08)                                                      ║
║ [2] Delimitare parcele (Colab GPU → PC): FTW (ftw-tools 1.4.3) →  ║
║     17.466 parcele; filtrare JRC EUCROPMAP 2022 → 13.237 arabile  ║
║ [3] Productivitate & climă 2017–2024: CLMS HR-VPP (TPROD & EOSD,  ║
║     V101/V105, 10 m) + ERA5-Land (precip/Tmax)                    ║
║ [4] Grupa culturii (în fiecare an): NDVI aprilie (prag 0,40:      ║
║     <0,38 primăvară / >0,45 toamnă); acord 93,7% cu EUCROPMAP;    ║
║     excluse 1.036 incerte                                         ║
║ [5] Ținta: minim 2 ani comparabili în aceeași grupă (11.048       ║
║     parcele); LOSS_REL = 1 − TPROD_2024 / mediana(TPROD_2017..    ║
║     2023, aceeași grupă). Primăvară +30,1% (4.973 parcele);       ║
║     Toamnă −0,2% (6.075 parcele)                                  ║
╚══════════════════════════════════════════════════════════════════╝
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
╔═════════════════╗ ╔═════════════════╗ ╔═════════════════╗
║ TEST 1: TEREN   ║ ║ TEST 2: IRIGARE ║ ║ TEST 3: CALENDAR║
║ & SOL           ║ ║ RADAR           ║ ║ (EOSD)          ║
║ LightGBM + SHAP ║ ║ Sentinel-1 (34  ║ ║ HR-VPP EOSD     ║
║ 11 factori      ║ ║ treceri), VV ≥  ║ ║ 2017–2024       ║
║ GroupKFold 82   ║ ║ +1,5 dB / 12    ║ ║ Toamna termină  ║
║ blocuri, 5 km   ║ ║ zile fără ploaie║ ║ pe 9 iunie      ║
║ R²=0,003 prim.  ║ ║ în aug.         ║ ║ Primăvara pe    ║
║ R²=0,006 toamnă ║ ║ Primăvară 3,40% ║ ║ 26 iulie (−17,5 ║
║ ► INFIRMAT      ║ ║ Placebo 3,91%   ║ ║ zile)           ║
║                 ║ ║ Dif. −0,52 pp   ║ ║ ► CONFIRMAT     ║
║                 ║ ║ ► INFIRMAT      ║ ║   (Cauza)       ║
╚═════════════════╝ ╚═════════════════╝ ╚═════════════════╝
                               ▼
╔══════════════════════════════════════════════════════════════════╗
║ VALIDARE EXTERNĂ & LIVRABILE FINALE (GIS DAY 2026 — FIFIM)        ║
║ • INS (2024 vs 2023): porumb −29,0%, floarea-soarelui −36,8%,     ║
║   grâu −1,3% → confirmă tiparul satelitar                         ║
║ • Livrabile: 2 animații video (deck.gl) + Hartă Web (MapLibre GL  ║
║   / GitHub)                                                       ║
╚══════════════════════════════════════════════════════════════════╝
```

*(Diagrama e redesenată din exportul Gemini; în original, caracterele de tip box-drawing sunt într-un bloc de cod.)*

Întrebarea finală din export: dacă vrei diagrama și ca pagină vizuală / imagine pentru documentația de pe GitHub.

## 12. Observații de verificat

Aceste puncte apar în exportul Gemini și **diferă de ce e scris în restul repo-ului** (`ppt/_audit/context.md`, `DECIZII.md`) sau între secțiunile exportului. De clarificat înainte de 18.11:

| Subiect | În exportul Gemini | În repo / alt loc din export |
|---|---|---|
| INS floarea-soarelui | −36,8% (sec. 6) / −37% (discurs) / „−29%, grâu −1,3%" (sec. 5) | Audit slide 5: floarea-soarelui **−37%**, grâu **−1%**, porumb **−29%**; Anexa A din deck: porumb **−31,5%**, floarea-soarelui **−26,0%** (INS provizoriu martie 2025) |
| Pragul NDVI | 0,40 pe Planșa 7, dar intervale 0,38 / 0,45 pe Planșa 4 | `DECIZII.md` D21: prag 0,40; de unificat pe slide (vezi retușul 1) |
| GPU A100 | „Placa NVIDIA A100 (40 GB)" în glosar | `ppt/_audit/context.md`: tipul GPU **nedovedit** (fișa tehnică §2); pe slide-ul deck-ului de după, tipul nu e afirmat |
| `Tmax` pe luni | +4,3 °C iunie, +3,9 iulie, +3,4 august (sec. 6) vs. „3,4–4,3 °C iunie–august" (sec. 4) | Audit: iunie **+3,4**, iulie **+4,3**, august **+3,8** (`meteo_2024.json`) |
| Zile cu Tmax ≥ 35 °C | 3 iunie / 13 iulie / 7 august | Audit: 13 în iulie, 10 în august (total 23) |
| Distribuție 13% vs 14% | rotunjire diferită Planșa 4 vs. 5 | de aliniat (retușul 2) |
| „Unde a pierdut seceta" | formulare ambiguă | de reformulat (retușul 3) |
| Siglele USAMV/FIFIM/UGR | pixelate | de înlocuit cu SVG/PNG (retușul 4) |

Numerele din audit sunt cele din `ppt/_audit/audit.md` (verificate de agent față de fișierele din `data/out/`). Pentru orice cifră spusă public, sursa de adevăr rămâne `DECIZII.md` și `data/out/`, nu acest export.
