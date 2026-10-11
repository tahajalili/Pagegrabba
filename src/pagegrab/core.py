"""Platform-independent pieces: image comparison, trimming, PDF building."""
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageStat


def distance(a, b):
    """Mean per-pixel difference (0-255) between two images, on small grayscale copies."""
    size = (160, 160)
    ia = Image.open(a).convert("L").resize(size)
    ib = Image.open(b).convert("L").resize(size)
    return ImageStat.Stat(ImageChops.difference(ia, ib)).mean[0]


def flatten(path):
    """Drop the alpha channel (screenshots carry one) so PDFs stay small and clean."""
    im = Image.open(path)
    if im.mode != "RGB":
        im.convert("RGB").save(path)


def content_bbox(path, threshold=25):
    """Bounding box of non-white content, or None for a blank page."""
    gray = ImageOps.invert(Image.open(path).convert("L"))
    return gray.point(lambda p: 255 if p > threshold else 0).getbbox()


def trim_all(paths, margin=20):
    """Crop every page to the SAME box: the union of all pages' content plus a margin.

    A shared box keeps page sizes identical, which looks right in a PDF viewer.
    """
    boxes = [b for b in (content_bbox(p) for p in paths) if b]
    if not boxes:
        return None
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[2] for b in boxes)
    bottom = max(b[3] for b in boxes)
    for p in paths:
        im = Image.open(p)
        box = (
            max(left - margin, 0),
            max(top - margin, 0),
            min(right + margin, im.width),
            min(bottom + margin, im.height),
        )
        im.crop(box).save(p)
    return box


def build_pdf(images, out_pdf, lang="eng", ocr=True):
    """Merge images into one PDF, then (optionally) run OCR so the text is selectable/searchable."""
    import img2pdf

    out_pdf = Path(out_pdf)
    raw = out_pdf.with_suffix(".raw.pdf")
    with open(raw, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in images]))
    if not ocr:
        raw.replace(out_pdf)
        return
    exe = shutil.which("ocrmypdf")
    if not exe:
        raw.replace(out_pdf)
        print("ocrmypdf not found - wrote a PDF WITHOUT OCR. Install it with `brew install ocrmypdf`.")
        return
    subprocess.run([exe, "-l", lang, "--skip-text", "--optimize", "1", str(raw), str(out_pdf)], check=True)
    raw.unlink()
