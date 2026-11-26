"""Offline package and pixel-protection smoke check. Run from any working directory."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
required = ("SKILL.md", "references/layout-rules.md", "references/translation-rules.md",
            "references/product-fidelity.md", "references/quality-checklist.md",
            "references/portability.md", "package.json", "scripts/ocr.cjs",
            "scripts/protect_pixels.py")
for relative in required:
    if not (root / relative).is_file():
        sys.exit(f"Missing: {relative}")
for doc in [root / "SKILL.md", *(root / "references").glob("*.md")]:
    for link in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf8")):
        if "://" not in link and not (doc.parent / link).is_file():
            sys.exit(f"Broken reference in {doc.name}: {link}")
print("Package files and relative references: OK")
try:
    from PIL import Image
    from protect_pixels import restore
except ModuleNotFoundError as error:
    sys.exit(f"Pixel helper unavailable ({error}); install Pillow in this Python environment")
source = Image.new("RGBA", (3, 1), (1, 2, 3, 99))
edit = Image.new("RGBA", source.size, (5, 6, 7, 128))
mask = Image.new("L", source.size)
mask.putpixel((1, 0), 255)
output, protected = restore(source, edit, mask)
if protected != 2 or [output.getpixel((x, 0)) for x in range(3)] != [
        source.getpixel((0, 0)), edit.getpixel((1, 0)), source.getpixel((2, 0))]:
    sys.exit("Pixel helper failed the protection check")
print("RGB and alpha protection: OK. Check image_gen availability in the target Codex session.")
