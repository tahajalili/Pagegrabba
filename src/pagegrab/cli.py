"""Command line interface: displays | pick | grab | run | pdf."""
import argparse
import sys
import time
from pathlib import Path

from . import NOTICE, __author__, __version__, core, macos


def parse_region(s):
    try:
        x, y, w, h = (int(v) for v in s.split(","))
    except ValueError:
        raise SystemExit("--region must look like x,y,w,h (four integers)")
    return x, y, w, h


def global_region(args):
    """Region is relative to --display's top-left corner (0 = already global coordinates)."""
    x, y, w, h = parse_region(args.region)
    if args.display:
        d = macos.get_display(args.display)
        return d.x + x, d.y + y, w, h
    return x, y, w, h


def cmd_displays(args):
    for d in macos.displays():
        print(f"#{d.index}  {d.w}x{d.h} at ({d.x},{d.y}){'  [main]' if d.is_main else ''}")


def cmd_pick(args):
    pts = []
    for label in ("TOP-LEFT", "BOTTOM-RIGHT"):
        print(f"Hover the mouse on the {label} corner of the area to capture...")
        for i in range(args.countdown, 0, -1):
            print(f"  {i}", end="\r", flush=True)
            time.sleep(1)
        pts.append(macos.mouse_pos())
        print(f"  got {pts[-1]}")
    (x1, y1), (x2, y2) = pts
    d = macos.display_at(x1, y1)
    print(f"\nUse:  --display {d.index} --region {x1 - d.x},{y1 - d.y},{x2 - x1},{y2 - y1}")


def cmd_grab(args):
    print(f"Capturing in {args.countdown}s - show the LAST page you want...")
    time.sleep(args.countdown)
    macos.screenshot(global_region(args), args.out)
    core.flatten(args.out)
    print(f"Saved stop image: {args.out}")


def cmd_run(args):
    print(NOTICE + "\n")
    region = global_region(args)
    stop = Path(args.stop_image) if args.stop_image else None
    if not stop and not args.max_pages:
        sys.exit("Give --stop-image and/or --max-pages so it knows when to stop.")
    if stop and not stop.exists():
        sys.exit(f"Stop image not found: {stop} (create it with `pagegrab grab`)")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting in {args.countdown}s - switch to the first page now (Ctrl+C to abort)...")
    time.sleep(args.countdown)

    images, prev, n = [], None, 0
    try:
        while True:
            n += 1
            path = out_dir / f"page_{n:04d}.png"
            macos.screenshot(region, path)
            core.flatten(path)
            print(f"captured {path.name}", flush=True)

            # Page may still be loading/animating: if it hasn't changed, wait and retry before giving up.
            tries = 0
            while prev is not None and core.distance(path, prev) < args.same_threshold and tries < args.retries:
                tries += 1
                time.sleep(args.delay)
                macos.screenshot(region, path)
                core.flatten(path)
            if prev is not None and core.distance(path, prev) < args.same_threshold:
                print("Page stopped changing - reached the end (or the key isn't reaching the app).")
                path.unlink()
                break
            images.append(path)

            if stop and core.distance(path, stop) < args.threshold:
                print("Reached the stop image.")
                break
            if args.max_pages and n >= args.max_pages:
                print("Hit --max-pages.")
                break

            prev = path
            macos.press_key(args.key, args.app)
            time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\nInterrupted - building a PDF from what was captured so far.")

    if not images:
        sys.exit("No pages captured.")
    if args.trim:
        print(f"Trimmed to {core.trim_all(images)}")
    print(f"Building {args.output} from {len(images)} pages (OCR {'off' if args.no_ocr else 'on'})...")
    core.build_pdf(images, args.output, args.lang, ocr=not args.no_ocr)
    print(f"Done: {args.output}")


def cmd_pdf(args):
    images = sorted(Path(args.out_dir).glob("page_*.png"))
    if not images:
        sys.exit(f"No page_*.png files in {args.out_dir}")
    if args.trim:
        core.trim_all(images)
    core.build_pdf(images, args.output, args.lang, ocr=not args.no_ocr)
    print(f"Done: {args.output}")


def add_region_args(p):
    p.add_argument("--region", required=True, help="x,y,w,h in screen points (relative to --display if given)")
    p.add_argument("--display", type=int, default=0, help="display number from `pagegrab displays`; 0 = global coordinates")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pagegrab", description=__doc__ + "\n\n" + NOTICE, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__} by {__author__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("displays", help="list displays and their positions").set_defaults(fn=cmd_displays)

    p = sub.add_parser("pick", help="print --display/--region from two mouse positions")
    p.add_argument("--countdown", type=int, default=5)
    p.set_defaults(fn=cmd_pick)

    g = sub.add_parser("grab", help="screenshot the region once (use it on the last page as the stop image)")
    add_region_args(g)
    g.add_argument("--out", default="stop.png")
    g.add_argument("--countdown", type=int, default=5)
    g.set_defaults(fn=cmd_grab)

    r = sub.add_parser("run", help="capture, press a key, repeat; then build a searchable PDF")
    add_region_args(r)
    r.add_argument("--stop-image", help="image from `pagegrab grab`; stops when a page matches it")
    r.add_argument("--max-pages", type=int, help="stop after N pages (alternative or safety cap)")
    r.add_argument("--key", default="right", help="key that advances the page (default: right)")
    r.add_argument("--delay", type=float, default=1.0, help="seconds to wait after each key press")
    r.add_argument("--retries", type=int, default=2, help="extra waits if the page looks unchanged before ending")
    r.add_argument("--threshold", type=float, default=2.0, help="stop-image match tolerance (lower = stricter)")
    r.add_argument("--same-threshold", type=float, default=0.3, help="below this, two shots count as the same page")
    r.add_argument("--app", help="app name to bring to the front before each key press")
    r.add_argument("--trim", action="store_true", help="crop white margins (same box for all pages)")
    r.add_argument("--out-dir", default="pages")
    r.add_argument("--output", default="capture.pdf")
    r.add_argument("--lang", default="eng", help="tesseract language code(s), e.g. eng or eng+fra")
    r.add_argument("--no-ocr", action="store_true")
    r.add_argument("--countdown", type=int, default=8)
    r.set_defaults(fn=cmd_run)

    q = sub.add_parser("pdf", help="rebuild the PDF from saved page_*.png files")
    q.add_argument("--out-dir", default="pages")
    q.add_argument("--output", default="capture.pdf")
    q.add_argument("--lang", default="eng")
    q.add_argument("--trim", action="store_true")
    q.add_argument("--no-ocr", action="store_true")
    q.set_defaults(fn=cmd_pdf)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
