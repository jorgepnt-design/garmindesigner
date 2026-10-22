"""Connect the editor's native pixel export to the existing release workflow."""
import base64,io,json,uuid
from pathlib import Path
from PIL import Image
from editor_build import generate
SAMPLES={'time':'20:35','hours':'20','minutes':':35','seconds':':42','date':'22.10.2026','battery':'78%','temperature':'16°C','distance':'8.42','alarmCount':'2','alarmStatus':'AKTIV'}
def build_editor(design,out,slug):
    if design.get('renderVersion')!=1:raise ValueError('Expected editor pixel export')
    generate(design,out)
    manifest=out/'manifest.xml';manifest.write_text(manifest.read_text().replace('c5fa872a0f294834a22d4d4ad44c0641',uuid.uuid5(uuid.UUID('6f1d3c2e-5a4b-4c8d-9e7f-0a1b2c3d4e5f'),slug).hex))
    preview=Image.new('RGBA',(448,486),design['background'])
    for i,e in enumerate(design['elements']):
        if not e.get('visible',True):continue
        a=design['renderAssets'][str(i)];im=Image.open(io.BytesIO(base64.b64decode(a['data'].split(',')[1]))).convert('RGBA')
        if a['kind']=='bitmap':preview.alpha_composite(im,(a['x'],a['y']))
        else:
            x=round(e['x'])
            for ch in SAMPLES[e['type']]:
                if ch not in a['glyphs']:continue
                g=a['glyphs'][ch];mask=im.crop((g['x'],0,g['x']+g['w'],a['height'])).getchannel('A');tile=Image.new('RGBA',mask.size,e['color']);tile.putalpha(mask);preview.alpha_composite(tile,(x,round(e['y'])));x+=g['w']
    preview.convert('RGB').save(out/'vorschau.png')
    (out/'build.json').write_text(json.dumps({'slug':slug,'name':design.get('name',slug),'devices':['venux1'],'warnings':[],'renderVersion':1}))
    print('Editor pixel export preserved:',slug)
