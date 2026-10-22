"""Vorschau: zeichnet das Zifferblatt mit den erzeugten BMFonts wie onUpdate()."""
import re
import sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
F = P / "resources" / "fonts"
D = P / "resources" / "drawables"

def load(fid):
    chars, atlas = {}, Image.open(F / f"{fid}.png").convert("RGBA")
    for line in (F / f"{fid}.fnt").read_text(encoding="utf-8").splitlines():
        if line.startswith("char "):
            kv = dict(re.findall(r"(\w+)=(-?\d+)", line))
            chars[chr(int(kv["id"]))] = {k: int(v) for k, v in kv.items()}
    return chars, atlas

fonts = {f: load(f) for f in ["hours", "seconds", "value", "battery", "date", "label"]}
img = Image.new("RGB", (448, 486), "black")

def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def text(x, y, fid, color, s, just="left"):
    chars, atlas = fonts[fid]
    width = sum(chars[c]["xadvance"] for c in s)
    if just == "center":
        x -= width // 2
    elif just == "right":
        x -= width
    for c in s:
        g = chars[c]
        if g["width"]:
            glyph = atlas.crop((g["x"], g["y"], g["x"] + g["width"], g["y"] + g["height"]))
            solid = Image.new("RGB", glyph.size, hexrgb(color))
            img.paste(solid, (x + g["xoffset"], y + g["yoffset"]), glyph.split()[3])
        x += g["xadvance"]

GOLD, CREAM, GREY = "#e8cd91", "#f2e7cf", "#d9dde1"
text(36, 44, "date", GOLD, "MI 22. OKT")
text(413, 36, "battery", CREAM, "87%", "right")
for y in (95, 320):
    img.paste(Image.new("RGB", (378, 1), hexrgb(GOLD)), (35, y))
text(28, 144, "hours", GOLD, "10")
text(184, 144, "hours", GOLD, "42")
text(368, 192, "seconds", GOLD, "37")
cols = [84, 226, 368]
for cx, name in zip(cols, ["sun", "run", "alarm"]):
    img.paste(Image.open(D / f"icon_{name}.png").convert("RGB"), (cx - 22, 333))
text(cols[0], 389, "value", GOLD, "18°", "center")
text(cols[1], 388, "value", GOLD, "4.2", "center")
text(cols[2], 389, "value", GOLD, "2", "center")
text(cols[0], 432, "label", GREY, "WETTER", "center")
text(cols[1], 431, "label", GREY, "KM HEUTE", "center")
text(cols[2], 431, "label", GREY, "WECKER", "center")
img.save(sys.argv[2])
