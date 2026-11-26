"""Restore source pixels outside a reviewed, binary text-edit mask. No text rendering."""
import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


def read_image(path):
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGBA")


def restore(source, edit, mask):
    if source.size != edit.size or mask.size != source.size:
        raise ValueError("Align the edited image and mask to the upright source dimensions first")
    if mask.mode not in ("1", "L"):
        raise ValueError("Use a grayscale mask; white permits edits, black protects pixels")
    mask = mask.convert("L")
    counts = mask.histogram()
    if sum(counts[1:255]) or not counts[0] or not counts[255]:
        raise ValueError("Provide a binary mask with both protected and edited pixels")
    result = Image.composite(edit, source, mask)
    protected = ImageOps.invert(mask)
    for channel in ImageChops.difference(result, source).split():
        if ImageChops.multiply(channel, protected).getbbox():
            raise ValueError("Protected pixels differ")
    return result, counts[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "edit", "mask", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    if args.output.suffix.lower() != ".png":
        parser.error("Choose a fresh .png output")
    with Image.open(args.mask) as mask:
        result, count = restore(read_image(args.source), read_image(args.edit), mask)
    # Exclusive creation protects the input and any earlier delivery.
    with args.output.open("xb") as target:
        result.save(target, format="PNG")
    print(f"Protected pixels verified: {count}/{result.width * result.height}")


if __name__ == "__main__":
    main()
