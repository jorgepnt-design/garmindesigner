"""Erzeugt aus einer Design-JSON-Datei ein komplettes Connect-IQ-Zifferblatt-Projekt.

Aufruf: python3 tools/build_face.py designs/mein-design.json build/mein-design
Ergebnis: Projektordner mit manifest.xml, monkey.jungle, Quelltext, Schriften, Icons
und vorschau.png. Bauen mit: monkeyc -d venux1 -f <ordner>/monkey.jungle ...
"""
import json
import re
import shutil
import sys
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TOOLS = Path(__file__).resolve().parent
SUPPORT = json.loads((TOOLS.parent / "web" / "support.json").read_text(encoding="utf-8"))
FONTS = TOOLS / "fonts"
SERIF = FONTS / "CormorantGaramond-600.ttf"
SERIF_LIGHT = FONTS / "CormorantGaramond-500.ttf"
SANS = FONTS / "Inter-Medium.otf"

DIGITS = "0123456789"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ"
DEFAULT_DEVICES = ["venux1"]
APP_NAMESPACE = uuid.UUID("6f1d3c2e-5a4b-4c8d-9e7f-0a1b2c3d4e5f")

JUSTIFY = {"left": "Graphics.TEXT_JUSTIFY_LEFT", "center": "Graphics.TEXT_JUSTIFY_CENTER",
           "right": "Graphics.TEXT_JUSTIFY_RIGHT"}


def slugify(name):
    s = name.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "design"


def parse_color(value, default="#ffffff"):
    v = (value or default).strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", v):
        v = default.lstrip("#")
    return int(v, 16)


def font_file(name):
    n = (name or "").lower()
    if "label" in n or "sans" in n or "mono" in n:
        return SANS
    if "battery" in n or "light" in n:
        return SERIF_LIGHT
    return SERIF


def charset(spec, element):
    if spec == "text":
        return element.get("text") or ("WECKER" if element["type"] == "alarmStatus" else "")
    if spec == "upper":
        return UPPER + DIGITS + ".,- "
    if spec.startswith("digits"):
        return DIGITS + spec[len("digits"):]
    return spec


def element_text(element):
    if element["type"] == "alarmStatus":
        return element.get("text") or "WECKER"
    return element.get("text", "")


class BitmapFont:
    """Rendert eine BMFont (.fnt + .png) fuer genau die benoetigten Zeichen."""

    def __init__(self, path, size, chars):
        font = ImageFont.truetype(str(path), size)
        self.size = size
        self.ascent, self.descent = font.getmetrics()
        self.glyphs = {}
        for ch in sorted(set(chars)):
            bbox = font.getbbox(ch, anchor="ls")
            adv = round(font.getlength(ch))
            if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                self.glyphs[ch] = (None, 0, 0, adv)
                continue
            img = Image.new("L", (bbox[2] - bbox[0] + 2, bbox[3] - bbox[1] + 2), 0)
            ImageDraw.Draw(img).text((1 - bbox[0], 1 - bbox[1]), ch, font=font, fill=255, anchor="ls")
            self.glyphs[ch] = (img, bbox[0] - 1, self.ascent + bbox[1] - 1, adv)

    def save(self, out_dir, fid):
        sheet_w = 1024 if any(g[0] is not None and g[0].width > 120 for g in self.glyphs.values()) else 512
        x = y = row_h = 0
        self.places = {}
        for ch, (img, *_rest) in self.glyphs.items():
            if img is None:
                self.places[ch] = (0, 0)
                continue
            if x + img.width + 1 > sheet_w:
                x, y, row_h = 0, y + row_h + 1, 0
            self.places[ch] = (x, y)
            x += img.width + 1
            row_h = max(row_h, img.height)
        sheet_h = 1
        while sheet_h < y + row_h + 1:
            sheet_h *= 2
        atlas = Image.new("RGBA", (sheet_w, sheet_h), (255, 255, 255, 0))
        lines = [
            f'info face="{fid}" size={self.size} bold=0 italic=0 charset="" unicode=1 '
            f'stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=1,1',
            f"common lineHeight={self.ascent + self.descent} base={self.ascent} "
            f"scaleW={sheet_w} scaleH={sheet_h} pages=1 packed=0",
            f'page id=0 file="{fid}.png"',
            f"chars count={len(self.glyphs)}",
        ]
        for ch, (img, xo, yo, adv) in self.glyphs.items():
            px, py = self.places[ch]
            w = h = 0
            if img is not None:
                w, h = img.size
                white = Image.new("RGBA", img.size, (255, 255, 255, 255))
                white.putalpha(img)
                atlas.paste(white, (px, py))
            lines.append(f"char id={ord(ch)} x={px} y={py} width={w} height={h} "
                         f"xoffset={xo} yoffset={yo} xadvance={adv} page=0 chnl=15")
        atlas.save(out_dir / f"{fid}.png")
        (out_dir / f"{fid}.fnt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def draw(self, img, x, y, text, color, align):
        width = sum(self.glyphs[c][3] for c in text if c in self.glyphs)
        if align == "center":
            x -= width // 2
        elif align == "right":
            x -= width
        rgb = ((color >> 16) & 255, (color >> 8) & 255, color & 255)
        for c in text:
            if c not in self.glyphs:
                continue
            glyph, xo, yo, adv = self.glyphs[c]
            if glyph is not None:
                img.paste(Image.new("RGB", glyph.size, rgb), (x + xo, y + yo), glyph)
            x += adv


def colored_icon(name, size, color, background):
    mask = Image.open(TOOLS / "icons" / f"{name}.png").getchannel("A").resize((size, size), Image.LANCZOS)
    rgb = lambda c: ((c >> 16) & 255, (c >> 8) & 255, c & 255)
    img = Image.new("RGB", (size, size), rgb(background))
    img.paste(Image.new("RGB", (size, size), rgb(color)), (0, 0), mask)
    return img


def mc_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build(design_path, out):
    design = json.loads(Path(design_path).read_text(encoding="utf-8"))
    name = (design.get("name") or Path(design_path).stem).strip()[:30]
    slug = slugify(Path(design_path).stem)
    width, height = int(design.get("width", 448)), int(design.get("height", 486))
    devices = design.get("devices") or DEFAULT_DEVICES
    background = parse_color(design.get("background"), "#000000")

    if out.exists():
        shutil.rmtree(out)
    (out / "source").mkdir(parents=True)
    fonts_dir = out / "resources" / "fonts"
    draw_dir = out / "resources" / "drawables"
    fonts_dir.mkdir(parents=True)
    draw_dir.mkdir(parents=True)
    (out / "resources" / "strings").mkdir(parents=True)

    warnings = []
    font_keys, font_chars = [], {}
    icon_keys, icons = [], {}
    items = []

    for el in design.get("elements", []):
        if not el.get("visible", True):
            continue
        t = el.get("type")
        if t not in SUPPORT["types"]:
            warnings.append(f"Element-Typ '{t}' wird noch nicht unterstuetzt und fehlt.")
            continue
        x, y = round(el.get("x", 0)), round(el.get("y", 0))
        size = max(1, round(el.get("size", 20)))
        color = parse_color(el.get("color"))
        if t == "icon":
            icon = el.get("icon", "")
            if icon in SUPPORT["shapes"]:
                items.append(("shape", icon, x, y, size, color,
                              round(el.get("width", size)), round(el.get("height", size))))
                continue
            alias = SUPPORT["iconAliases"].get(icon)
            if alias is None:
                warnings.append(f"Icon '{icon}' gibt es noch nicht und fehlt.")
                continue
            key = (alias, size, color)
            if key not in icons:
                icons[key] = len(icon_keys)
                icon_keys.append(key)
            items.append(("icon", icons[key], x, y))
            continue
        chars = charset(SUPPORT["types"][t]["chars"], el)
        if not chars:
            continue
        fkey = (font_file(el.get("font")), size)
        if fkey not in font_chars:
            font_chars[fkey] = set()
            font_keys.append(fkey)
        font_chars[fkey] |= set(chars)
        items.append(("text", t, x, y, font_keys.index(fkey), color, el.get("align", "left"), element_text(el)))

    # Kleine Uhrzeit fuer den Always-on-Modus
    aod_key = (SERIF, 60)
    if aod_key not in font_chars:
        font_chars[aod_key] = set()
        font_keys.append(aod_key)
    font_chars[aod_key] |= set(DIGITS + ":")
    aod_font = font_keys.index(aod_key)
    time_colors = [it[5] for it in items if it[0] == "text" and it[1] in ("hours", "time")]
    tc = time_colors[0] if time_colors else 0xE8CD91
    aod_color = (((tc >> 16) & 255) // 2 << 16) | (((tc >> 8) & 255) // 2 << 8) | ((tc & 255) // 2)

    # Ressourcen schreiben
    bitmap_fonts = []
    font_xml = ["<fonts>"]
    for i, (path, size) in enumerate(font_keys):
        bf = BitmapFont(path, size, font_chars[(path, size)])
        bf.save(fonts_dir, f"f{i}")
        bitmap_fonts.append(bf)
        font_xml.append(f'    <font id="F{i}" filename="f{i}.fnt" antialias="true"/>')
    font_xml.append("</fonts>")
    (fonts_dir / "fonts.xml").write_text("\n".join(font_xml) + "\n", encoding="utf-8")

    icon_images = []
    draw_xml = ["<drawables>", '    <bitmap id="LauncherIcon" filename="launcher_icon.png"/>']
    for i, (alias, size, color) in enumerate(icon_keys):
        img = colored_icon(alias, size, color, background)
        img.save(draw_dir / f"b{i}.png")
        icon_images.append(img)
        draw_xml.append(f'    <bitmap id="B{i}" filename="b{i}.png"/>')
    draw_xml.append("</drawables>")
    (draw_dir / "drawables.xml").write_text("\n".join(draw_xml) + "\n", encoding="utf-8")

    launcher = Image.new("RGB", (70, 70), "black")
    d = ImageDraw.Draw(launcher)
    accent = ((tc >> 16) & 255, (tc >> 8) & 255, tc & 255)
    d.ellipse((3, 3, 66, 66), outline=accent, width=2)
    d.text((35, 37), name[:1].upper(), font=ImageFont.truetype(str(SERIF), 38), fill=accent, anchor="mm")
    launcher.save(draw_dir / "launcher_icon.png")

    (out / "resources" / "strings" / "strings.xml").write_text(
        f"<strings>\n    <string id=\"AppName\">{name.replace('&', '&amp;').replace('<', '&lt;')}</string>\n</strings>\n",
        encoding="utf-8")

    app_id = uuid.uuid5(APP_NAMESPACE, slug).hex
    products = "\n".join(f'            <iq:product id="{dev}"/>' for dev in devices)
    (out / "manifest.xml").write_text(f"""<?xml version="1.0"?>
<iq:manifest version="3" xmlns:iq="http://www.garmin.com/xml/connectiq">
    <iq:application id="{app_id}" type="watchface" name="@Strings.AppName" entry="FaceApp" launcherIcon="@Drawables.LauncherIcon" minApiLevel="3.2.0">
        <iq:products>
{products}
        </iq:products>
        <iq:permissions/>
        <iq:languages>
            <iq:language>deu</iq:language>
            <iq:language>eng</iq:language>
        </iq:languages>
        <iq:barrels/>
    </iq:application>
</iq:manifest>
""", encoding="utf-8")
    (out / "monkey.jungle").write_text("project.manifest = manifest.xml\n", encoding="utf-8")

    for f in ("FaceApp.mc", "Data.mc"):
        shutil.copy(TOOLS / "template" / f, out / "source" / f)

    # Zeichenbefehle fuer onUpdate
    draw = []
    for it in items:
        if it[0] == "text":
            _, t, x, y, fi, color, align, literal = it
            value = mc_string(literal) if SUPPORT["types"][t]["chars"] == "text" else f"Data.{t}()"
            draw.append(f"        text(dc, {x}, {y}, {fi}, 0x{color:06X}, {value}, {JUSTIFY.get(align, JUSTIFY['left'])});")
        elif it[0] == "icon":
            _, bi, x, y = it
            draw.append(f"        dc.drawBitmap(_ox + {x}, _oy + {y}, _b[{bi}]);")
        else:
            _, shape, x, y, size, color, w, h = it
            draw.append(f"        dc.setColor(0x{color:06X}, Graphics.COLOR_TRANSPARENT);")
            if shape in ("line", "rect"):
                draw.append(f"        dc.fillRectangle(_ox + {x}, _oy + {y}, {max(1, w)}, {max(1, h)});")
            elif shape == "ring":
                r = size // 2
                draw.append("        dc.setPenWidth(2);")
                draw.append(f"        dc.drawCircle(_ox + {x + r}, _oy + {y + r}, {r});")
            else:
                r = max(1, size // 2)
                draw.append(f"        dc.fillCircle(_ox + {x + r}, _oy + {y + r}, {r});")

    font_loads = ", ".join(f"WatchUi.loadResource(Rez.Fonts.F{i}) as FontResource" for i in range(len(font_keys)))
    bitmap_loads = ", ".join(f"WatchUi.loadResource(Rez.Drawables.B{i}) as BitmapResource" for i in range(len(icon_keys)))
    view = f"""import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

// Automatisch erzeugt aus {Path(design_path).name} – nicht von Hand bearbeiten.
class FaceView extends WatchUi.WatchFace {{

    private var _f as Array<FontResource> = [];
    private var _b as Array<BitmapResource> = [];
    private var _ox as Number = 0;
    private var _oy as Number = 0;
    private var _sleeping as Boolean = false;

    function initialize() {{
        WatchFace.initialize();
    }}

    function onLayout(dc as Dc) as Void {{
        _f = [{font_loads}];
        _b = [{bitmap_loads}];
        _ox = (dc.getWidth() - {width}) / 2;
        _oy = (dc.getHeight() - {height}) / 2;
    }}

    function onUpdate(dc as Dc) as Void {{
        dc.setColor(0x{background:06X}, 0x{background:06X});
        dc.clear();
        if (_sleeping) {{
            // Always-on: kleine, gedimmte Uhrzeit, die jede Minute wandert (Einbrennschutz)
            dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
            dc.clear();
            var minute = System.getClockTime().min;
            var dx = (minute % 5) * 6 - 12;
            var dy = ((minute / 5) % 5) * 6 - 12;
            dc.setColor(0x{aod_color:06X}, Graphics.COLOR_TRANSPARENT);
            dc.drawText(dc.getWidth() / 2 + dx, dc.getHeight() / 2 - 30 + dy, _f[{aod_font}], Data.time(), Graphics.TEXT_JUSTIFY_CENTER);
            return;
        }}
{chr(10).join(draw)}
    }}

    private function text(dc as Dc, x as Number, y as Number, font as Number, color as Number,
                          value as String, justify as Number) as Void {{
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(_ox + x, _oy + y, _f[font], value, justify);
    }}

    function onEnterSleep() as Void {{
        _sleeping = System.getDeviceSettings().requiresBurnInProtection;
        WatchUi.requestUpdate();
    }}

    function onExitSleep() as Void {{
        _sleeping = false;
        WatchUi.requestUpdate();
    }}
}}
"""
    (out / "source" / "FaceView.mc").write_text(view, encoding="utf-8")

    # Vorschau mit Beispielwerten
    bgc = ((background >> 16) & 255, (background >> 8) & 255, background & 255)
    preview = Image.new("RGB", (width, height), bgc)
    pd = ImageDraw.Draw(preview)
    for it in items:
        if it[0] == "text":
            _, t, x, y, fi, color, align, literal = it
            sample = literal if SUPPORT["types"][t]["chars"] == "text" else SUPPORT["types"][t]["sample"]
            bitmap_fonts[fi].draw(preview, x, y, sample, color, align)
        elif it[0] == "icon":
            _, bi, x, y = it
            preview.paste(icon_images[bi], (x, y))
        else:
            _, shape, x, y, size, color, w, h = it
            rgb = ((color >> 16) & 255, (color >> 8) & 255, color & 255)
            if shape in ("line", "rect"):
                pd.rectangle((x, y, x + max(1, w) - 1, y + max(1, h) - 1), fill=rgb)
            elif shape == "ring":
                pd.ellipse((x, y, x + size, y + size), outline=rgb, width=2)
            else:
                pd.ellipse((x, y, x + size, y + size), fill=rgb)
    preview.save(out / "vorschau.png")

    (out / "build.json").write_text(json.dumps({"slug": slug, "name": name, "devices": devices,
                                                "warnings": warnings}, ensure_ascii=False), encoding="utf-8")
    for w in warnings:
        print(f"::warning file={design_path}::{w}")
    print(f"{design_path} -> {out} ({slug}, Geraete: {', '.join(devices)})")


if __name__ == "__main__":
    build(sys.argv[1], Path(sys.argv[2]))
