import base64
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from editor_build import generate,identity
from editor_adapter import build_editor
from package_editor import package

class PixelBuildTest(unittest.TestCase):
    def design(self):
        image=Image.new('RGBA',(50,32),'white')
        data=io.BytesIO();image.save(data,format='PNG')
        return dict(version=1,name='Elegant',background='#000000',buildId='ABCDEF12',renderVersion=1,
            elements=[dict(type='minutes',font='original-elegant',size=32,x=188,y=136,color='#e8cd91')],
            renderAssets={'0':dict(kind='font',height=32,width=50,glyphs={ch:dict(x=i*2,w=2) for i,ch in enumerate('0123456789:. SoMDiFra')},data='data:image/png;base64,'+base64.b64encode(data.getvalue()).decode())})
    def test_required_colon_cannot_silently_disappear(self):
        d=self.design();del d['renderAssets']['0']['glyphs'][':']
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'Missing glyphs for minutes: :'):generate(d,Path(t))
    def test_device_uses_exported_pixels_at_editor_position(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);d=self.design();d['elements'].append(dict(type='date',font='original-date',size=32,x=28,y=44,color='#e8cd91'));d['renderAssets']['1']=d['renderAssets']['0'];generate(d,p)
            code=(p/'source/Custom.mc').read_text()
            self.assertIn('":"+mm,188,136',code)
            self.assertIn('["So.","Mo.","Di.","Mi.","Do.","Fr.","Sa."][date.day_of_week-1] + " " + date.day.format("%02d") + "." + date.month.format("%02d") + "."',code)
            self.assertNotIn('WECKER',code)
            self.assertFalse(list((p/'resources').glob('*.fnt')))
            im=Image.open(p/'resources/Glyph0_10.png')
            self.assertEqual(im.size,(2,32));self.assertEqual(im.getpixel((0,0)),(232,205,145,255))
    def test_build_has_own_app_identity(self):
        d=self.design();a=identity(d);d['buildId']='ABCDEF13';b=identity(d)
        self.assertNotEqual(a[2],b[2]);self.assertEqual(a[1],'Elegant P2-ABCDEF12')
    def test_packaged_prg_preview_and_receipt_match(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);out=p/'build/editor-elegant';build_editor(self.design(),out,'editor-elegant')
            dist=p/'dist';dist.mkdir();(dist/'editor-elegant-venux1.prg').write_bytes(b'compiled pixels')
            package(p/'build',dist)
            r=json.loads((dist/'editor-elegant-P2-ABCDEF12-venux1.json').read_text())
            self.assertEqual((dist/r['file']).read_bytes(),b'compiled pixels')
            self.assertTrue((dist/r['preview']).is_file());self.assertEqual(r['dateFormat'],'ddd. DD.MM.')

if __name__=='__main__':unittest.main()
