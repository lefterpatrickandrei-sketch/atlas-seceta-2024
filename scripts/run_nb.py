"""Execută un notebook pe kernelul local (.venv) și îl salvează pe loc cu output-urile, inclusiv la eroare.

Utilizare, din rădăcina proiectului: .venv/Scripts/python.exe -X utf8 scripts/run_nb.py notebooks/X.ipynb [timeout_pe_celulă_în_secunde]
"""
import asyncio
import sys

import nbclient
import nbformat

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

path = sys.argv[1]
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 7200
nb = nbformat.read(path, as_version=4)
client = nbclient.NotebookClient(nb, kernel_name='python3', timeout=timeout, resources={'metadata': {'path': 'notebooks'}})
status = 'OK'
try:
    client.execute()
except nbclient.exceptions.CellExecutionError as err:
    status = 'EROARE: ' + str(err).strip().splitlines()[-1][:600]
finally:
    nbformat.write(nb, path)
print('STATUS', status)
for index, cell in enumerate(nb.cells):
    if cell.cell_type != 'code':
        continue
    for output in cell.get('outputs', []):
        text = output.get('text') or ''.join(output.get('data', {}).get('text/plain', ''))
        if output.get('output_type') == 'error':
            text = f"{output.get('ename')}: {output.get('evalue')}"
        if text:
            print(f'--- celula {index} ---')
            print(text[-3000:])
sys.exit(0 if status == 'OK' else 1)
