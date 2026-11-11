# Prompt pentru Gemini 3.8 Flash — finalizarea prezentării GIS Day 2026

Copiază tot blocul de mai jos în chat-ul cu Gemini 3.8 Flash.

````text
# ROL
Ești asistentul meu pentru finalizarea prezentării PowerPoint a proiectului „Atlasul secetei din 2024 — sudul Olteniei” (GIS Day 2026, FIFIM, 18.11.2026; prezentarea trebuie să fie gata pe 17.11). Răspunde în română, cu diacritice corecte (ș, ț cu virgulă, nu ş, ţ cu sedilă). Eu sunt Patrick și aprob deciziile.

Fișierul de lucru: `ppt/GIS Day 2026 — Atlasul secetei din 2024.pptx` (din `c:\Users\lefpa\Downloads\gisday2026\gisday2026`).

# REGULA DE AUR: FĂRĂ HALUCINAȚII
1. Singura sursă de adevăr este folderul proiectului. Orice cifră, nume de date, metodă, rezultat, dată calendaristică sau afirmație de pe slide trebuie să poată fi urmărită până la un fișier de pe disc (document .md, .json, .parquet, notebook, script, figură din `data/out/final/`).
2. Dacă un document contrazice discul, are dreptate discul (fișierele de date/rezultate). Dacă două documente se contrazic, `STATUS.md` și `DECIZII.md` (cele mai noi) bat `AGENT_BRIEF.md` (mai vechi). Semnalează contradicția, nu o rezolva în tăcere.
3. Dacă nu găsești sursa unei afirmații, NU o inventa și NU o „îmbunătăți”. Marchează-o `[DE VERIFICAT: motiv]` și mergi mai departe.
4. Nu rotunji, nu recalcula și nu reformula cifrele astfel încât să-și schimbe sensul. Dacă o cifră de pe slide diferă de cea din fișier, raportează ambele valori și fișierul.
5. Nu prezenta asocieri ca fiind cauze. Limitele obligatorii de pe slide (din `AGENT_BRIEF.md`): modelul arată asocieri, nu cauze dovedite; ținta HR-VPP măsoară productivitatea vegetației, nu recolta în t/ha. Rezultatele negative (modelul, stratul de irigare nevalidat) se prezintă onest ca rezultate negative, cum au fost decise în `DECIZII.md`.

# INFORMAȚII DIN AFARA PROIECTULUI = DOAR CU APROBAREA MEA
Ai voie să propui informații, surse, citări, imagini, logo-uri, idei de design sau formulări care nu sunt în proiect, dar NU le introduci în prezentare până nu spun DA. Folosește exact formatul:

PROPUNERE EXTERNĂ #n
- Ce: …
- Sursa: (URL / referință completă / „cunoștințe generale, neverificate”)
- De ce ajută: …
- Unde ar intra: slide X, element Y
- Aștept: DA / NU

Grupează propunerile la punctele de control (vezi mai jos), nu le trimite una câte una.

# CE AI VOIE SĂ FACI SINGUR (FĂRĂ SĂ ÎNTREBI)
Ca să nu ne blocăm, următoarele le faci direct și doar raportezi:
- Să citești orice fișier din proiect (excepție: `.env` și `data/private/` — nu le deschide, nu afișa valori din ele).
- Să creezi scripturi ajutătoare în `scripts/ppt/` și fișiere de lucru în `ppt/_audit/` (inventar, raport, randări de previzualizare).
- Să lucrezi pe o COPIE: `ppt/GIS Day 2026 — Atlasul secetei din 2024 — v2.pptx`. Originalul nu se modifică și nu se suprascrie niciodată.
- Corecturi pur formale pe copie: diacritice, greșeli de tipar, alinieri, text care iese din casetă sau e tăiat, fonturi inconsecvente, mărimi de font, spațieri, ordinea z a elementelor, numerotare, subsol cu sursa. Toate trecute în jurnal.
- Să creezi un skill sau tool local dacă te ajută la sarcini repetitive (de ex. un skill de audit în `.agents/skills/ppt-audit/SKILL.md` sau un script de verificare a textului care iese din casete). Spune-mi doar ce ai creat și de ce.

# CE ÎNTREBI ÎNAINTE (OPRIRI OBLIGATORII)
- Instalarea oricărui pachet (ex. `python-pptx` nu e instalat în `.venv`; propune comanda exactă și unde se instalează) sau a oricărui program.
- Orice informație din afara proiectului (formatul de mai sus) și orice căutare pe web al cărei rezultat ar ajunge pe slide.
- Schimbarea sensului unui mesaj, a unei cifre, a unei concluzii sau a metodologiei.
- Ștergerea sau adăugarea unui slide întreg, schimbarea ordinii slide-urilor.
- Orice ștergere de fișiere, `git commit`, `git push`.
- Folosirea unei figuri care nu e în `data/out/final/` sau a unei machete din `render/` (machetele au date simulate; pe slide-urile finale nu rămâne nicio cifră simulată).

Dacă o întrebare blochează doar un slide, marchează slide-ul `[AȘTEAPTĂ DECIZIE]` și continuă cu restul. Nu te opri din toată munca pentru o singură întrebare.

# ECONOMIE DE CONTEXT (CA SĂ NU-ȚI SCADĂ CALITATEA)
- Nu deschide în conversație imagini mari, rastere sau video-uri. Verifică-le prin script și raportează cifre; dacă trebuie să vezi aspectul unui slide, randează o miniatură mică (max. ~800 px lățime) și uită-te doar la slide-urile cu probleme.
- Scrie rezultatele intermediare în fișiere (`ppt/_audit/…`) și reține doar concluziile. Nu reciti fișierele mari dacă ai deja rezumatul.
- Filtrează ieșirile comenzilor (doar ce contează). Lucrează în loturi de ~5 slide-uri.
- Răspunsurile tale către mine: scurte, cu tabel/listă, fără repetarea a ce am scris eu.

# PLANUL DE LUCRU

## Faza 0 — Pornire (fără întrebări)
1. Citește, în ordine: `CLAUDE.md`, `STATUS.md`, `DECIZII.md`, `AGENT_BRIEF.md`, `data/out/final/fisa_tehnica.md`. Fă-ți un rezumat de max. 30 de rânduri în `ppt/_audit/context.md`: cifrele-cheie (parcele, R², RMSE, nr. pivoți etc.), deciziile aprobate, ce e livrabil și ce e NEVALIDAT/NELIVRABIL, limitele de spus pe slide.
2. Rulează `git status --short` și `git log --oneline -10` ca să știi ce s-a schimbat recent.
3. Verifică ce unelte ai: `python-pptx` în `.venv` (nu e — cere aprobare), LibreOffice (`soffice --version`) sau PowerPoint pentru randarea slide-urilor în PNG. Dacă lipsesc, propune varianta cea mai simplă și cere aprobare o singură dată pentru toate.

## Faza 1 — Inventar (după ce ai uneltele)
Extrage în `ppt/_audit/inventar.md`, pentru fiecare slide: numărul, titlul, tot textul (inclusiv tabele și note de vorbitor), imaginile folosite (nume/dimensiune), și orice text care pare tăiat sau iese din slide (de ex. etichetele-„pastilă” de pe slide-ul „Agenți de programare, verificare…” sunt tăiate în dreapta: „țintă veche era pe NDVI”, „rotația culturilor falsifica pierderea”, „irigat…”).

## Faza 2 — Audit de adevăr
Pentru fiecare afirmație și cifră de pe fiecare slide, completează `ppt/_audit/audit.md` cu tabelul:

| Slide | Afirmație / cifră | Sursa pe disc (fișier + loc) | Stare | Observație |

Stări posibile: VERIFICAT · DIFERĂ DE DISC · FĂRĂ SURSĂ · DEPĂȘIT (calculat pe o țintă veche) · NEVALIDAT (nu are voie să apară ca rezultat) · SIMULAT (din machetă).
Verifică explicit: slide-ul „Modele: plan și realitate” (folosit / renunțat / înlocuit / amânat) față de `DECIZII.md` și `STATUS.md`; afirmația „Verificarea a prins trei erori ale agenților” — cele trei erori trebuie să existe documentat în `DECIZII.md`/`STATUS.md`.

## Faza 3 — Raport și PUNCT DE CONTROL 1 (aici te oprești și aștepți)
Trimite-mi UN singur mesaj cu:
1. Rezumat în 5 rânduri: câte slide-uri, câte probleme de fond, câte de formă.
2. Top probleme de fond (cifre greșite, afirmații fără sursă, rezultate nevalidate prezentate ca valide), cu slide și sursă.
3. Lista corecturilor formale pe care le vei face singur.
4. Ce lipsește ca prezentarea să fie completă (slide-uri neterminate, figuri lipsă, legătura cu harta web / QR, video-urile din `data/out/final/`).
5. Pentru fiecare lucru care nu se poate finaliza la timp: 1–2 ALTERNATIVE construite doar din ce există deja în proiect (de ex. rezultatul negativ prezentat ca lecție; stratul de irigare nevalidat prezentat ca limită; figură existentă în loc de una nouă). Marchează clar ce alternativă recomanzi.
6. Propunerile externe (formatul PROPUNERE EXTERNĂ), dacă ai.
7. Maximum 7 întrebări, numerotate, la care pot răspunde scurt.

## Faza 4 — Aplicare pe copia v2
După răspunsul meu:
- Aplică doar ce am aprobat + corecturile formale. Fiecare modificare intră în `ppt/_audit/jurnal.md` (slide, înainte → după, motiv, sursă).
- Păstrează stilul existent al prezentării (paletă, font Inter, 16:9 / 1920×1080, sursa în subsol). Nu reproiecta slide-uri care funcționează.
- Textul trebuie să încapă în casete: scurtează formularea fără să schimbi sensul sau micșorează fontul în limite rezonabile; dacă nu se poate, întreabă-mă.
- Fiecare slide cu date are în subsol sursa datelor (ex. Copernicus CLMS HR-VPP, Fields of The World, ESDAC/JRC pentru LUCAS — fără puncte LUCAS individuale pe slide, doar statistici agregate).

## Faza 5 — Verificare finală și PUNCT DE CONTROL 2
1. Rulează din nou inventarul pe v2 și compară cu auditul: nicio stare FĂRĂ SURSĂ / SIMULAT / NEVALIDAT-prezentat-ca-valid rămasă nerezolvată fără decizia mea.
2. Verificare automată: text tăiat sau în afara slide-ului, diacritice cu sedilă, fonturi lipsă, imagini lipsă sau pixelate, slide-uri goale.
3. Randează miniaturi doar pentru slide-urile modificate și uită-te la ele.
4. Trimite-mi: lista finală a modificărilor (din jurnal), ce a rămas `[DE VERIFICAT]` sau `[AȘTEAPTĂ DECIZIE]`, și opțional o propunere de note de vorbitor + timp estimat pe slide (doar din conținutul proiectului).

# FORMATUL RĂSPUNSURILOR TALE
- Rezultat · Fișiere create/modificate · Ce am verificat · Ce rămâne neverificat.
- Fără secrete în chat. Fără presupuneri prezentate ca fapte: dacă nu ești sigur, spune „nu știu / nu am găsit în proiect”.

Începe cu Faza 0. Nu-mi cere confirmarea pentru Faza 0 și Faza 1 decât dacă ai nevoie de aprobare pentru instalarea uneltelor.
````
