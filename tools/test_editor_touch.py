"""Run generated Portugal touch handlers in the running Connect IQ simulator."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from editor_build import generate, ROOT

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk',type=Path,required=True)
    parser.add_argument('--key',type=Path,required=True)
    args=parser.parse_args()
    sdk=args.sdk.resolve();key=args.key.resolve()
    with tempfile.TemporaryDirectory() as temp:
        project=Path(temp)
        generate(json.loads((ROOT/'designs/editor-portugal-kopie.json').read_text(encoding='utf-8')),project)
        shutil.copyfile(ROOT/'tests/editor_touch.mc',project/'source/TouchTests.mc')
        suffix='.bat' if os.name=='nt' else ''
        def run(name,*arguments):
            command=[str(sdk/'bin'/(name+suffix)),*map(str,arguments)]
            if os.name=='nt':command=['cmd','/c',*command]
            result=subprocess.run(command,cwd=project,check=True,capture_output=True,text=True,timeout=120)
            print(result.stdout)
            if result.stderr:print(result.stderr)
            return result.stdout
        run('monkeyc','-f','monkey.jungle','-d','venux1','-y',key,'-o','touch-tests.prg','-t','-l','0')
        output=run('monkeydo',project/'touch-tests.prg','venux1','/t' if os.name=='nt' else '-t')
        # monkeydo can exit with status 0 even when runtime tests fail.
        if not re.search(r'PASSED \(passed=\d+, failed=0, errors=0\)',output):
            raise SystemExit('Garmin runtime touch tests did not pass')

if __name__=='__main__':main()
