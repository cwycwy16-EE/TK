"""Render one reviewed locale plan onto source pixels and repaired background patches."""
import argparse
import json
import math
import os
import tempfile
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.pdfbase.ttfonts import TTFont


def region(box, size):
    x, y, r, b = box
    if not (0 <= x < r <= size[0] and 0 <= y < b <= size[1]):
        raise ValueError(f"Rectangle outside canvas: {box}")
    return tuple(box)


def wrap(text, font, width):
    lines = []
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if line and font.getlength(candidate) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return "\n".join(lines)


def draw_block(canvas, block):
    x, y, r, b = region(block["box"], canvas.size)
    text = unicodedata.normalize("NFC", block["text"])
    if not text.strip():
        raise ValueError("Empty reviewed copy")
    font_path = block["font"]
    glyphs = TTFont("coverage", font_path).face.charToGlyph
    if any(not glyphs.get(ord(c)) for c in text if not c.isspace()):
        raise ValueError(f"Missing glyph in {font_path}: {text}")
    minimum = math.ceil(28 * min(canvas.size) / 1080)
    align = block.get("align", "left")
    draw = ImageDraw.Draw(canvas)
    for px in range(block["px"], minimum - 1, -1):
        font = ImageFont.truetype(font_path, px)
        lines = wrap(text, font, r - x)
        opts = dict(font=font, align=align, spacing=max(2, round(px * 0.1)))
        l, t, right, bottom = draw.multiline_textbbox((0, 0), lines, **opts)
        w, h = right - l, bottom - t
        if w <= r - x and h <= b - y:
            gap = {"left": 0, "center": (r-x-w)//2, "right": r-x-w}[align]
            draw.multiline_text((x+gap-l, y+(b-y-h)//2-t), lines,
                                fill=block["color"], **opts)
            return {"text": text, "lines": lines, "px": px, "box": block["box"]}
    raise ValueError(f"Replan text area at mobile minimum {minimum}px: {text}")


def render(plan, output):
    source = Path(plan["source"])
    if output.suffix.lower() != ".png" or output.exists():
        raise ValueError(f"Choose a fresh .png output: {output}")
    with Image.open(source) as original:
        canvas = original.convert("RGBA")
    if plan.get("patches"):
        with Image.open(plan["repair"]) as edited:
            if edited.size != canvas.size:
                raise ValueError("Register the repair to source dimensions before compositing")
            for box in plan["patches"]:
                rect = region(box, canvas.size)
                patch = edited.crop(rect).convert("RGBA")
                feather = plan.get("feather", 0)
                mask = None
                if feather:
                    mask = Image.new("L", patch.size, 0)
                    ImageDraw.Draw(mask).rectangle(
                        (feather, feather, patch.width-1-feather, patch.height-1-feather), fill=255)
                    mask = mask.filter(ImageFilter.GaussianBlur(feather / 2))
                canvas.paste(patch, rect, mask)
    used = [draw_block(canvas, block) for block in plan["blocks"]]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        canvas.save(tmp_path, "PNG")
        os.link(tmp_path, output)
    finally:
        tmp_path.unlink(missing_ok=True)
    return used


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8-sig"))
    print(json.dumps(render(plan, args.output), ensure_ascii=True, indent=2))
