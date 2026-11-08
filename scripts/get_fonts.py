"""Aduce fonturile Inter (licență OFL) în render/fonts/. Rulare: .venv/Scripts/python.exe scripts/get_fonts.py"""
import io
import re
import zipfile
from pathlib import Path

import requests

URL = 'https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip'
PATTERN = r'extras/otf/(Inter|InterDisplay)-(Regular|Medium|SemiBold|Bold)\.otf|LICENSE\.txt'

dest = Path(__file__).resolve().parents[1] / 'render' / 'fonts'
dest.mkdir(parents=True, exist_ok=True)
response = requests.get(URL, timeout=180)
response.raise_for_status()
archive = zipfile.ZipFile(io.BytesIO(response.content))
for name in archive.namelist():
    if re.fullmatch(PATTERN, name):
        (dest / Path(name).name).write_bytes(archive.read(name))
print(sorted(p.name for p in dest.iterdir()))
