"""Publish a separately named PRG, preview and receipt for each editor build."""
import hashlib
import json
import shutil
import sys
from pathlib import Path


def package(build_root, dist):
    for folder in sorted(Path(build_root).iterdir()):
        metadata = folder / 'build.json'
        if not metadata.is_file():
            continue
        receipt = json.loads(metadata.read_text())
        if receipt.get('renderer') != 'P2':
            continue
        slug = receipt['slug']
        stem = f"{slug}-P2-{receipt['buildId']}-venux1"
        source = Path(dist) / f'{slug}-venux1.prg'
        if not source.is_file() or not source.stat().st_size:
            raise ValueError(f'Missing compiled PRG: {source}')
        receipt.update(file=stem+'.prg', preview=stem+'.png',
                       sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        shutil.copyfile(source, Path(dist) / receipt['file'])
        shutil.copyfile(folder / 'vorschau.png', Path(dist) / receipt['preview'])
        (Path(dist) / (stem+'.json')).write_text(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    package(*sys.argv[1:])
