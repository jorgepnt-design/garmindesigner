#!/usr/bin/env python3
"""Build an editor JSON (including embedded PNGs) as a Venu X1 watchface."""
import argparse,base64,hashlib,io,json,math,os,re,subprocess,shutil,uuid
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]
FONTS=ROOT/'docs/assets/editor-fonts'
TYPES={'time','hours','minutes','seconds','date','battery','temperature','distance','alarmCount','alarmStatus','text','image','icon'}
def validate(d):
    if d.get('version')!=1 or not isinstance(d.get('elements'),list) or len(d['elements'])>40:raise ValueError('Expected editor format v1, at most 40 elements')
    if not re.fullmatch('#[a-fA-F0-9]{6}',d.get('background','')):raise ValueError('Invalid background')
    for e in d['elements']:
        if e.get('type') not in TYPES or e.get('font') not in {'sans','bold','serif','mono',*[('original-'+n) for n in ['sport','elegant','bold','sport-seconds','elegant-seconds','bold-seconds','date','battery','value','label']]}:raise ValueError('Unknown field or font')
        for k,lo,hi in [('x',0,447),('y',0,485),('size',1 if e['type']=='icon' else 12,150)]:
            if type(e.get(k)) not in (int,float) or not math.isfinite(e[k]) or not lo<=e[k]<=hi:raise ValueError('Invalid '+k)
        if not re.fullmatch('#[a-fA-F0-9]{6}',e.get('color','')):raise ValueError('Invalid color')
        if e['type']=='text' and (not isinstance(e.get('text'),str) or len(e['text'])>35 or not re.fullmatch('[\x20-\x7eÄÖÜäöüß°]*',e['text'])):raise ValueError('Unsupported text')
        if e['type']=='icon' and e.get('icon') not in {'sun','run','alarm','battery','heart','line'}:raise ValueError('Unknown icon')
        if e['type']=='image':
            if not re.fullmatch('data:image/png;base64,[A-Za-z0-9+/=]+',e.get('data','')) or len(e['data'])>1500000:raise ValueError('Invalid embedded PNG')
            for k,hi in [('width',448),('height',486)]:
                if type(e.get(k)) not in (int,float) or not 8<=e[k]<=hi:raise ValueError('Invalid image dimensions')
    return d

def font_resource(out,name,font,size,chars):
    if font.startswith('original-'):
        original=font[9:];meta=json.loads((ROOT/'docs/assets/fonts/atlas.json').read_text())[original];scale=size/meta['height'];height=size;baseline=size
        chars=''.join(meta['glyphs']);widths={c:max(1,round(meta['glyphs'][c]['w']*scale)) for c in chars};atlas=Image.new('L',(sum(widths.values()),height));source=Image.open(ROOT/'shared/resources/fonts'/(original+'.png')).convert('L');x=0;rows=[]
        for c,w in widths.items():
            g=meta['glyphs'][c];im=source.crop((g['x'],0,g['x']+g['w'],meta['height'])).resize((w,height),Image.Resampling.LANCZOS);atlas.paste(im,(x,0));rows.append(f'char id={ord(c)} x={x} y=0 width={w} height={height} xoffset=0 yoffset=0 xadvance={w} page=0 chnl=15');x+=w
        atlas.convert('RGB').save(out/(name+'.png'));(out/(name+'.fnt')).write_text('\n'.join([f'info face="{name}" size={size} bold=0 italic=0 unicode=1 smooth=1 aa=1',f'common lineHeight={height} base={baseline} scaleW={x} scaleH={height} pages=1 packed=0 alphaChnl=4 redChnl=0 greenChnl=0 blueChnl=0',f'page id=0 file="{name}.png"',f'chars count={len(rows)}',*rows])+'\n');return
    ft=ImageFont.truetype(str(FONTS/(font+'.ttf')),size);height=math.ceil(size*1.17);baseline=round(size*.93)
    widths={c:max(2,round(ft.getlength(c))) for c in chars};atlas=Image.new('L',(sum(widths.values()),height));draw=ImageDraw.Draw(atlas);x=0;rows=[]
    for c,w in widths.items():
        draw.text((x,baseline),c,font=ft,fill=255,anchor='ls')
        rows.append(f'char id={ord(c)} x={x} y=0 width={w} height={height} xoffset=0 yoffset=0 xadvance={w} page=0 chnl=15');x+=w
    atlas.convert('RGB').save(out/(name+'.png'))
    (out/(name+'.fnt')).write_text('\n'.join([f'info face="{name}" size={size} bold=0 italic=0 unicode=1 smooth=1 aa=1',f'common lineHeight={height} base={baseline} scaleW={x} scaleH={height} pages=1 packed=0 alphaChnl=4 redChnl=0 greenChnl=0 blueChnl=0',f'page id=0 file="{name}.png"',f'chars count={len(rows)}',*rows])+'\n')

def static_image(e):
    s=round(e['size']);color=e['color'];kind=e['type']
    if kind=='image':
        im=Image.open(io.BytesIO(base64.b64decode(e['data'].split(',')[1],validate=True)))
        if im.width>448 or im.height>486:raise ValueError('Embedded image must be normalized to 448 x 486 or smaller')
        return im.convert('RGBA').resize((round(e['width']),round(e['height'])),Image.Resampling.LANCZOS)
    if kind=='text':
        if e['font'].startswith('original-'):
            name=e['font'][9:];meta=json.loads((ROOT/'docs/assets/fonts/atlas.json').read_text())[name];scale=s/meta['height'];source=Image.open(ROOT/'docs/assets/fonts'/(name+'.png'));pieces=[]
            for c in e['text']:
                if c not in meta['glyphs']:raise ValueError('Character unavailable in original font: '+c)
                g=meta['glyphs'][c];pieces.append(source.crop((g['x'],0,g['x']+g['w'],meta['height'])).resize((max(1,round(g['w']*scale)),s),Image.Resampling.LANCZOS))
            im=Image.new('RGBA',(max(1,sum(p.width for p in pieces)),s));x=0
            for p in pieces:im.paste(p,(x,0));x+=p.width
            tint=Image.new('RGBA',im.size,color);tint.putalpha(im.getchannel('A'));return tint
        ft=ImageFont.truetype(str(FONTS/(e['font']+'.ttf')),s);im=Image.new('RGBA',(max(1,math.ceil(ft.getlength(e['text']))+2),math.ceil(s*1.17)));ImageDraw.Draw(im).text((0,round(s*.93)),e['text'],font=ft,fill=color,anchor='ls');return im
    k=e['icon'];w=round(e.get('width',s)) if k=='line' else s;h=round(e.get('height',2)) if k=='line' else s
    if not 1<=w<=448 or not 1<=h<=486:raise ValueError('Invalid icon dimensions')
    im=Image.new('RGBA',(w+2,h+2));d=ImageDraw.Draw(im)
    def line(a,b,c,f):d.line((round(a*s),round(b*s),round(c*s),round(f*s)),fill=color,width=2)
    def ellipse(a,b,c,f):d.ellipse((round(a*s),round(b*s),round(c*s),round(f*s)),outline=color,width=2)
    if k=='line':d.rectangle((0,0,w-1,h-1),fill=color)
    elif k=='sun':
        ellipse(.27,.27,.73,.73)
        for i in range(8):
            a=i*math.pi/4;line(.5+math.cos(a)*.34,.5+math.sin(a)*.34,.5+math.cos(a)*.48,.5+math.sin(a)*.48)
    elif k=='alarm':
        ellipse(.2,.2,.8,.8)
        for p in [(.5,.3,.5,.5),(.5,.5,.7,.6),(.15,.1,.02,.25),(.85,.1,.98,.25),(.3,.78,.2,.98),(.7,.78,.8,.98)]:line(*p)
    elif k=='battery':d.rectangle((s*.06,s*.3,s*.86,s*.7),outline=color,width=2);d.rectangle((s*.88,s*.42,s*.96,s*.57),outline=color,width=2)
    elif k=='heart':
        pts=[]
        for i in range(101):
            a=i*math.tau/100;x=16*math.sin(a)**3;y=13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a);pts.append((s*(.5+x/36),s*(.45-y/36)))
        d.line(pts,fill=color,width=2)
    else:
        ellipse(.52,.04,.68,.2)
        for p in [(.5,.3,.35,.6),(.35,.6,.6,.72),(.6,.72,.5,.98),(.35,.6,.08,.93),(.18,.4,.5,.3),(.5,.3,.75,.5),(.75,.5,.95,.35)]:line(*p)
    return im

def rendered_image(asset):
    data=asset.get('data','')
    if not isinstance(data,str) or not re.fullmatch('data:image/png;base64,[A-Za-z0-9+/=]+',data) or len(data)>3000000:raise ValueError('Invalid rendered asset')
    im=Image.open(io.BytesIO(base64.b64decode(data.split(',')[1],validate=True)))
    if im.width>16000 or im.height>486 or im.width*im.height>4000000:raise ValueError('Rendered asset dimensions too large')
    return im.convert('RGBA')

RENDERER_VERSION = "P2"
def identity(d):
    build_id = str(d.get("buildId") or hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()[:8]).upper()
    if not re.fullmatch("[A-F0-9]{8}",build_id):raise ValueError("Invalid build identifier")
    name = str(d.get("name") or "Jorge Custom")[:18]+" "+RENDERER_VERSION+"-"+build_id
    app_id = uuid.uuid5(uuid.UUID("6f1d3c2e-5a4b-4c8d-9e7f-0a1b2c3d4e5f"),RENDERER_VERSION+":"+build_id+":"+hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()).hex
    return build_id,name,app_id

def generate(d,out):
    validate(d);build_id,app_name,app_id=identity(d);out.mkdir(parents=True,exist_ok=True);res=out/'resources';res.mkdir(exist_ok=True);src=out/'source';src.mkdir(exist_ok=True)
    resources=[];initial=[];render=[];fontids={};pixel_tables=[];chars='0123456789:.-% °CkmAKTIVUSSoMDiFra'
    for i,e in enumerate(d['elements']):
        if not e.get('visible',True):continue
        x,y=round(e['x']),round(e['y']);kind=e['type']
        asset=d.get('renderAssets',{}).get(str(i))
        if d.get('renderVersion')==1:
            if asset is None:raise ValueError('Missing rendered asset; save this design again in the editor')
            im=rendered_image(asset)
            if asset.get('kind')=='bitmap':
                bx,by=asset.get('x'),asset.get('y')
                if type(bx)!=int or type(by)!=int or not 0<=bx<448 or not 0<=by<486 or im.width>448 or im.height>486:raise ValueError('Invalid bitmap bounds')
                im.save(res/f'Exact{i}.png');resources.append(f'<bitmap id="Exact{i}" filename="Exact{i}.png" packingFormat="png" automaticPalette="false" dithering="none"/>');initial.append(f'images[{i}] = WatchUi.loadResource(Rez.Drawables.Exact{i});');render.append(f'dc.drawBitmap({bx},{by},images[{i}]);');continue
            if asset.get('kind')!='font' or im.height!=asset.get('height'):raise ValueError('Invalid font pixel asset')
            required={'time':'0123456789:','hours':'0123456789','minutes':'0123456789:','seconds':'0123456789:','date':'0123456789. SoMDiFra','battery':'0123456789%','temperature':'0123456789-°C','distance':'0123456789.-','alarmCount':'0123456789','alarmStatus':'AKTIVUS'}.get(kind,'')
            missing=set(required)-set(asset.get('glyphs',{}))
            if missing:raise ValueError('Missing glyphs for '+kind+': '+''.join(sorted(missing)))
            table=[]
            for n,(ch,g) in enumerate(asset.get('glyphs',{}).items()):
                gx,w=g.get('x'),g.get('w')
                if len(ch)!=1 or type(gx)!=int or type(w)!=int or gx<0 or w<1 or gx+w>im.width or n>255:raise ValueError('Invalid glyph bounds')
                mask=im.crop((gx,0,gx+w,im.height)).getchannel('A');glyph=Image.new('RGBA',(w,im.height),e['color']);glyph.putalpha(mask);rid=f'Glyph{i}_{n}';glyph.save(res/(rid+'.png'));resources.append(f'<bitmap id="{rid}" filename="{rid}.png" packingFormat="png" automaticPalette="false" dithering="none"/>');table.append(json.dumps(ch,ensure_ascii=False)+'=>[Rez.Drawables.'+rid+','+str(w)+']')
            pixel_tables.append(f'pixels[{i}] = '+'{'+','.join(table)+'};')

        if kind in {'text','icon','image'}:
            static_image(e).save(res/f'Image{i}.png');resources.append(f'<bitmap id="Image{i}" filename="Image{i}.png" packingFormat="png" automaticPalette="false"/>');initial.append(f'images[{i}] = WatchUi.loadResource(Rez.Drawables.Image{i});');render.append(f'dc.drawBitmap({x},{y},images[{i}]);');continue
        key=(e['font'],round(e['size']))
        if asset is None and key not in fontids:
            name='Font'+str(len(fontids));fontids[key]=name;font_resource(res,name,*key,chars);resources.append(f'<font id="{name}" filename="{name}.fnt" antialias="true"/>');initial.append(f'fonts[{json.dumps(name)}] = WatchUi.loadResource(Rez.Fonts.{name});')
        name=fontids.get(key);expr={'time':'hh + ":" + mm','hours':'hh','minutes':'":"+mm','seconds':'":" + clock.sec.format("%02d")','date':'["So.","Mo.","Di.","Mi.","Do.","Fr.","Sa."][date.day_of_week-1] + " " + date.day.format("%02d") + "." + date.month.format("%02d") + "."','battery':'System.getSystemStats().battery.format("%.0f") + "%"','temperature':'temp','distance':'km','alarmCount':'alarms.toString()','alarmStatus':'(alarms > 0 ? "AKTIV" : "AUS")'}[kind]
        if asset is not None:render.append(f'drawPixels(dc,pixels[{i}],{expr},{x},{y});')
        else:render.append(f'dc.setColor(0x{e["color"][1:]},Graphics.COLOR_TRANSPARENT); dc.drawText({x},{y},fonts[{json.dumps(name)}],{expr},Graphics.TEXT_JUSTIFY_LEFT);')
    fontxml=[s for s in resources if s.startswith('<font')];bitmaps=[s for s in resources if s.startswith('<bitmap')]
    Image.new('RGB',(65,65),'black').save(res/'launcher.png');bitmaps.append('<bitmap id="LauncherIcon" filename="launcher.png"/>')
    (res/'resources.xml').write_text('<resources><fonts>'+''.join(fontxml)+'</fonts><bitmaps>'+''.join(bitmaps)+'</bitmaps><strings><string id="AppName">'+escape(app_name)+'</string></strings></resources>')
    manifest='''<?xml version="1.0"?><iq:manifest xmlns:iq="http://www.garmin.com/xml/connectiq" version="3"><iq:application id="c5fa872a0f294834a22d4d4ad44c0641" type="watchface" name="@Strings.AppName" entry="CustomApp" launcherIcon="@Drawables.LauncherIcon" minApiLevel="4.2.0"><iq:products><iq:product id="venux1"/></iq:products><iq:permissions/><iq:languages><iq:language>deu</iq:language><iq:language>eng</iq:language></iq:languages><iq:barrels/></iq:application></iq:manifest>'''
    manifest=manifest.replace('c5fa872a0f294834a22d4d4ad44c0641',app_id)
    (out/'manifest.xml').write_text(manifest);(out/'monkey.jungle').write_text('project.manifest = manifest.xml\nbase.sourcePath = source\nbase.resourcePath = resources\n')
    code='''import Toybox.Application;
import Toybox.WatchUi;
import Toybox.Graphics;
import Toybox.System;
import Toybox.Time;
import Toybox.Time.Gregorian;
import Toybox.ActivityMonitor;
import Toybox.Weather;
class CustomApp extends Application.AppBase {
 function initialize() { AppBase.initialize(); }
 function getInitialView() { return [new CustomFace()]; }
}
class CustomFace extends WatchUi.WatchFace {
 var fonts = {}; var images = {}; var pixels = {}; var sleeping = false;
 function initialize() { WatchFace.initialize(); INITIAL }
 function drawPixels(dc,table,value,x,y) {
  for(var k=0;k<value.length();k+=1) {
   var ch=value.substring(k,k+1);if(table.hasKey(ch)) { var g=table[ch];dc.drawBitmap(x,y,WatchUi.loadResource(g[0]));x+=g[1]; }
  }
 }
 function onEnterSleep() { sleeping=true; }
 function onExitSleep() { sleeping=false; WatchUi.requestUpdate(); }
 function onUpdate(dc) {
 dc.setColor(Graphics.COLOR_WHITE,BGCOLOR);dc.clear();
 var clock=System.getClockTime();var hh=clock.hour.format("%02d");var mm=clock.min.format("%02d");
 if(sleeping) { dc.setColor(0x666666,Graphics.COLOR_BLACK);dc.drawText(224,220,Graphics.FONT_NUMBER_MEDIUM,hh+":"+mm,Graphics.TEXT_JUSTIFY_CENTER);return; }
 var date=Gregorian.info(Time.now(),Time.FORMAT_SHORT);var alarms=System.getDeviceSettings().alarmCount;
 var temp="--";var weather=Weather.getCurrentConditions();
 if(weather!=null && weather.temperature!=null) { temp=weather.temperature.format("%.0f")+"°C"; }
 var info=ActivityMonitor.getInfo();var km="--";
 if(info.distance!=null) { var n=info.distance/100000.0;km=n.format(n<100?"%.2f":n<1000?"%.1f":"%.0f"); }
 RENDER
 }
}
'''.replace('INITIAL','\n'.join(initial+pixel_tables)).replace('BGCOLOR','0x'+d['background'][1:]).replace('RENDER','\n'.join(render))
    (src/'Custom.mc').write_text(code);(out/'design.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));return out

def main():
    p=argparse.ArgumentParser();p.add_argument('design',type=Path);p.add_argument('--sdk',type=Path);p.add_argument('--key',type=Path);p.add_argument('--generate-only',action='store_true');a=p.parse_args()
    if a.design.stat().st_size>8000000:p.error('Design file exceeds 8 MB')
    d=validate(json.loads(a.design.read_text(encoding='utf-8')));out=ROOT/'build/custom'
    if out.exists():shutil.rmtree(out)
    generate(d,out)
    if a.generate_only:print('Generated project:',out);return
    if not a.sdk or not a.key:p.error('--sdk and --key required for compilation')
    compiler=a.sdk.resolve()/'bin'/('monkeyc.bat' if os.name=='nt' else 'monkeyc');destination=out/'Jorge-custom.prg'
    cmd=[str(compiler),'-f','monkey.jungle','-d','venux1','-y',str(a.key.resolve()),'-o',str(destination),'-w']
    subprocess.run((['cmd','/c']+cmd) if os.name=='nt' else cmd,cwd=out,check=True)
    print('Compiled:',destination,'\nTest in the Garmin simulator and on the watch before daily use.')
if __name__=='__main__':main()
