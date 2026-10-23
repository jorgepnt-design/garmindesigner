"""Connect the editor's native pixel export to the existing release workflow."""
import base64,io,json,uuid
from pathlib import Path
from PIL import Image
from editor_build import generate,identity,RENDERER_VERSION
SAMPLES={'time':'20:35','hours':'20','minutes':':35','seconds':':42','date':'Fr. 23.10.','battery':'78%','temperature':'16°C','distance':'8.42','alarmCount':'2','alarmStatus':'AKTIV'}
def build_editor(design,out,slug):
    if design.get('renderVersion')!=1:raise ValueError('Expected editor pixel export')
    generate(design,out)
    build_id,app_name,app_id=identity(design)
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
    (out/'build.json').write_text(json.dumps({'slug':slug,'name':design.get('name',slug),'devices':['venux1'],'warnings':[],'renderVersion':1,'renderer':RENDERER_VERSION,'buildId':build_id,'appName':app_name,'appId':app_id,'dateFormat':'ddd. DD.MM.'}))
    print('Editor pixel export preserved:',slug)
