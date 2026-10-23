import base64
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from editor_build import generate,identity,touch_zones
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
        self.assertNotEqual(a[2],b[2]);self.assertEqual(a[1],'Elegant P8-ABCDEF12')
    def test_packaged_prg_preview_and_receipt_match(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);out=p/'build/editor-elegant';build_editor(self.design(),out,'editor-elegant')
            dist=p/'dist';dist.mkdir();(dist/'editor-elegant-venux1.prg').write_bytes(b'compiled pixels')
            package(p/'build',dist)
            r=json.loads((dist/'editor-elegant-P8-ABCDEF12-venux1.json').read_text())
            self.assertEqual((dist/r['file']).read_bytes(),b'compiled pixels')
            self.assertTrue((dist/r['preview']).is_file());self.assertEqual(r['dateFormat'],'ddd. DD.MM.')

    def test_image_asset_is_embedded_with_alpha_and_exact_position(self):
        d=self.design();im=Image.new('RGBA',(12,10),(255,0,0,200));buf=io.BytesIO();im.save(buf,format='PNG')
        data='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
        d['elements']=[dict(type='image',font='sans',size=30,x=44,y=55,width=12,height=10,data=data,color='#ffffff')]
        d['renderAssets']={'0':dict(kind='bitmap',x=44,y=55,width=12,height=10,data=data)}
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);generate(d,p)
            saved=Image.open(p/'resources/Exact0.png');self.assertEqual(saved.getpixel((0,0)),(255,0,0,200));self.assertEqual(saved.size,(12,10))
            self.assertIn('dc.drawBitmap(44,55,images[0])',(p/'source/Custom.mc').read_text())
    def test_long_press_tracks_moved_data_fields(self):
        d=self.design();d['elements'][0]['type']='temperature';d['elements'][0]['x']=40;d['elements'][0]['y']=100
        first=touch_zones(d)[0];self.assertEqual(first[-1],'weather')
        d['elements'][0]['y']=300;second=touch_zones(d)[0];self.assertEqual(second[1]-first[1],200)
        with tempfile.TemporaryDirectory() as t:
            # Generate a supported minutes field to verify the actual delegate wiring.
            p=Path(t);generate(self.design(),p);code=(p/'source/Custom.mc').read_text()
            self.assertIn('new CustomDelegate(face)',code);self.assertIn('function onPress(event)',code)
            self.assertIn('Complications.exitTo(new Complications.Id(type))',code)
            self.assertNotIn('if(face.sleeping)',code)
            self.assertNotIn('face.sleeping=false;',code)
            self.assertIn('P8: Frei ',code)
            self.assertNotIn('Complications.getComplication(',code)


    def test_weather_details_open_locally_and_keep_native_launch_separate(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);generate(self.design(),p);code=(p/'source/Custom.mc').read_text()
            self.assertIn('if(target.equals("weather")) { face.showWeather();return true; }',code)
            self.assertIn('if(target.equals("nativeWeather")) { type=Complications.COMPLICATION_TYPE_CURRENT_WEATHER; }',code)
            self.assertIn('drawWeather(dc);drawNotice(dc);return;',code)
            self.assertIn('function onEnterSleep() { sleeping=true; }',code)
            self.assertIn('face.closeWeather();return true;',code)
            self.assertIn('Keine Garmin-Wetterdaten',code)
            self.assertIn('current.observationTime',code)
            self.assertIn('current.windSpeed*3.6',code)

    def test_portugal_weather_symbol_value_and_label_route_to_weather(self):
        d=json.loads((Path(__file__).resolve().parents[1]/'designs/editor-portugal-kopie.json').read_text(encoding='utf-8'))
        zones=touch_zones(d)
        for x,y in [(82,352),(80,404),(80,441)]:
            target=next((t for x1,y1,x2,y2,t in zones if x1<=x<x2 and y1<=y<y2),None)
            self.assertEqual(target,'weather',(x,y))

if __name__=='__main__':unittest.main()
