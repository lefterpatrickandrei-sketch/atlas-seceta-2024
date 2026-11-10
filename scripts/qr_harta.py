"""Codul QR spre harta web publică: data/out/final/qr_harta.png, negru pe alb, cel puțin 1000 px, cu margine albă de 4 module.

Verificare: codul se decodifică din imaginea finală și dintr-o copie micșorată la 300 px (ca o fotografie de pe ecran);
textul decodificat trebuie să fie exact adresa.

Cere segno (generare) și zxing-cpp (decodificare), care nu sunt în .venv-ul proiectului:
  pip install segno zxing-cpp
  python -X utf8 scripts/qr_harta.py
"""
import math
from pathlib import Path

import segno
import zxingcpp
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://lefterpatrickandrei-sketch.github.io/atlas-seceta-2024/'
TARGET = ROOT / 'data' / 'out' / 'final' / 'qr_harta.png'
MIN_PX, BORDER = 1000, 4


def decode(image):
    found = zxingcpp.read_barcodes(image)
    return [r.text for r in found if r.format == zxingcpp.BarcodeFormat.QRCode]


def main():
    qr = segno.make(URL, error='m', micro=False)
    modules = qr.symbol_size(scale=1, border=BORDER)[0]
    scale = math.ceil(MIN_PX / modules)
    qr.save(str(TARGET), kind='png', scale=scale, border=BORDER, dark='#000000', light='#ffffff')
    image = Image.open(TARGET).convert('L')
    small = image.resize((300, 300), Image.LANCZOS)
    full_text, small_text = decode(image), decode(small)
    assert image.size[0] >= MIN_PX and image.size[0] == image.size[1], image.size
    assert full_text == [URL] and small_text == [URL], (full_text, small_text)
    corners = [image.getpixel(xy) for xy in ((0, 0), (image.size[0] - 1, 0), (0, image.size[1] - 1), (image.size[0] - 1, image.size[1] - 1))]
    print(f'scris: {TARGET.relative_to(ROOT).as_posix()} | {image.size[0]}×{image.size[1]} px | versiune-corecție {qr.designator} | '
          f'{modules} module cu margine, {scale} px/modul, margine albă {BORDER * scale} px (colțuri {set(corners)}) | '
          f'decodificat: {full_text[0]} (și din copia de 300 px)')


if __name__ == '__main__':
    main()
