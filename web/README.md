# Atlasul secetei din 2024 — sudul Olteniei: harta web

Site static pentru telefon (codul QR de pe slide). **Nu este publicat.** Publicarea se face doar cu decizia lui Patrick.

## Fișiere

| Fișier | Ce conține |
|---|---|
| `index.html` | Pagina: MapLibre GL JS 4.7.1 de pe jsDelivr, fixat cu hash SRI; stilul și codul sunt în pagină |
| `date/parcele.geojson.gz` | 17.466 de parcele în EPSG:4326 (doar pentru web), GeoJSON comprimat gzip, 1,31 MB |
| `date/meta.json` | Legenda (aceleași clase și culori ca harta-erou) și încadrarea zonei |
| `README.md` | Acest fișier |

Fiecare parcelă are doar 4 atribute, fără id-uri: `c` = clasa (0–5 pierdere, 6 fără an comparabil, 7 grup incert, 8 non-arabil), `p` = pierderea în % (clasele 0–5), `g` = grupul de cultură 2024 (1 primăvară, 2 toamnă), `a` = suprafața în ha.

## Cum se deschide local

Pagina citește datele prin `fetch`, deci are nevoie de un server web; direct din fișier (`file://`) nu merge.

```
python -m http.server --directory web 8000
```

Apoi deschizi `http://localhost:8000`. Pe orice găzduire statică (de exemplu GitHub Pages sau Netlify) merge fără configurare: fișierul `.gz` se decomprimă în browser.

## Date și prelucrare

- **Sursa:** `data/out/loss_2024.gpkg` (EPSG:3844), prin `scripts/web_date.py`. Livrabilele rămân în EPSG:3844; reproiectarea în EPSG:4326 e doar pentru web.
- **Geometria nu e simplificată.** Poligoanele FTW au deja ~15 vârfuri pe parcelă. O toleranță de 1–5 m scotea sub 0,5% din vârfuri, dar deforma parcelele mici (la 5 m, până la 20% din arie).
- **Coordonatele sunt rotunjite la 5 zecimale (~1 m).** Deplasarea maximă e 0,68 m. Aria desenată se schimbă cu sub 1,9% la 99% din parcele și cu cel mult 4,6%. Suprafața din fereastră vine din datele originale, calculate în Stereo 70. După rotunjire, 3 poligoane au mici auto-atingeri, dar se desenează normal.
- **Mărime:** pagina se încarcă cu ~1,8 MB transferați (date 1,3 MB, MapLibre ~0,2 MB comprimat, fundal ~0,3 MB la vederea inițială).

## Atribuiri și restricții (verificate pe 10.11.2026)

| Sursă | Licență și condiții | Atribuire pe pagină | Restricții |
|---|---|---|---|
| Copernicus Sentinel-2 (imaginile pe care a rulat FTW și NDVI-ul din aprilie pentru grupele de cultură) | Date Copernicus libere și deschise | „Contains modified Copernicus Sentinel data 2024” | — |
| CLMS HR-VPP, TPROD sezonul 1 ([politica de date CLMS](https://land.copernicus.eu/en/data-policy)) | Acces „full, open and free”; trebuie spusă sursa, trebuie spus că produsul e modificat și nu se sugerează aprobarea UE | „Generated using European Union's Copernicus Land Monitoring Service information (HR-VPP, modificat)” | Fără sigle UE și fără formulări care sugerează aprobarea UE |
| Fields of The World, modelul `3_Class_FULL_FTW_Pretrained` ([ftw-baselines](https://github.com/fieldsoftheworld/ftw-baselines), [versiuni](https://github.com/fieldsoftheworld/ftw-baselines/releases)) | Checkpoint-urile FULL sunt pentru uz necomercial și academic; versiunile originale erau CC BY-NC, fiindcă datele de antrenare includ țări cu licențe necomerciale. Pentru uz comercial există checkpoint-uri CC-BY separate | „parcele Fields of The World (model CC BY-NC, uz necomercial)” | **Doar uz necomercial.** Documentația nu spune nimic explicit despre rezultatele modelului, așa că le tratăm prudent ca necomerciale |
| EUCROPMAP 2022, JRC ([`copyright.txt` pe serverul JRC](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EUCROPMAP/2022/copyright.txt); articol: Ghassemi et al. 2024, *Scientific Data* 11, [doi:10.1038/s41597-024-03884-y](https://doi.org/10.1038/s41597-024-03884-y)) | **CC BY 4.0** pentru date („© European Union, 1995–2026”, Decizia Comisiei 2011/833/UE). Licența CC BY-NC-ND 4.0 de pe pagina articolului e a articolului, nu a datelor | „EUCROPMAP 2022 © Uniunea Europeană, JRC (CC BY 4.0, folosit pentru masca de arabil)” | Atribuire și mențiunea modificării |
| OpenStreetMap, prin fundal ([copyright OSM](https://www.openstreetmap.org/copyright)) | ODbL; pagina doar afișează fundalul și nu redistribuie date OSM | „Data from OpenStreetMap”, afișat de MapLibre din stilul fundalului | Atribuirea trebuie să rămână vizibilă (e afișată permanent, nu ascunsă după buton) |
| Fundal OpenFreeMap, stilul `dark` ([openfreemap.org](https://openfreemap.org/), [termeni](https://openfreemap.org/tos/)) | Gratuit, fără limită de afișări sau cereri, fără înregistrare, chei API sau cookie-uri; uz comercial permis; serviciul e „as is” și poate fi oprit fără anunț | „OpenFreeMap © OpenMapTiles Data from OpenStreetMap” (automat) | Descărcările offline sunt limitate; pagina nu face descărcări offline |
| MapLibre GL JS 4.7.1 (BSD-3-Clause) și pako 2.1.0 (MIT și Zlib; se încarcă doar pe browsere fără `DecompressionStream`) | Biblioteci de cod, de pe jsDelivr, fixate cu SRI | — | — |

**De ce nu tile-urile OpenStreetMap standard:** [politica OSMF](https://operations.osmfoundation.org/policies/tiles/) permite blocarea fără anunț la „heavy use”, iar un cod QR la o conferință poate aduce un vârf de trafic. OpenFreeMap nu are limite declarate.

**Nimic din licențele verificate nu interzice publicarea** unei pagini necomerciale de prezentare, cu atribuirile de mai sus.

## Ce nu conține `web/`

Nu conține `.env`, `data/private/`, LUCAS, `labels.csv`, stratul `irigat` (nevalidat, D36), pivoții, chei, căi de pe PC sau id-uri de parcele.

## Confidențialitate

Pagina nu pune cookie-uri. Browserul vizitatorului contactează `cdn.jsdelivr.net` (biblioteca) și `tiles.openfreemap.org` (fundalul), care văd adresa IP a vizitatorului.
