# Atlasul secetei din 2024 — sudul Olteniei

Hartă web pentru telefon: pierderea de productivitate a vegetației în 2024, parcelă cu parcelă, în sudul Olteniei (Sadova – Bechet – Dăbuleni – Corabia). Prezentată la GIS Day 2026.

**Adresa:** https://lefterpatrickandrei-sketch.github.io/atlas-seceta-2024/

**Uz necomercial.** Parcelele provin dintr-un model publicat pentru uz necomercial (vezi „Atribuiri și restricții”).

## Ce arată

Fiecare parcelă e colorată după pierderea de productivitate a vegetației (HR-VPP TPROD) din 2024, față de mediana anilor 2017–2023 în care a avut același tip de cultură (primăvară sau toamnă). „Câștig” înseamnă 2024 peste mediana acelor ani. **Nu e recoltă în t/ha.** Gri închis: fără an comparabil. Gri deschis: grup incert, adică tipul de cultură din 2024 nu e sigur. Contur: parcelă non-arabilă.

La atingerea unei parcele apar doar pierderea în %, grupul de cultură 2024 și suprafața în hectare.

## Fișiere

| Fișier | Ce conține |
|---|---|
| `index.html` | Pagina: MapLibre GL JS 4.7.1 de pe jsDelivr, fixat cu hash SRI; stilul și codul sunt în pagină |
| `date/parcele.geojson.gz` | 17.466 de parcele în EPSG:4326, GeoJSON comprimat gzip, 1,31 MB |
| `date/meta.json` | Legenda și încadrarea zonei |
| `.nojekyll` | Spune GitHub Pages să servească fișierele așa cum sunt |
| `README.md` | Acest fișier |

Fiecare parcelă are doar 4 atribute, fără identificatori: `c` = clasa (0–5 pierdere, 6 fără an comparabil, 7 grup incert, 8 non-arabil), `p` = pierderea în % (clasele 0–5), `g` = grupul de cultură 2024 (1 primăvară, 2 toamnă), `a` = suprafața în ha.

## Date și prelucrare

- **Proiecție:** analiza e făcută în Stereo 70 (EPSG:3844). Pentru web, parcelele sunt reproiectate în EPSG:4326.
- **Geometria nu e simplificată.** Poligoanele au deja ~15 vârfuri pe parcelă; simplificarea ar fi scos foarte puține vârfuri, dar ar fi deformat parcelele mici.
- **Precizie:** coordonatele sunt rotunjite la 5 zecimale (~1 m). Deplasarea maximă e 0,68 m, iar aria desenată se schimbă cu sub 1,9% la 99% din parcele. Suprafața afișată la atingere vine din datele originale.
- **Mărime:** pagina se încarcă cu ~1,8 MB transferați.

## Atribuiri și restricții (verificate pe 10.11.2026)

| Sursă | Licență și condiții | Atribuire pe pagină | Restricții |
|---|---|---|---|
| Copernicus Sentinel-2 (imaginile pentru delimitarea parcelelor și pentru tipul de cultură) | Date Copernicus libere și deschise | „Contains modified Copernicus Sentinel data 2024” | — |
| CLMS HR-VPP, TPROD sezonul 1 ([politica de date CLMS](https://land.copernicus.eu/en/data-policy)) | Acces „full, open and free”; trebuie spusă sursa, trebuie spus că produsul e modificat și nu se sugerează aprobarea UE | „Generated using European Union's Copernicus Land Monitoring Service information (HR-VPP, modificat)” | Fără sigle UE și fără formulări care sugerează aprobarea UE |
| Fields of The World, modelul `3_Class_FULL_FTW_Pretrained` ([ftw-baselines](https://github.com/fieldsoftheworld/ftw-baselines), [versiuni](https://github.com/fieldsoftheworld/ftw-baselines/releases)) | Checkpoint-urile FULL sunt pentru uz necomercial și academic; versiunile originale erau CC BY-NC, fiindcă datele de antrenare includ țări cu licențe necomerciale | „parcele Fields of The World (model CC BY-NC, uz necomercial)” | **Doar uz necomercial** |
| EUCROPMAP 2022, JRC ([`copyright.txt`](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EUCROPMAP/2022/copyright.txt); articol: Ghassemi et al. 2024, *Scientific Data* 11, [doi:10.1038/s41597-024-03884-y](https://doi.org/10.1038/s41597-024-03884-y)) | **CC BY 4.0** pentru date („© European Union, 1995–2026”) | „EUCROPMAP 2022 © Uniunea Europeană, JRC (CC BY 4.0, folosit pentru masca de arabil)” | Atribuire și mențiunea modificării |
| OpenStreetMap, prin fundal ([copyright OSM](https://www.openstreetmap.org/copyright)) | ODbL; pagina doar afișează fundalul și nu redistribuie date OSM | „Data from OpenStreetMap”, afișat permanent pe hartă | Atribuirea rămâne vizibilă |
| Fundal OpenFreeMap, stilul `dark` ([openfreemap.org](https://openfreemap.org/), [termeni](https://openfreemap.org/tos/)) | Gratuit, fără limită de afișări sau cereri, fără înregistrare, chei API sau cookie-uri; serviciul e „as is” și poate fi oprit fără anunț | „OpenFreeMap © OpenMapTiles Data from OpenStreetMap” (automat) | — |
| MapLibre GL JS 4.7.1 (BSD-3-Clause) și pako 2.1.0 (MIT și Zlib; se încarcă doar pe browsere fără `DecompressionStream`) | Biblioteci de cod, de pe jsDelivr, fixate cu SRI | — | — |

## Confidențialitate

Pagina nu pune cookie-uri. Browserul vizitatorului contactează `cdn.jsdelivr.net` (biblioteca) și `tiles.openfreemap.org` (fundalul), care văd adresa IP a vizitatorului.

## Cum se deschide local

Pagina citește datele prin `fetch`, deci are nevoie de un server web; direct din fișier (`file://`) nu merge. Din folderul site-ului:

```
python -m http.server 8000
```

Apoi deschizi `http://localhost:8000`.
