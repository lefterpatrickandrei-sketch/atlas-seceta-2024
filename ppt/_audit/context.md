# Context și cifre-cheie (Atlasul secetei 2024 — sudul Olteniei)

- **Produs:** „Atlasul secetei din 2024 — sudul Olteniei” (D23), GIS Day 2026 (18.11.2026).
- **Parcele:** 17.466 parcele Fields of The World (FTW) ≥ 0,5 ha (826,5 km²); 13.237 arabile; 11.048 cu țintă calculată (1.036 grup incert excluse, D26).
- **Ținta:** `loss_rel` like-for-like (TPROD 2024 vs mediana 2017–2023 pe același grup de cultură, NDVI apr. prag 0,40).
- **Pierdere 2024:** Primăvară: 30% (interval 24–30% după referință); Toamnă: 0–18% după referință (D34).
- **Model 04 (rezultat negativ):** LightGBM pe 11 factori structurali; R² spațial cv 5 km: +0,0033 (primăvară), +0,0058 (toamnă), 0,086 global. Factorii structurali NU explică pierderea. Nu se cartografiază (D22).
- **Irigat 2024 (rezultat negativ / nelivrabil):** Regula S1 radar (Varianta B) nu separă irigarea (placebo miriști toamnă 3,91% vs primăvară 3,40%, D30). Evaluarea Olofsson din `labels.csv` este INVALIDĂ (etichete neconforme cu criteriul foilor, D36). Stratul este NEVALIDAT și NELIVRABIL.
- **Pivoți:** 121 geometrici (majoritatea pătrate/dreptunghiuri); doar 6 rotunzi (77,4 ha) desenați pe harta-erou (D31).
- **Sfârșit sezon (EOSD):** Sezonul 2024 s-a încheiat mai devreme: −10 zile pe primăvară (referință V105 2021–2023, D33).
- **Resurse GPU / EE:** Inferență FTW pe Colab GPU este nedovedită ca A100 (fișa tehnică §2); orele EE sunt necunoscute (fișa tehnică §5).
- **Livrabile în `data/out/final/`:** 7 PNG 1920×1080 (`harta_erou`, `parcele_ftw`, `model_negativ`, `placebo_radar`, `sfarsit_sezon`, `tprod_pe_ani`, `meteo_2024`), 1 QR (`qr_harta.png`), 2 video MP4 (`atlas_tprod_2017_2024.mp4`, `zbor_3d_pierdere_2024.mp4`).
- **Harta web:** Publicată necomercial pe GitHub Pages: `https://lefterpatrickandrei-sketch.github.io/atlas-seceta-2024/` (D38).
- **Limite obligatorii pe slide:** Modelul arată asocieri, nu cauze dovedite; TPROD măsoară productivitatea vegetației, nu recolta în t/ha; datele LUCAS rămân strict agregate, fără puncte individuale (D09).

