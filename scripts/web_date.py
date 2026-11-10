"""Datele pentru harta web (web/): parcelele din data/out/loss_2024.gpkg, reproiectate în EPSG:4326 doar pentru web.

Livrabilele rămân în EPSG:3844; aici se scriu doar:
  web/date/parcele.geojson.gz   GeoJSON comprimat gzip, cu 4 atribute pe parcelă și fără id-uri interne:
                                c = clasa (0–5 pierdere, 6 fără an comparabil, 7 grup incert, 8 non-arabil),
                                p = pierderea în % (doar clasele 0–5), g = grupul de cultură 2024 (1 primăvară, 2 toamnă; doar c ≤ 6),
                                a = suprafața în ha
  web/date/meta.json            legenda (aceleași clase și culori ca harta-erou, din render/atlas.py), numărul de parcele și încadrarea

Geometria nu se simplifică: poligoanele FTW au deja ~15 vârfuri pe parcelă, iar o toleranță de 1–5 m scoate sub 0,5% din
vârfuri, dar deformează parcelele mici (la 5 m, până la 20% din arie). Se reduce doar precizia la 5 zecimale (~1 m).

Rulare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/web_date.py
"""
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'render')]

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402

import atlas  # noqa: E402
from gisday_config import OUT  # noqa: E402

WEB = ROOT / 'web' / 'date'
DECIMALS = 5
EXTRA = {'fără an comparabil': 6, 'grup incert': 7, 'non-arabil': 8}
GROUP = {'primavara': 1, 'toamna': 2}


def hex_color(rgb):
    return '#' + ''.join(f'{int(v):02x}' for v in rgb)


def thousands(n):
    return f'{n:,}'.replace(',', '.')


def rings(geom):
    """Coordonatele unei geometrii ca listă de poligoane, rotunjite la DECIMALS."""
    return [[[[round(x, DECIMALS), round(y, DECIMALS)] for x, y in ring.coords] for ring in (poly.exterior, *poly.interiors)]
            for poly in getattr(geom, 'geoms', [geom])]


def main():
    G = gpd.read_file(OUT / 'loss_2024.gpkg')
    assert G.crs.to_epsg() == 3844
    code = {label: i for i, label in enumerate(atlas.LOSS_CLASS_LABELS)} | EXTRA
    assert set(G.clasa_pierdere) <= set(code), set(G.clasa_pierdere) - set(code)
    G['c'] = G.clasa_pierdere.map(code).astype(int)
    assert G.loc[G.c <= 6, 'tip_cultura_2024'].isin(list(GROUP)).all(), 'clasă cu pierdere fără grup primăvară/toamnă'
    assert G.loc[G.c <= 5, 'loss_pct_lfl'].notna().all()

    web = G.to_crs(4326)
    features = []
    for row, geom in zip(G.itertuples(), web.geometry):
        props = {'c': int(row.c)}
        if row.c <= 5:
            props['p'] = round(float(row.loss_pct_lfl), 1)
        if row.c <= 6:
            props['g'] = GROUP[row.tip_cultura_2024]
        props['a'] = round(float(row.area_ha), 1)
        polys = rings(geom)
        geometry = {'type': 'Polygon', 'coordinates': polys[0]} if len(polys) == 1 else {'type': 'MultiPolygon', 'coordinates': polys}
        features.append({'type': 'Feature', 'properties': props, 'geometry': geometry})
    raw = json.dumps({'type': 'FeatureCollection', 'features': features}, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    packed = gzip.compress(raw, compresslevel=9, mtime=0)

    # Ce se pierde prin rotunjire: deplasarea maximă și schimbarea de arie, măsurate înapoi în EPSG:3844
    rounded = gpd.GeoSeries([shapely.geometry.shape(f['geometry']) for f in features], crs=4326).to_crs(3844).values
    shift = shapely.hausdorff_distance(G.geometry.values, rounded)
    area = np.abs(shapely.area(rounded) / shapely.area(G.geometry.values) - 1) * 100

    counts = G.c.value_counts().to_dict()
    legend = [{'cod': i, 'eticheta': label, 'culoare': hex_color(rgb), 'tip': 'umplere'}
              for i, (label, rgb) in enumerate(zip(atlas.LOSS_CLASS_LABELS, atlas.LOSS_CLASS_COLORS))]
    legend += [{'cod': 7, 'eticheta': f'Grup incert ({thousands(counts.get(7, 0))})', 'culoare': hex_color(atlas.INCERT_COLOR), 'tip': 'umplere'},
               {'cod': 6, 'eticheta': f'Fără an comparabil ({thousands(counts.get(6, 0))})', 'culoare': hex_color(atlas.NO_REF_COLOR), 'tip': 'umplere'},
               {'cod': 8, 'eticheta': f'Non-arabil ({thousands(counts.get(8, 0))})', 'culoare': hex_color(atlas.NON_ARABLE_OUTLINE), 'tip': 'contur'}]
    w, s, e, n = (round(float(v), 4) for v in web.total_bounds)
    meta = {'titlu': 'Atlasul secetei din 2024 — sudul Olteniei',
            'parcele': int(len(G)), 'parcele_cu_referinta': int((G.c <= 5).sum()),
            'legenda_titlu': f'Pierderea observată în 2024 ({thousands(int((G.c <= 5).sum()))} parcele cu referință)',
            'legenda': legend, 'incadrare': [w, s, e, n], 'zecimale_coordonate': DECIMALS}

    WEB.mkdir(parents=True, exist_ok=True)
    (WEB / 'parcele.geojson.gz').write_bytes(packed)
    (WEB / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    keys = sorted({k for f in features for k in f['properties']})
    print(f'parcele {len(features)} | atribute {keys} | geojson {len(raw) / 1e6:.2f} MB | gzip {len(packed) / 1e6:.2f} MB | vârfuri {int(shapely.get_num_coordinates(G.geometry.values).sum())}')
    print(f'rotunjire la {DECIMALS} zecimale: deplasare max {shift.max():.2f} m, P99 {np.percentile(shift, 99):.2f} m | arie |dif| P99 {np.percentile(area, 99):.3f}%, max {area.max():.2f}% '
          f'| invalide după rotunjire {int((~shapely.is_valid(rounded)).sum())}')
    print('clase', dict(sorted(counts.items())), '| încadrare', meta['incadrare'])


if __name__ == '__main__':
    main()
