# GIS Day 2026: Atlasul secetei din 2024 — sudul Olteniei

Proiect separat de StratumRO. Răspunde în română. Prezentarea e pe 18.11.2026.

## La pornire
Citește, în ordine: `STATUS.md`, `DECIZII.md`, `AGENT_BRIEF.md`.
Apoi verifică pe disc: `git status --short` și `git log --oneline -15`.
Nu te baza pe memorie: dacă un document contrazice discul, are dreptate discul.

## Reguli
1. Fără secrete în chat: nu afișa, nu cere și nu copia valori din `.env` sau `data/private/`. Dacă lipsește o cheie, spune fișierul și numele variabilei.
2. `.env` și `data/private/` nu intră în git. La commit adaugă fișierele pe nume, nu cu `git add -A`.
3. Toate livrabilele sunt în EPSG:3844. Configurarea comună stă doar în `gisday_config.py`.
4. Output-uri scurte: filtrează ieșirile comenzilor. Raportul are rezultatul, fișierele, verificarea făcută și ce rămâne neverificat.
5. Nu deschide în conversație imagini mari (hărți, foi de etichetare, rastere). Verifică-le prin script și raportează cifre.
6. Oprește-te și întreabă la punctele din „Opriri obligatorii” din `data/PROMPT_OPUS.md` (fișier local, neversionat): cheie sau fișier lipsă, autentificare în browser, eroare 401/403, `git push` când în arbore e altceva decât cod, notebook, config sau rezultate mici, orice ștergere, schimbare de metodologie, R² spațial sub 0,3, cota Earth Engine sau Colab pe terminate.

## Evidența
După fiecare etapă actualizează `STATUS.md` (stare, dovadă, pasul următor).
Orice decizie nouă intră în `DECIZII.md`, cu data și sursa.
