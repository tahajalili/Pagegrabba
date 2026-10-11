# pagegrab

Capture a region of your screen, press a key to advance to the next page, and repeat until you reach
a page you chose. Then merge everything into one **searchable (OCR) PDF**.

Handy for turning your own slide decks, scanned-document viewers, lecture recordings played back in a
player, web documentation, or your own notes apps into a single searchable PDF.

> ## Disclaimer — please read
> - pagegrab only automates things you could do by hand: take screenshots and press a key.
>   It **does not** remove, bypass, or defeat any DRM, paywall, login, or other access control.
> - **You are solely responsible** for making sure you have the right to copy what you capture.
>   Only use it on content you own, created, or have explicit permission or a licence to copy
>   (including what copyright law allows where you live).
> - Respect the terms of service of any app or site you use it with. Many services forbid automated
>   copying; using this tool against such terms is your responsibility, not the authors'.
> - Do not redistribute captured copyrighted material.
> - The software is provided "as is" without warranty (see [LICENSE](LICENSE)). The authors are not
>   liable for how it is used.
> - Not affiliated with or endorsed by any application, publisher, or service.

## Requirements (macOS)

- Python 3.9+
- [`ocrmypdf`](https://ocrmypdf.readthedocs.io) for OCR: `brew install ocrmypdf` (without it you still get an image-only PDF)
- System Settings → Privacy & Security: grant your terminal **Screen Recording** (screenshots)
  and **Accessibility** (key presses). Without Screen Recording the screenshots are blank wallpaper.

```sh
pip install .          # from this folder; installs the `pagegrab` command
```

## Usage

Commands go in a normal shell (don't put a `!` in front of them in a plain terminal).

```sh
pagegrab displays                       # list monitors
pagegrab pick                           # hover top-left, then bottom-right; prints --display/--region

# On the LAST page you want, save its region as the stop image:
pagegrab grab --display 2 --region 540,138,1294,870 --out stop.png

# Go back to the FIRST page, then run (you get a countdown to switch to the app):
pagegrab run --display 2 --region 540,138,1294,870 \
    --stop-image stop.png --max-pages 300 --delay 1.5 --trim --output notes.pdf
```

| Option | Meaning |
| --- | --- |
| `--display N` | Region is relative to display N's top-left (see `pagegrab displays`). `0` = global coordinates. |
| `--stop-image` | Stop when a page matches this image. |
| `--max-pages` | Stop after N pages (alternative stop, or a safety cap). |
| `--key` | Key that advances the page: `right` (default), `left`, `down`, `up`, `space`, `pagedown`, `pageup`, `return`. |
| `--delay` | Seconds to wait after each key press (raise for slow-loading pages). |
| `--app NAME` | Bring this app to the front before each key press. |
| `--trim` | Crop white margins using one box for all pages. |
| `--lang` | OCR language, e.g. `eng`, `eng+fra`. |
| `--no-ocr` | Skip OCR. |

It also stops automatically if the page stops changing (end of document, or the key isn't reaching the app).
Ctrl+C builds the PDF from what was captured so far. Screenshots stay in `pages/`;
`pagegrab pdf` rebuilds the PDF without recapturing.

## Troubleshooting

- **Blank/wallpaper-only screenshots** → grant Screen Recording to your terminal, then restart it.
- **Page doesn't advance** → grant Accessibility; try `--app "Your App"` and a larger `--delay`.
- **Stops too early / never stops** → tune `--threshold` (lower = stricter match).

## Development

```sh
python -m unittest discover -s tests
```

## Author

Developed by Taha J.

## License

MIT — see [LICENSE](LICENSE).
