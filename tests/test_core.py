import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PIL import Image, ImageDraw  # noqa: E402

from pagegrab import cli, core  # noqa: E402


def make_page(path, text="hello", size=(400, 300), box=(100, 100)):
    im = Image.new("RGBA", size, "white")
    ImageDraw.Draw(im).rectangle([box[0], box[1], box[0] + 80, box[1] + 40], fill="black")
    ImageDraw.Draw(im).text((box[0], box[1] + 60), text, fill="black")
    im.save(path)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_distance_same_and_different(self):
        a, b = self.dir / "a.png", self.dir / "b.png"
        make_page(a, box=(50, 50))
        make_page(b, box=(250, 200))
        self.assertEqual(core.distance(a, a), 0)
        self.assertGreater(core.distance(a, b), 0.3)

    def test_flatten_drops_alpha(self):
        a = self.dir / "a.png"
        make_page(a)
        core.flatten(a)
        self.assertEqual(Image.open(a).mode, "RGB")

    def test_trim_uses_same_box_for_all_pages(self):
        a, b = self.dir / "a.png", self.dir / "b.png"
        make_page(a, box=(50, 50))
        make_page(b, box=(250, 180))
        core.trim_all([a, b], margin=10)
        self.assertEqual(Image.open(a).size, Image.open(b).size)
        self.assertLess(Image.open(a).width, 400)

    def test_blank_pages_are_not_trimmed(self):
        a = self.dir / "a.png"
        Image.new("RGB", (100, 100), "white").save(a)
        self.assertIsNone(core.trim_all([a]))

    def test_build_pdf_without_ocr(self):
        pages = []
        for i in range(2):
            p = self.dir / f"page_{i}.png"
            make_page(p)
            core.flatten(p)
            pages.append(p)
        out = self.dir / "out.pdf"
        core.build_pdf(pages, out, ocr=False)
        self.assertTrue(out.read_bytes().startswith(b"%PDF"))

    def test_parse_region(self):
        self.assertEqual(cli.parse_region("1,2,3,4"), (1, 2, 3, 4))
        with self.assertRaises(SystemExit):
            cli.parse_region("1,2,3")


if __name__ == "__main__":
    unittest.main()
