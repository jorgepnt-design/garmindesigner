"""Erzeugt BMFont-Dateien (.fnt + .png) fuer das Connect-IQ-Zifferblatt."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1])          # Projektordner
FONTDIR = Path(sys.argv[2])       # Ordner mit den Schrift-Dateien
OUT = ROOT / "resources" / "fonts"
OUT.mkdir(parents=True, exist_ok=True)

SERIF = str(FONTDIR / "cormorant-garamond-latin-600-normal.woff")
SERIF_M = str(FONTDIR / "cormorant-garamond-latin-500-normal.woff")
SANS = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

DIGITS = "0123456789"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ"

# id, Datei, Groesse (aus dem Design), Zeichen, Laufweite (px)
FONTS = [
    ("hours", SERIF, 140, DIGITS, 0),
    ("seconds", SERIF, 60, DIGITS + ":", 0),
    ("value", SERIF, 36, DIGITS + "°-.,:CFKMI ", 0),
    ("battery", SERIF_M, 45, DIGITS + "%", 0),
    ("date", SERIF, 35, UPPER + DIGITS + ".,- ", 1),
    ("label", SANS, 18, UPPER + DIGITS + ".- ", 2),
]

FEATURES = ["lnum", "tnum"]

for fid, path, size, chars, tracking in FONTS:
    font = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    ascent, descent = font.getmetrics()
    glyphs = []
    for ch in chars:
        bbox = font.getbbox(ch, features=FEATURES, anchor="ls")
        adv = round(font.getlength(ch, features=FEATURES)) + tracking
        if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
            glyphs.append((ch, None, 0, 0, adv))
            continue
        w, h = bbox[2] - bbox[0] + 2, bbox[3] - bbox[1] + 2
        img = Image.new("L", (w, h), 0)
        ImageDraw.Draw(img).text((1 - bbox[0], 1 - bbox[1]), ch, font=font,
                                 fill=255, features=FEATURES, anchor="ls")
        # xoffset/yoffset relativ zur Oberkante der Zeile (Baseline = ascent)
        glyphs.append((ch, img, bbox[0] - 1, ascent + bbox[1] - 1, adv))

    # Glyphen zeilenweise in einen Atlas packen
    sheet_w = 1024 if size >= 100 else 512
    x = y = row_h = 0
    places = []
    for ch, img, xo, yo, adv in glyphs:
        if img is None:
            places.append((0, 0))
            continue
        if x + img.width + 1 > sheet_w:
            x, y, row_h = 0, y + row_h + 1, 0
        places.append((x, y))
        x += img.width + 1
        row_h = max(row_h, img.height)
    sheet_h = 1
    while sheet_h < y + row_h + 1:
        sheet_h *= 2

    atlas = Image.new("RGBA", (sheet_w, sheet_h), (255, 255, 255, 0))
    lines = [
        f'info face="{fid}" size={size} bold=0 italic=0 charset="" unicode=1 '
        f'stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=1,1',
        f"common lineHeight={ascent + descent} base={ascent} scaleW={sheet_w} "
        f"scaleH={sheet_h} pages=1 packed=0",
        f'page id=0 file="{fid}.png"',
        f"chars count={len(glyphs)}",
    ]
    for (ch, img, xo, yo, adv), (px, py) in zip(glyphs, places):
        w = h = 0
        if img is not None:
            w, h = img.size
            white = Image.new("RGBA", img.size, (255, 255, 255, 255))
            white.putalpha(img)
            atlas.paste(white, (px, py))
        lines.append(
            f"char id={ord(ch)} x={px} y={py} width={w} height={h} "
            f"xoffset={xo} yoffset={yo} xadvance={adv} page=0 chnl=15")
    atlas.save(OUT / f"{fid}.png")
    (OUT / f"{fid}.fnt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(fid, size, "ascent", ascent, "descent", descent, "sheet", sheet_w, sheet_h)
